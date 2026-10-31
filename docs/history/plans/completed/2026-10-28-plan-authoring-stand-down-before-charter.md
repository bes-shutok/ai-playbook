# Plan: Bound No-Charter Cleanup to Verified Authoring Stand-Downs

Backlog origin: docs/history/backlog/2026-10-26-plan-authoring-stand-down-before-charter.md
Driving force: simplicity + reliability
Plan review record: the staging series .ai-playbook/reviews/2026-10-28-plan-review-plan-authoring-stand-down-before-charter-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3.0h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-26-plan-authoring-stand-down-before-charter.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms

- No-charter stand-down: an authoring run stops after its worktree is provisioned but before its first plan-file write.
- Authoring claim: the existing per-item claim file used to bind plan-authoring work to a session and backlog origin.
- Actionability evidence: rerun the origin's own probe against current source; only a green result plus a reachable commit whose change matches every stated expectation proves the work already landed, while uncertainty keeps authoring eligible.
- Close-as-covered: the existing completion disposition that names the implementing commit, removes the satisfied backlog row, and prunes its prompt entry with the accepted receipt format; for a pre-provision source-history closure, the prompt log must also recognize that evidence as a covered origin class.
- `PLAN-PROMPTS` entry: the rolling authoring queue item, frozen and pruned under its existing origin and receipt rules, including the added pre-provision source-history close-as-covered eligibility case.
- `gate-removal`: the existing worktree-closeout check for plan identity, review artifacts, owned-artifact accounting, and branch state.
- Run evidence: the done-run manifest binds the plan path and `start_commit` (the commit recorded when setup began); its owned-artifact set lists files assigned to that run.

## Why

The origin can become non-actionable when its requested behavior has already landed, and the existing open-plan check does not detect that case before authoring state is created. Such a result needs an accepted backlog and prompt disposition with the implementing commit as its witness. A later stand-down before the first plan write also has no charter for gate-removal, so safe cleanup can be stranded. Reuse the existing close-as-covered and prompt-receipt contracts before reservation, then extend the current closeout gate for an unavoidable post-provision stand-down while keeping ordinary closeout protections intact.

## Gist & Examples

TLDR: Close already-landed origins with their existing evidence before provisioning and add verified cleanup for later no-charter stand-downs, reducing stranded work through simplicity.

**Before:** A plan-authoring session checks whether an open plan covers its origin, but not whether source and landed history show that the requested behavior is already complete. If it stands down after setup but before the first plan write, gate-removal refuses because the plan file does not exist, leaving the worktree and branch for manual disposition.

**After:** Before creating run state, maintenance reruns the origin's own probe. If it is green and a reachable commit matches every stated expectation, one targeted close-as-covered commit removes the satisfied backlog row and prompt entry, with the existing `PLAN-PROMPTS-PRUNE` receipt naming the implementing commit. The existing prompt receipt records the implementing commit, and the prompt log’s existing `Coverage and removal rule` gains a pre-provision source-history close-as-covered eligibility case: the origin’s own probe is green against current source, each explicit expectation matches, and a reachable implementing commit witnesses those exact expectations. The backlog row and prompt entry close in one targeted commit; the existing receipt and prune audit remain in force. If the closeout write cannot complete, both records remain intact and maintenance continues with another independent target. Incomplete or ambiguous evidence keeps the item eligible and authoring continues without an operator question. For a later no-charter stand-down, the existing gate accepts cleanup only when the authoring claim matches the frozen prompt entry and origin, the done-run manifest names the expected plan, the worktree and branch derive from that claim under the existing placement rule, the branch remains at the recorded start commit, and the owned-artifact set is empty and accounted for. It removes only those exact run resources through the existing branch-closeout sequence.

**Edge cases:** A covered or missing origin, or an exact already-landed match with a reachable implementation commit, is resolved before a claim, prompt freeze, or worktree exists. The prompt receipt cites that commit and the close-as-covered commit deletes the origin row; if this disposition cannot be committed, the files are preserved and another target is selected. Ambiguous actionability evidence proceeds to authoring. A changed worktree, branch, claim, manifest, or unaccounted artifact keeps the existing preservation behavior. Ordinary plan closeout follows the current charter and artifact checks.

## Outcome

A verified already-landed origin is closed with its existing source, history, and prompt-receipt evidence before authoring state is created; an ambiguous origin continues through plan authoring without asking the operator. A verified no-charter stand-down can clean up its own empty authoring setup, while uncertain resources remain preserved and unrelated maintenance work can continue.

- Covered and missing origins use the existing pre-provision disposition; a green origin probe with a matching landed commit uses the existing close-as-covered and prompt-receipt formats before authoring state is created.
- Ambiguous or incomplete source/history evidence keeps the origin eligible and adds no refusal or operator question. A refused close-as-covered write preserves the row and prompt and continues to an independent eligible target.
- A post-provision stand-down removes only a clean, exact-session worktree and branch whose owned artifacts are fully accounted for.
- A normal plan closeout keeps its current gate and identity checks.

