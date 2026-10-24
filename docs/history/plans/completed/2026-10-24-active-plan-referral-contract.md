# Plan: Active-plan referral contract

Backlog origin: docs/history/backlog/2026-10-10-plan-referral-runtime-contract-gap.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-24-plan-review-active-plan-referral-contract-r*.md (highest round for this source-plan path is authoritative)
Execution budget: 1.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-plan-referral-runtime-contract-gap.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Active-plan referral**: a user scope-change request naming the plan bound to a running execute-plan session.
- **Referral pause**: the interval after a referral arrives when no new task starts until the request is reviewed and resolved.
- **Active run placement**: the checkout or worktree and branch recorded for the running plan.
- **Authoring claim**: the session-owned claim that reserves the backlog item while its plan is authored.
- **Execution claim**: the existing claim that reserves the running plan's implementation work.
- **Run baseline (`source_digest`)**: the SHA-256 of the active plan stored in the execute-plan manifest. It must match the plan bytes immediately before a referral edit; after changed bytes, refresh it only after fresh review and readiness pass.
- **Pre-implementation readiness check**: `python3 scripts/plan_readiness.py --pre-round <plan-path>`, run before implementation and again when the plan digest or task scope changes.
- **Finalization lock**: the normal `done` lock for the current checkout, acquired before learn, docs-branch sync, and project commits. The parent runs `done` once at final closeout and acquires no nested finalization lock during referral authoring.
- **Frozen line**: the tracked prompt-log marker for an entry being authored. A worktree run verifies it on the default branch; a primary-checkout run on another branch verifies it on that run's branch and names the branch in its completion record.

## Why

The existing execute-plan interruption contract handles stop, status, and recovery, but it does not route a message naming the active plan into a recorded scope change and fresh plan review. This plan defines that route within the existing run, including how the plans workflow edits the exact active run placement, primary checkout or worktree, without creating a second run, and preserves current task and claim recovery guarantees.

## Gist & Examples

TLDR: define and test named active-plan referrals, improving code-quality by making scope edits safe and resumable in the existing run placement.

Before: a message naming the active plan for a scope change can be treated as an ordinary interruption; no procedure binds the request, edits the plan, refreshes review, and resumes.

After: the orchestrator binds the named plan to the active run, pauses before another task claim, records and adjudicates the requested change, edits the plan at its verified primary or worktree placement through the plans workflow, refreshes review and digest when plan bytes change, and resumes through the existing run.

Example (worktree placement): if the user names the active plan while Task 2's worker is running, the orchestrator records the referral and makes no new task claim; after the worker returns, it verifies and records the successful Task 2 boundary, applies the plan edit in the active worktree through the plans skill, obtains fresh review and readiness evidence, updates the run digest, and only then resumes. If the worker failed, it records that terminal attempt without inventing a successful boundary and processes the referral before retry or fallback.

Edge cases: primary-checkout placement uses the same verified plan, branch, authoring claim, and checks before editing as worktree placement; final closeout follows its usual serialization step. A referral naming a different plan does not mutate the current run; an explicit stop, pause, or abort takes precedence and defers any referral until a later explicit resume; unknown worker liveness keeps the referral pending without a write or new claim; an unchanged plan digest does not relaunch work or reseed a claim; a requested extension follows the plans skill's existing scope rules.

## Outcome

An operator can refer an active execute-plan run to a scope change, and the run safely records, reviews, and resumes that change.

- A referral before the next task claim is processed before the next task starts.
- An in-flight worker is not raced, and its successful task boundary or unsuccessful terminal attempt is recorded accurately before referral processing.
- A changed plan resumes only after a fresh plan review, all required checks before implementation, and a refreshed hash in the same run; an unchanged hash follows existing recovery behavior.
- The plan edit uses the active run placement and existing claims. It follows the usual checks before writing, then resumes through ordinary closeout. It creates no second worktree, branch, or execution run.

Gate delta: no new operational gate, refusal class, claim type, runtime schema, scheduler, second lock, or parallel recovery path. The active referral uses the usual plan-authoring claim and checks before writing. The execution claim stays unchanged and plan changes follow existing run recovery. One read-only regression test covers the incident class. Witness: the blocking plan-review finding in the backlog origin. Expected catch frequency is low, at most one regression per year; false-positive cost is a focused test update when the contract intentionally changes. Review the test's continued value by 2027-01-24.

## Assumptions

### Referral authoring lifecycle

