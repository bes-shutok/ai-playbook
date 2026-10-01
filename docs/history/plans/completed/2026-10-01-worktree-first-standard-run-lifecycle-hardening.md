# Worktree-first standard run-lifecycle hardening

Backlog origins (scope of record): `docs/history/backlog/2026-09-28-adoption-gitignored-state-conjunct.md`, `docs/history/backlog/2026-09-28-bootstrap-test-env-hermeticity.md`, `docs/history/backlog/2026-09-28-execute-plan-resume-reentry-arm.md`, `docs/history/backlog/2026-09-28-reverse-squash-guard-absent-skips-tracked-dirt-check.md`, `docs/history/backlog/2026-09-28-worktree-branch-naming-single-home.md`, `docs/history/backlog/2026-09-28-worktree-creation-record-phantom-referent.md`

Classification: [class: fix-class] correctness + test hermeticity + one recorded design decision; authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Adoption**: a session entering its dispatch-provisioned ad-hoc worktree instead of creating a second one, gated by the canonical Provisioned-worktree adoption rule's conjunct list.
- **Identity block**: the Step 0.4 session-manifest fields `canonical_root`, `run_worktree`, `run_branch`, `run_base` recorded when Phase 0 completes, AUTHORED by the closeout group plan `2026-10-01-worktree-closeout-artifact-migration-and-residue.md` (its Task 5) but NOT YET on disk - the plan document landed, its tasks are unexecuted. The closeout group executes before this plan in the queue; Tasks 2 and 4 carry the ordering precondition and wire consultations to those fields without adding new ones.
- **Fork point**: the commit a run branch started from; the reflog `branch: Created from` entry is the primary recovery source, the run's worktree-creation record the secondary.
- **Sanitized environment**: a minimal subprocess env carrying `PATH` and a scratch `HOME`, with git-redirecting variables unset, so a test's verdict depends only on its fixture.

## Coverage dispositions (re-verified against disk 2026-10-01)

- The session-manifest worktree field is the closeout group plan's Task 5 (identity block plus resume sentence) and the survey arm its Task 6: AUTHORED AND LANDED AS PLAN DOCUMENTS, NOT YET EXECUTED - no skill file carries the fields today (verified by grep: zero skill-file hits for the field names; the only other corpus hit is the runtime driver's own canonical_root local variable, not the manifest field). This plan adds only the missing consultation sites (Phase 0 recognition arm, discovery ladder, payload resume rule) and depends on that plan's execution landing first (ordering precondition recorded in Tasks 2 and 4).
- The severed-ancestry fork point's named field will be `run_base` (base branch ref and commit captured at creation, equal to the branch start point for a fresh run worktree) once the closeout group's Task 5 executes; Task 4 wires the landing rule's citation to it under the same ordering precondition, without which the citation would recreate the very phantom referent its origin removes.

## Tasks

### Task 1: adoption verifies pre-existing gitignored state; start-empty restated fresh-worktree-only

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -c 'absent or byte-identical to the primary checkout' agents/skills/execute-plan/SKILL.md` returns 1
- `grep -c 'fresh-worktree-only' agents/skills/execute-plan/SKILL.md` returns at least 1

- [ ] Run → expect RED: both Evidence greps return 0 [class: REPOSITORY_TEST]
- [ ] In the canonical Provisioned-worktree adoption paragraph, append one conjunct to the adoption checks: the adopted worktree's pre-existing gitignored state (the facts file, the reviews directory) must be absent or byte-identical to the primary checkout's sources, standing the run down on anything else (a stale or planted facts snapshot passes the noclobber copy untouched, and the unconditional reviews copy would clobber a newer prior run's staging docs; the pins suite's normalized count of the paragraph's lead-in phrase is unaffected by the addition) [class: IMPLEMENTATION_REQUIRED]
- [ ] In the Transfer-in implementation's lead-in, restate the start-empty invariant as fresh-worktree-only: a fresh run worktree's gitignored directories start empty, and adoption is the verified exception whose pre-existing state the adoption conjunct introduced above verifies before any copy runs [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: adoption verifies pre-existing gitignored state` [class: IMPLEMENTATION_REQUIRED]

### Task 2: resume re-entry consults the recorded worktree at all three sites

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `grep -c "consult the session manifest's identity block" agents/skills/execute-plan/SKILL.md` returns 1 (the recognition-arm insertion; a literal unique to this plan's dictation, unaffected by the closeout group's two earlier identity-block occurrences)
- `grep -c 'carries the identity block' agents/skills/execute-plan/SKILL.md` returns 1 (the rung 2 insertion)
- `grep -q 're-enter the recorded worktree' agents/skills/maintenance/prompt-templates.md`

