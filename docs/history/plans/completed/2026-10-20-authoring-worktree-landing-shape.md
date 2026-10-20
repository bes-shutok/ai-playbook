# Plan: Close the plan-authoring worktree lifecycle

Backlog origins (scope of record):
- docs/history/backlog/2026-10-20-authoring-worktree-landing-shape.md
- docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md
- docs/history/backlog/2026-10-14-authoring-worktree-create-path.md
Driving force: reliability (the witnessed fast-forward preserved authoring checkpoints despite an existing squash contract; the plan closes the handoff and create-path gaps without adding machinery)
Plan review record: the staging series `.ai-playbook/reviews/2026-10-20-plan-review-authoring-worktree-landing-shape-r*.md` (the highest rN for this source-plan path is authoritative).
Authoring claim: docs/tmp/authoring-claims/2026-10-20-authoring-worktree-landing-shape.md (session no-session)
Execution budget: 1.5h total, largest task 1.0h

## Terms

- Authoring claim: the per-backlog-item file under `docs/tmp/authoring-claims/` that records the authoring session and target item; its basename deterministically names the authoring branch under the rule added by Task 1.
- Authoring worktree: the dedicated worktree created before a plan file exists, on an `authoring/` branch.
- Worktree-first standard: the canonical lifecycle in `agents/skills/execute-plan/SKILL.md`.
- Landing helper: `scripts/land_squash.sh`, whose `land-worktree` mode serializes squash landing and verifies source-tree equality.
- Primary placement: the facts-resolved placement where authoring commits directly and does not create a run worktree or squash landing.
- Done closeout: the final `done` run that learns, migrates records, runs landing gates, and commits owned work.
- Merge landing lock: the repository lock that serializes changes to the base branch.
- Tree-equality proof: the helper check that the squash result has the source worktree's exact tree.
- Artifact migration: transfer of the run's gitignored plan-review records into their primary homes, followed by verification.
- Checkpoint commit: an authoring branch commit marked `wip:` that preserves plan bytes during drafting.

## Why

A recent authoring run fast-forwarded its checkpoint branch to `main` even though the Worktree-first standard and the plans Phase 0 contract already require the landing helper. The plans Final Step describes `done` and removal gates without making the intervening helper landing an explicit handoff, and the standard's single worktree-create path requires a plan file that authoring has not written yet.

## Gist & Examples

TLDR: connect authoring worktree creation, squash landing, and claim deletion through the existing lifecycle owners, without adding a new gate.

**Before:** Phase 0 has no named create arm for a not-yet-authored plan; the Final Step hands off to `done` and lists removal gates without an explicit landing handoff; the claim-delete duty has no named closeout call site.

**After:** the authoring claim identifies the session and target item, and its basename deterministically selects the authoring branch for one documented pre-plan `git worktree add` path; `done` first migrates and verifies review artifacts while the source worktree remains; after successful `done`, the Final Step calls the Worktree-first landing step, then reruns the removal checks before deleting the source worktree and branch; the same closeout deletes its still-owned claim only after verified landing and migration. Primary placement keeps its immediate-commit and no-landing path.

**Edge cases:** keep branch identity and live-sibling protections; retain the worktree and branch when landing, artifact migration, or removal gates refuse; delete a claim only after rechecking ownership; never create a squash landing for primary placement.

## Outcome

Plan-authoring worktree sessions follow one traceable lifecycle from pre-plan worktree creation through helper-based squash landing, artifact verification, claim deletion, and exact source cleanup. Primary-placement sessions continue to commit directly and record no landing.

Gate delta: none; no refusal class, hard gate, fence, protocol layer, schema field, task pause, or blocking review duty is added, removed, or promoted.

## Assumptions

- The existing squash contract is present and correct: Worktree-first standard step 4 mandates `land_squash.sh land-worktree`; plans Phase 0 says `wip:` checkpoints are absorbed by the final squash; the 2026-10-20 main reflog records a fast-forward at `6f103becef10b1504ea6173d24cc2acfd0cb9801`, and its first-parent history includes the authoring `wip:` commits. The witnessed failure was an out-of-contract command choice, with the Final Step handoff leaving the required helper sequence implicit at the authoring call site.
- The authoring claim records the session and target item but has no branch field; the plan defines the branch as `authoring/<claim-file-stem>` and verifies it against the Git worktree registration. This adds no claim field, second claim gateway, or `execution_claim.sh` mode.
- The claim freshness reader already treats an expired heartbeat as stale; this plan makes the existing owned-delete duty explicit and adds no recurring cleanup.
- The authoring-create origin's direct `git worktree add` arm remains the smallest path because the authoring claim exists before the plan operand does.

Decision points requiring a grill: none remain.


## Standing constraints

- Keep the Worktree-first standard as the single owner of landing mechanics; the plans skill calls its named step instead of restating helper flags or proof details.
- Preserve the existing helper, merge lock, tree-equality proof, artifact migration, cited-record verification, and gate-removal protections.
- Keep primary placement separate: no new worktree, branch, squash landing, or branch-removal step.
- Do not add a gate, validator, sweeper, claim surface, or execution-claim gateway mode.
- Preserve the `wip:` checkpoint commits on the source branch until the helper creates the squash landing.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the documented sequence uses the existing helper and preserves its refusal behavior.
- Maintainability: create, landing, and claim-delete duties each have one owner and consumers point to those owners.

