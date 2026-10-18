# Plan: receipt-backed execute-plan archive transition and the run-filed-rows landing guarantee

Authoring claim: docs/tmp/authoring-claims/2026-10-10-execute-plan-done-terminal-gate-cycle.md (session automation-f1c15500-resume-20261015)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-10-execute-plan-done-terminal-gate-cycle.md
- docs/history/backlog/2026-10-10-execute-plan-run-filed-backlog-rows-stranded.md

Driving force: reliability

Plan review record: the staging series .ai-playbook/reviews/2026-10-15-plan-review-execute-plan-closeout-cycle-and-filed-records-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 2h total, largest task 1h

## Terms

- Pre-archive receipt: the `pre_archive_receipt` object the Phase 4 pre-archive stage writes into the run's gate-consumed session state file (`{tmp_dir}/execute-plan/<plan-slug>/runtime_state.json`, the file `gate_execute_plan_closeout` discovers and parses; a prompt-mediated run creates and maintains it during the run) before the archive commit is requested: the declared archive pathset (plan source path, archived destination, promoted origin dispositions, the run's filed-row paths), the plan digest at pre-archive, pointers to the Phase 2 validation and Phase 3 exit evidence, and a recorded-at timestamp.
- Bounded pre-archive arm: the new arm in `gate_execute_plan_closeout` that replaces the unconditional all-tasks-done refusal when the owned run's state carries a well-formed pre-archive receipt; it passes with a note naming the receipt and the declared archive destination.
- Declared archive transition: the one closeout whose declared set equals the receipt's declared pathset; the only all-tasks-done closeout the bounded arm permits. Set equality stays owned by the existing staged-scope guard the runner already feeds with the declared set; this plan adds no second comparator.
- Landed-archive verification: the extension of the gate's landed-complete verification (`_closeout_verify_landed_complete`): when the receipt records the archived destination and digest, the terminal boundary checks the archived path exists in the commit tree with bytes matching the recorded digest; the first unmet condition fails the gate with the resume remedy, per the arm's existing contract.
- Filed-row paths: the durable backlog rows the run filed during Phase 3, recorded in the receipt.
- Owned filed-row guarantee: a run-filed row lands in the run's own archive transition or carries a tracked landing path; the Phase 5 closeout reconciles the receipt's filed-row paths against `git status --short` and an untracked owned filing with neither disposition fails closeout.
- Review completeness check: the execution-review panel duty added to the execute-plan review composition: a run record claiming backlog filings while the tree leaves them uncommitted is a blocking finding, never pass-with-notes.
- Vendored twin: the runtime-side copy under `~/.agents/skills/` of each touched `agents/skills/` file, synced byte-equal in the same change per the repository guidelines' Vendored Asset Sync Rules.

## Why

The witnessed deadlock: Phase 4 requires the archive commit before the driver writes `terminal_receipt`, but the closeout gate refuses the archive commit exactly because all tasks are done and no receipt exists, and its only remedy re-enters Phase 4, which reaches the same refusal; the owned run has no supported path through its own archive commit (origin 1). The same incident's recovery landing stranded six durable backlog rows the run had filed, because the Phase 4 transition authorizes only pre-declared archive paths and no step owns the run's filings (origin 2). One receipt object written by the run before the archive request lets the existing gate admit exactly the declared transition while keeping every refusal class for runs without evidence, and recording the filed rows in the same receipt gives the closeout and the review panel the ownership surface they need without a new state system.

## Gist & Examples

TLDR: the execute-plan closeout gate gains a bounded pre-archive arm keyed to a receipt the run itself writes before the archive commit, the terminal boundary verifies the landed archive bytes against that receipt, and run-filed backlog rows become a closeout obligation with a review-completeness net and an AGENTS.md line; reliability, because the witnessed deadlock stopped an authorized run and its recovery stranded the run's own durable filings.

Before: an all-tasks-done run staging its declared archive and origin dispositions is refused by `execute-plan-closeout` (no `terminal_receipt`), the remedy re-enters Phase 4 into the same refusal, and the only escape edits machine state or suppresses the gate; a deadlocked run's recovery landing commits plan artifacts while its filed backlog rows stay untracked with no owner.

