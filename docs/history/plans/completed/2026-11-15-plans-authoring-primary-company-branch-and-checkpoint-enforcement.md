# Plan: Observable authoring placement duties under company primary placement

Backlog origins (scope of record):
- docs/history/backlog/2026-11-15-plans-authoring-company-primary-branch-choice-and-checkpoint-gap.md
- docs/history/backlog/2026-11-15-plans-run-skipped-branch-choice-and-checkpoint-invocation.md

Driving force: reliability (primary), clarity (secondary)
Force justification: reliability is not a taxonomy principle; it is implemented anyway because the witnessed cost is lost evidence (a plan untracked through certification, an unbindable seal, one wasted review round) on the authoring lane, and the fix is bounded text edits plus two message-only observation surfaces, not a redesign. Clarity is not a taxonomy principle; it is implemented anyway because the incident's second half was a silent rule conflict the agent resolved invisibly (origin row 2) and a policy paragraph that was never loaded, and the fix is one authorization line plus one required-read pointer.
Plan review record: the staging series .ai-playbook/reviews/2026-11-15-plan-review-plans-authoring-primary-company-branch-and-checkpoint-enforcement-r*.md (the highest rN for this source-plan path is authoritative)
Execution budget: 2.5h total, largest task 1h
Executed: yes (b5ccd534f00211531ddf35062303d29e711a1e61)
Authoring claim: plans-authoring-primary-company-branch-and-checkpoint-enforcement.md (session sess_747bbdcc-88c4-4ba2-af11-8f2e1f21cbb7)

## Terms

- primary placement: a project whose facts declare `worktree_policy = "primary"`; every lane of that project runs in the primary checkout, no run worktree is created.
- company profile: a project whose facts declare `project_type = "company"`.
- branch choice: the per-run operator choice the worktree-first policy paragraph gives a company-profile primary-placement run: keep the current branch, or create a named task branch from the current HEAD.
- round-start anchor: the `wip:` checkpoint commit verified before the first review round; its bytes hash to the recorded `round_start_digest`.
- warning-only probe: a check that prints evidence lines and never changes an exit code, adds no schema field, and prints nothing on failure paths.
- shared check surface: the both-gate-paths function pattern `plan_files_coverage_warnings` established in `scripts/plan_readiness.py`.
- delta classifier: `scripts/plan_delta_classifier.py`, which classifies plan-file deltas per hunk against a `--since` baseline commit.
- absent-baseline refusal: the classifier's refusal when the delta has no before side (the plan path is not tracked at `--since` and no checkpoint commit adds it).
- machinery registry: `scripts/machinery_registry.json`, validated by `scripts/machinery_inventory.py --check`.
- byte-budget gate: `scripts/skill_text_budget.py --check`, blocking posture over skill-file caps.
- round-close seal: the certification record `.ai-playbook/review-certs/<artifact-slug>.md` the review loop writes when a round closes clean.
- router dispatch bullet: one entry of the plans skill's Module dispatch list in `agents/skills/plans/SKILL.md`; "required read" means the named module loads on dispatch.
- hygiene scan: `scan-public-hygiene.sh` from the user facts document, the pre-commit public-hygiene gate (exit 0 required).

## Why

An interactive plans authoring run in a company-profile project declaring primary placement ran on the base branch, never offered the branch choice, and never made the `wip:` checkpoint commits, so the plan stayed untracked through two review rounds and certification. Measured costs, re-derived 2026-11-15 in this repository's worktree placement (probes over an untracked plan copy under `docs/history/plans/`):

