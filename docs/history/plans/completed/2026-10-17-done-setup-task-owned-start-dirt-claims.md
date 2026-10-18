# Plan: done setup claims the task's owned paths before classification

Backlog origin: docs/history/backlog/2026-10-16-done-setup-after-task-edits-foreign-staging-trap.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-done-setup-task-owned-start-dirt-claims-p550c6979-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-16-done-setup-after-task-edits-foreign-staging-trap.md (session sess_zcode-auth-20261017-2051)

## Terms

- done boundary: the `done` skill run (setup, learn, commit) opened at a work boundary; here the per-task or direct-work commit boundary.
- start-dirt: a path already recorded dirty or untracked when `done_run.sh setup` records the Step 0 baseline (the baseline reads untracked-inclusive status); unowned start-dirt is attributed to no claim set.
- owned-path claim: a `--owned-path <path>` setup argument that tells the run the boundary's own work already modified or created that path, so the commit stage's foreign-staging gate resolves it as owned.
- foreign-staging gate: the landing-sweep gate refusing a staged path recorded as start-dirt but not owned by the run.
- foreign-staging leg: the foreign-staging gate as it runs inside the commit stage's landing sweep; the plan uses the gate name except when naming that stage.
- direct work: implementation done outside an execute-plan task boundary (an interactive or ad-hoc session), the second witnessed occurrence class.
- verified changed paths: the full changed-path set the session's own work produced, read from untracked-inclusive status at boundary time: modified tracked paths, session-created untracked files, deleted tracked paths, and both sides of session renames; never assumed from memory.
- Files: list: the `Files:` section of the current execute-plan task, the per-task claim source Step 1.4 derives claims from.
- pins suite: the pinned literal spans and their enforcement suite in `scripts/check_maintenance_pins.sh`; a pin needle is one pinned literal span.

## Why

Twice witnessed (2026-10-16 execute-plan Task 1, 2026-10-17 direct implementation), a done boundary opened after authorized edits refused the session's own task files as unowned start-dirt, costing a lock release, a re-setup with claims, and a re-run per occurrence. The `--owned-path` mechanism exists and execute-plan Step 1.4 already derives its claims from the task's `Files:` list; the done skill's own setup guidance never tells direct work to derive and pass the current task's changed paths, so the input reaches the gate only after a refusal names it.

## Gist & Examples

TLDR: done's setup guidance gains the direct-work claims duty, deriving the current task's verified changed paths and passing each as a repeated `--owned-path` claim at setup and never the full dirty set, because twice witnessed a boundary opened after authorized edits refused the run's own files as unowned start-dirt and paid a recovery cycle per hit. Driving force: efficiency.

Before: a direct session edits nine task files, opens the done boundary, and stages those files; the foreign-staging gate refuses all nine as "start-dirt but not owned", the held lock is released, setup is re-run with the nine paths as claims, and the commit is re-issued. After: the same session derives the nine paths from `git status` at boundary time and passes them at setup, so the first commit lands; a peer's coexisting dirty path, never claimed, still refuses.

## Outcome

A done boundary opened after authorized direct work lands the task's own paths on the first setup, while unclaimed peer dirt keeps refusing.

- Direct work carries its task ownership into Step 0 as explicit claims, so the foreign-staging gate resolves the run's own paths as owned without a recovery cycle.
- The strict refusal class is unchanged: a staged path dirty at setup with no claim still refuses as start-dirt but not owned.
- The two claim sources (execute-plan `Files:` lists, direct-work verified changed paths) read as one contract.

Gate delta: none - no refusal class, gate, fence, protocol layer, or schema field is added or removed; the production-surface change is clarifying setup-claims guidance in done SKILL.md, priced by one discriminating regression test over the existing gate.

## Assumptions

- assume execute-plan Step 1.4 already carries the `Files:`-derived claims duty and needs no text change; basis: the section on disk reads "run `done_run.sh` setup with `--owned-path` naming every path in the current task's `Files:` list that the run has already modified (derived from `git status` in the run worktree at boundary time)", verified 2026-10-17.
- assume the foreign-staging gate keeps its strict refusal byte-identical; basis: the origin row's Suggested direction and the completed landing-guard plan's protective-value record (docs/history/plans/completed/2026-10-03-squash-landing-failure-path-guard.md).
- assume the origin row stays open through this plan's authoring landing, its covered flip an execution-time completion step; basis: the dispatch entry's acceptance keeps the origin open until implementation and a discriminating test show claimed task dirt landing while unclaimed peer dirt refuses.
- assume the existing presence pins over done SKILL.md span unrelated regions and tolerate insertion between them; basis: the pin needles in scripts/check_maintenance_pins.sh target other sections, and the suite runs green in Validation Commands.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the discriminating test shows a claimed dirty task path stage and commit while the same path unclaimed refuses, on the real gate.
- minimality: no new gate, refusal class, ledger, flag, or ceremony; the production-surface change is done SKILL.md guidance text only.
- readability: the inserted duty sits beside the setup syntax it governs and references execute-plan Step 1.4 by name instead of restating it.