After: the run's Phase 4 pre-archive stage writes `pre_archive_receipt` (declared pathset, plan digest, Phase 2/3 evidence pointers); the gate's bounded arm passes that closeout with a note while a receipt-free all-tasks-done state keeps today's refusal byte-identical and a malformed receipt fails closed; the terminal boundary verifies the archived bytes against the recorded digest before `terminal_receipt` is written; Phase 5 fails closeout on an untracked owned filing that lacks a tracked landing path, and the execution-review panel reports blocking when a run record claims filings the tree does not carry.

Edge cases: a run paused between the last task and Phase 4 has no receipt and refuses exactly as today (the paused shape is deliberately unchanged); a receipt naming a narrower set than the boundary declares passes the gate but still refuses at the staged-scope guard, so set equality keeps its single owner; an aborted run stays out of scope; a run whose archived destination was later moved fails the landed-archive verification with the resume remedy instead of silently passing; filed rows carrying a recorded tracked landing path satisfy the guarantee without being committed by this run.

## Outcome

- An owned all-tasks-done run commits its declared archive and origin dispositions through the supported closeout route on the strength of its own pre-archive receipt, then reaches `terminal_receipt` after the landed-archive verification passes.
- Every receipt-free refusal keeps today's text and remedy; no new refusal class exists for runs without a receipt, and the bounded arm cannot widen past the run's own manifest-scoped state file.
- Run-filed backlog rows cannot reach `workflow_state: complete` uncommitted and untracked: the closeout reconciliation, the review completeness check, and the AGENTS.md line say the same contract at three owners.

Gate delta: no gate is added or removed; one existing promoted gate (`execute-plan-closeout`) gains a bounded pre-archive arm keyed to an in-run receipt and one verification condition in its landed-complete arm (admission line: incidents `docs/history/backlog/2026-10-10-execute-plan-done-terminal-gate-cycle.md` and `docs/history/backlog/2026-10-10-execute-plan-run-filed-backlog-rows-stranded.md`; expected catch frequency = every owned execute-plan archive transition, witnessed once as the deadlock; false-positive cost = zero new refusals, the arm fires only on a well-formed receipt and every receipt-free state keeps the byte-identical refusal; review by 2027-01-14 or after ten execute-plan archive transitions, whichever comes first).

## Review Scope

- scripts/done_sweep_gates_lib.py (`gate_execute_plan_closeout`, `_closeout_verify_landed_complete`, the owned-state payload handling)
- scripts/test_done_sweep_gates_lib.py, scripts/test_done_run_wrapper.py (the validation surfaces)
- agents/skills/execute-plan/SKILL.md (Phase 4 pre-archive and terminal stages, Phase 5 closeout) and its vendored twin
- agents/skills/review-agents/review-panel-selection.md (the execute-plan review composition) and its vendored twin
- AGENTS.md (the vendored-sync landing-path rule neighborhood)
- Out of review scope: every other sweep gate, the done skill text, the runtime state schema's other consumers, the foreign-staging and staged-scope guards (their contracts are consumed, not changed)

## Assumptions

- assume the receipt lives inside the run's existing `runtime_state.json`; basis: the gate already owns and parses that file, and a sidecar file would add a state surface the origins do not need (the runner's declared-set machinery already owns pathset equality).
- assume set equality between the boundary's declared set and the receipt's declared pathset stays with the existing staged-scope guard; basis: the guard already refuses declared-versus-staged mismatches at the same boundary, and a second comparator inside the closeout gate would duplicate its failure mode.
- assume the Phase 5 filed-row reconciliation and the terminal-stage verification are duty text in the execute-plan skill (the lifecycle is prompt-mediated with no executable driver), while their executable nets are the gate's landed-archive verification and the review completeness check; basis: the 2026-10-13 discharge of the sequential-trace entry records that no executable orchestration driver owns launch/result/checkpoint transitions.
- assume the AGENTS.md line lands beside the existing vendored-twin landing-path rule and stays one imperative line; basis: origin 2's best-practice arm names that rule as the model and demands wording consistent with it.
- assume the review completeness duty lands in `review-panel-selection.md` because it is the only review-agents surface naming the execute-plan composition; basis: repository search, 2026-10-15.
- assume the archive move itself keeps today's `git mv` mechanics and registry validation; basis: the origins' defect is the boundary ordering and the filings ownership, not the archive mechanics.