Gate delta: use the origin's own probe and existing close-as-covered, backlog-deletion, and prompt-receipt paths before provisioning; remove the existing plan-file-not-found refusal only for a verified pre-plan authoring stand-down. Add no lane-blocking gate, refusal class, lock, registry, ledger, or state field. Ordinary plan-closeout checks remain unchanged.

## Assumptions

- Maintenance can rerun the origin's own probe and identify an implementing commit before authoring setup; its existing deletion and prompt-receipt formats can record the close-as-covered result without a new ledger. Confirm the receipt remains accepted by the prune audit. Ambiguity proceeds to authoring, so actionability adds no refusal or operator question.
- gate-removal remains the single closeout authority. A separate cleanup script, global sweep, or weakened ordinary-plan path would add machinery without improving the witnessed no-charter case.
- The authoring claim and done-run manifest provide existing evidence to bind a pre-plan closeout; implementation must confirm the current records are sufficient before adding any new field.

Decision points requiring a grill: none remain.

## Standing constraints

- Do not create a second gate or a required ceremony for ordinary plan authoring.
- Do not delete a worktree, branch, or artifact when identity, liveness, or ownership is unclear.
- Do not add a global sweep, broad delete path, new registry, or new persistent state field.
- A refused cleanup preserves resources and reports an exact next action; it never prevents selecting independent work.

## Evaluation Criteria

- Correctness: only a pre-plan run with matching claim and done-run evidence, unchanged start commit, clean worktree, and fully accounted artifacts qualifies for no-charter cleanup.
- Actionability: a green origin probe and reachable commit matching all origin expectations are recorded through existing backlog-deletion and prompt-receipt formats before claim, freeze, or worktree creation; ambiguity proceeds with authoring and no operator question.
- Preservation: a mismatch, unaccounted artifact, competing worktree, or unclear branch owner leaves the affected resource untouched with a specific reason.
- Compatibility: ordinary plan closeout still requires its charter and passes every current identity, review-artifact, and branch check.
- Continuity: the pre-provision check remains ahead of prompt freeze and worktree creation, and a cleanup refusal does not hold the authoring lane from independent work.
- Simplicity: the change reuses the existing gate and closeout sequence and adds no separate cleanup mechanism or persistent state.

## Review Scope

**Explicit must-fix:** valid findings on the production and workflow paths below.

**Production code:**
- scripts/worktree_closeout_migrate.py (cmd_gate_removal and its current branch identity checks) (Task 1)

**Workflow contracts:**
- agents/skills/maintenance/decisions.md (Task 2)
- docs/history/backlog/PLAN-PROMPTS.md (Task 2)
- agents/skills/plans/SKILL.md (Task 3)
- agents/skills/maintenance/template-authoring.md (Task 3)

**Context-only behavior anchors (read-only):**
- scripts/done_run.sh (review-only) and scripts/done_sweep_gates_lib.py (review-only) for the existing run manifest and start-commit evidence
- agents/skills/execute-plan/worktree-first.md (review-only) for worktree creation and branch closeout
- docs/history/plans/completed/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md (review-only) for the existing terminal owner
- scripts/check_prompt_log_origins.py (review-only) for accepted deletion and prompt-receipt evidence

**Tests:**
- Regression coverage for the no-charter clean case with an unrelated record in the shared reviews home (cleanup passes and leaves that record unchanged while the run owns none), ambiguous identity and run-owned artifact preservation, and unchanged ordinary plan closeout.
- Given a green origin probe and a reachable commit matching every expectation, verify the backlog row and prompt entry close with the existing deletion and receipt evidence before claim, freeze, or worktree creation; when closure is refused, preserve both records and continue with an independent target. Given incomplete or ambiguous evidence, verify authoring continues without a refusal or user question.
- Verify the existing open-plan covered-or-gone pre-provision ordering remains intact.

**Out of scope; reject unless plan-related:**
- A new standalone cleanup tool, global sweep, registry, ledger, persistent schema field, or authoring stop gate.
- Changes to unrelated plan-review, scheduling, or worktree lifecycle behavior.
- Weakening the normal gate-removal charter, artifact, ownership, or branch checks.

## Validation Commands

    python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-28-plan-authoring-stand-down-before-charter.md
    python3 scripts/plan_readiness.py docs/history/plans/2026-10-28-plan-authoring-stand-down-before-charter.md
    python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-10-28-plan-authoring-stand-down-before-charter.md --repo-root .
    BASE="$(git merge-base HEAD main)"
    python3 scripts/check_prompt_log_origins.py --prune-audit --base "$BASE"

After implementation, run the repository-configured test suite for the closeout helper and the public-hygiene scan over every changed file. Confirm the scenario matrix in this plan against source behavior and the final gate output.

