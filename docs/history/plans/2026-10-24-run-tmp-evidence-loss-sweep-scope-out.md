# Plan: Scope the Run-Tmp Session Sweep to Recognize Live No-Date Sessions
Backlog origin: docs/history/backlog/2026-10-19-run-tmp-evidence-loss-mid-run.md
Driving force: code-quality, efficiency
Plan review record: .ai-playbook/reviews/2026-10-24-plan-review-run-tmp-evidence-loss-sweep-scope-out-r*.md
Execution budget: 1.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-19-run-tmp-evidence-loss-mid-run.md (session eeeb11c6-d563-49b3-805a-d0238fedc586)

## Terms

- **Canonical session slug:** `<PLAN_SLUG>` per the execute-plan Step 0.4 session-slug rule: a date-prefixed plan file `YYYY-MM-DD-<name>.md` derives `<name>` (leading date and `.md` stripped).
- **Live session:** a `docs/tmp/execute-plan/<dir>/` directory belonging to a run whose plan is still pending (top-level or under a nested plans_dir scope, excluding the completed archive).
- **Pending-name set:** the set of directory names the sweep's live-session check compares `session.name` against.

## Why

The done sweep's `docs-tmp-sweep` gate deletes live runs' session directories. Witnessed 2026-10-18 (origin row): during an execution run, the run's session directory under `docs/tmp/execute-plan/` was emptied twice across done boundary steps — the recorded pins-suite baseline was gone by the Task 3 battery and the session manifest was gone after the next done commit.