Decision points requiring a grill: none; the mechanism shape (the receipt inside the run's own state file, pathset equality delegated to the existing staged-scope guard, the executable nets at the gate's two arms and the review panel) is pinned by the origins' fix shapes and acceptance rows, and no operator decision is pending before review.

## Tasks

### Task 1: the bounded pre-archive arm and the landed-archive verification in the closeout gate
Files:
- scripts/done_sweep_gates_lib.py
- scripts/test_done_sweep_gates_lib.py
Primary class anchors: gate_execute_plan_closeout in scripts/done_sweep_gates_lib.py

- [x] [class: IMPLEMENTATION_REQUIRED] In `gate_execute_plan_closeout`'s all-tasks-done arm, before the unconditional refusal, inspect the owned payload for a well-formed `pre_archive_receipt` (the declared archive pathset non-empty, a string plan digest, evidence pointers, a recorded-at timestamp); a well-formed receipt routes to the new bounded arm, which passes with one note naming the receipt and the declared archive destination.
- [x] [class: IMPLEMENTATION_REQUIRED] A receipt that is present but malformed (missing keys, wrong types) fails the gate naming the offending field with the existing re-enter-Phase-4 remedy (`CLOSEOUT_RESUME_REMEDY` in scripts/done_sweep_gates_lib.py, which both consuming sites interpolate); a receipt-free all-tasks-done state keeps today's refusal text byte-identical (pin the existing text in the suite before the change).
- [x] [class: IMPLEMENTATION_REQUIRED] Extend `_closeout_verify_landed_complete`: when the receipt records the archived destination and digest, add the conditions that the destination path exists in the commit tree and its bytes hash to the recorded digest; the first unmet condition fails with that condition and the resume remedy, per the arm's existing first-unmet-condition contract; when the receipt records no destination the arm behaves exactly as today.
- [x] [class: REPOSITORY_TEST] Lib suite pins and cases: the byte-identical no-receipt refusal text captured verbatim; a well-formed receipt passes the all-tasks-done boundary with the note; a malformed receipt refuses naming the field; a landed-archive verification mismatch (destination absent, digest divergent) fails naming the condition.

### Task 2: the execute-plan skill's receipt duty, terminal verification, and filed-row reconciliation
Files:
- agents/skills/execute-plan/SKILL.md
Primary class anchors: the '## Phase 4: Archive Plan' and '## Phase 5: Remove session tmp files (success only)' sections in agents/skills/execute-plan/SKILL.md