| Step | Contract |
|---|---|
| Bind and edit | Verify the active plan path, manifest `source_digest`, run state, execution claim, and recorded placement. The manifest digest must equal the plan's current SHA-256 before writing. Use the recorded worktree and branch or checkout and branch. A mismatch, active merge or rebase, or another finalization in progress leaves the referral pending without a write or task claim. |
| Review and resume | Preserve the execution claim and create no second worktree, branch, baseline, or run. After changed bytes, obtain a fresh plan review with `ready=yes`, pass the Pre-implementation readiness check, then refresh `source_digest` and the existing run records before another task claim. An unchanged plan follows existing recovery behavior. |
| Final closeout | Keep the authoring claim through execute-plan completion. At final closeout, the parent runs the ordinary `done` workflow once under the Finalization lock; the maintenance template's claim-deletion procedure runs only after placement-specific completion evidence is verified. |

| Placement | Completion evidence before claim deletion |
|---|---|
| Worktree | Transfer the plan and review records to the primary checkout; commit or transfer all run-owned files; land the authoring branch; pass `owned-files-clean` and `gate-removal`; remove the worktree only after `gate-removal` reports `OUTCOME: pass`; verify the Frozen line on the default branch. Remove the branch only when its work is landed or accounted for and no live worktree or run uses it. |
| Primary checkout | Complete the `done` commits and verify the plan and review records at their primary homes. If the current branch is not the default branch, verify the Frozen line on the run's branch and name that branch in the completion record. |

The lifecycle applies ordinary plan authoring to a plan already in progress. Keep its existing placement and claims; the maintenance template owns claim deletion after the placement evidence above passes.

- Only a message naming the plan bound to the active run enters this procedure; identify it from the run's recorded plan path and existing claims. Basis: the backlog's named-plan requirement and execute-plan's resume identity contract.
- An explicit stop, pause, or abort takes precedence; process a pending referral only after a later resume. Basis: execute-plan's existing interruption handling.
- A referral prevents another task from starting but does not cancel a worker already running. After its termination is verified, record its actual result and process the referral before another task or retry. Basis: execute-plan's interruption handling and the backlog's pause-before-claim requirement.
- Referral authoring follows the lifecycle table below and uses the running plan's placement with the normal authoring claim and pre-writing checks. Basis: execute-plan's placement setup and the maintenance authoring template.
- Record the request, its decision, and the next action in the run's existing records; add no new state or artifact. Basis: `agent-logs.md` assigns run decisions and digest to those records.
- Plan edits follow the plans skill's edit, scope, review, and readiness rules. Changed bytes require fresh review, passing readiness checks, and an updated digest in the run's records before resumption. Basis: `agents/skills/plans/SKILL.md` and the recovery rule established by the 2026-09-25 execute-plan recovery plan.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep interruption handling in the existing interruption section and plan-edit placement in the existing plans/execute-plan integration; these are the current owners.
- Preserve the existing stop/status rules, run identity, worker handling, execution claim, and unchanged-plan recovery.
- Covered-origin exception applies only when the active run manifest and execution claim bind the referral to the same plan and the active plan is the sole covering plan; all other covered-origin refusals remain.
- Add no state field, scheduler action, claim type, second lock, claim reseed, extra worktree or branch, or maintenance lane change. Use the existing authoring claim and pre-writing checks; keep final serialization in closeout.
- Keep the earlier plan's deferral as historical context; do not revise completed history.

## Evaluation Criteria

- Correctness: an exact active-plan referral is bound to the right run and prevents another task claim until adjudication.
- Interruption safety: before-claim, active-worker, successful-terminal, failed-terminal, post-boundary, and explicit-stop cases have ordered outcomes without racing a worker or inventing a boundary.
- Placement safety: before editing, verify the plan path and manifest `source_digest`, confirm the execution claim, and use the exact recorded worktree/branch or checkout/branch. Any mismatch or failed pre-writing check leaves the referral pending without changes.
- Review integrity: an edited plan gets a fresh review with `ready=yes`, passes the Pre-implementation readiness check, and has its current `source_digest` recorded before resume.
- Simplicity: reuse the run's identity, placement, records, claims, and review path; create no second worktree, branch, run, or finalization sequence.

**Done when:** the lifecycle and focused regression cover before-claim, live-worker, successful and unsuccessful worker termination, post-boundary, explicit stop, mismatched plan, pre-edit digest drift, changed/unchanged plan bytes, claim retention and placement-matched closeout deletion; the authoring claim allows a covered origin only for the exact active run plan while retaining refusal for any other covering plan; the regression and full plan-readiness gate pass.

**Ship when:** the contract and its regression land together; no external prerequisite exists.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Operational contracts:**
- `agents/skills/execute-plan/SKILL.md` (`## User Interruption`, `## Worktree-first standard`, and only the Phase 0 and final closeout integration spans needed for the referral authoring lifecycle)
- `agents/skills/plans/SKILL.md` (Phase 0 active-run placement and authoring-claim rule plus `With execute-plan` integration only)
- `agents/skills/maintenance/template-authoring.md` (only the AUTHORING CLAIM covered-origin pre-work eligibility for exact active-plan referrals; retain all other guard and claim-deletion behavior)

