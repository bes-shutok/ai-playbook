# Plan: Closeout migration replaces same-run mirrors
Backlog origin: docs/history/backlog/2026-10-21-closeout-migration-collision-renames-run-mirrors.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-closeout-migration-same-run-mirror-replace-p<identity>-r*.md
Execution budget: 2.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/closeout-migration-same-run-mirror-replace.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Same-run mirror:** A primary-home copy written by the current run's Step 1.4 record-mirror duty.
- **Mirror receipt:** A JSON object in a `task_boundary` row naming one repository-relative path, type, and copied state (SHA-256 for a regular file or link target for a symlink). The row binds it to the stable run tuple.
- **Stable run tuple:** The session manifest's immutable `run_session_id`, exact `plan_path`, and registered `run_worktree`.
- **Foreign collision:** A different existing primary file whose current state is not proven by the latest valid receipt for that exact path from a lock-cooperating workflow writer.

## Why

The record-mirror duty copies review records and session logs to the primary checkout at each light boundary. At final closeout, migration sees those same files as collisions and renames them, leaving stale canonical copies behind. The closeout gate can then read stale runtime evidence even though the latest run records are available under `.wt-*` names.

## Gist & Examples

TLDR: Replace receipt-proven same-run mirrors at closeout, preserve foreign files, for code-quality.

**Before (today):** A run mirrors `runtime_state.json` at a task boundary. The run later updates that file, then closeout migration sees different bytes at the primary path and moves the incoming file to a `.wt-<suffix>` sibling. The canonical path still describes the earlier boundary.

**After (this plan):** Each boundary records the exact primary mirror state it verified in the existing `task_boundary` verification results. For writers using the shared repository merge lock, closeout replaces a different-byte primary file only when the source session manifest binds that exact path and the current primary bytes or link target still match its latest valid receipt. Changes visible at the final recheck keep their bytes and follow the existing `.wt-*` rename and `COLLISION:` path; a process bypassing the lock after that recheck is outside this concurrency guarantee.

An identical target remains a verified no-op. Replacement stages and verifies incoming content beside the destination, rechecks it immediately before atomic installation, then installs it; failure preserves the prior destination and source.

## Outcome

Closeout migration leaves current run artifacts at their canonical primary paths only when the recorded mirror receipt still proves ownership of the current target.

- A valid receipt must match the stable run tuple, exact repository-relative path, file type, and current primary content digest or symlink target.
- Invalid JSON, unknown row status, tuple mismatch, or task-boundary row boundaries that cannot be parsed invalidates run history. A malformed item with a recoverable path, unknown item status, or duplicate path invalidates only that path; an item whose path cannot be recovered invalidates run history. Failed/skipped items invalidate only their path, untouched paths retain history, and invalid paths never fall back. Missing/mismatched identity, absent path, or changed target preserves the current file and uses foreign rename with `COLLISION:` evidence.
- Identical targets remain skipped; successful replacements are recorded separately from renames and counted in the CLI summary.
- A failed staged copy, verification, final recheck, or atomic replacement preserves the previous target and source, removes temporary siblings, records failure, and keeps migration unsuccessful.

Gate delta: no dispatch condition or run-blocking gate/refusal is added; one boundary-mirror operation in the existing migration script holds the `worktree-closeout-migrate` repository merge lock (normalized `git rev-parse --git-common-dir` key) through staged mirror copies and atomic task-boundary manifest replacement. It handles SIGINT and SIGTERM through rollback and token-fenced release; lock contention remains a report-only skip with the existing copy-error outcome. The `task_boundary` verification value gains the machine-consumed per-path `mirror_receipts` schema; the migration manifest adds `replaced`. This schema is justified by the completed wrong-state witness in the [2026-10-21 origin](../backlog/2026-10-21-closeout-migration-collision-renames-run-mirrors.md) and its [prompt-log evidence](../backlog/PLAN-PROMPTS.md): migration emitted `COLLISION:` for this run's `manifest.md`, `runtime_state.json`, `closeout-baseline.json`, and metrics log, leaving the primary manifest with pre-rebase data and no terminal receipt for the closeout gate. Expected catch frequency: each closeout with a different-byte same-run collision after a boundary mirror. False-positive cost: an unmirrored path retains its worktree source and is named by the existing copy-error report. Review the schema and contention behavior by 2026-11-24.

