# Plan: Empty-diff no-op closeout route for already-landed authoring branches

Backlog origins (scope of record):
- docs/history/backlog/2026-10-31-plan-empty-diff-closeout-route.md
- docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md

Required agent type: none (runtime-neutral)

Driving force: simplicity (primary), efficiency (secondary)
Plan review record: the staging series .ai-playbook/reviews/2026-11-03-plan-review-empty-diff-closeout-route-p39cc91ef-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.25h total, largest task 1.0h

## Terms

- landing handoff: the plans Final Step paragraph that calls `land_squash.sh land-worktree` once under the merge landing lock.
- empty-diff refusal: the landing helper's refusal when the candidate commit's tree is identical to its parent tree, so there is no change to land.
- empty-diff no-op arm: the fail-closed skill-text arm added by this plan that routes an empty-diff refusal to the existing gate-removal proofs instead of stranding the worktree.
- gate-removal: `scripts/worktree_closeout_migrate.py gate-removal`, the existing removal gate whose `branch-closeout` verdicts `ancestry-accounted` and `exact-tree-accounted` prove content and artifacts at the destination (`retained` reports the branch-authored delta still absent and, under clean guards, retains only the branch ref while the printed worktree removal stands).
- exact-tree proof: the gate's verdict that the branch tip's complete tree equals a destination-history commit's tree without ancestry.
- superseded draft: authoring branch bytes (for example a stale plan draft) that differ from what landed but are preserved at the destination before removal.
- branch-only terminal state: the sibling origin's separate defect (branch-only `unknown-ref` recovery and its completion signal); explicitly out of scope here.

## Why

When an authoring branch is already fully represented at the destination, the landing helper correctly refuses an empty-diff landing, but the plans Final Step gives no route from that refusal to the existing gate-removal proofs, so a completed worktree, branch, and claim are stranded until operator recovery (witnessed 2026-10-31 and again 2026-11-01). The proof machinery already exists; only the workflow's route text is missing.

## Gist & Examples

TLDR: a fail-closed no-op route in the plans Final Step routes an empty-diff landing refusal to the existing gate-removal ancestry and exact-tree proofs, for simplicity and efficiency.

Today: the Final Step's landing handoff says a landing refusal retains the worktree, branch, and claim, with no exception when nothing is left to land. After: the closeout may proceed through the existing `gate-removal` verdicts when the branch is proven fully represented at the destination; every other refusal keeps today's retention unchanged.

Example: an authoring branch whose plan and closeout rider commits already landed fast-forwards to the current base; the helper refuses (tree-identical candidate); the closeout runs the gate, reads `ancestry-accounted`, verifies artifacts, and removes the worktree and branch through the existing sanctioned sequence. A non-ancestor branch carrying a superseded draft preserves the draft bytes at their destination and removes the draft from the branch first; the helper then refuses with the tree-identical candidate, and the gate reads `exact-tree-accounted` for the now-clean tip tree.

## Outcome

A completed authoring worktree whose branch is already fully landed closes out without operator recovery.