**Tests:**
- `scripts/test_execute_plan_referral_contract.py`

**Plan-related extension:**
Implementation and review may change unlisted paths only when causally required by this plan task. Keep all other sections and methods frozen.

## Validation Commands

Authoring evidence: `bash scripts/check-no-em-dash.sh touched` passed; the public-hygiene scan passed. The first pre-round readiness attempt failed only because the new test path lacked the required `*(new)*` annotation; after correcting it, `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-24-active-plan-referral-contract.md` passed. Rule 19 RED-today execution is not applicable because no wrapped forbidden-phrase sweep is specified. Rule 22 mechanical audit is not applicable because no literal validation span is pinned to a prescribed task snippet. Pre-computation bug-pattern checks are not applicable because this plan changes no data-processing behavior.

Run from the repository root; every gate must be green at done:

```bash
python3 -m unittest discover -s scripts -p 'test_execute_plan_referral_contract.py' -v
python3 scripts/plan_readiness.py docs/history/plans/2026-10-24-active-plan-referral-contract.md
bash scripts/check-no-em-dash.sh touched
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md agents/skills/maintenance/template-authoring.md scripts/test_execute_plan_referral_contract.py
```

### Task 1: Define and test active-plan referral handling

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/template-authoring.md`
- `scripts/test_execute_plan_referral_contract.py` *(new)*

Evidence:
- `docs/history/backlog/2026-10-10-plan-referral-runtime-contract-gap.md` names the missing referral lifecycle and required timing cases.
- `agents/skills/execute-plan/SKILL.md`, `## User Interruption`, owns stop/status classification, active worker state, and resumption.
- `agents/skills/execute-plan/agent-logs.md` assigns run decisions and digest to the existing briefing and manifest.
- `agents/skills/plans/SKILL.md` owns plan edits, scope handling, review, and readiness.

- [x] Define the referral transition table in `## User Interruption`, including before-claim, live-worker, success, failure/partial/timeout/cancellation, post-boundary, explicit-stop, and identity-mismatch outcomes; stop wins and no unsuccessful attempt invents a successful boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the referral authoring lifecycle in plans Phase 0 and execute-plan integration. Verify exact worktree/branch or primary checkout/branch, plan path, digest, manifest, and execution claim; use the existing lock-free pre-work guard and acquire no nested done lock. Mismatches or a busy lock leave the referral pending; create no second placement, baseline, or run. [class: IMPLEMENTATION_REQUIRED]
- [x] Create or refresh the normal plans authoring claim in Phase 0, retain it through execute-plan completion, and invoke the existing maintenance-template deletion procedure only after placement-matched completion-claims evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Require a pre-edit digest match against the active run; on mismatch, leave the referral pending and use existing digest-drift recovery. After changed bytes, run fresh plan review and full readiness, recompute the digest, and update the same run records before another task claim; unchanged bytes follow current recovery. [class: IMPLEMENTATION_REQUIRED]
- [x] Add read-only regression cases for before-claim, live-worker, successful and failed/partial/timeout/cancelled outcomes, post-boundary, explicit-stop precedence, mismatched identity, matching and mismatching pre-edit digest, changed/unchanged plan bytes, and unknown liveness. Assert no plan write, new claim, retry, or replacement before termination is verified; then record the original worker's actual terminal result before referral handling. [class: REPOSITORY_TEST]
- [x] Assert exact worktree/branch and primary-checkout/branch adoption, authoring-claim creation and retention, lock-free pre-work refusal, no nested done-lock acquisition, execution-claim continuity, and claim deletion only after the placement-matched completion-claims evidence and execute-plan closeout. [class: REPOSITORY_TEST]
- [x] Update both mirrored pre-work stand-down gates and permit the covered-origin authoring claim only when the exact active plan path, manifest identity, and execution claim match and no other plan covers the origin; regression tests assert claim creation for that case and refusal for a different covering plan or identity mismatch against both gate copies. [class: REPOSITORY_TEST]
- [x] Run `python3 -m unittest discover -s scripts -p 'test_execute_plan_referral_contract.py' -v` and `python3 scripts/plan_readiness.py docs/history/plans/2026-10-24-active-plan-referral-contract.md`; record outcomes. [class: REPOSITORY_TEST]
- [x] Run `bash scripts/check-no-em-dash.sh touched` and `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md agents/skills/maintenance/template-authoring.md scripts/test_execute_plan_referral_contract.py`; record outcomes. [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: define active-plan referral handling` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-10-plan-referral-runtime-contract-gap.md`: implemented by this plan; archive the origin with the covered flip in the same landing change.