## Assumptions

- assume the existing session manifest is authoritative for the stable run tuple and each `task_boundary` row is bound to it; basis: execute-plan Step 0.4 and Step 1.4 define those fields and bindings.
- assume receipts can be appended as a compact JSON field to the existing verification-results value without a new manifest field or ledger; basis: that value already records verified boundary outcomes.
- assume the closeout baseline and session manifest are siblings in the run's existing session directory; basis: Step 0.4 writes both under `{tmp_dir}/execute-plan/<PLAN_SLUG>/`.
- assume one boundary-mirror helper owns the live lock from acquisition through the verified path copies and receipt-row append; legacy rows without receipt tokens cannot authorize replacement, while row and per-path statuses distinguish success, copy error, and lock contention.
- assume the receipt guarantee covers workflow and operator writers that use the shared repository merge lock; changes visible at final recheck are foreign, while a writer bypassing the lock after that point is outside the guarantee; basis: the existing lock serializes participating writers and no atomic compare-and-swap primitive is in scope.

Decision points requiring a grill: add per-path receipt status within the existing verification-results value, reuse the existing repository merge lock, and scope concurrency to writers using it; source: r4 reconciliation, existing `cmd_migrate` lock span, and the completed stale-primary state recorded in the origin; date: 2026-10-24; affected plan sections: Gate delta, Outcome, Task 1, Task 2, and Evaluation Criteria.

## Standing constraints

- Preserve unknown or foreign primary files; replace only a current target whose exact path, run tuple, and state are proven by valid receipt history from writers using the shared lock.
- Keep the source file, checksum verification, and the existing fail-closed migration behavior.
- Add no new gate, lock, ledger, flag, or broad-copy path; reuse only the repository merge lock already held by migration.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: receipt-proven same-run collisions replace the canonical target and are recorded as replacements; foreign collisions retain the current unique rename and report behavior.
- Data safety: unknown ownership never authorizes overwrite; malformed receipt history never falls back; failure/skipped status invalidates only the named path; staged content is verified and the destination is rechecked before installation; source and prior target remain available on failure. The serialization guarantee names lock-cooperating workflow/operator writers and excludes writes that bypass the lock after final recheck.
- Maintainability: the existing session manifest carries the receipt and the migration manifest distinguishes replacement from rename.

**Done when:**
- Migration fixtures prove exact-path replacement, cross-path same-digest rejection, identity mismatch, changed destination, malformed history including unparseable row boundaries and path, path-scoped partial/skipped status, a concurrent writer detected by final recheck, post-install manifest-write rollback, failure-safe replacement, and byte-identical no-op.
- The Step 1.4 mirror helper and migration use the same existing repository merge lock. Contention copies no primary files, records a skipped item per planned path and no verified receipt, appends the local row, and continues. An injected post-acquire failure proves lock release; a held span beyond the dead-holder grace proves a second acquire remains refused. Unlocked copies emit verified receipts only after atomic install and durable row append.
- Changed-file hygiene, em-dash, and maintenance-pins checks pass.
- The plan review is certified with no blocking findings.

**Ship when:** The implementation plan is executed and its completion evidence is archived.

## Review Scope