**Done when:**
- done SKILL.md Step 0 carries the direct-work claims duty: derive the current task's verified changed paths from untracked-inclusive `git status` (modified, created, deleted, and renamed paths) and pass each as a repeated `--owned-path` claim at setup, never claim the full dirty set, and stage only claimed task paths at commit.
- the pins suite exits 0 and the done test suites run green under the venv pytest invocation.

**Ship when:**
- none; no deployed or human-owned condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/done/SKILL.md`

**Tests:**
- `scripts/test_done_run_wrapper.py` and `scripts/test_done_sweep_gates_lib.py` (the existing foreign-staging pins the plan's witness verification runs; the plan adds no new fixture)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py`; reason: the gate's refusal behavior is unchanged by design, and a behavior change there voids the plan's strict-gate assumption.
- `agents/skills/execute-plan/SKILL.md`; reason: Step 1.4 already carries its leg; the plan adds at most a by-name reference from the done side.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
```

### Task 1: Direct-work setup claims duty in done SKILL.md

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `done_run.sh` in `scripts/done_run.sh`

- [x] Step 0's setup guidance carries the direct-work claims duty: given a boundary opened after authorized direct edits, setup receives each task-verified changed path (modified, created, deleted, or renamed paths alike) as a repeated `--owned-path` claim derived from untracked-inclusive `git status` at boundary time, expects the commit stage's foreign-staging gate to resolve those paths as owned [class: IMPLEMENTATION_REQUIRED]
- [x] The duty forbids claiming the full dirty set: given peer dirt coexisting in the checkout, expects only explicitly claimed task paths staged, unclaimed paths left unstaged and refusing [class: IMPLEMENTATION_REQUIRED]
- [x] given the landed Step 0 duty text, expects a by-name reference to execute-plan Step 1.4's `Files:`-derived claims leg with no restatement of the derivation, so the one-contract read is greppable [class: IMPLEMENTATION_REQUIRED]
- [x] the direct-commit route paragraph's claim clause points at the Step 0 claims duty as the claim surface, so setup-time claims and commit-time staging read as one claim story [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the pins suite over the inserted text region (the placement pins and the rearm-on-touch pointer still present; the insertion sits between pinned spans) and the diff over agents/skills/done/SKILL.md adds guidance text only, no new flag, ledger, or ceremony, the Step 0 insertion's growth paid by the same-edit rewording of the direct-commit route paragraph's claim clause (replacement bytes, not pure addition) [class: REPOSITORY_TEST]
- [x] Commit: `docs: require explicit owned-path claims at direct-work done boundaries` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Discriminating witness verification over the existing foreign-staging pins

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/test_done_run_wrapper.py` (the wrapper setup-and-commit pair: a claimed start-dirty task file stages and commits; the same path unclaimed refuses with the commit count unchanged)
- `scripts/test_done_sweep_gates_lib.py` (the gate-level claimed and unclaimed pair)

Primary class anchors:
- `done_sweep_gates_lib.py` in `scripts/done_sweep_gates_lib.py`

- [x] Claimed arm witnessed: given the existing wrapper test that claims a start-dirty task file via `--owned-path` at setup, expects its run to stage and commit that file through the landing commit [class: REPOSITORY_TEST]
- [x] Unclaimed arm witnessed: given the existing wrapper test that stages the same start-dirty path with no claim, expects the commit stage's foreign-staging gate to refuse it as start-dirt but not owned with the commit count unchanged [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the venv pytest invocation over both suites runs the claimed and unclaimed pairs green; the gate behavior exists today and the plan changes guidance text, not gate behavior, so no RED leg exists, and this task records the discriminating witness the origin row's acceptance cites instead of duplicating existing coverage [class: REPOSITORY_TEST]
- [x] Record the witness: the test ids and outcomes from both suites land in the session run record, naming the claimed-passes/unclaimed-refuses pair the origin acceptance requires [class: REPOSITORY_TEST]