### Task 1: Add the no-charter case to the existing closeout gate

Context surface: Terms, Gist & Examples, Outcome, and Standing constraints.

Files:
- scripts/worktree_closeout_migrate.py

Primary class anchors:
- `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py`

Primary behavior anchors: cmd_gate_removal, the current plan-file refusal, the authoring claim and frozen PLAN-PROMPTS entry, the done-run manifest's owned plan and start_commit, and the current exact branch and artifact checks.

- [x] Enter the no-charter arm only when an explicit authoring-claim operand is supplied in worktree mode and the expected plan file is absent; validate claim session and origin, frozen prompt binding, and done-run manifest identity (`owned_plan_paths` and `start_commit`) before any plan-specific check is skipped [class: IMPLEMENTATION_REQUIRED]
- [x] For that arm only, bypass plan-header citation parsing and the ordinary empty-owned-set refusal; accept zero owned review records only when manifest ownership and actual run artifacts both prove the run owns none, and refuse with preservation if any review record owned by this run or any unaccounted run-owned artifact exists [class: IMPLEMENTATION_REQUIRED]
- [x] Keep target/worktree operands, exact branch and ref identity, clean-worktree checks, owned-artifact accounting, and branch closeout checks common to both arms; preserve every ordinary-plan gate-removal check unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Derive the expected plan, worktree, and branch from the frozen entry, claim file stem, and existing placement rule; permit cleanup only when the done-run manifest names that plan, the branch remains at `start_commit`, the worktree is clean, and no unaccounted owned artifact exists [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the worktree and branch with a specific refusal when any identity or artifact evidence is missing, changed, or ambiguous [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: scripts: support verified no-charter authoring cleanup [class: IMPLEMENTATION_REQUIRED]

### Task 2: Close already-landed origins before authoring setup

Context surface: Terms, Gist & Examples, Outcome, and Standing constraints.

Files:
- agents/skills/maintenance/decisions.md
- docs/history/backlog/PLAN-PROMPTS.md

- [x] Re-run the origin's own probe before creating claim, frozen prompt entry, or worktree; short-circuit only when it is green and a reachable implementation commit matches every stated expectation [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the existing `Prune rule` and `Coverage and removal rule` with one pre-provision source-history close-as-covered class: the origin probe reruns green against current source, each explicit expectation matches, and a reachable implementing commit witnesses those expectations; for full removal, the existing `PLAN-PROMPTS-PRUNE: <slug> -> <implementing-commit>` receipt names that commit and the existing prune audit remains in force [class: IMPLEMENTATION_REQUIRED]
- [x] For that exact already-landed case, delete the satisfied backlog row and prompt entry in one targeted close-as-covered commit, adding the existing `PLAN-PROMPTS-PRUNE` receipt that names the implementing commit; verify the existing deletion and prune-audit checks accept the evidence [class: IMPLEMENTATION_REQUIRED]
- [x] If the close-as-covered write is refused, preserve both records and continue selection with an independent eligible target; incomplete or ambiguous probe/history evidence keeps the origin eligible for authoring without a question [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: maintenance: close already-landed origins before authoring [class: IMPLEMENTATION_REQUIRED]

### Task 3: Route post-provision stand-downs through the existing closeout

Context surface: Terms, Gist & Examples, Outcome, and Standing constraints.

Files:
- agents/skills/plans/SKILL.md
- agents/skills/maintenance/template-authoring.md

- [x] Keep the existing covered-or-gone pre-provision check ahead of the Task 2 actionability disposition, claim, prompt freeze, and worktree creation [class: IMPLEMENTATION_REQUIRED]
- [x] Route a stand-down after provisioning and before the first plan write through the new evidence-bound gate-removal case and the existing done branch-closeout sequence; after the same claim, frozen-prompt, and manifest identity checks pass, run `owned-files-clean` without `--expect-plan` for this no-charter arm, retaining its clean-worktree and artifact-accounting checks [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the ordinary chartered closeout on its existing `owned-files-clean --expect-plan` path; preserve resources on any no-charter identity, clean-worktree, or artifact-accounting refusal [class: IMPLEMENTATION_REQUIRED]
- [x] On cleanup refusal, preserve the resources, record the reason through the existing authoring outcome path, remove the claim only when its existing ownership rule allows it, and continue with an independent eligible target without asking the user to repeat authorization [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the no-charter scenarios from the Review Scope, run plan readiness, origin coverage, prompt-log prune audit, and public hygiene [class: REPOSITORY_TEST]
- [x] Commit: plans: route post-provision stand-down through verified closeout [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-26-plan-authoring-stand-down-before-charter.md` covered: the no-charter gate-removal arm (Task 1), the pre-provision origin close (Task 2), and the stand-down routing text (Task 3) all landed; status: covered (docs/history/plans/completed/2026-10-28-plan-authoring-stand-down-before-charter.md).