- [ ] Run → expect RED: the three Evidence greps miss today (both count literals are unique to this plan's insertions, so the counts stay 0 even after the closeout group executes) [class: REPOSITORY_TEST]
- [ ] In the Phase 0 worktree setup step's Already-provisioned recognition arm, add: when the session is not already inside a worktree, consult the session manifest's identity block before creating one, and when `run_worktree` names an existing worktree of this run, re-enter it through the canonical provisioned-worktree adoption rule instead of creating a second (ordering precondition: the identity block is recorded by the closeout group plan's Task 5, which executes before this plan in the queue - until that execution lands, this consult is dormant by construction, never broken) [class: IMPLEMENTATION_REQUIRED]
- [ ] In the Live-session discovery ladder's rung 2 (session-manifest heartbeat), add one sentence after the heartbeat signals: when the manifest carries the identity block, `run_worktree` names the run's canonical checkout, and a live recorded worktree routes resumption through the canonical provisioned-worktree adoption rule rather than a duplicate creation (the rung 1 spans pinned exactly-once are untouched) [class: IMPLEMENTATION_REQUIRED]
- [ ] In the execution payload's Resume rule in prompt-templates.md, extend the manifest read: after refreshing `updated:`, when the manifest records the identity block, re-enter the recorded worktree (adopting it per the canonical provisioned-worktree adoption rule) and continue from the first unchecked task there [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the three Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: resume re-enters the recorded run worktree at all consult sites` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the guard-absent branch stops and reports instead of skipping

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -c 'tracked-dirt check skipped' agents/skills/execute-plan/SKILL.md` returns 0
- `grep -q 'reverse-squash guard is missing' agents/skills/execute-plan/SKILL.md`

- [ ] Run → expect RED: the first Evidence grep returns 1 (the skip branch exists today), the second returns nothing [class: REPOSITORY_TEST]
- [ ] In the tracked-dirt inversion check recipe, replace the `if [ -z "$GUARD" ]` skip branch (`echo "reverse-squash guard absent; tracked-dirt check skipped"` falling through) with the stop-and-report shape: print `reverse-squash guard is missing; the tracked-dirt check cannot run - removal refused` naming both resolution paths (the repo-local scripts copy and the deployed home copy), and `exit 1` so the removal and transplant decisions are refused, mirroring the readiness gate's missing-validator treatment; the two-tier resolution arms stay unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: guard-absent tracked-dirt check refuses removal` [class: IMPLEMENTATION_REQUIRED]

### Task 4: the severed-ancestry fork point cites the recorded run_base field

Files:
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `grep -c 'run.s worktree-creation record (the session manifest' agents/skills/maintenance/prompt-templates.md` returns 1

- [ ] Run → expect RED: the Evidence grep returns 0 [class: REPOSITORY_TEST]
- [ ] In the severed-ancestry landing rule's fork-point parenthetical, give the secondary source its concrete home: `or from the run's worktree-creation record (the session manifest's run_base field, recorded at Step 0.4 as the base branch ref and commit captured at creation - the branch start point for a fresh run worktree)`, keeping the reflog arm primary and the fail-closed stand-down unchanged (ordering precondition: the run_base field is recorded by the closeout group plan's Task 5, which executes before this plan in the queue - landing this citation first would recreate the phantom referent the origin removes) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence grep [class: REPOSITORY_TEST]
- [ ] Commit: `payload: severed-ancestry fork point cites the recorded run_base field` [class: IMPLEMENTATION_REQUIRED]

### Task 5: the branch-naming asymmetry becomes a recorded decision

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -q 'Branch naming (decision of record)' agents/skills/execute-plan/SKILL.md`
- `grep -q 'intentionally unconstrained' agents/skills/execute-plan/SKILL.md`

- [ ] Run → expect RED: both Evidence greps return nothing [class: REPOSITORY_TEST]
- [ ] In the canonical Worktree-first section, directly after the Provisioned-worktree adoption paragraph (beside lifecycle step 1; the execution lane's convention sentence itself lives in the Phase 0 branch-naming block outside the canonical section, so the canonical anchor is the adoption paragraph), add the decision paragraph: Branch naming (decision of record): the execution lane's Phase 0 convention is the execution lane's rule; the authoring lane's branch name is intentionally unconstrained (dispatcher- or session-chosen), its durable records bind the name through the dispatching payload's witness (the claim file, work order, or pending_landing record), and the adoption predicate's otherwise-recorded-by-witness arm is the authoring lane's matching arm - the asymmetry is a decision, not a gap [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `skills: authoring-lane branch naming recorded as an unconstrained decision` [class: IMPLEMENTATION_REQUIRED]

### Task 6: the bootstrap smoke test runs hermetic subprocesses

Files:
- `scripts/test_execute_plan_worktree_bootstrap.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_worktree_bootstrap -q` exits 0
- `grep -c 'sanitized_env' scripts/test_execute_plan_worktree_bootstrap.py` returns at least 4

- [ ] Run → expect RED: `grep -c 'sanitized_env' scripts/test_execute_plan_worktree_bootstrap.py` returns 0 [class: REPOSITORY_TEST]
- [ ] Add a module-level `sanitized_env()` helper returning a minimal environment: `PATH` kept, `HOME` pointed at a fresh scratch directory, and `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` explicitly unset; use it in `run_readiness_validator` (replacing `dict(os.environ)`), in the recipe invocation's `subprocess.run`, and in the `_git` helper; keep the validator's `PLAN_READINESS_VALIDATOR` override applied on top of the sanitized base [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence commands (coordination precondition: this suite also carries the fence-ordinal extraction failure owned by the closeout group plan's Task 4; if that fix has not landed when this task runs, land it first - the sanitized env change assumes the suite's green baseline) [class: REPOSITORY_TEST]
- [ ] Commit: `test: bootstrap smoke suite runs under a sanitized environment` [class: IMPLEMENTATION_REQUIRED]

### Task 7: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers the adoption conjunct, the three re-entry sites, the guard refusal, the fork-point citation, the naming decision, and the hermetic suite

- [ ] Run the full Validation Commands block from the repository root; every line exits 0, except the `tracked-dirt check skipped` count line, which passes by printing 0 (grep -c exits 1 at a zero count; the printed count is the assertion) [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_worktree_bootstrap -q
PYTHONPATH=scripts python3 -m unittest scripts.test_worktree_closeout_migrate -q
grep -c 'absent or byte-identical to the primary checkout' agents/skills/execute-plan/SKILL.md
grep -c 'fresh-worktree-only' agents/skills/execute-plan/SKILL.md
grep -c "consult the session manifest's identity block" agents/skills/execute-plan/SKILL.md
grep -c 'carries the identity block' agents/skills/execute-plan/SKILL.md
grep -c 'tracked-dirt check skipped' agents/skills/execute-plan/SKILL.md
grep -q 'reverse-squash guard is missing' agents/skills/execute-plan/SKILL.md
grep -q 'Branch naming (decision of record)' agents/skills/execute-plan/SKILL.md
grep -q 'intentionally unconstrained' agents/skills/execute-plan/SKILL.md
grep -q 're-enter the recorded worktree' agents/skills/maintenance/prompt-templates.md
grep -c 'run.s worktree-creation record (the session manifest' agents/skills/maintenance/prompt-templates.md
grep -c 'sanitized_env' scripts/test_execute_plan_worktree_bootstrap.py
```

## Assumptions

- The Worktree-first standard owns the canonical lifecycle; the payload edits touch only the resume rule and the severed-ancestry fork-point parenthetical in prompt-templates.md, and no other consumer file changes.
- The identity block and the lifecycle survey arm are authored by the closeout group plan (Tasks 5 and 6) but not yet executed; this plan only wires the remaining consultation sites, adds no manifest field, and orders after that plan's execution in the same queue.
- The tracked-dirt check's removal-gate failure direction is fail-closed (stop-and-report), matching the readiness gate's missing-validator treatment; no no-guard-repo exception is recorded.
- The branch-naming choice is the recorded free-form decision (option 2 of the origin): the authoring lane stays dispatcher-chosen and witness-bound; a canonical cross-lane naming rule is rejected because the authoring lane's durable records already bind the name and a second predicate would gate without adding a witness.
- Task 6's suite baseline depends on the closeout group plan's Task 4 (extraction anchor repair) landing first; both plans sit in the same execution queue and the task records the ordering.
- The pins suite's exact-once spans (the adoption paragraph lead-in, the discovery ladder rung 1 bounds) tolerate all dictated insertions; keyed pins are re-verified green at landing.

Decision points requiring a grill: Task 1 conjunct failure direction (adoption stand-down, never a silent copy over divergent bytes); Task 2 re-entry routing (the canonical adoption rule, never a raw cd into the recorded path); Task 3 guard-absent direction (stop-and-report, no recorded no-guard exception); Task 4 secondary-source shape (cite run_base, do not delete the record arm); Task 5 naming decision (recorded free-form authoring lane, rejecting a canonical cross-lane rule); Task 6 sanitized-env surface (helper shared by validator, recipe, and _git, override kept on top).

## Review Scope

- `docs/history/plans/2026-10-01-worktree-first-standard-run-lifecycle-hardening.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/test_execute_plan_worktree_bootstrap.py`
- `docs/history/backlog/2026-09-28-adoption-gitignored-state-conjunct.md`
- `docs/history/backlog/2026-09-28-bootstrap-test-env-hermeticity.md`
- `docs/history/backlog/2026-09-28-execute-plan-resume-reentry-arm.md`
- `docs/history/backlog/2026-09-28-reverse-squash-guard-absent-skips-tracked-dirt-check.md`
- `docs/history/backlog/2026-09-28-worktree-branch-naming-single-home.md`
- `docs/history/backlog/2026-09-28-worktree-creation-record-phantom-referent.md`
