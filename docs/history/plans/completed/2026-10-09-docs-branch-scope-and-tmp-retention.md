# Plan: shared docs-branch archive and tmp retention
Backlog origins (scope of record):
- `docs/history/backlog/2026-10-07-docs-branch-temporal-sync-retention.md`
- `docs/history/backlog/2026-10-08-docs-branch-overlapping-shadow-candidates.md`
- `docs/history/backlog/2026-10-08-docs-branch-sync-persisted-copy.md`
- `docs/history/backlog/2026-10-09-done-docs-branch-sync-overhead.md`
- `docs/history/backlog/2026-10-09-docs-branch-configured-root-safety.md`
Driving force: simplicity
Plan review record: the staging series docs/history/reviews/2026-10-09-plan-review-docs-branch-scope-and-tmp-retention-r*.md
Execution budget: 2.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-09-docs-branch-scope-and-tmp-retention.md (session no-session)

## Terms

- **Docs branch:** the local `docs` branch that stores ignored review and metrics files between working branches.
- **Allowed roots:** fixed `docs/reviews/` plus facts-resolved review/metrics roots under `docs/`; absent keys default to `docs/history/reviews/` and `docs/history/metrics/`.
- **Branch pruning:** removing files from the current `docs` branch tree while keeping prior commits reachable.
- **Expired branch copy:** an allowed archive path whose latest `refs/heads/docs` change is strictly older than the UTC cutoff two calendar months before now, clamping to the target month's last day when needed.
- **Local-source renewal:** an already-present archive with docs-branch history renews an expired branch copy only when its mtime is within the cutoff and its bytes differ from the latest historical docs-branch blob. A recent path with no docs-branch history may be archived based on its local mtime.

## Why

The shared sync copies broad documentation and runtime roots, restores absent branch files, and used separate implementations for two backend modes before this plan consolidated them. That makes each closeout handle unrelated history.

## Gist & Examples

TLDR: keep only recent review and metrics archives, for simplicity.

Before, a sync can copy `.ai-playbook/`, `docs/tmp/`, plans, and other ignored paths to the docs branch, then restore missing branch paths into the checkout. A second sync implementation and persisted copies make it harder to know which code is authoritative.

After, every project preserves only `docs/reviews/`, its validated configured review root, and its validated metrics root, all within `docs/`. For example, a docs-branch-only `docs/tmp/old-log.md` or `.ai-playbook/facts.md` is removed from the branch tree while any local copy stays untouched. A recent metrics record remains available. Branch age is checked before restoring missing local files, so an expired branch copy cannot get a fresh local timestamp from restoration and renew itself. An already-present archive with branch history renews only when its source timestamp is within the two-month window and its bytes differ from the latest historical docs-branch blob. This also prevents a legacy sync restore with a refreshed mtime but unchanged bytes from renewing an expired archive.

## Outcome

Every project's docs branch retains recent review and metrics records while excluded branch content is removed safely.

- Sync copies only review and metrics roots and reports every excluded or pruned branch path, including paths absent from the checkout.
- Allowed branch copies older than two calendar months leave the current tree while earlier branch commits remain reachable; a later sync does not restore an expired branch-only path or re-add an unchanged expired local source, while a recently modified local source is archived again.

Gate delta: remove broad discovery and extraction, duplicate sync bodies, helper resolution, and plans/backlog-only branch guards; check branch age before restore and prune expired copies; add fail-closed root and escaping-link checks because overrides and path-text checks alone cannot prove a path resolves inside the allowed docs root; warning and continuing still permits exposure and pruning; retain review retention, done deferral, and mode safety; add no local deletion or review duty.

## Assumptions

