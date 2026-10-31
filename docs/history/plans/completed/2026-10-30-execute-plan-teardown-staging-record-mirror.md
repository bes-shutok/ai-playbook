# Plan: Execute Plan Teardown Record Mirroring

Backlog origin: docs/history/backlog/2026-10-30-execute-plan-teardown-staging-record-mirror.md
Driving force: reliability
Authoring claim: docs/tmp/authoring-claims/2026-10-30-execute-plan-teardown-staging-record-mirror.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)
Plan review record: the staging series .ai-playbook/reviews/2026-10-30-plan-review-execute-plan-teardown-staging-record-mirror-pbe9afa5d-r*.md
Execution budget: 2.0h total, largest task 1.0h

## Terms

- **Boundary mirror:** the existing operation that copies a run's named artifacts from its worktree to the primary checkout and records a receipt.
- **Closeout migration manifest:** the existing JSON file that records verified artifact destinations and source branch identity during final transfer.
- **Review seal:** the record in the `review-certs` home that binds a review round to the bytes it certified.
- **Plans-egress pointer:** the per-round Phase 4 record written before archive, named `<date>-plan-review-<slug>-exec-r<N>.md`.

## Why

A worktree can hold the only copies of a run's review record pairs, seal entries, and Phase 4 plans-egress pointers. Removing it before those files are mirrored and verified can erase evidence after a successful landing.

## Gist & Examples

TLDR: mirror each run's review evidence before teardown, improving reliability without adding another gate.

Before: a boundary mirror names session logs only, and a later teardown can reach branch removal without the migration manifest that records the review files.

After: the run names each newly produced review document, `.stats.json` sidecar, seal entry, and Phase 4 plans-egress pointer in the existing mirror flow; closeout migration records successful mirror receipts as verified destinations even when the primary copy is already byte-identical; the existing removal gate checks those destinations before teardown.

Edge cases: when a manifest-listed artifact is absent or the gate outcome is not pass, keep the worktree and branch intact.

## Outcome

Every review artifact produced by a worktree run is preserved in the primary checkout before the run removes its worktree or source branch.

- The existing mirror flow carries each run-produced review staging document, its `.stats.json` sidecar, its seal entry, and the Phase 4 plans-egress pointer by exact path.
- Closeout migration carries successful per-run mirror receipts into its existing verified `migrated` destinations, including when the primary copy already has identical bytes; the existing removal gate checks those destinations before teardown.
- A refused or indeterminate gate leaves the worktree and source branch available for recovery.

Gate delta: no new gate, refusal class, or fence. The existing `gate-removal` predicate stays unchanged; closeout migration repairs its existing `migrated` inventory by recording successful same-run mirror receipts as verified destinations instead of marking byte-identical copies `skipped`. Witness: the 2026-10-30 record loss in the backlog origin's Evidence section, where a clean review record pair, seal entry, and plans-egress pointer were deleted with the worktree. Expected catch: a run-produced artifact that is mirrored and then missing or unverified at teardown. False-positive cost: retain the worktree and branch until the named artifact is restored. Review date: 2027-01-30. The guard-liveness ledger has no dedicated closeout row; its current repo-wide tally is 29 catches to 48 incidents (`scripts/gate_liveness_ledger.py show`). The simplification is using exact successful paths already captured by mirror receipts and migration in place of an unverified caller-maintained record list.

## Assumptions

- The branch-closeout arm already checks destinations recorded under `migrated` and `renamed`, but the baseline migration currently records byte-identical mirror targets as `skipped`, which the gate excludes; basis: `scripts/worktree_closeout_migrate.py` `_resolve_closeout_reference_state`, `_gate_branch_closeout`, and the baseline `cmd_migrate` path.
- The boundary-mirror helper takes explicit `--mirror-path` operands; its caller owns the per-run path set, including Phase 4's plans-egress pointer after its final write; basis: `cmd_boundary_mirror`, its CLI parser, and `agents/skills/execute-plan/SKILL.md` Phase 4.
- The Phase 5 worktree and branch remain available until the final migration and removal checks pass; basis: the existing Worktree-first standard's refusal-retention rule.
- Broader docs/tmp retention policy and unrelated closeout machinery are outside this origin; disposition: omit-extension under the maintenance-selected arm.

Decision points requiring a grill: none remain: add exact run-produced review paths at their producer call sites rather than copying the reviews directory (backlog origin and `boundary-mirror` parser, Task 1); have closeout migration carry successful receipt-backed paths into the existing verified-destination list, including byte-identical targets, then pass that manifest to `gate-removal` before deletion (migration implementation and gate CLI, Tasks 2-3); retain the existing manifest and removal gate without adding a schema field or separate ledger (Tasks 2-3).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the migration manifest names run-produced review documents, sidecars, seal entries, and plans-egress pointers from successful mirror receipts, including byte-identical destinations, and the removal gate observes their primary-home presence.
- safety: a missing destination or a refused gate preserves the source worktree and branch.
- simplicity: no whole-directory copy, second gate, new state field, or separate record ledger.

