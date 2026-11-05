# Plan: agent resource cleanup disposition

Executed: yes (57c2b2158713d884e66155fb1c274b5e0860047a)

Backlog origins (scope of record):
- docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md
- docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md
Driving force: efficiency (primary), simplicity (secondary)
Plan review record: the staging series {reviews_dir}/2026-11-04-plan-review-agent-resource-cleanup-disposition-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1.25h
Authoring claim: agent-resource-cleanup-disposition.md (session sess_2ef2f7d4-cfc2-4dac-8d4b-fde95273bf35)

## Terms

- Authored delta: the content a branch's own commits introduced, measured from the branch's recorded start commit rather than a current merge base.
- Base drift: destination-history change after a branch's landing that makes the current merge base differ from the branch's start, injecting inherited path differences into any merge-base diff.
- Branch-only retry: a closeout adjudication of a branch whose worktree is already removed.
- Disposition: the one terminal outcome recorded per in-scope resource: verified removal, named retention (owner plus exact unmerged work), or continuation through the owning authorized closeout.
- In-scope resource: a worktree registration or local branch ref named by, or plausibly owned by, the cleanup request being answered.
- Completion claim: the response sentence asserting the request is complete; valid only when it enumerates the inventory and matches the per-resource dispositions.
- Owner handoff: binding a resource to its originating run or claim record (execution claim, authoring claim, done run manifest) to decide who may dispose of it.
- Recorded start commit: the base commit a run recorded when its branch was created (execution claim, authoring claim, or the closeout migration manifest's branch record as Task 1 extends it), used as the authored-delta base.
- Landing identity: the landing commit's object id and touched path set, recorded by Task 1 in the closeout migration manifest's branch record so the proof reads recorded evidence when the landing commit is unreachable from the destination tip.
- Migration manifest: the closeout manifest recording a run's branch record, start commit, and owned paths for the gate's adjudication.

## Why

A cleanup request lost resources across turns: the assistant removed two branch refs, stopped at a partial result, and implied completion, so the operator had to ask again. The same cleanup witnessed the closeout gate retaining a completed branch because destination history drifted past its landing. No shared contract defines what a complete cleanup response must contain, and the branch closeout proof judges authored content through a drift-prone base.

## Gist & Examples

TLDR: every cleanup response inventories, binds, and dispositions each resource before claiming completion, and the branch closeout gate judges a branch's authored delta from its recorded start commit, because partial results and drift-masked landings cost operator rework and strand completed branches.

Before (today), on a "clean up the worktrees and branches" request: the assistant deletes two quota branch refs, sees two registered worktrees remaining, classifies them as workflow-managed from a prior summary's caution, and stops. The operator asks again; a fresh inventory shows the remaining branches carry unmerged commits and one authoring branch advanced during the exchange. Separately, a completed plan's execution branch survives its own closeout with "branch content outside the landing's file set: README.md", because the landing commit fell out of the default branch's ancestry and the merge-base diff inherited later destination edits as branch content.

After (this plan), the same request produces one disposition per resource before any completion claim: each worktree and branch is bound to its run or claim record, compared against the base, and answered as verified removal, named retention (owner plus exact unmerged work), or continuation through its owning closeout; the completion claim enumerates that inventory. A completed branch whose tip tree matches its recorded landing, judged from its recorded start commit, deletes through the normal gate; a branch with any unproven authored delta still retains exactly as today.

Edge cases: a branch whose start commit is unrecorded keeps today's retain-and-report behavior (the fallback is retention, never guessed ancestry); a live foreign claim or active worktree retains regardless of the request's breadth; an unmerged authored delta never deletes on a broad request whose discard intent is not explicit, and the response names the specific decision required; a branch-only retry after worktree removal reads the primary-slug manifest identity so the strand's evidence survives the removal.

## Outcome

A cleanup request ends with every in-scope resource dispositioned and a completion claim that matches the inventory, and a completed branch whose landing is masked by base history deletes through the normal closeout instead of stranding.

- A cleanup response ends with a per-resource disposition list and a completion claim that enumerates it.
- A completed branch masked by destination drift deletes through the normal closeout gate.
- A branch-only retry keeps its strand's evidence after the worktree is removed.
- Gate delta: none (no gate, validator, lock, ledger, or fence added or removed; the existing branch-accounting guard's base-drift false-positive arm is narrowed in the same change, retiring that false-positive shape; the closeout migration manifest's existing branch record gains landing-identity and start-commit fields as evidence persistence on an existing append-only surface, per the Machinery admission protocol's demotion clause).

## Assumptions

- assume the disposition contract lives in `agents/skills/self-heal/SKILL.md` as a new section beside Recovery; basis: the origin row names self-heal Recovery 1-4 as the carrying surface and the contract is disposition-shaped (self-heal's domain), while the done and execute-plan surfaces are run-scoped; the simpler-design comparison rejected a runtime evidence adaptor (no witnessed runtime-specific lookup need; the git inventory is portable, per the completed Codex task-resource investigation) and a standalone cleanup skill (no unique workflow logic beyond the contract; the skill merge rule prices cross-skill duplication).
- assume origin 2 resolves as the narrowing fix, not guard removal; basis: the guard is witnessed protective (the closeout-accounting plan's catches) and the row's own option comparison prices removal as the riskiest shape; the narrowing retires only the base-drift false-positive arm and preserves retention for any unproven authored delta, satisfying the Machinery admission protocol's demotion clause without a removals row.
- assume branch-only retry evidence persists at the primary slug home; basis: the execution strand's manifest already survives there and the authoring strand's manifest loss is the witnessed recovery cost.
- assume the cleanup rehearsal never deletes peer or foreign resources; basis: this plan's Review Scope restricts removals to fixture-created resources, and the owner contract's retention rules preserve active-owner and unmerged work (docs/history/plans/completed/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md).

Decision points requiring a grill: none remain (all resolved by recorded receipt under the maintenance-selected standing authorization).
Scope extensions (grilled): none proposed.
Sources inspected: not a tracker-linked request.

## Standing constraints

- Runtime neutrality: shared skill text carries no agent-specific lookup details; any runtime-specific evidence lookup stays in that runtime's own overlay or adapter files.
- Machinery admission protocol: any blocking-rule change names its incident, expected catch, false-positive cost, and what existing blocker it retires or simplifies; this plan narrows an existing guard and adds none.
- Preserve verbatim: all current artifact-transfer, active-owner, and unmerged-work retention protections keep their behavior; the plan changes only how base drift is excluded from the authored-delta proof and where branch-only evidence persists.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the drifted-base completed-branch fixture deletes through the gate and an unlanded-delta branch retains, both pinned by failing-then-passing tests
- compatibility: a branch with no recorded start commit and no exact-tree landing proof keeps today's retain-and-report verdict
- maintainability: the contract is one section with integration pointers; the disposition vocabulary appears once, never duplicated across skills

**Done when:**
- the new tests pass and the full closeout-migrate gate test suite passes
- the contract section exists with the per-resource disposition vocabulary and the completion-claim rule, and the three integration pointers resolve
- the hygiene scan and the pins suite exit 0

**Ship when:**
- none stated (repository-verifiable work only)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/worktree_closeout_migrate.py` (Task 1)

**Docs:**
- `agents/skills/self-heal/SKILL.md` (Task 2)
- `agents/skills/done/SKILL.md` (Task 2)
- `agents/skills/execute-plan/SKILL.md` (Task 2)
- `agents/skills/plans/SKILL.md` (Task 2)
- `docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md` (Task 3; coverage flip rides the landing)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` (Task 1, Task 3) *(new or extended; selected at execution from repository evidence)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/doing-code-review/SKILL.md`; reason: the panel of record is plan-route only
- any cleanup execution against live worktrees or branches outside task fixtures; reason: the origin entry forbids executing cleanup during authoring, and only fixture-created resources may be removed

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q
python3 scripts/machinery_inventory.py --check
bash scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
```

### Task 1: Branch closeout base-drift narrowing and branch-only evidence persistence

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py` *(new or extended)*

Primary class anchors:
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`
- `_branch_landing_content_scope` in `scripts/worktree_closeout_migrate.py`

- [x] RED fixture for the drifted-base false positive: given a completed-plan branch whose tip tree equals its recorded landing commit's tree, with the landing commit unreachable from the current destination tip and the landing identity recorded in the closeout migration manifest, expects the closeout adjudication to authorize deletion with no retention [class: REPOSITORY_TEST]
- [x] RED fixture for the guard direction: given a branch whose authored delta from its recorded start commit contains a path absent at the destination, expects retention with the unaccounted reason [class: REPOSITORY_TEST]
- [x] RED fixture for the fallback: given a branch with no recorded start commit and no exact-tree landing proof, expects today's retain-and-report verdict [class: REPOSITORY_TEST]
- [x] RED fixture for branch-only evidence: given a removed authoring worktree, expects the branch-only retry to read the strand's identity row from the primary slug home's migration manifest [class: REPOSITORY_TEST]
- [x] Implement the landing-identity record: at closeout transfer time the closeout migration manifest's branch record gains the landing commit's object id and touched path set, so the proof reads recorded evidence instead of walking only destination-reachable history [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the authored-delta proof: judge the branch's changed paths from its recorded start commit instead of the current merge base, so inherited base drift never enters the content scope [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the landing-aware landing proof: when the recorded landing commit is unreachable from the destination tip, match its recorded tree and touched set and require the branch's authored delta present at the destination before authorizing any deletion, so a destination rewrite that dropped the landed content still retains the branch [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the authoring-strand manifest binding: the authoring closeout appends its strand's branch identity row to the primary slug home's existing migration manifest the execution strand already uses, so a removed worktree's branch-only retry reads that manifest and no second evidence surface is created [class: IMPLEMENTATION_REQUIRED]
- [x] Run the new fixtures, then the full closeout-migrate gate suite, expects GREEN with no sibling regression [class: REPOSITORY_TEST]
- [x] Commit: `fix: judge branch closeout authored delta from recorded start commit` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Resource cleanup disposition contract in self-heal with integration pointers

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/self-heal/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`

Primary class anchors:
- `## Resource cleanup disposition` in `agents/skills/self-heal/SKILL.md`

- [x] The contract section defines the per-resource disposition vocabulary (verified removal, named retention with owner and exact unmerged work, continuation through the owning authorized closeout) and the rule that a completion claim is valid only when it matches the full inventory [class: IMPLEMENTATION_REQUIRED]
- [x] The contract section binds the cleanup handoff to the existing Recovery terminal-condition duty by pointer, never restating it [class: IMPLEMENTATION_REQUIRED]
- [x] The contract section names the runtime-neutral inventory sources (worktree list, branch ancestry, run and claim records) and forbids a new inventory surface [class: IMPLEMENTATION_REQUIRED]
- [x] One-line integration pointers from the done worktree-removal report, the execute-plan worktree closeout, and the plans landing handoff name the contract section without duplicating its vocabulary [class: IMPLEMENTATION_REQUIRED]
- [x] Run the hygiene scan and the pins suite, expects exit 0 on both [class: REPOSITORY_TEST]
- [x] Commit: `docs: add resource cleanup disposition contract to self-heal` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Acceptance rehearsal of the multi-resource disposition contract

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_worktree_closeout_migrate.py` *(rehearsal fixture test added here)*
- `docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md` *(coverage flip rides the landing)*

Primary class anchors:
- `## Resource cleanup disposition` in `agents/skills/self-heal/SKILL.md`
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`

- [x] Rehearsal fixture test recorded in the Task 1 test file: given a temporary repository holding a landed branch, an unmerged branch, and an active foreign worktree, expects the disposition steps to produce one verified outcome per resource and the completion claim inventory to match [class: REPOSITORY_TEST]
- [x] The rehearsal preserves every foreign or active resource and removes only fixture-created resources [class: REPOSITORY_TEST]
- [x] Commit: `test: rehearse multi-resource cleanup disposition contract` [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md: covered by this plan's Tasks 1-2 (disposition contract + base-drift closeout narrowing); origin row flipped covered by the execution landing.
- docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md: covered by Task 1 (the base-drift false-positive arm narrowed; recorded-start authored-delta judgment); origin row flipped covered by the execution landing.
- docs/history/backlog/2026-11-05-agent-resource-cleanup-pin-coverage-residuals.md: created by this run as the durable residual home (items 1-18); stays open by design.