- assume `reviews_dir` and `metrics_dir` are read from each project's facts, with the shared skill's current documented defaults when a key is absent; basis: `agents/skills/docs-branch/SKILL.md`.
- assume local reviews and metrics remain untouched by branch pruning; basis: the confirmed requirements preserve their bytes.
- assume prior docs-branch commits remain reachable after current-tree pruning; basis: the confirmed requirements preserve branch history.
- assume branch age uses the latest commit that changed a path on `refs/heads/docs`, with the latest path-changing commit's committer timestamp and a strict UTC cutoff two calendar months earlier, clamping to the target month's final day; basis: `2026-10-07-docs-branch-temporal-sync-retention.md` and the confirmed requirements.
- assume branch expiry is evaluated from the docs ref before any missing-path restore; an expired branch-only path is pruned without materializing a local copy, and an already-present source with branch history can renew it only when it is recent and differs from the latest historical blob; a recent source with no branch history can seed a new archive; basis: reconciliation after r4 and the existing retained docs history.
- assume generated `graphify-out/` and local runtime configuration remain local; basis: the user's confirmed boundary and their generated or environment-specific role.

Resolved decisions and receipts:
- Apply the allowlist to every project; source: user reply 2026-10-09; affected sections: Outcome and Review Scope.
- Keep generated `graphify-out/` local; source: user accepted the recommended option 2026-10-09; affected sections: Gist and Review Scope.
- Retain branch history and keep local review and metrics files unchanged; source: user confirmation 2026-10-09; affected sections: invariants and tasks.
- Use two-calendar-month pruning for docs-branch copies and preserve all corresponding local checkout sources; source: user confirmation 2026-10-09; affected sections: retention and Design Invariants.
- Keep the shared foreign-checkout `done` gate redesign separate and use an exact-path scoped commit as the immediate workaround; source: user reply 2026-10-09; affected sections: scope boundaries and handoff.

Decision points requiring a grill: none remain.

## Scope extensions (grilled)

- Shared `done` foreign-checkout hard-lock redesign: defer to the separate plan prompt `done-mutual-checkout-scoped-landing`. For the current authorized landing, use a path-scoped commit containing only the reviewed owned paths; do not wait for unrelated checkout changes or alter the shared closeout lock here.

## Standing constraints

- Never push the docs branch.
- Never delete local review or metrics files during branch pruning.
- Keep the existing done merge-lock ordering and explicit availability-checked sync deferral.
- Keep the separate three-month, manifest-gated review-retention lifecycle unchanged; the two-month cutoff applies to the docs branch tree and does not delete local review bytes.
- Do not add a wait on unrelated checkout dirt or change the shared `done` lock contract in this plan; `docs/history/backlog/2026-10-09-done-foreign-checkout-dirt-blocks-scoped-commit.md` remains a separate plan-worthy change, with exact-path scoped commits as the immediate operator-approved workaround.
- For allowed roots, retain add-only restoration unless an explicit deletion or the retention cutoff applies.

## Cleanup scope ledger

- **Base ref:** `3bada1181f398dc96bacf7f5c036149fabe111c5`, the main checkout HEAD after the scoped tmp-cleanup backlog commit and before this plan update.
- **Task-owned paths:** the production and test paths listed under `Review Scope`; these own the shared sync contract, runtime deployment, and maintenance pins.
- **Frozen areas:** all code and docs outside those paths unless a direct call-site or contract search proves the plan requires an update. Metrics production, review staging format, session manifests, lock implementation, `.ai-playbook/facts.md`, `AGENTS.md`, `graphify-out/`, `.claude/`, and `.zcode/` remain unchanged.
- **Pre-existing dirt:** the Time Machine-restored checkout's unrelated tracked changes and deletions were not imported. This main checkout was clean before the scoped tmp-cleanup backlog commit; no implementation changes are present. The prior plan-review artifacts are being transferred by exact path from the continuation worktree.
- **Explicit branch-delete permission:** remove every path outside the allowed roots from the current `refs/heads/docs` tree, regardless of whether a local source exists; prune allowed branch paths older than the cutoff. Keep the branch ref and its earlier commits.
- **Other affected surfaces:** keep the review roots and metrics root; remove all other roots from the docs branch, including tmp, plans, backlog, agent configuration, instructions, `.gitignore`, and generated output; preserve all corresponding local checkout sources; leave local tmp cleanup, closeout migration, locks, review format, and metrics generation unchanged.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: isolated sync fixtures prove only allowed roots remain, old branch copies are pruned, and absent excluded paths are deleted.
- Data integrity: local review and metrics bytes remain identical, and earlier docs-branch commits remain reachable.
- Local data integrity: docs-branch pruning leaves all working-tree files, including tmp and excluded roots, unchanged.
- Retention interaction: a branch copy older than two months stays absent on repeated sync while its unchanged local bytes remain untouched; source edits inside the cutoff are eligible to renew the archive only when bytes differ from the latest historical blob; a fresh mtime alone cannot renew an unchanged legacy-restored copy. The separate manifest-gated three-month review-retention lifecycle remains unchanged.
- Retention ordering: an expired branch-only path missing from the checkout is pruned without restore; a recent branch-only path may be restored; a recent changed-byte edit to an already-present local source may renew an expired branch copy; a recent new path with no branch history may be archived using its mtime.
- Simplicity: one canonical sync implementation replaces broad candidate discovery and duplicated mode bodies without adding a closeout blocker.