**Done when:** the authoring create path is explicit before the plan exists; the plans Final Step names the existing landing step after successful `done` migration and before final removal checks; the claim-delete duty has one closeout call site with an ownership recheck; the primary-placement arm remains unchanged; all three origins have accurate dispositions.

**Ship when:** none; this is a repository-local workflow contract update.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production code:** none; this is a workflow-text plan.

**Tests:** none; no executable surface changes are proposed.

**Docs:**
- `agents/skills/execute-plan/SKILL.md` - Worktree-first standard step 1's pre-plan authoring arm.
- `agents/skills/plans/SKILL.md` - Phase 0 authoring placement and Final Step handoff.
- `agents/skills/maintenance/template-authoring.md` - claim lifecycle and closeout handoff wording.
- `docs/history/backlog/2026-10-14-authoring-worktree-create-path.md`, `docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md`, and `docs/history/backlog/2026-10-20-authoring-worktree-landing-shape.md` - record their disposition under this plan and remove them in the landing change per the repository backlog-completion rule.
- `docs/history/backlog/PLAN-PROMPTS.md` - prune this plan's entry with its witness receipt and tidy cluster pointers.

**Out of scope:**
- `scripts/land_squash.sh` and the landing lock protocol; the current contract already covers the witnessed landing shape.
- `scripts/execution_claim.sh`; no authoring mode is added to the execution gateway.
- Main history rewriting; preserve the landed history and correct the future closeout path.
- Any machinery admission surface; no new blocker or recurring actor is proposed.

## Validation Commands

- Run `python3 scripts/plan_readiness.py docs/history/plans/2026-10-20-authoring-worktree-landing-shape.md` after the final plan bytes are written.
- Run the plan-origin disposition checker on the plan and its three named origins before landing.
- Run the public hygiene scan over changed paths and `git diff --check` before the implementation landing.
- Inspect the authoring worktree and primary placement branches in the final review to confirm that only the worktree arm calls the landing helper.

### Task 1: Name the pre-plan authoring worktree create arm

Context surface: this task, `## Terms`, and the `Authoring claim` and `Authoring worktree` definitions.

Files:
- `agents/skills/execute-plan/SKILL.md` *(edited)*
- `agents/skills/maintenance/template-authoring.md` *(edited)*
- `docs/history/backlog/2026-10-14-authoring-worktree-create-path.md` *(disposition)*

Primary class anchors:
- `Worktree-first standard` in `agents/skills/execute-plan/SKILL.md`
- `WORKTREE DUTY` in `agents/skills/maintenance/template-authoring.md`

- [x] Given a fresh authoring claim whose plan file does not yet exist, the documented create arm derives `authoring/<claim-file-stem>` from the claim path and creates a non-detached worktree on exactly that branch; an existing branch with no matching live authoring worktree, a missing claim, or a foreign claim creates no worktree. [class: IMPLEMENTATION_REQUIRED]
- [x] Given execution of an existing plan, `execution_claim.sh take` remains the create path and its behavior is unchanged; the authoring template points to the authoring arm without copying lifecycle text. [class: IMPLEMENTATION_REQUIRED]
- [x] Disposition the create-path origin as covered by the named standard step and cite the plan as its witness. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Complete the authoring closeout handoff

Context surface: this task, `## Outcome`, `## Assumptions`, `## Standing constraints`, and `## Evaluation Criteria`.

Files:
- `agents/skills/plans/SKILL.md` *(edited)*
- `agents/skills/maintenance/template-authoring.md` *(edited)*
- `docs/history/backlog/2026-10-20-authoring-worktree-landing-shape.md` *(disposition)*
- `docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md` *(disposition)*
- `docs/history/backlog/PLAN-PROMPTS.md` *(prune and cluster cleanup)*

Primary class anchors:
- `Final Step: Run done` in `agents/skills/plans/SKILL.md`
- `AUTHORING CLAIM` in `agents/skills/maintenance/template-authoring.md`
- `Worktree-first standard` in `agents/skills/execute-plan/SKILL.md`

- [x] Given a worktree authoring run with `wip:` checkpoints, `done` first migrates and verifies review artifacts, then the documented post-`done` handoff calls the existing landing helper and produces one squash commit whose tree equals the source worktree tree before the source worktree or branch is removed. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a landing or artifact-migration refusal, the worktree, branch, and authoring claim remain; after successful migration and squash proof, rerun the owned-files-clean and gate-removal checks, and delete the owned claim only after those checks pass and branch ownership is rechecked. [class: IMPLEMENTATION_REQUIRED]
- [x] Given primary placement, authoring commits directly and records no helper landing or worktree branch removal. [class: IMPLEMENTATION_REQUIRED]
- [x] Record the root cause as a missed helper handoff while preserving that the squash contract already existed; do not add a blocker or rewrite `main`. [class: IMPLEMENTATION_REQUIRED]
- [x] Dispose of both remaining origin rows, prune the plan's prompt entry with its witness receipt, and tidy pointers in the same landing. [class: IMPLEMENTATION_REQUIRED]
- [x] Validate the text against worktree creation, successful squash landing, refused landing, artifact-migration refusal, branch retention, claim ownership change, and primary-placement cases. [class: IMPLEMENTATION_REQUIRED]