- [x] [class: IMPLEMENTATION_REQUIRED] Phase 4, before the archive commit request: ensure the run's session state file `{tmp_dir}/execute-plan/<plan-slug>/runtime_state.json` exists in the shape the closeout gate consumes (`workflow_state`, `tasks`, the run's `plan_slug`); the adapter-backed runtime that previously owned the shape retired 2026-10-12, so the orchestrator parent owns creating and updating the file during the run.
- [x] [class: IMPLEMENTATION_REQUIRED] Write `pre_archive_receipt` into that state file: the declared archive pathset including the filed-row paths and promoted origin dispositions, the plan digest at pre-archive, Phase 2 and Phase 3 evidence pointers, and a recorded-at timestamp; the declared set handed to the closeout boundary is composed from the receipt's pathset.
- [x] [class: IMPLEMENTATION_REQUIRED] Terminal stage: before writing `terminal_receipt`, verify the archived destination exists and its bytes match the receipt digest, and record the archive commit sha into the receipt record; on a mismatch, stop before the receipt and name the resume remedy; mirror the gate's landed-archive verification wording so the two surfaces say one contract.
- [x] [class: IMPLEMENTATION_REQUIRED] Phase 5: reconcile the receipt's filed-row paths against `git status --short`; an untracked owned filing with no recorded tracked landing path fails the closeout; the tracked-landing-path record is the sanctioned alternative disposition.
- [x] [class: IMPLEMENTATION_REQUIRED] The Phase 4 refusal-remedy wording in the skill mirrors the gate's updated `CLOSEOUT_RESUME_REMEDY` constant (the bounded-transition arm beside the existing re-enter-Phase-4 remedy), so the skill text and the gate message name the same two remedies.
- [x] [class: REPOSITORY_TEST] Presence pins (fail before, pass after): the receipt key and the verification phrase appear in the skill and its vendored twin byte-equal (`diff` exits 0, the Validation Commands' pinned diff line for this file); `bash scripts/check_maintenance_pins.sh` failing set is byte-identical to a baseline captured green before the change.

### Task 3: the review completeness duty and the AGENTS.md landing-path line
Files:
- agents/skills/review-agents/review-panel-selection.md
- AGENTS.md
Primary class anchors: the '## Recommended five-worker panel' section in agents/skills/review-agents/review-panel-selection.md

- [x] [class: IMPLEMENTATION_REQUIRED] In the execute-plan review composition, add one completeness duty: a run record claiming backlog filings whose tree leaves them uncommitted and untracked is a blocking finding, never pass-with-notes; a recorded tracked landing path satisfies the check.
- [x] [class: IMPLEMENTATION_REQUIRED] In AGENTS.md beside the vendored-twin landing-path rule, add one imperative line generalizing it: a run that files durable records lands them in the same run or leaves a tracked landing path; never strand them as untracked residue.
- [x] [class: REPOSITORY_TEST] Presence pins for both surfaces and byte-equal vendored twins (`diff` exits 0 for each touched file under `agents/skills/`, the Validation Commands' pinned diff line for the catalog).

### Task 4: end-to-end regression and negative arms
Files:
- scripts/test_done_sweep_gates_lib.py
- scripts/test_done_run_wrapper.py
Primary class anchors: the execute-plan-closeout fixtures in scripts/test_done_sweep_gates_lib.py

- [x] [class: REPOSITORY_TEST] One gate-level end-to-end witness: all-tasks-done state plus a well-formed receipt passes the closeout at the archive-commit boundary; the follow-up boundary with the archived destination and matching digest passes landed-complete verification, and a divergent digest fails naming the condition (origin 1's acceptance sequence).
- [x] [class: REPOSITORY_TEST] Negative arms: no receipt refuses byte-identical; a malformed receipt fails closed naming the field; an aborted run stays out of scope; the paused mid-run shape (tasks not all done) keeps the pass-with-note guard.
- [x] [class: REPOSITORY_TEST] Validation: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_done_run_wrapper.py -q` exits 0.

## Evaluation Criteria

Done when: the lib and wrapper suites are green under the pinned PATH including the new receipt cases and the byte-identical refusal pin; the execute-plan skill, the review composition, and AGENTS.md carry their duty lines with byte-equal vendored twins; the pins suite failing set is unchanged from the captured green baseline.
Ship when: all tasks' validation lines pass on the landed tree.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_done_run_wrapper.py -q
bash scripts/check_maintenance_pins.sh
diff agents/skills/execute-plan/SKILL.md "$HOME/.agents/skills/execute-plan/SKILL.md"
diff agents/skills/review-agents/review-panel-selection.md "$HOME/.agents/skills/review-agents/review-panel-selection.md"
```

## Out of scope

- No change to any other sweep gate, the done skill text, the foreign-staging or staged-scope guard contracts, or the runtime state schema beyond the one additive receipt object.
- No new validator, ledger, gate, or receipt file format; no scheduler state changes; no execute-plan driver or harness (the lifecycle stays prompt-mediated per the conditional trace entry's recorded discharge).
- No archive-mechanics change (the `git mv`, registry row, and registry validation stay as landed).
- Mixed skill/vendored vintages are not handled beyond the same-change twin sync: a stale twin degrades to today's text and the execution phase records the symptom note.