**Explicit must-fix:**
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`

**Out of scope; reject unless plan-related:**
- Other migration subcommands or closeout gates; they are unrelated unless a finding shows a direct regression from the replacement behavior.

## Validation Commands

- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_worktree_closeout_migrate.py'`
- `bash scripts/check-no-em-dash.sh touched`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files scripts/worktree_closeout_migrate.py scripts/test_worktree_closeout_migrate.py agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/worktree-first.md`
- `bash scripts/check_maintenance_pins.sh`

### Task 1: Replace only receipt-proven same-run mirror collisions

Context surface: the plan's Terms, Outcome, and Standing constraints.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `cmd_migrate` in `scripts/worktree_closeout_migrate.py`
- `_cmd_migrate_transfer` in `scripts/worktree_closeout_migrate.py`

- [ ] Add fixtures: exact-path match replaces; same-digest other-path, identity mismatch, changed target, and identical target produce foreign rename or no-op as specified. Assert primary/incoming bytes and disposition. [class: REPOSITORY_TEST]
- [ ] Add parser cases for older-valid/newer-malformed, invalid JSON, unknown row status, tuple mismatch, duplicate path, unknown item status, unparseable path, and task-boundary row boundaries that cannot be parsed; assert run-wide invalidation versus recoverable path-only invalidation as specified. [class: REPOSITORY_TEST]
- [ ] In one row with valid path A and malformed recoverable path B, assert A remains eligible after target recheck while B is preserved and renamed; separately assert an unrecoverable path invalidates run history. [class: REPOSITORY_TEST]
- [ ] Add a partial-row fixture: one failed/skipped path invalidates only itself, while an untouched path keeps and can use its prior receipt after digest recheck. [class: REPOSITORY_TEST]
- [ ] Add an interleaving fixture that changes a destination between staging and final recheck; assert preservation and foreign rename. [class: REPOSITORY_TEST]
- [ ] Inject copy, verification, install, and migration-manifest persistence failures; each preserves the prior target and source, preserves the prior manifest when its atomic install fails, removes temporary siblings, and records failure. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the exact-path positive case fails because current code renames different-byte collisions; existing foreign cases stay green. [class: REPOSITORY_TEST]
- [ ] Have `migrate` read the session manifest beside the supplied baseline and validate its stable tuple against the source worktree; missing or mismatched identity authorizes no replacement. [class: IMPLEMENTATION_REQUIRED]
- [ ] Parse terminal `mirror_status=<complete|partial|skipped> mirror_receipts=<JSON array>` tokens. File items use `path,status=verified,type=file,sha256`; links use `path,status=verified,type=symlink,target`; failed/skipped items use `path,status`. Use compact JSON and `\u007c` for table pipes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Ignore legacy rows without tokens. Invalid JSON, unknown row status, tuple mismatch, or task-boundary row boundaries that cannot be parsed invalidates run history. A malformed item with a recoverable path, unknown item status, or duplicate path invalidates only that path; an item whose path cannot be recovered invalidates run history. Never fall back. [class: IMPLEMENTATION_REQUIRED]
- [ ] Resolve each path from its latest row item: verified updates it; failed/skipped invalidates it; absent paths retain history. Complete empty rows change no path. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep compare, stage, final recheck and install under the existing `worktree-closeout-migrate` lock keyed by normalized git common dir. A changed target uses foreign rename; writers bypassing the lock after recheck are outside the guarantee. [class: IMPLEMENTATION_REQUIRED]
- [ ] Stage incoming bytes at a unique sibling, verify type/content, then atomically replace. Any failure preserves old target/source, removes temp, records failure, and keeps migration unsuccessful. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the prior target or symlink recoverable until the migration manifest containing the `replaced` disposition is atomically installed; if manifest persistence fails, restore the prior target and manifest, retain the source, and return failure. Record source/destination, prior/incoming states and run identity; include `replaced N` in the success summary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Assert every replacement payload field and summary count; inject migration-manifest write failure after staged installation and assert the prior target, prior manifest, and source remain intact; retry and assert a durable `replaced` record. Round-trip a path containing `|`, quote and backslash, checking `\u007c` and the exact decoded path. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: run the migration test module and record its outcome. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: replace proven same-run closeout mirrors` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Run boundary mirror and receipt as one operation

Context surface: the plan's Terms, Outcome, and Task 1 consumer contract.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors:
- `cmd_migrate` in `scripts/worktree_closeout_migrate.py`
- `_cmd_migrate_transfer` in `scripts/worktree_closeout_migrate.py`
- `_merge_lock_acquire` in `scripts/worktree_closeout_migrate.py`
- `_migrate_merge_lock_release` in `scripts/worktree_closeout_migrate.py`