- `plan_readiness.py --pre-round` exited 0 (`OUTCOME: pass`) on the fully untracked plan; the full mode passed the same way in the witnessed run (origin row 1's reproduction evidence), so both gate modes are blind to the untracked state.
- `plan_delta_classifier.py --plan <untracked> --since HEAD` refused with the generic absent-baseline text; no distinct reason names the skipped authoring checkpoint duty, so every fold fell back to the unclassified fresh-review path and a cosmetic fold forced a whole extra review round (about 13 minutes of reviewer time in the witnessed run).
- The round-close seal had no commit to bind to (both staging validators degraded to the exact-match digest rule).
- The host runtime's commit default and the plans checkpoint duty pointed in opposite directions with no user-level line resolving the conflict, so the agent silently chose "do not commit" (origin row 2).

Existing coverage is the sibling certification-time row (checkpoint duties at the round-close turn only, carried by an exec-log entry); neither Phase 0 nor the pre-first-round boundary is observed today.

## Gist & Examples

TLDR: the authoring lane under company primary placement gains a named branch-choice step, a visible checkpoint duty, and two observation surfaces, so a skipped duty is reported instead of silently losing the plan's evidence (driving force: reliability).

Before: a primary-placement authoring run skips the checkpoint duty; both readiness modes pass with the plan untracked; the classifier cannot name the cause; the seal cannot bind; nobody is told.

After: Phase 0 renders the branch choice as a named step before the first plan write (ask once, or record the applied default with the evidence that no directive existed); the checkpoint duty has its own announce line and a pre-first-round anchor step; the readiness probe warns in both modes on an untracked plan or a missing round-start anchor; the classifier emits a distinct "plan has no start commit" reason; the hard rules carry the checkpoint-commit authorization line so the duty and the host default no longer conflict silently.

Edge cases: an unattended company run with no directive records the keep-current-branch default instead of asking (the policy paragraph's own default); conversational-draft plans that never reach the gate never trigger the probe (warning-only, no refusal); a personal or pet profile primary-placement run is unchanged (base-branch-only rule, no choice exists); the classifier's indeterminate and tool-error outcomes are never relabeled as the no-start-commit reason.

## Outcome

Company-profile primary-placement authoring runs become deliberate and observable: the branch choice and the checkpoint duty are named steps, and a skipped duty is reported instead of silently costing evidence.

- The readiness probe warns on an untracked plan and on a missing round-start anchor in both gate modes; exit codes stay unchanged.
- The delta classifier names the missing start commit distinctly on the probed shape, keeping the generic absent-baseline text on the ordinary shape.
- Phase 0 carries the branch-choice step (ask once, or record the applied default with no-directive evidence) and the visible checkpoint-duty announce line.
- The hard rules carry the operator-confirmed checkpoint-commit authorization line, so the duty and the host commit default no longer conflict silently.
- Gate delta: net machinery added is one warning-only probe on both readiness gate paths plus its one machinery-registry row, and a message-only classifier refusal-text growth (no refusal class, exit, or routing change).

## Design Invariants

- Warning-only: the new readiness probe never changes an exit code, adds no schema field, refuses nothing, and prints zero lines on every failure path (the `plan_files_coverage_warnings` contract).
- Single-homing: no policy paragraph text moves or is copied; Phase 0 points at the single policy home in `agents/skills/execute-plan/worktree-first.md`.
- Message-only classifier change: exit codes, routing (fresh-review path, no corrections row, no operator acknowledgement), and outcome vocabulary are unchanged.
- Branch-agnostic and push-agnostic plan: nothing here instructs execution to stay on a branch, names a branch for execution, or authorizes pushes.
- Personal and pet primary-placement behavior is unchanged (the base-branch-only rule stands; no branch choice exists for those profiles).
- The machinery admission is warning-only posture with pre-registered review; no new refusal path anywhere.

## Tasks

### Task 1: Phase 0 named branch-choice step and visible checkpoint duty

Files:
- agents/skills/plans/phase-0-placement.md
- agents/skills/plans/SKILL.md

Steps:
1. In `phase-0-placement.md`, insert a named step between Step 0.1 and the existing Step 0.2 (renumber the existing Step 0.2 heading to 0.3, and sweep the heading's in-file references in the same edit: the already-provisioned recognition arm's "per Step 0.2" reference moves to Step 0.3 beside the heading itself): the step applies only to a company-profile primary-placement authoring run, and orders, before the first plan write, either asking the operator once (keep the current branch, or a named task branch from the current HEAD) or, for an unattended run with no directive, recording the applied keep-current-branch default with the evidence that no operator directive existed; the step points at the single policy home (the Project worktree policy paragraph in `agents/skills/execute-plan/worktree-first.md`) without copying its text, and records the chosen or defaulted branch where the authoring run records placement.
2. Render the authoring checkpoint duty as a visible Phase 0 step with its own announce line ("I'll checkpoint the plan file under the `wip:` marker at every authored plan write and verify the round-start anchor commit before the first review round."), and add the pre-first-round anchor verification to that step's body (the duty paragraph's existing round-start-anchor sentences are the content; the step references the D-10 paragraph rather than duplicating its mechanics).
3. In `plans/SKILL.md`, extend the router's Authoring placement setup (Phase 0) dispatch bullet with one clause naming the Project worktree policy paragraph as a required read when the project's facts declare a company profile (origin row 2's outcome sought; the pointer, not the text).
4. Pay for the growth in the same change: compress redundant sentences in `phase-0-placement.md`'s Authoring-run continuation ownership and Authoring ownership marker paragraphs without changing any rule, so `scripts/skill_text_budget.py --check` stays at zero blocking breaches.

Acceptance:
- [x] The branch-choice step appears in `phase-0-placement.md` before the first-plan-write boundary, names both arms (ask once; record applied default with no-directive evidence), and points at `agents/skills/execute-plan/worktree-first.md` without quoting the policy paragraph's task-branch sentences. [class: REPOSITORY_TEST]
- [x] The checkpoint-duty step carries its own announce line and the pre-first-round anchor verification is reachable from Phase 0's step list. [class: REPOSITORY_TEST]
- [x] The router Phase 0 dispatch bullet names the required read for company-profile facts. [class: REPOSITORY_TEST]
- [x] Run: expect GREEN: `python3 scripts/skill_text_budget.py --check` exits 0 with zero blocking breaches. [class: REPOSITORY_TEST]
- [x] Run: expect GREEN: `grep -cE "keeps? the current branch by default" agents/skills/plans/phase-0-placement.md` prints 0 (no copied policy text; the needle matches both moods of the policy default sentence). [class: REPOSITORY_TEST]
- [x] Run: expect GREEN: `python3 scripts/plan_readiness.py --pre-round <this plan>` exits 0. [class: REPOSITORY_TEST]


### Task 2: Warning-only readiness probe and distinct classifier reason

Files:
- scripts/plan_readiness.py
- scripts/plan_delta_classifier.py
- scripts/test_plan_readiness.py
- scripts/test_plan_delta_classifier.py
- scripts/machinery_registry.json

Steps:
1. In `plan_readiness.py`, add a warning-only probe function on the `plan_files_coverage_warnings` pattern (the shared check surface both gate paths call): given the plan path and repo root, both arms consult git keyed to the PASSED repo root (never the process cwd, the classifier precedent of resolving plumbing from the operand). Arm 1 (untracked): `git ls-files` run against the passed root misses the plan path; the line names the untracked state and the `wip:` checkpoint duty. Arm 2 (missing round-start anchor): the plan file is tracked AND no `wip:`-prefixed commit touches the plan path through HEAD (the checkpoint duty's own commit marker, keyed by subject prefix per the Authoring checkpoint duty convention), naming the missing anchor; the arm is silent when a `wip:` commit exists and silent when the plan path's newest touching commit's subject starts with `execute-plan: land ` (the landed state: the squash absorbed the checkpoint history, so execution-time full-gate runs never see the warning). Arm 2 is skipped entirely when arm 1 fired (an untracked plan has no commit history to inspect). Call the probe from the pre-round gate after all probes pass (mirroring the Files-coverage precedent's stderr position) and from the full gate's pass path before its summary lines. The probe never changes an exit code, adds no schema field, and prints nothing on failure paths.
2. Register the probe in `scripts/machinery_registry.json` as a `script:` row with disposition keep and warning-only posture, carrying the machinery admission fields from the dispatch entry: incident = the witnessed run recorded in the first origin row's reproduction evidence (untracked plan through certification, classifier unusable, seal unbindable); expected catch frequency = every primary-placement authoring run that skips the checkpoint duty (witnessed once, same duty class in the sibling row); false-positive cost = low (warning-only, no refusal, conversational drafts never reach the gate); review date 2027-02-15.
3. In `plan_delta_classifier.py`, give the FIRST-CHECKPOINT-ABSENT shape (no commit adds the plan path anywhere through HEAD) a distinct refusal reason naming that the plan has no start commit and the authoring checkpoint duty produced no `wip:` commit, distinct from the generic absent-baseline wording; message-only: the refusal's class (unclassified), routing, and exit behavior are unchanged, and the indeterminate and tool-error outcomes keep their existing texts. Update the stale module-docstring sentence that says the shape "emits the named absent-baseline refusal" so the docstring names the distinct reason for the no-commit-anywhere shape.
4. Tests: pin each behavior with its own canary. In `test_plan_readiness.py`: arm 1 prints the untracked warning for an untracked plan path and is silent for a tracked one; arm 2 warns for a tracked plan whose history carries no `wip:`-prefixed touching commit (newest touching commit not landing-shaped), stays silent with one `wip:` commit present, and stays silent when the newest touching commit's subject starts with `execute-plan: land `; all in both the pre-round and full-mode call sites, with exit codes asserted unchanged; in `test_plan_delta_classifier.py`: the no-commits shape emits the distinct reason and the ordinary absent-baseline shape (tracked at an earlier commit, absent at `--since`) keeps the generic text.

Acceptance:
- [x] RED first: the new tests fail before the implementation edits and pass after (TDD labels in checklists only). [class: REPOSITORY_TEST]
- [x] Run: expect GREEN: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_readiness.py -q` exits 0 - met with the recorded known-red exception: ReviewTrajectoryPolicyFixtureTest (asserts a review-plan/SKILL.md witness sentence absent on main) fails pre-existing at base c0f0caf33, on main, and at run HEAD; owned by docs/history/backlog/2026-11-20-review-plan-trajectory-fixture-witness-drift.md; all Task 2 canaries pass. [class: REPOSITORY_TEST]
- [x] Run: expect GREEN: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_delta_classifier.py -q` exits 0. [class: REPOSITORY_TEST]
- [x] Run: expect GREEN: `python3 scripts/plan_readiness.py --pre-round <this plan>` exits 0 (the probe itself is warning-only, so the gate's exit is unchanged). [class: REPOSITORY_TEST]
- [x] The registry row carries the four admission fields and the row id follows the `script:` vocabulary; `python3 scripts/machinery_inventory.py --check` reports no new failure beyond the one pre-existing red (baseline re-derived 2026-11-20, recorded in Assumptions; the row the plan adds resolves). [class: REPOSITORY_TEST]


### Task 3: Hard-rules checkpoint authorization draft

Files:
- docs/AGENTS.md

Steps:
1. Draft the hard-rules line (authorize form, mirroring the Execute-plan entry's shape): "- **Plans checkpoints:** plans `wip:` checkpoint commits on the authoring run's recorded branch (the worktree authoring branch, or the primary-placement current or recorded task branch) are authorized for the authoring run only; push still requires explicit instruction. See `plans` skill." Carry the forbid variant in the plan ("- **Plans checkpoints:** plans authoring sessions must not commit; checkpoint commits require explicit operator instruction. See `plans` skill.") so the operator can choose either form without redrafting.
2. Resolve authorize-versus-forbid with the operator during this plan's execution Phase 1 (a user decision; the user-level canonical file is never edited without it), then land the confirmed form as one bullet beside the Execute-plan entry in the cross-project hard rules list.
3. Sweep the drafted line text against the hygiene scan's deny patterns before commit (no personal paths, no machine-specific values).

Acceptance:
- [x] The confirmed line appears in `docs/AGENTS.md` beside the Execute-plan entry, in the operator-confirmed form (authorize or forbid), with the plans skill pointer. [class: REPOSITORY_TEST]
- [x] The line grants no push authorization and no commit authorization beyond the authoring run's own checkpoint commits. [class: REPOSITORY_TEST]
- [x] Run: expect GREEN: `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0 over the repo (tracked hits outside agents/skills and projects report only). [class: REPOSITORY_TEST]


## Assumptions

- assume the router's Phase 0 dispatch bullet may carry the company-profile required-read pointer; basis: origin row 2's outcome sought names that surface and the dispatch entry routes both rows as one mechanism.
- assume byte balance comes from compressing `phase-0-placement.md`'s own verbose sentences; basis: the budget gate is blocking and the file carries the growth; current check shows zero blocking breaches, so the growth must not create one.
- assume the probe's missing-anchor arm keys on the `wip:`-prefixed commit history (the Authoring checkpoint duty's own commit marker), not on the `round_start_digest`; basis: Task 2 Step 1 arm 2, keyed by subject prefix per the Authoring checkpoint duty convention.
- assume the machinery inventory's one pre-existing failure is repaired or owned by its own lane, not by this plan (baseline re-derived at execution 2026-11-20: the authoring-time `duty:carrier-liveness-missed-fire` stale witness was repaired 2026-11-16; the live pre-existing red is the `regrowth: unregistered script file scripts/stack_review_round.sh` failure, present before this plan's first task); basis: `scripts/machinery_inventory.py --check` output at the run base and at HEAD.
- Decision receipts (Phase 1, maintenance-selected arm): branch-choice step over a new refusal path (entry rejected alternative 1); warning-only probe over refusal (shared-check-surface precedent, priced false-positive cost); policy pointer over copy (entry rejected alternative 3); hard-rules authorize draft with the operator deciding the final form (entry prompt Task 3); classifier distinct reason over the origin's tool-error class (origin row 1's outcome sought names a tool-error reason; a tool-error exit would reroute the hop away from the fresh-review fallback, so the message-only refusal keeps the unclassified class and exit vocabulary, the origin rewrite recorded here per the authoring rule). Scope extensions: none proposed; Sources inspected: not a tracker-linked request.

Decision points requiring a grill: none remain. Decision receipt (Task 3 execution-time, 2026-11-20): operator confirmed the AUTHORIZE form for the Task 3 hard-rules line, with the rationale that the host-level commit default conflicts with minimal-intervention unattended runs and that run-branch checkpoint commits are squashed away at landing anyway; recorded beside the Execute-plan entry in docs/AGENTS.md. (the four material points above resolved on the maintenance-selected arm with recorded receipts; the operator's authorize-versus-forbid choice is Task 3's own execution-time user decision, not an authoring ambiguity)

## Evaluation Criteria

- observability: both readiness modes print the untracked-plan warning on the probed untracked shape (re-derived probe, 2026-11-15) and stay silent on tracked plans.
- anchor-arm witness: the missing-anchor warning fires on a tracked plan with no `wip:`-prefixed touching commit (newest touching commit not landing-shaped), and stays silent with a `wip:` commit present or a landing-shaped newest commit, in both call sites, with exit codes unchanged.
- precision: the classifier emits the distinct no-start-commit reason on the probed shape and keeps the generic absent-baseline text on the ordinary shape.
- single-homing: no policy-paragraph text appears in `phase-0-placement.md` (`grep -cE "keeps? the current branch by default"` prints 0, the widened needle matching both moods of the policy sentence).
- budget: `scripts/skill_text_budget.py --check` stays at zero blocking breaches after Task 1's growth.

## Review Scope

- Tier A (behavior and files; must-fix): `scripts/plan_readiness.py`, `scripts/plan_delta_classifier.py`, `scripts/test_plan_readiness.py`, `scripts/test_plan_delta_classifier.py`, `scripts/machinery_registry.json` (the probe's warning-only contract; the classifier's message-only contract; the registry row's admission fields); `docs/AGENTS.md` (the Task 3 line's authorization scope).
- Tier A (text with behavior-adjacent gates; must-fix): `agents/skills/plans/phase-0-placement.md`, `agents/skills/plans/SKILL.md` (the byte-budget gate binds both; the single-homing grep binds the first).
- Tier B (text-only, no behavior): the Task 1 skill-text edits and their byte-balance deletions; the Task 3 draft wording.
- Out of scope: `agents/skills/execute-plan/worktree-first.md` (untouched single home), any new refusal path, hook-based auto-checkpointing, execution-side branching behavior.

## Validation Commands

- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement.md`
- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement.md`
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_readiness.py scripts/test_plan_delta_classifier.py -q`
- `python3 scripts/skill_text_budget.py --check`
- `python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement.md --repo-root <repo-root>`
- `python3 scripts/check_plan_origins_closed.py --mark-covered docs/history/plans/2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement.md`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- `python3 scripts/machinery_inventory.py --check` (baseline: one pre-existing failure, re-derived at execution 2026-11-20 and recorded in Assumptions)

## Documentation Impact Assessment

- README.md: no change (skill names, paths, and usage unchanged).
- `docs/AGENTS.md`: one hard-rules bullet added (Task 3); no other cross-references move.
- Machinery registry: one row added (Task 2); no rows removed.
- The sibling certification-time row stays open and dispatchable; its Cluster pointers are unchanged (this plan cites it, it does not cover it).