**Done when:** the closeout regression fixture passes for both a complete record set and a missing primary-home artifact, and the existing worktree-closeout suite passes.

**Ship when:** none.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (Task 1)
- `agents/skills/execute-plan/SKILL.md` (Task 2)
- `agents/skills/execute-plan/worktree-first.md` (Task 2)
- `scripts/worktree_closeout_migrate.py` (Task 2)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above when the causal link to this plan is clear. A weak or speculative link is out of scope.

**Out of scope; reject unless plan-related:**
- `scripts/machinery_registry.json`; reason: the existing removal gate and manifest schema stay in place; this plan does not add a gate or a new machinery row.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q
```

### Task 1: Mirror every run-produced review artifact

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/execute-plan/SKILL.md`

Primary class anchors:
- `cmd_boundary_mirror` in `scripts/worktree_closeout_migrate.py`, which installs and receipts each explicit mirror path.

Evidence:
- The boundary-mirror helper accepts an exact, repeatable `--mirror-path` list.
- The current Phase 3 and Phase 4 instructions do not require the run-produced review files and seals to be included in that list.

- [x] Update the execute-plan record-mirror instructions so each run-produced review staging document, its `.stats.json` sidecar, and seal entry are named in the existing per-run mirror inputs at the producing review boundary, and the Phase 4 plans-egress pointer is mirrored after its final write. Given a review round that creates these four path classes, expects all exact paths to be mirrored and receipted; no whole-directory copy is introduced. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the existing mirror receipt and failure behavior. Given a mirror refusal or partial copy, expects the run to retain and report the source artifacts for final closeout recovery. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: mirror execute-plan review records before teardown` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Require migration-backed removal

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`
- `scripts/worktree_closeout_migrate.py`

Primary class anchors:
- `cmd_migrate` in `scripts/worktree_closeout_migrate.py`, which writes verified transfer destinations to the migration manifest.
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`, which checks the manifest's verified destinations before teardown.

Evidence:
- The baseline migration currently records byte-identical boundary-mirror targets as `skipped`; `_resolve_closeout_reference_state` collects only verified `migrated` and `renamed` destinations.
- `gate-removal` accepts the exact migration manifest and checks each collected destination before reporting its branch disposition.

- [x] Update the Phase 5 recipe to complete migration, then invoke `gate-removal` with the exact run's `closeout-migration.json` while the source worktree is still registered. Given every receipt-backed review path has a verified migration entry and remains at the primary home, expects the manifest-backed gate to pass before the removal command; no branch-only invocation without an explicit manifest remains. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the existing refusal class and gate code while making baseline migration record each successful receipt-backed review path under `migrated`, even when source and primary bytes are identical. Given a successful mirror receipt and identical source/target files, expects a verified `migrated` row without rewriting the primary file; a missing or unverified transfer must not produce that row. [class: IMPLEMENTATION_REQUIRED]
- [x] Make worktree and branch removal conditional on the gate's `OUTCOME: pass`; a fail, indeterminate, tool error, or missing outcome keeps both resources and reports the gate evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep branch accounting, exact-OID binding, and existing migration digest verification unchanged. Given an unrelated or peer worktree, expects the closeout to leave it untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: gate execute-plan teardown on migrated records` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Pin the record-preservation contract

Context surface: the plan's Terms and this task.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `WorktreeCloseoutTest` in `scripts/test_worktree_closeout_migrate.py`, which owns migration fixtures.
- `GateRemovalTest` in `scripts/test_worktree_closeout_migrate.py`, which owns removal-gate fixtures.
- `_resolve_closeout_reference_state` in `scripts/worktree_closeout_migrate.py`, which selects manifest destinations for the gate.

- [x] Add a complete end-to-end fixture with a review document, matching `.stats.json`, seal entry, and plans-egress pointer. Given those four exact paths in the boundary-mirror operands, expects verified receipts, then verified migration destinations even when the primary copies are byte-identical, and a passing `gate-removal` result while every destination exists. [class: REPOSITORY_TEST]
- [x] Add the missing-primary-artifact control after migration for each of the four path classes. Given one mirrored destination removed from the primary home, expects `gate-removal` to refuse with that path named while the source worktree and branch remain registered. [class: REPOSITORY_TEST]
- [x] Pin caller path completeness: the fixture's document, sidecar, seal, and plans-egress pointer operands match the four path classes required by Task 1; no whole-directory copy is used. [class: REPOSITORY_TEST]
- [x] Keep existing branch identity, digest, and unrelated-worktree fixtures unchanged and green. [class: REPOSITORY_TEST]
- [x] Run the Validation Commands battery and commit: `test: cover execute-plan teardown record retention` [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-30-execute-plan-teardown-staging-record-mirror.md: covered by this plan (deleted from the living backlog at the landing; its Evidence section is the gate-delta witness cited in the Outcome).