**Done when:**
- The shared skill and runtime helper enforce the same allowlist and retention policy in every project.
- Focused fixtures cover the unconditional sync backend, initial and existing branch trees, cutoff boundaries, local-byte preservation, and excluded-root behavior.
- The obsolete sync copies and branch-only plan and backlog helpers are absent from the skill, runtime script set, active runtime registration, and maintenance pins; registry retirement tombstones remain as historical records.

**Ship when:**
- This plan's deliverable is the reviewed, committed shared skill and canonical helper in this repository. Deployment to consuming projects is the responsibility of each project's maintainer through its existing skill-sync process and is not a gate for this repository change.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production code:**
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/done/SKILL.md`
- `scripts/docs_branch_sync.sh` *(new)*
- `scripts/docs_branch_sync_noworktree.sh` *(remove after caller search)*
- `scripts/docs_branch_plan_guard.py` *(remove after caller search)*
- `scripts/docs_branch_backlog_dedupe.py` *(remove after caller search)*
- `scripts/runtime-scripts.list`
- `scripts/machinery_registry.json`
- `scripts/check_maintenance_pins.sh`

**Tests:**
- `scripts/test_docs_branch_sync.py` (new canonical sync and allowlist fixtures)
- `scripts/test_docs_branch_plan_guard.py` (remove with retired helper)
- `scripts/test_docs_branch_backlog_dedupe.py` (remove with retired helper)
- `scripts/test_docs_branch_sync_noworktree.py` (retire after migrating any still-required coverage to the canonical suite)
- Deferred by user to `docs/history/backlog/2026-10-09-docs-branch-step2-selector-test.md`: `scripts/test_docs_branch_step2_selector.py` is outside this task's implementation scope and remains unchanged.
- Update remaining focused sync tests discovered from repository evidence; remove helper-only tests when their helper is retired.

**Plan-related extension:** implementation and review may change unlisted files when causally required to complete a task, fix a regression, update wiring or docs implied by a listed change, or satisfy a changed contract. Validate all such paths before expanding scope. Drop weak or speculative links.

**Out of scope; reject unless plan-related:**
- `graphify-out/`, `.ai-playbook/`, `.claude/`, `.zcode/`, and `docs/` outside the allowed roots: leave those local checkout paths unchanged while pruning corresponding docs-branch paths from refs/heads/docs.
- Review staging format and metrics generation: this plan changes their retention only.
- Local tmp cleanup and `scripts/done_sweep_gates_lib.py`: unchanged here; local recursive cleanup is tracked separately in `docs/history/backlog/2026-10-09-done-recursive-tmp-sweep-safety.md`.
- `scripts/done-lock.sh`, worktree migration, session manifests, and closeout lock ordering: the existing behavior remains in force.

## Design Invariants (CR Guard)

- The sync remains local and never pushes. The shared skill owns the behavior and the one runtime script carries its executable implementation. One unconditional repository-level `commit-tree` and compare-and-swap path uses a temporary index and never registers a temporary Git worktree.
- The backend leaves the live checkout's HEAD, index, and source bytes unchanged. Before reading the docs tree or changing repository state, it verifies that `refs/heads/docs` is a direct ref. Ref reads, absent-ref checks, and compare-and-swap publication do not follow symbolic refs. A failed check or compare-and-swap preserves every ref and does not restore branch-only files.
- Sync continues to use the `done` merge lock and existing migration-before-removal ordering. The current availability-checked deferral still permits local commit when its owned-review check passes.
- Add-only restoration remains for allowed review and metrics roots, apart from explicit deletion and age pruning. Branch pruning never deletes local source files.
- The allowlist applies globally to all projects consuming the shared skill. Their configured roots are resolved from each project's facts.
- Sync excludes tmp from the docs branch but does not delete local tmp files or change the existing `done` tmp-sweep behavior.

## Validation Commands

```bash
python3 scripts/test_docs_branch_sync.py
bash scripts/check_maintenance_pins.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-10-09-docs-branch-scope-and-tmp-retention.md --pre-round
```

### Task 1: Replace duplicated sync with one allowlisted canonical runner

Context surface: the plan's Terms, Standing constraints, and Design Invariants (CR Guard).

Files:
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/done/SKILL.md`
- `scripts/docs_branch_sync.sh` *(new)*
- `scripts/test_docs_branch_sync.py` *(new)*
- `scripts/runtime-scripts.list`
- `scripts/machinery_registry.json`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `docs_branch_sync_main` in `scripts/docs_branch_sync.sh`