Reproduced 2026-10-24 (canary pair across the per-task sweep battery in an authoring worktree, this plan's admission evidence): a session directory named by the no-date canonical slug with a canary file inside was reported `removed: ... (plan archived)` by the battery, while a control directory named by a pending plan's full dated stem was reported `kept: ... (active: plan still pending)`. The mechanism: `_sweep_execute_plan_sessions` (`scripts/done_sweep_gates_lib.py`) matches `session.name` against `pending_stems`, the set of **full plan-file stems** (date prefix included), while live sessions are named by the **no-date canonical session slug**. A live run's session name therefore never matches, so the sweep classifies it as a completed run's leftover and `rmtree`s it at every done sweep battery run — unless a fresh (≤48h) `closeout-baseline.json` exists in the directory, which is why only some runs lose evidence and the loss lands mid-run, after a run has written evidence but before its closeout baseline exists.

The loss contradicts the execute-plan anti-pattern row forbidding deletion of `{tmp_dir}/execute-plan/<PLAN_SLUG>/` before successful completion (tmp removal is Phase 5 only), and the sweep battery runs with exit 0 either way, so nothing flags the deletion.

## Gist & Examples

TLDR: Make the done sweep recognize live sessions named by the no-date canonical session slug so it stops deleting them mid-run, for code quality (a standing no-delete rule gains a matching behavior) and run efficiency (no more mid-run re-derivation from the base commit).

Before, a live run's session directory (named by the no-date slug, no closeout baseline yet) is deleted as "(plan archived)" by the next done sweep battery; evidence a later phase must consult (pins baselines, manifests, logs) silently disappears. After, the sweep's pending-name set contains both the full dated stem and the date-stripped canonical slug of every pending plan, so a live session by either name is kept as "(active: plan still pending)"; archived plans' session directories (dated or not) are still removed exactly as today, and the stale-baseline arm is unchanged.

For example, with pending plan `2026-10-18-plan-declared-missing-input-fallback.md`, both `2026-10-18-plan-declared-missing-input-fallback/` and `plan-declared-missing-input-fallback/` are kept while that plan is pending; once it archives to `completed/`, a `plan-declared-missing-input-fallback/` directory with no fresh closeout baseline is still removed as "(plan archived)".

Interim mitigation (recorded, never the fix): development lesson 106's durable-copy discipline — evidence a later phase must consult is kept outside the run's gitignored `docs/tmp/` scratch as well, and re-verified after any `done_run.sh` step.

## Outcome

The done sweep's session sweep keeps live sessions named by either the full dated stem or the no-date canonical session slug, and never removes a live run's session directory mid-run.

- A live session named by the canonical no-date slug is reported `kept (active: plan still pending)`, not removed.
- A session of an archived plan (either name form) is still removed by the existing arms; the stale-closeout-baseline arm is unchanged.
- The suite covering the sweep asserts both the keep and the still-removes behaviors.

Gate delta: a behavioral scope-out of one existing sweep arm's name matching; no new gate, no new refusal class, no pin change, no schema or writer change.

## Assumptions

- Assume the date-stripped name is the right keep-set extension (rather than patching the sweep to derive the slug per session), because the canonical session-slug rule is the shared producer/consumer convention and extending the comparison set is the smallest arm; basis: execute-plan Step 0.4 slug rule and the 2026-10-24 canary reproduction.
- Assume no migration is owed for existing directories, because the change only widens the keep set; wrongly-kept stale directories remain covered by the existing stale-baseline and archived-plan arms.

Decision points requiring a grill: maintenance-selected standing authorization selects extending the sweep's pending-name set with date-stripped stems over (a) giving execute-plan a registry of live sessions and (b) moving evidence duties into the boundary step; both alternatives add machinery the witnessed incident does not require, and the scope-out arm fixes the identified name-form mismatch directly; source: reproduction report and origin row; 2026-10-24; Assumptions and Task 1.

## Standing constraints

- Keep the change within the existing `_sweep_execute_plan_sessions` arm and its suite; no new gate, ledger, or enforcement surface. Until the byte-budget gate lands, treat operative-text growth without a deletion as a review-time finding under the existing finding-class documentation.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the keep decision recognizes both name forms of a pending plan's session; removals for archived plans and stale baselines are byte-behavior-identical.
- Testability: the suite exercises the no-date live keep, the dated live keep, the archived-plan removal, and the stale-baseline removal.
- Maintainability: one helper derives the pending-name set; no duplicated slug logic outside it.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q` passes with the new keep-set cases.
- `bash scripts/check_maintenance_pins.sh` passes (the docs-tmp-sweep gate pin unchanged).

**Ship when:**
- The next done sweep battery run reports a live no-date session as kept; no run loses session evidence mid-run.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/done_sweep_gates_lib.py` (`_sweep_execute_plan_sessions` only)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`

**Plan-related extension:** findings that directly complete the keep-set contract or its tests are in scope.

**Out of scope; reject unless plan-related:**
- `gate_docs_tmp_sweep`'s other arms (run-start marker pruning, plan-requirements cleanup, protected scratch); the witnessed incident is the execute-plan session sweep only.
- The execute-plan skill's Phase 5 cleanup and the anti-pattern table; both are correct as written.
- `closeout-baseline.json` grace semantics (`STALE_BASELINE_GRACE_H`).

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
bash scripts/check_maintenance_pins.sh
```

### Task 1: Extend the sweep's pending-name set with canonical no-date slugs

Context surface: the plan's Terms, Why, and Gist & Examples; `_sweep_execute_plan_sessions` in `scripts/done_sweep_gates_lib.py`.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

- [ ] Given pending plan files under `plans_dir` (recursive, completed archive excluded), expect the sweep's live-session check to compare `session.name` against a pending-name set containing each plan's full stem and, for date-prefixed plans, the date-stripped canonical slug; derive both forms in one helper. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a live session directory named by the no-date canonical slug of a pending plan with no `closeout-baseline.json`, expect the sweep to keep it and report `(active: plan still pending)`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a session directory of an archived plan (either name form) with no fresh closeout baseline, expect removal exactly as today; given a stale (past-grace) baseline, expect the stale-baseline removal unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add suite cases covering: no-date live keep, dated live keep, archived-plan removal (either name form), stale-baseline removal, and a no-date dir matching no pending plan still removed (the keep set must not widen into a universal keep). [class: REPOSITORY_TEST]
- [ ] Run the suite and the pins checker per Validation Commands and expect pass. [class: REPOSITORY_TEST]
- [ ] Commit: `done-sweep: keep live no-date sessions in the tmp sweep` [class: IMPLEMENTATION_REQUIRED]
