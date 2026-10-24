# Plan: Complete Worktree Closeout in the Owning Run

Backlog origin: docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md
Driving force: efficiency + simplicity
Plan review record: .ai-playbook/reviews/2026-10-24-plan-review-ad-hoc-worktree-lifecycle-owner-gap-r*.md
Execution budget: 2.0h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/ad-hoc-worktree-lifecycle-owner-gap.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- Closeout gate: the existing `worktree_closeout_migrate.py` check that decides whether this run's worktree and branch can be removed.
- Owning run orchestrator: the plans or execute-plan parent session responsible for the run's terminal closeout.
- Retained branch: the exact worktree-run branch that the closeout gate preserves because it is still used or its content is not accounted for. A company task branch kept for its PR-ready result is a run output, not a retained cleanup candidate.
- Primary placement: a configured run that stays in the primary checkout and has no run worktree; a company-profile run may keep or create a PR-ready task branch.
- Sanctioned branch closeout: the writer-quiesced gate, reconciliation, expected-OID verification, and compare-delete sequence owned by `agents/skills/done/SKILL.md`.

## Why

The existing migration and removal gates protect run artifacts and refuse unsafe deletion. Closeout still leaves operator work when a passing gate prints safe removal steps but the owning run does not carry them through to verification and reporting. Branch deletion also has a sanctioned writer-quiescence and expected-OID sequence that the owning run must complete.

## Gist & Examples

TLDR: Make the owning run orchestrator finish and verify safe worktree cleanup, reducing repeated operator follow-up through efficiency.

**Before (today):** A plan run lands its work, migrates review artifacts, passes `owned-files-clean` and `gate-removal`, and receives the authorized removal steps. The run ends with a registered worktree or branch, and the operator must ask for the remaining cleanup. A lesson also says the operator owns the printed step.

**After (this plan):** For the same successful worktree run, its orchestrator follows the gate's exact removal disposition and the done skill's sanctioned branch-closeout sequence, removes only eligible run resources, verifies the exact worktree and branch are gone, and includes that result in the final report. The lesson distinguishes this orchestrated path from a stand-alone gate invocation. A company-profile primary-placement task branch remains the PR-ready result and is excluded from worktree-branch teardown.

**Edge cases:** A blocked artifact transfer or a failed gate keeps the worktree and branch and reports the owner and next action. A live sibling worktree keeps its shared branch. An unaccounted delta keeps the exact branch and reports the missing paths and contents. A primary-placement run reports that no worktree cleanup applies; a company task branch stays as its PR-ready output.

## Outcome

The run that owns a plan worktree completes its authorized closeout when the existing safety checks pass and reports verifiable removal or a precise preservation reason.

- Fully removable run resources are gone before the orchestrator reports completion.
- Unsafe or unclear branch content and live siblings remain preserved with their evidence.
- Primary placement remains a no-worktree path; a company task branch stays PR-ready and is not removed as a worktree branch.

Gate delta: none; this plan clarifies the owner and completes the existing sequence without adding or removing a gate, refusal, fence, field, lock, registry, or review-layer blocker.

## Assumptions

- The helper's current output is authoritative for exact resource identity and disposition; broader name-based cleanup is excluded. Simpler-design comparison: a new cleanup registry is unnecessary because the witnessed gate passed and the missing action was follow-through (origin witness and `scripts/worktree_closeout_migrate.py`).
- A plan or execution request authorizes its own successfully gated closeout; the orchestrator does not ask the user to repeat that authorization after the pass. Simpler-design comparison: deferring to a later operator adds a second handoff without changing the safety checks (backlog Witness: authorized execution closeout).
- Primary placement has no run worktree. A company task branch may remain as the PR-ready output and is not a worktree branch eligible for this teardown. Simpler-design comparison: creating a cleanup-only worktree would add lifecycle cost without an owned resource (Worktree-first standard).
- Lesson 139 should retain its gate-seeding evidence while distinguishing stand-alone gate use from a run with an owning orchestrator. Simpler-design comparison: deleting the lesson would lose its valid `--claims` remedy (lesson 139).

Decision points requiring a grill: none remain.

## Standing constraints

- Apply the existing artifact migration, tracked-dirt, owned-files-clean, gate-removal, exact-identity, and sibling-worktree protections in their current order.
- For branch deletion, follow the done skill's sanctioned sequence: quiesce every writer, clear stale registrations, re-run the closeout gate, reconcile every candidate file to its verified destination, confirm the branch still has the gate's expected OID, then delete with an expected-OID comparison while writers remain stopped. Any changed OID, failed guard, or incomplete reconciliation retains the branch.
- Remove only resources the current run owns; never sweep by age, prefix, or authoring-looking name.
- Treat every gate refusal as preservation: keep resources and report the owner and next closeout action.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each success and refusal outcome follows the existing gate disposition.
- Ownership: the owning orchestrator, not a later operator or worker, performs safe terminal actions and verifies them.
- Simplicity: both consumer workflows refer to one shared cleanup-owner contract.