- [x] Use one temporary-index `commit-tree`/CAS backend for every `worktree_policy`; accept and ignore unknown policy values. Emit no mode label or create a worktree. Preserve checkout HEAD/index/source bytes and the worktree registry; never push; fixture absent, `worktrees`, `primary`, and unknown values [class: REPOSITORY_TEST]
- [x] One allowlist snapshot preserves prior commits and keeps only recent review/metrics archives; fixtures verify local bytes stay unchanged and excluded paths, including locally absent paths, are pruned and reported [class: REPOSITORY_TEST]
- [x] Replace inline/duplicate sync with one entry point; after full-repo caller search, retire the no-worktree wrapper, guard/dedupe helpers, helper-only tests and active registrations; retain retirement tombstones; add the canonical focused suite [class: IMPLEMENTATION_REQUIRED]
- [x] Both skills exclude tmp from docs sync, preserve local tmp, and keep separate `done` `docs-tmp-sweep` behavior [class: IMPLEMENTATION_REQUIRED]
- [x] Both skills document the unconditional shared runner behavior; neither describes a mode selector or temporary detached worktree as a sync backend [class: IMPLEMENTATION_REQUIRED]
- [x] Only absent facts keys use review/metrics defaults; missing or malformed facts and malformed roots refuse. Normalize narrow relative roots under `docs/`, merge same-role overlaps, and reject empty, absolute, dot/parent, broad, wrong-role, escaped, or cross-role-overlapping roots; test custom roots and swapped roles [class: REPOSITORY_TEST]
- [x] Instrument refusal: invalid roots stop before candidate walk/snapshot/prune; docs ref stays unchanged [class: REPOSITORY_TEST]
- [x] If fixed `docs/reviews` is a symlink to configured `docs/team/archive/reviews`, visit once and archive only the resolved target; reject targets outside `docs/` or with the wrong role [class: REPOSITORY_TEST]
- [x] An allowed-root symlink escaping its root is never read/copied; a regular candidate replaced by an escaping symlink before open is rejected, with instrumentation proving zero reads from the target and a full sync-path assertion that `refs/heads/docs` stays unchanged [class: REPOSITORY_TEST]
- [x] Resolve permitted aliases to canonical in-docs roots before walking; traverse canonical roots and descendants through repository-relative no-follow descriptors. If a canonical root or ancestor is swapped to a symlink, refuse before snapshot/ref update with no outside reads and an unchanged docs ref [class: REPOSITORY_TEST]
- [x] Test before/at/after the strict two-month UTC cutoff, month-end clamp, and divergent author/committer dates; prune by path-changing committer time, independent of host timezone or unrelated tip [class: REPOSITORY_TEST]
- [x] Restore recent allowed branch-only files through no-follow directory descriptors; if an allowed-root parent is a symlink or is swapped for one, refuse without writing outside the root. Prune expired branch-only files before restore, retaining history [class: REPOSITORY_TEST]
- [x] Identical historical bytes with fresh mtime do not renew; recent changed bytes renew even if their mtime predates the latest docs-branch path-change timestamp, as long as it remains within the cutoff; recent new paths archive; local bytes stay unchanged [class: REPOSITORY_TEST]
- [x] The unconditional backend preserves checkout HEAD/index/source bytes and lock order, never pushes. CAS conflicts keep the competing tip current, local bytes unchanged and branch-only files unrestored; no-op sync CAS-checks the observed tip against itself [class: REPOSITORY_TEST]
- [x] Build the complete replacement tree before publishing it with one no-dereference compare-and-swap ref update; fail before tree reads or mutation if `refs/heads/docs` is symbolic, and test that a symbolic docs ref to `refs/heads/main` remains unchanged with main tip and tree preserved [class: REPOSITORY_TEST]
- [x] Subprocess fixtures pin minimal Git/`DOCS_SYNC_*` environment, clock and timezone [class: REPOSITORY_TEST]
- [x] Qualified explicit done deferral with owned reviews at primary keeps local-commit eligibility [class: REPOSITORY_TEST]
- [x] Commit: `docs-branch: keep only recent analysis archives` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

