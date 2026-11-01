# Plan: Runtime scripts home reconcile and retire

Backlog origin: docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md
Driving force: simplicity; secondary: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-28-plan-review-runtime-scripts-home-reconcile-and-retire-r*.md
Execution budget: 2.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-18-runtime-scripts-home-residue.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms

- **Runtime home**: the scripts directory used as the deployment destination; the helpers default to `$HOME/.ai-playbook/scripts` and accept `--home` or `DEPLOYED_ROOT` overrides. User facts resolve the canonical repository source, not this destination.
- **Deployment manifest**: `scripts/runtime-scripts.list`, the list of canonical files that deployment keeps available through the runtime home.
- **Home-only delta**: bytes in a runtime-home copy that are absent from the canonical repository copy.
- **Runtime data**: non-executable state or configuration files kept beside deployed scripts, including the liveness ledger and skill budget caps.

## Why

The runtime home still contains stale executable copies and dangling links, so a command can resolve to old behavior or fail at its target. Reconcile deployed helpers to repository sources and remove only artifacts proven stale, preserving live data and helpers whose external use cannot be ruled out.

## Gist & Examples

TLDR: Align the repository manifest with runtime consumers and preserve home-only state until its behavior has a safe disposition through simplicity.

Before, a runtime-home `reconcile_post_landing.py` lacks the repository's read-only `--check-primary` option, two quota helpers are duplicate regular files, and dangling backup links point into removed worktrees.

After, the repository manifest names the helpers that consumers need, and a separately tracked operation can safely reconcile runtime-home entries after the repository change lands.

Edge cases: home-only code is recovered only when current repository consumers or history show it is still needed; mutable JSON state and the no-twin credential helper remain untouched; a per-entry backup collision leaves that entry in place while other entries continue.

## Outcome

The repository declares the helpers needed by runtime consumers, and a separately tracked runtime-home operation can reconcile them after each home-only behavior has a safe disposition.

- Repository consumers and runtime-home callers have a canonical source for each manifest-managed helper.
- Existing user state and unresolved helper behavior stay preserved until a safe migration or retirement is evidenced.
- A runtime-home operation failure leaves independent repository and maintenance work available to continue.

Gate delta: no new gate, refusal class, lock, ledger, protocol, state field, approval step, or dispatch pause; the repository manifest and existing deployment verification are reused, while runtime-home mutations remain a separately tracked operation.

## Assumptions

- The operations follow-up resolves the runtime-home destination from the effective `--home` or `DEPLOYED_ROOT` setting, defaulting to `$HOME/.ai-playbook/scripts`; user facts' `skills_repo_path` resolves the canonical repository source. Basis: `scripts/deploy_runtime_helpers.sh` and `scripts/sync_runtime_scripts.sh`.
- The deployment manifest is the managed executable set. Basis: `scripts/runtime-scripts.list` defines one deployed filename per line and both runtime-home deployment helpers read it.
- A read-only inventory on 2026-10-28 found 25 regular files, 134 symlinks, and 60 dangling symlinks. Several regular files are data or backups, so counts are re-derived at execution and do not define deletion scope.
- The runtime-home `quota_governor.py` and `quota_pressure_stats.py` match their repository twins; `reconcile_post_landing.py` does not. Basis: same-session SHA-256 comparison.
- The home copies of `gate_liveness_ledger.json` and `skill_text_budget_caps.json` differ from repository data, and `sync-mcp-credentials.sh` has no repository twin. Basis: same-session byte comparison and repository-wide name search. Preserve all three unless a current repository consumer proves a safe migration.
- The runtime-home `review_record_selection.py` has a recorded 42-line home-only delta and a dated backup. Its live consumers and delta still need an explicit behavior disposition before the active home entry is switched to its repository link.
- No in-repository caller for `sync-mcp-credentials.sh` was found. This does not establish that no external caller exists, so the helper is retained by default without an operator decision.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: a managed runtime-home helper resolves to its canonical repository file and accepts the current caller's arguments.
- Data safety: mutable runtime data and home-only behavior are retained or recovered before stale copies are removed.
- Recovery: collisions or tool errors are recorded per entry; an unresolved active delta keeps runtime-home sync open while unrelated repository and maintenance work continues.
- Simplicity: no new gate, refusal class, lock, validator, or required operator ceremony is introduced.

**Done when:**
- The repository manifest names the three confirmed runtime-resolved helpers and the quota import dependency.
- The selected existing manifest and deployment tests pass, and their exact results plus the home-only paths needing operational disposition are recorded in the task log.