**Done when:**
- Removable worktree runs, preserved branches, live siblings, blocked transfers, and primary placement including company task-branch retention have explicit, consistent outcomes across the shared standard, both consumers, and the done skill.
- Branch teardown follows the existing writer-quiesced expected-OID sequence.
- No additional gate, cleanup registry, or broad sweep is introduced.
- Lesson 139 no longer assigns an orchestrated run's cleanup step to a later operator.

**Ship when:** the plan is implemented and archived after its review and closeout gates pass.

## Design Invariants

- Artifact transfer remains verified before removal.
- A passing removal gate authorizes only the exact run resources it accounts for; live sibling use or unaccounted content preserves the branch.
- Branch deletion occurs only through the sanctioned writer-quiesced sequence and an expected-OID compare.
- A company task branch in primary placement remains the PR-ready output, outside worktree-branch teardown.
- Every exit names whether resources were removed, retained, or not applicable, with an owner and next step for retained work.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid).

**Production code:**
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/done/SKILL.md`
- `docs/maintenance/development_lessons.md`

**Context-only behavior anchor (read-only):**
- `scripts/worktree_closeout_migrate.py` (`cmd_gate_removal` and `_capture_branch_oid` remain the authority for removal eligibility and expected branch identity).

**Tests:**
- No new automated test file; use existing plan-readiness and prompt-log validation, plus the scenario matrix below.

**Out of scope; reject unless plan-related:**
- Changes to `scripts/worktree_closeout_migrate.py`; its identity, migration, and deletion checks already passed for the witnessed cleanup and it remains a read-only behavior anchor.
- New registries, hooks, gates, locks, ledgers, or recurring sweeps; no missing safety predicate is evidenced.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md
python3 scripts/check_plan_origins_closed.py --plan docs/history/plans/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md
BASE="$(git merge-base HEAD main)"
python3 scripts/check_prompt_log_origins.py --prune-audit --base "$BASE"
```

After implementation, run the repository-configured public-hygiene scan over every changed file. Walk these cases against the shared standard, both consumers, the done skill, and lesson 139: removable worktree and eligible branch, retained branch with exact missing delta, live sibling worktree, blocked artifact transfer, ordinary primary placement, and company primary placement with its PR-ready branch retained. No runtime test is added because no runtime mechanism changes.

### Task 1: Assign the shared terminal owner

Context surface: Terms, Gist & Examples, Outcome, and Standing constraints.

Files:
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/done/SKILL.md`

Primary behavior anchors (existing, read-only): `cmd_gate_removal` and `_capture_branch_oid` in `scripts/worktree_closeout_migrate.py`; `agents/skills/done/SKILL.md` owns the sanctioned branch-closeout sequence.

- [ ] Given a passing gate and removable run worktree, expect the owning orchestrator to run the gate's exact worktree-removal command and verify the registration is gone [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a gate-authorized removable branch, expect the owning orchestrator to quiesce writers, clear stale registrations, re-run the gate, reconcile candidate contents, confirm the expected OID, compare-delete the ref, and verify it is gone [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a retained branch, live sibling, failed gate, or blocked transfer, expect preservation with the exact reason and next owner reported [class: IMPLEMENTATION_REQUIRED]
- [ ] Given company-profile primary placement with a task branch, expect the PR-ready branch to remain and be excluded from worktree-branch teardown [class: IMPLEMENTATION_REQUIRED]
- [ ] Given primary placement, expect a reported no-worktree no-op without creating cleanup resources [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: assign terminal worktree cleanup to run owner` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Align plan authoring and execution consumers

Context surface: Terms, Gist & Examples, Outcome, and Standing constraints.

Primary behavior anchors (existing, read-only): `cmd_gate_removal` and `_capture_branch_oid` in `scripts/worktree_closeout_migrate.py`; both consumer skills must preserve the gate disposition and its exact branch identity.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [ ] Given plans or execute-plan closeout, expect both consumers to name the parent orchestrator as the owner of the shared removal and verification sequence [class: IMPLEMENTATION_REQUIRED]
- [ ] Given gate-preserved branch evidence, expect execute-plan to report the exact delta without assigning later cleanup to the operator [class: IMPLEMENTATION_REQUIRED]
- [ ] Given ordinary primary placement, expect both consumers to report no worktree cleanup; given company task-branch placement, expect the PR-ready branch to remain [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: align plan closeout owners` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Reconcile the removal lesson and validate outcomes

Context surface: Terms, Gist & Examples, Outcome, and Standing constraints.

Primary behavior anchors (existing, read-only): `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py` and the sanctioned operator branch-closeout procedure in `agents/skills/done/SKILL.md`.

Files:
- `docs/maintenance/development_lessons.md`
- Files changed by Tasks 1 and 2

- [ ] Given a stand-alone gate invocation, expect lesson 139 to preserve its operator-run instruction and `--claims` remedy [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an orchestrated plans or execute-plan run, expect lesson 139 to defer cleanup ownership to that run's parent [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the scenario matrix including company task-branch retention, expect one consistent owner, preservation rule, and report outcome across every consumer [class: REPOSITORY_TEST]
- [ ] Run plan readiness, origin coverage, prompt-log prune audit, and configured public-hygiene scan with fresh output [class: REPOSITORY_TEST]
- [ ] Commit: `docs: scope removal lesson to standalone gate use` [class: IMPLEMENTATION_REQUIRED]
