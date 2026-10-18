# Plan: Split the done landing-sweep gate roster by done boundary class

Backlog origin: docs/history/backlog/2026-10-16-worktree-done-boundary-primary-gate-block.md
Authoring claim: docs/tmp/authoring-claims/worktree-done-boundary-gate-roster-split.md (session sess_9f5841ba-7ce8-4463-80a1-895bb1e7dea4)
Driving force: reliability + simplicity; off-taxonomy justification: reliability is implemented because a per-task done boundary has no bounded response to live peer staging in the primary checkout, so one concurrent staging window stalls every parallel lane (the origin row's witnessed 2026-10-16 incident); park-triage would not take it because the stall re-bites on every concurrent-staging window and the fix removes a mismatched check rather than adding one
Plan review record: the staging series .ai-playbook/reviews/2026-10-16-plan-review-worktree-done-boundary-gate-roster-split-p7bd24974-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h

## Terms

- done boundary class: whether a done run's commit stage is a per-task boundary inside a live execute-plan run or the run's final closeout; the class this plan's discriminator declares.
- per-task boundary: a done commit inside a running execution whose worktree keeps living after the boundary; this covers the Step 1.4 done commit for one task and the Step 3.4 review-iteration done launch between review rounds, both mid-run.
- final closeout: the done boundary that ends a run and owns the landing critical section under the merge landing lock.
- landing sweep: the one `done_sweep_gates.sh landing` invocation over the staged set inside the done commit ladder.
- repo-keyed gate: a landing-roster gate whose refusal depends on primary state this run does not own (the primary checkout's index, the primary reviews home, repo-keyed registries), beyond the run's own manifest, markers, and declared claims.
- run-checkout-scoped gate: a landing-roster gate whose check reads only the invoking checkout.
- docs-publication leg: the docs-branch sync stage of the commit ladder, which publishes review docs to the repository-keyed docs ref.
- review-artifact migration: the commit-ladder stage that copies the run's gitignored review staging docs and session logs from the run worktree to the primary reviews home; a deliverable transfer, not a publication, and unchanged at every boundary.

## Why

A per-task done boundary executing in an ad-hoc worktree currently runs the full landing roster, including the gate that inspects the primary checkout's index. When a live peer session holds staged files there, the boundary refuses with no bounded response: a retry cannot change the state, the operator escape excludes peer-live dirt, and the run must not touch peer staging. The primary-checkout inspection protects landings, and landings happen at final closeouts, so the inspection belongs there and per-task boundaries should run only the checks scoped to their own checkout.

## Gist & Examples

TLDR: the done landing sweep's gate roster splits by declared done boundary class, so a per-task boundary stops refusing on live peer staging in the primary checkout while the final closeout keeps the full roster and the docs-publication leg, naming reliability and simplicity.

Before: a per-task done commit in a run worktree refuses when any live peer session holds staged files in the primary checkout (witnessed 2026-10-16: an execution run's Task 1 boundary stayed blocked for a full peer authoring cycle; evidence in the origin row).

After: a per-task boundary runs the landing roster minus the primary-checkout inspection and completes; the primary-checkout inspection and the docs-publication leg run only at the final closeout, which owns the landing under the merge lock, while the review-artifact migration keeps its position at every boundary.

Edge cases: the class is declared by the invoking boundary, never inferred from checkout shape, so a final closeout that runs inside a worktree still gets the full roster; an unset class reads as final-closeout, so every existing invocation keeps today's behavior byte-identically; a per-task run prints one trace line naming the deferred leg so the skip stays visible in the run record.

## Outcome

Per-task done boundaries complete under concurrent peer staging while the landing boundary keeps its full protection.

- A per-task done commit in an ad-hoc worktree passes while peers hold staged files in the primary checkout.
- The final closeout still refuses on foreign staged entries in the primary checkout; the invariant is unchanged and fixture-pinned in both directions, and the per-task boundary keeps every run-checkout-scoped check including the warning-posture set.
- The narrowing is admitted in the guard liveness ledger with its incident, unchanged final-closeout catch frequency, false-positive cost, and sunset review recorded.

Gate delta: net machinery narrows, nothing is added: the post-landing-staging refusal class is removed at per-task boundaries (unchanged at final closeout) and the docs-branch sync skips per-task boundaries while the review-artifact migration keeps its position; one new declared input (the boundary-class flag, spelled --boundary-class on both the runner and the sweep lib) and one trace line are added; removals priced by the origin row's completed-integrity-failure witness (the live 2026-10-16 stall), with the ledger's measured ratio at authoring time: post-landing-staging catches=3, incidents=8 (scripts/gate_liveness_ledger.json, `show`); no gate or fence is added and no refusal class is added.

## Assumptions

- assume the origin row's gate names map to machinery as: "staged-scope guard" is the staged-scope check family, the runner's staged-scope-guard ladder stage and its `foreign-staging` sweep re-run over the final staged set; "hygiene" is the `sensitive-data-scan` sweep gate; "dirt regression" and "lesson-scope" name done_run.sh ladder stages that already run at every boundary and are unchanged by this plan; "learn" is done Step 1, unchanged; basis: the commit-ladder description in agents/skills/done/SKILL.md Step 3 and the `LANDING_GATES` registry in scripts/done_sweep_gates_lib.py.
- assume the discriminator is explicit and declared by the invoking boundary (a flag on the commit subcommand, forwarded to the sweep lib), never inferred from checkout shape; basis: final closeouts also run inside worktrees since the worktree-complete landing lifecycle, so checkout shape cannot distinguish the classes, and the origin row names boundary class, not placement, as the discriminator.
- assume the per-task skip covers the docs-branch sync only; the review-artifact migration keeps its position at every boundary because it is the deliverable transfer that keeps the done skill's owned-review availability check satisfiable and a dead worktree from holding owned review records; basis: the origin row's Expected section names only the docs-branch publication, and the done skill's explicit-sync-deferral duty requires the migration that fills the primary reviews home to run before a commit when claimed review records are still worktree-local.
- assume the per-task roster is exactly `LANDING_GATES` minus `post-landing-staging`; basis: the plan review verified `gate_post_landing_staging` is the only landing-roster gate whose check reads the primary checkout, so the subtraction preserves every run-checkout-scoped check at the per-task boundary, which supersedes the origin row's shorter named subset in the safer direction; the origin row's "dirt regression" and "lesson-scope" names map to the runner's own ladder stages and the learn step, which already run at every boundary and are unchanged ("hygiene" maps per the first assumption).
- assume the per-task boundary keeps the existing warning-posture behavior of the gates it retains; basis: the roster's warning set is orthogonal to this split.
Decision points requiring a grill: none remain; the origin row records the operator direction and the entry records the rejected alternatives (removal outright, escape reliance, acknowledgment channel), so the design space is pinned.

## Standing constraints

- Validators and test suites run with `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH"` prefixed.
- No em-dash in committed files; run scripts/fix_plan_em_dashes.py over changed plan-adjacent docs before commit.
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0 before every commit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the declared class changes exactly the roster membership and the docs-publication leg, and nothing else; final-closeout behavior stays byte-identical (fixture-pinned both directions).
- simplicity: one roster split constant, one flag, one trace line; no new gate, no new state field, no second sweep invocation.
- maintainability: the split's classification rule (repo-keyed versus run-checkout-scoped) is documented beside the roster constant; the skills reference the runner's usage text instead of restating the roster.

**Done when:**
- the per-task fixture passes a landing with a foreign staged entry present in the primary checkout, and the final-closeout fixture refuses the same state;
- the sweep-gates lib suite, the runner wrapper suite, the pins suite, and the hygiene scan all exit 0.

**Ship when:**
- none stated.

## Review Scope

**Explicit must-fix:** findings on the files below are always in scope.

**Production code:**
- `scripts/done_sweep_gates_lib.py` *(modified: boundary-class argument, per-task roster, admission docstring)*
- `scripts/done_sweep_gates.sh` *(modified: usage text for the forwarded argument)*
- `scripts/done_run.sh` *(modified: `--boundary-class` flag, class forwarding, per-task docs-branch sync skip)*
- `agents/skills/done/SKILL.md` *(modified: one reference sentence in the commit-ladder text)*
- `agents/skills/execute-plan/SKILL.md` *(modified: one reference sentence in Step 1.4 and one in the Step 3.4 launch text)*
- `agents/skills/execute-plan/subagent-prompts.md` *(modified: the Done (per review iteration) template names the boundary class by reference)*
- `scripts/gate_liveness_ledger.json` *(modified: narrowing row recorded at first landing)*

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` *(modified: per-task and final-closeout fixtures)*
- `scripts/test_done_run_wrapper.py` *(modified: skip and keep fixtures for the docs-publication leg)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the gate helper implementations behind the roster ids other than the split itself; reason: this plan changes which gates run where, not how any gate decides.
- the automation primitives, the launchd machinery, and the scheduler state file; reason: unrelated surface.
- new backlog rows beyond the ledger narrowing record; reason: the admission fields live in the ledger row and the lib docstring per the entry's orientation.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/test_done_sweep_gates_lib.py
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/test_done_run_wrapper.py
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/test_done_sweep_gates_wrapper.py
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Boundary-class discriminator and per-task roster in the sweep lib

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_sweep_gates_lib.py` *(modified)*
- `scripts/done_sweep_gates.sh` *(modified)*
- `scripts/test_done_sweep_gates_lib.py` *(modified)*


Primary class anchors:
- `LANDING_GATES` in `scripts/done_sweep_gates_lib.py`
- `run_phase` in `scripts/done_sweep_gates_lib.py`
- `gate_post_landing_staging` in `scripts/done_sweep_gates_lib.py`

- [ ] `run_phase` accepts the declared boundary class for the landing phase through a `--boundary-class per-task|final-closeout` argument on the lib invocation (default final-closeout), forwarded by the wrapper with the same flag name on both surfaces; given the per-task class, expects the phase to run exactly `LANDING_GATES` minus `post-landing-staging` inside the existing landing phase, not a new phase; [class: IMPLEMENTATION_REQUIRED]
- [ ] the warning-posture set applies unchanged to the per-task roster, and an invalid class value is the usage-error tool error (exit 3), never a silent default; [class: IMPLEMENTATION_REQUIRED]
- [ ] Roster composition witness: given the per-task class with the gate registry stubbed, expects the executed gate set to equal `LANDING_GATES` minus `post-landing-staging` exactly, and the same stubbed context under the final-closeout class to execute the full `LANDING_GATES` set; [class: REPOSITORY_TEST]
- [ ] Warning-posture witness: given the per-task class with a warning-class gate stubbed to breach, expects the phase to exit 0 carrying that gate's warning-posture line, proving the per-task roster keeps the warning set; [class: REPOSITORY_TEST]
- [ ] the per-task roster is a named constant derived from `LANDING_GATES` by documented subtraction of `post-landing-staging` alone, with the docstring recording the subtraction basis (`gate_post_landing_staging` is the only landing-roster gate whose check reads the primary checkout, verified at authoring); [class: IMPLEMENTATION_REQUIRED]
- [ ] the module docstring carries the machinery admission fields for the narrowed `gate_post_landing_staging` reach: incident (the origin row), catch frequency unchanged at final closeout, false-positive cost (a per-task boundary forfeits early warning of primary residue), sunset (review at first misuse or beside the placement-awareness lineage), and the rule that a gate whose check later grows repo-keyed reach re-enters the final-closeout-only class; [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness pass arm: given the per-task class with a foreign staged entry fabricated inside the fixture repo only (git add in the fixture, no resolvable run manifest, never the real primary index), expects the landing phase to pass on the scoped roster; [class: REPOSITORY_TEST]
- [ ] Safety witness refuse arm: the same fabricated context under the final-closeout class refuses with today's message shape, the fixture pinning `DONE_LOCK_SCRIPT` to the repo-local done-lock.sh and `MERGE_LOCK_ROOT` to a temp root so the refusal arm is consulted, not the indeterminate arm; [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the per-task fixture fails (today every landing invocation runs the full roster, so the fabricated primary residue refuses) and the invalid-class fixture fails (today the lib silently ignores trailing phase arguments, so an invalid class rides the full roster and never exits 3) while the final-closeout fixture passes today; [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on all three fixtures and the existing suite [class: REPOSITORY_TEST]
- [ ] Commit: `check: split the done landing sweep roster by boundary class` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Runner plumbing and the two skill boundary texts

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_run.sh` *(modified)*
- `agents/skills/execute-plan/SKILL.md` *(modified)*
- `agents/skills/execute-plan/subagent-prompts.md` *(modified)*
- `agents/skills/done/SKILL.md` *(modified)*
- `scripts/test_done_run_wrapper.py` *(modified)*

Primary class anchors:
- `main` in `scripts/done_run.sh`
- `cmd_commit` in `scripts/done_run.sh`

- [ ] `cmd_commit` accepts `--boundary-class per-task|final-closeout` (default final-closeout), documents the flag and the class split in the runner's usage header, and forwards the class to the sweep invocation under the same flag name, forwarding the value verbatim without re-validating it: the sweep lib is the single validation surface for the class vocabulary; [class: IMPLEMENTATION_REQUIRED]
- [ ] at a per-task boundary the runner skips the docs-branch sync stage while the review-artifact migration keeps its existing position, printing one trace line naming the skipped leg; given a per-task commit in a worktree, expects the sync skipped, the migration run, and the trace line present, observing the migration through its stdout line or the worktree-migrate-manifest file it writes (that stage carries no trace line); [class: IMPLEMENTATION_REQUIRED]
- [ ] the execute-plan Step 1.4 boundary text and the Step 3.4 review-iteration launch text instruct the mid-run done run to pass `--boundary-class per-task`, by reference to the runner's usage text as the canonical split, in at most two sentences each; [class: IMPLEMENTATION_REQUIRED]
- [ ] the Done (per review iteration) template in agents/skills/execute-plan/subagent-prompts.md carries the same by-reference class instruction in its workflow sentence, so a template-launched review-iteration done declares the per-task class; [class: IMPLEMENTATION_REQUIRED]
- [ ] the done SKILL.md Step 2/3 commit-ladder text names the boundary-class split by reference in at most two sentences, with no roster restatement; the explicit-sync-deferral duty's availability check stays intact (the migration still fills the primary reviews home at every boundary, so claimed review records reach it before the commit); [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given an unset class, expects the runner's composed stages to match today's behavior exactly (the default is final-closeout, so existing invocations keep their roster and the sync); [class: REPOSITORY_TEST]
- [ ] Run → expect RED on the skip fixture, then GREEN after the plumbing; [class: REPOSITORY_TEST]
- [ ] Commit: `check: declare the done boundary class on the commit run` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Ledger narrowing row and the validation battery

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/gate_liveness_ledger.json` *(modified)*

- [ ] `record` in `scripts/gate_liveness_ledger.py` appends the narrowing row under the ledger guard key `post-landing-staging` (the entry the Gate delta's ratio cites; not the legacy `post-landing-staging-gate` key) at this plan's first landing: kind override, evidence the origin row path; [class: IMPLEMENTATION_REQUIRED]
- [ ] the narrowing row's note carries the four admission fields: incident witnessed 2026-10-16, final-closeout catch frequency unchanged, per-task false-positive cost accepted, sunset review at first misuse or beside the placement-awareness lineage; [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the full validation battery from `## Validation Commands` and expect every command green; [class: REPOSITORY_TEST]
- [ ] Commit: `check: record the post-landing-staging per-task narrowing in the liveness ledger` [class: IMPLEMENTATION_REQUIRED]