- The empty-diff refusal gains a bounded, evidence-gated route to removal instead of stranding the worktree, branch, and claim.
- Every other landing refusal keeps the existing retention unchanged, including the reachable-source presentation (the Landing-op uniqueness rule's refusal), which this plan records as out of scope by decision, not by omission.
- No new validator, ledger, retry loop, or deletion authority is added.

Gate delta: none (no refusal classes, gates, fences, protocol layers, or schema fields added or removed; the route reuses the existing gate-removal proofs; the branch-only terminal-state origin stays open as its own row).

## Assumptions

- assume the empty-diff refusal is recognizable from the helper's output (the origin evidence quotes the tree-identical candidate condition); basis: docs/history/backlog/2026-10-31-plan-empty-diff-closeout-route.md Evidence section, witnessed 2026-10-31 and 2026-11-01.
- assume the route belongs in skill text, not in a script; basis: the gate already implements every proof (`scripts/worktree_closeout_migrate.py` gate-removal content accounting, `ancestry-accounted` / `exact-tree-accounted` dispositions), and the origin's machinery admission forbids new validators or ledgers.
- assume the sibling branch-only terminal-state origin stays a separate plan; basis: the entry's scope arm and the origin's own narrowing history (r11 finding deferred out of the worktree-mode plan); no concrete contract dependency between it and the empty-diff route exists in either origin body.

Decision points requiring a grill: coordinated-vs-separate scope for the sibling origin - separate (best-supported in-scope option: the sibling's manifest-retention schema question has no dependency on the empty-diff route; source: both origin bodies and the entry's scope arms, 2026-11-02, affected sections: Assumptions, Review Scope)

## Standing constraints

- No validator, ledger, retry loop, or new deletion authority may be added (origin machinery admission, docs/history/backlog/2026-10-31-plan-empty-diff-closeout-route.md).
- The existing exact-tree, ancestry, and artifact checks stay authoritative; this plan never weakens them or the retention rule for any other landing refusal.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the arm fires only when the landing refusal is the empty-diff class and the gate's identity, tree, and artifact checks all pass; any unverified item retains the worktree.
- simplicity: the change is skill text plus a cross-reference; no code path in `scripts/land_squash.sh` or `scripts/worktree_closeout_migrate.py` changes.
- safety: a retained unlanded delta never routes to removal; the superseded-draft conservation arm preserves bytes before any non-ancestor branch removal.

**Done when:**
- the plans Final Step landing handoff names the empty-diff no-op arm with its condition, its required proofs, and its retention boundary, and the execute-plan Worktree-first landing step points at the same arm.
- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-02-empty-diff-closeout-route.md --pre-round` exits 0.

**Ship when:**
- none (repository-verifiable only).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (Task 1) *(new wording in the Final Step landing handoff; all other sections frozen)*
- `agents/skills/execute-plan/worktree-first.md` (Task 2) *(new pointer sentence only; all other content frozen)*

**Tests:**
- none (documentation-only plan; repository verification is the readiness and gates commands below)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh`; reason: the helper's empty-diff refusal is correct and unchanged by this plan
- `scripts/worktree_closeout_migrate.py`; reason: the gate's verdicts are the authoritative proofs this plan reuses, never edits
- `docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md` implementation; reason: the sibling origin's terminal-state design is a separate plan (see Assumptions)
- `agents/skills/done/SKILL.md` beyond the existing citation; reason: the Operator branch closeout sequence already sanctions the removal path this plan routes to

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-11-02-empty-diff-closeout-route.md --pre-round
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files
```

### Task 1: add the empty-diff no-op arm to the plans Final Step

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`

- [x] The Landing handoff paragraph gains the empty-diff no-op arm directly after the existing refusal-retention sentence; the arm's trigger is the landing helper's tree-identical-candidate refusal (the empty-diff class), and the arm applies only to an authoring closeout whose branch is already fully represented at the destination. [class: IMPLEMENTATION_REQUIRED]
- [x] The arm orders the superseded-draft conservation before the landing attempt for a non-ancestor branch carrying a draft: preservation writes and digest-verifies the draft bytes at their destination home (the manual-delta-carry remedy's digest-verify shape), and the orchestrator composes the draft-removal commit on the session's own authoring branch (never a base-branch amend). [class: IMPLEMENTATION_REQUIRED]
- [x] The arm orders: the owned-files-clean preflight after the draft-removal mutation as the cleanliness check, then the gate-removal invocation with the migration-manifest operand, then removal only on `OUTCOME: pass`, then the done skill's sanctioned branch-closeout sequence - the gate's content-accounting verdict substituting for the landed-branch precondition that cannot hold on this route. [class: IMPLEMENTATION_REQUIRED]
- [x] The arm names the preflight's operand shape for this route: it runs without the `--expect-plan` plan-transfer leg (the no-charter arm's precedent, because no plan file exists to transfer on this route - the plan's bytes are already at their archived primary home), keeping the clean-worktree check as the cleanliness check. [class: IMPLEMENTATION_REQUIRED]
- [x] The arm carries the conservation safety witness: given a non-ancestor authoring branch whose tip carries a superseded draft and a tree-identical refusal after the draft-removal commit, expects the draft bytes digest-verified at their destination home before any branch mutation and the removal chain (preflight, gate-removal, `OUTCOME: pass`) to run only after that commit. [class: IMPLEMENTATION_REQUIRED]
- [x] The arm's verdict gate: removal proceeds only on `ancestry-accounted` or `exact-tree-accounted` with the gate's identity and artifact checks passed; a gate outcome of fail or held (identity refusal, unknown-ref, ref-changed, or a guard-failed retained) keeps the worktree, branch, and claim standing unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] The arm states the retained-verdict semantics it relies on: a retained verdict under a passing gate retains only the branch ref (the delta stays safe in the ref) while the worktree removal follows the printed pass, matching the gate's outcome mapping and the Worktree-first standard's Terminal closeout ownership clause. [class: IMPLEMENTATION_REQUIRED]
- [x] The arm declares the receipt precedence over the Worktree-first landing step's stop-for-adjudication clause, scoped to the authoring-closeout class: on this route the gate's verdict and proven OID are the receipt of record, replacing the content-bearing-commit receipt the step-4 clause otherwise records. [class: IMPLEMENTATION_REQUIRED]
- [x] The arm cites the superseded-draft recovery shape by its true home, the first origin's Evidence second witness (2026-11-01 bullet), and adds no second verdict, ledger, or validator; given the landing refusal text, expects the closeout to name the gate invocation it ran and the verdict it read. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect pass: the Validation Commands above over the edited file. [class: REPOSITORY_TEST]
- [x] Commit: `plans: add empty-diff no-op closeout route to the Final Step`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: point the Worktree-first landing step at the arm

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/worktree-first.md`

- [x] The landing lifecycle step 4's stop-for-adjudication empty-diff clause gains one authoring-closeout-scoped pointer: on an authoring closeout, the tree-identical refusal follows the plans Final Step's empty-diff no-op arm, whose gate verdict and proven OID are the receipt of record, instead of the stop-and-record disposition; given a tree-identical refusal in an authoring closeout, expects the executor to consult the plans arm. [class: IMPLEMENTATION_REQUIRED]
- [x] The pointer adds no duplicate condition text: it names the plans arm and defers to it; no second copy of the condition or proofs appears in this file. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect pass: `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0 over the added lines. [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: point the worktree landing step at the plans empty-diff no-op arm`. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-31-plan-empty-diff-closeout-route.md`: covered by this plan (Tasks 1-2 executed and landed; code-review r2 certifying clean). Deleted in this completion pass per the Plan Lifecycle.
- `docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md`: stays open as its own row (explicitly out of scope by this plan's Assumptions; sibling branch-only terminal-state design).

## Origins dispositions

- `docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md` stays open at the backlog top level by recorded decision: the sibling branch-only terminal-state design is a separate plan (this plan's Assumptions; no concrete contract dependency), and this plan's Outcome records the reachable-source presentation out of scope by decision. Precedent: the quota-doctrine landing's deliberately-open origin row.