| Backlog origin | Disposition |
|---|---|
| `docs/history/backlog/2026-10-07-docs-branch-temporal-sync-retention.md` | Covered: Task 1 excludes temporal roots, including `docs/tmp/`, from docs-branch sync and applies the requested two-calendar-month retention policy. Local tmp deletion remains separate and is tracked by `docs/history/backlog/2026-10-09-done-recursive-tmp-sweep-safety.md`. |
| `docs/history/backlog/2026-10-08-docs-branch-overlapping-shadow-candidates.md` | Covered: Task 1 uses one deduplicated allowlist walk, removing duplicate nested candidate copies. |
| `docs/history/backlog/2026-10-08-docs-branch-sync-persisted-copy.md` | Covered: the single canonical `scripts/docs_branch_sync.sh` runner replaces extracted and persisted sync copies. |
| `docs/history/backlog/2026-10-09-done-docs-branch-sync-overhead.md` | Covered: sync work is narrowed to validated review and metrics roots, and the existing verified explicit-deferral path remains available for local commits. |
| `docs/history/backlog/2026-10-09-docs-branch-configured-root-safety.md` | Covered: configured roots and escaping links are validated before traversal or branch mutation, with refusal coverage in Task 1. |

## Related backlog boundaries

- `docs/history/backlog/2026-10-07-plan-authoring-done-closeout.md`: related only to the plan-authoring handoff; this plan uses the existing `done` workflow and does not redesign its completion enforcement.
- `docs/history/backlog/2026-10-08-docs-branch-overlapping-shadow-candidates.md`: direct origin, addressed by Task 1's single deduplicated allowlist walk.
- `docs/history/backlog/2026-10-09-authoring-plan-artifact-not-transferred-before-removal.md`: handoff-only; this recovery transfers the plan and its review series to the primary project before worktree removal, but does not broaden the docs-sync implementation scope.
- `docs/history/backlog/2026-10-09-done-foreign-checkout-dirt-blocks-scoped-commit.md`: separate closeout change, deferred by the user's decision. The current recovery uses a scoped artifact transfer and exact-path commit; the permanent shared-gate behavior remains owned by its plan prompt.
- `docs/history/backlog/2026-10-09-done-recursive-tmp-sweep-safety.md`: local tmp deletion is deliberately deferred to a separate `done` cleanup plan; this plan only excludes tmp from docs-branch sync.