- [ ] Add a boundary-mirror operation to the existing migration script and have Step 1.4 delegate its mirror and receipt work to it; pass the stable run tuple and exact primary mirror path list, including `runtime_state.json`, review records and sidecars, new session logs, and other path classes Step 1.4 currently mirrors. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep one live helper process from merge-lock acquire through all mirror installs and atomic task-boundary manifest replacement; use the existing normalized git common-dir lock. Handle SIGINT and SIGTERM by routing them through ordinary rollback and token-fenced release; SIGKILL and power loss are outside this cleanup guarantee. Other boundary legs remain lock-free. [class: IMPLEMENTATION_REQUIRED]
- [ ] If try-once acquisition refuses, copy no primary files, append a local row with one `status=skipped` item per planned path and no verified receipts, report the existing copy error, and continue the boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Stage each primary mirror beside its destination, verify type and bytes/link target, then atomically install it. Keep prior targets recoverable until the complete receipt row is durably installed; on a copy, receipt-write, or handled-signal failure restore prior targets, remove temporary siblings, retain worktree sources, and release the lock. [class: IMPLEMENTATION_REQUIRED]
- [ ] Preserve the Task 1 `mirror_status` and `mirror_receipts` grammar. Build the updated task-boundary manifest as a staged complete file and atomically replace the prior manifest; if replacement fails, leave prior manifest bytes and receipt rows intact. Record the verified primary copy of `manifest.md` before this row. Complete lists verified paths; partial lists every attempted path as verified or failed; skipped lists every planned path as skipped. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update Step 1.4 to call the boundary-mirror operation instead of spelling out separate acquire/copy/append/release commands. Keep the existing report-only contention and copy-error behavior. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update transfer-out to state that migration holds the same `worktree-closeout-migrate` lock across receipt comparison, staged copy, final recheck, manifest commit, and install. Changed or invalid receipts preserve the target and use foreign rename. [class: IMPLEMENTATION_REQUIRED]
- [ ] Pay for operative-text growth by deleting equivalent bytes in the same sections; remove repeated transfer-out wording while retaining current gate and ownership rules. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add producer fixtures for lock contention beyond the dead-holder grace, partial-copy rollback, and atomic manifest-install failure. Deliver SIGINT/SIGTERM after lock acquisition and after at least one primary mirror installs but before receipt replacement; assert rollback restores prior primary and manifest bytes, earlier receipts stay parseable, sources remain, temps are removed, lock releases, and retry succeeds. [class: REPOSITORY_TEST]
- [ ] Review acceptance: name both skill anchors and confirm producer serialization, handled-signal scope, exact JSON grammar, full mirror path inventory, atomic copy/manifest rollback, lock-cooperating-writer scope, failure fallback, and consumer behavior agree. A refused acquire records skipped items but no verified receipt. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: run the migration test module and record its outcome. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: serialize closeout mirror receipts` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

- `scripts/worktree_closeout_migrate.py` owns the process-scoped boundary-mirror transaction and migration lock; `agents/skills/execute-plan/SKILL.md` delegates Step 1.4 to it without repeating the transaction procedure.
- `agents/skills/execute-plan/worktree-first.md` updates the existing transfer-out implementation that owns migration invocation and receipt consumption.
- The migration manifest records replacement alongside its migrated, skipped, renamed, and failed outcomes, and commits that disposition atomically with replacement while the prior target remains recoverable. The `task_boundary` verification value carries the per-path receipt schema required by the 2026-10-21 stale-primary incident; review its catch rate and false-positive cost by 2026-11-24.

## Execution Handoff

Task 1 consumes only well-formed receipts for exact target paths and invalidates history on malformed rows; it commits each replacement and its manifest disposition while the previous target remains recoverable. Task 2 makes one existing-script process own the Step 1.4 mirror/receipt transaction and delegates to it from the workflow skill. Migration uses the same repository lock and rechecks target state immediately before installation. Lock contention stays report-only. The concurrency guarantee covers writers using the shared lock; a writer bypassing it after final recheck is outside scope.