**Ship when:**
- **[class: OPERATIONS_FOLLOW_UP]** Runtime-home reconciliation and cleanup remain a separately tracked operation owned by the runtime-home operator. Use the configured runtime-home destination and the task log's delta list. Resolve one `RUNTIME_HOME` value from the effective `--home` or `DEPLOYED_ROOT` setting, defaulting to `$HOME/.ai-playbook/scripts`, and pass that same value to both helpers. First inventory entries and assess every home-only code delta, including `review_record_selection.py`, against its backup, repository history, and live consumers. Recover needed behavior into the canonical source and file a separate backlog row for each recovered delta; if the evidence shows code is unused, record that evidence and retire it. If an active delta remains uncertain, preserve that active entry, record its exact next action, leave this follow-up and the origin open, and do not run whole-manifest sync; the sync helper has no per-entry skip, so do not claim safe entries were synced. This pauses only this runtime-home operation; unrelated repository and maintenance work continues. Run the whole-manifest sync only after every active home-only code delta has a safe disposition, and only from the stable primary checkout after this manifest change lands, using `DEPLOYED_ROOT="$RUNTIME_HOME" bash scripts/sync_runtime_scripts.sh`. Then verify managed link targets resolve into that checkout and run `bash scripts/deploy_runtime_helpers.sh --check --home "$RUNTIME_HOME"`. Treat check output as clean only when verification actually ran and the report contains no missing, stale, skipped-verification, or other advisory findings; `OUTCOME: pass` and exit 0 alone do not establish success. For per-entry sync failures, use one bounded retry when the named remedy is safe; otherwise preserve that entry, record the exact next action, and allow the helper to continue independent entries. Move preserved runtime data and the no-twin helper out of the scripts home only after a byte-verified safe migration, or add a canonical twin or retire the helper based on consumer evidence. Remove confirmed stale backups and dangling links only after recovery/source or target absence is verified. Close the operation only when a fresh inventory satisfies the origin's acceptance: no real files beside repository symlinks and no dangling links, with every removed or migrated entry accounted for. Keep the backlog origin open until that acceptance is met; this follow-up does not gate unrelated repository or maintenance work.

## Review Scope

**Explicit must-fix:**

**Production and deployment inventory:**
- `scripts/runtime-scripts.list` (Task 1)
- `scripts/reconcile_post_landing.py` (review-only)
- `scripts/quota_governor.py` (review-only)
- `scripts/quota_pressure_stats.py` (review-only)
- `scripts/review_record_selection.py` (review-only)
- `scripts/sync_runtime_scripts.sh` (review-only)
- `scripts/deploy_runtime_helpers.sh` (review-only)

**Plan-related extension:** deployment tests selected from repository evidence may be read or updated only to verify the manifest-driven behavior prescribed here. Do not change deploy failure policy, add enforcement, or alter unrelated runtime files.

**Backlog origin (read-only input):**
- `docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md`

**Out of scope; reject unless plan-related:**
- Changes to user-facts schemas, scheduler gates, or deployment failure behavior; reason: the existing deploy helpers already own this inventory and the plan must not add blockers.
- Deleting `gate_liveness_ledger.json`, `skill_text_budget_caps.json`, or `sync-mcp-credentials.sh`; reason: these are mutable data or a helper with possible external consumers, not a proven stale executable shadow.
- Broad recursive cleanup of the runtime home; reason: only exact inventoried paths with a verified stale or dangling disposition are in scope.

## Validation Commands

For repository changes, select the existing class-style suites that cover manifest parsing and deployment verification from repository evidence; record exact commands and results in the task log. From the repository root, run `CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/runtime-scripts.list scripts/reconcile_post_landing.py scripts/quota_governor.py scripts/quota_pressure_stats.py scripts/review_record_selection.py scripts/sync_runtime_scripts.sh scripts/deploy_runtime_helpers.sh` and `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files scripts/runtime-scripts.list scripts/reconcile_post_landing.py scripts/quota_governor.py scripts/quota_pressure_stats.py scripts/review_record_selection.py scripts/sync_runtime_scripts.sh scripts/deploy_runtime_helpers.sh`. If a selected test file is changed, add its repository-relative path to both scan commands before commit. Runtime-home inventory, sync, and deployment checks belong to the separately tracked operations follow-up, not this repository task. Do not add a new validation gate.

### Task 1: Recover live deltas and align the deployment manifest

Context surface: the home-only deltas named by the origin and the manifest consumers.

Files:
- `scripts/runtime-scripts.list`

Primary class anchors:
- `Invocation` in `scripts/reconcile_post_landing.py`
- `evaluate_pressure` in `scripts/quota_governor.py`
- `mine_day_detailed` in `scripts/quota_pressure_stats.py`

Evidence:
- The current manifest omits the three confirmed runtime-resolved helpers even though runtime-home callers rely on them.
- The quota helper pair shares an import dependency, so the manifest must include both files for the canonical runtime path to resolve.

- [x] Given the current manifest and runtime consumer references, add the three confirmed runtime-resolved helpers and quota import dependency; expects the manifest to list each once and resolve every declared repository source. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the updated manifest and repository-selected tests, record exact test results and the known home-only delta paths in the existing task log; expects the log to provide the operational follow-up's evidence list without running runtime-home mutations. [class: REPOSITORY_TEST]
- [x] Commit: `fix: reconcile runtime script deployment inventory` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

No new operator guide or skill is needed. The plan updates the existing deployment inventory, and the run report records the remaining non-deployment data and no-twin helper without introducing a new maintenance surface.

## Disposition of migrated backlog items

Origin row docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md: NOT covered by this landing — the plan's Ship when (class OPERATIONS_FOLLOW_UP) keeps the origin open until the separately tracked runtime-home operation meets its acceptance (no real files beside repository symlinks, no dangling links, every removed or migrated entry accounted for). The repository half of the plan is complete; the operational half (runtime-home reconcile, per-entry delta dispositions, whole-manifest sync, deployment check) remains a tracked follow-up owned by the runtime-home operator, with the evidence list recorded in the execution run's task log. No backlog rows were migrated by this plan.
