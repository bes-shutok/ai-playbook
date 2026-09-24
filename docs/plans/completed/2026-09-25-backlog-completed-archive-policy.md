# Plan: fold-then-delete completed-backlog archive policy (migrate the per-item completed corpus)

Backlog origin: docs/history/backlog/2026-09-25-backlog-completed-archive-policy.md
Driving force: simplicity

## Terms

- fold-then-delete: the completion disposal rule owned by `plans` **Plan Lifecycle**; the promoted backlog item's disposition is appended to the matching completed plan under `{plans_completed_dir}`, then the per-item file is deleted; per-item archives under `{backlog_completed_dir}` are never kept.
- completed inbox: the directory named by the `backlog_completed_dir` facts key (here `docs/history/backlog/completed/`); it exists for tooling compatibility and must stay empty of dated item files.
- disposition home: the completed plan (or, for a migrated item with no related completed plan, this plan's own migrated-disposition section) that carries the item's one-bullet disposition after its per-item file is deleted.
- destination plan: a completed plan under `{plans_completed_dir}` the matcher selects as a migrated item's disposition home.
- migration audit note: text appended to an existing registry row's `audit` cell recording the migration (date, destination, deletion); the row's `src` cell stays unchanged.
- self-host: the disposition home being this plan file itself, used for items the matcher cannot map to any completed plan.

## Assumptions

- assume the `backlog_completed_dir` facts key is kept and this plan retires nothing; basis: five in-repo tooling consumers read it (`scripts/check_backlog_inbox_location.py`, `scripts/doc_registry_validator.py`, `scripts/check_plan_origins_closed.py`, `scripts/test_check_plan_origins_closed.py`, `scripts/test_execute_plan_worktree_bootstrap.py`), `bootstrap-ai-playbook` teaches the key, and the origin's step 5 offers keep-or-retire with retirement deferred to a follow-up once external tooling stops reading it.
- assume items with no related completed plan fold their disposition into this plan's own `## Disposition of migrated backlog items` section, which rides to `{plans_completed_dir}` when this plan completes; basis: the origin's squash rule presumes a related plan exists, every deletion needs a durable disposition home (the registry freeze convention), and a synthetic host record would add a registry identity for no plan work.
- assume existing registry rows for migrated items keep their `src` cell (the now-deleted per-item path) and record the migration in the `audit` cell instead of retargeting `src`; basis: `doc_registry_validator` gates multiply-claimed srcs, and retargeting to the destination plan would duplicate the destination plan's own row src, while the validator's completed-history missing-entry scan is existence-driven so deleted files leave no gap.
- assume every migration audit note carries the validator's required leading token: an empty `audit` cell is replaced by `user-approved <migration date>: migration audit - disposition folded into <destination-plan-relpath>; per-item file deleted`, and a cell with existing content (already token-prefixed) gains `; migrated <migration date>: disposition folded into <destination-plan-relpath>; per-item file deleted` appended; basis: `doc_registry_validator` requires every non-empty `audit` cell on a completed row to begin with the exact `user-approved YYYY-MM-DD:` token (a real, non-future date) and HARD-fails anything else, and these notes are also the standing overrides that license the Task 3/4 writes (per-item deletions, destination body edits, the README add) through the done-boundary `check-writes` gate; corpus probe 2026-09-25 (review r1): 290 registry rows name completed-inbox srcs, 229 with empty audit cells.
- assume every migrated item ends with a registry row whose `src` names the (now-deleted) item path and whose `audit` cell carries the migration note: already-registered items keep their row and gain the note (empty cell replaced, pre-filled cell appended), and the unregistered items (review r2 probe: 33 of 318) gain a new row each (identity per the registry's filename-minus-date scheme, state completed, `archived` = the migration date - the actual move date, never the filename date prefix, per the registry header's archived-column rule; on identity collision the new row takes the registry's MMDD suffix, escalating to the directory tag when the date collides too, per the registry header's identity scheme - review r3 probe: exactly one of the 33 collides, 2026-09-18-maintenance-park-guard-externally-gated-plans); basis: the validator's validate-side scan never requires rows for deleted files, but the done-boundary `check-writes` gate HARD-fails the deletion of any completed-inbox path without a `user-approved`-noted override, so register-and-note is the only form that licenses every deletion.
- assume destination-plan body edits are licensed by a note on the destination plan's registry row: an unnoted destination row makes the body edit a HARD unlicensed immutable write at the done boundary (review r2 probe: 98 of 127 destination rows are unnoted today); destination rows are noted in the received form (empty cell replaced by the received-form note; a pre-filled cell gains `; received <former-item-relpath> disposition (per-item file deleted)` appended, review r4 probes prove validate exits 0 for the appended shape); 15 of the 142 completed plans have no registry row at all (review r4 alias-aware census) and the matcher routes 15 measured items to them, so `--apply` backfills a row-less destination with a new row (identity per the registry scheme with the collision escalation, state completed, `archived` = the migration date, received-form note) before editing it.
- assume self-host edits need no write-gate license: the self-host destination is this plan itself, a living top-level plan the gate does not freeze; when this plan completes, its own completion row covers the archived record.
- assume `docs/history/backlog/deferred/` and `docs/history/backlog/rejected/` stay byte-untouched; basis: origin step 2 ("Keep `rejected/` untouched") and the doc-hierarchy deferred revival rule (revival moves a file back to the backlog root; the archive is permanent history).
- assume skill texts need no edits unless the Task 5 sweep finds drift; basis: the 2026-09-25 authoring sweep over `agents/skills/` found zero move-teaching hits after commit 2eb72237 landed the fold-then-delete wording in `plans`, `execute-plan`, `receiving-review`, `doc-hierarchy`, and `bootstrap-ai-playbook`.
- assume the migration helper is stdlib-only python with unittest coverage following the `scripts/` test convention (mkdtemp fixtures, torn down per test; run `( cd scripts && python3 -m unittest test_migrate_backlog_completed )`), dry-run by default; basis: the `scripts/test_check_backlog_claimed.py` pattern.
- assume each per-item deletion and its disposition bullet land in the same commit, so no commit window holds a deleted item without its disposition home; basis: the `plans` Plan Lifecycle pairs fold and delete in one completion pass.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the repo's 318-file completed inbox collapses into fold-then-delete dispositions on the completed plans, so the second archive stops duplicating plan history, for simplicity.

**Before (today).** Completing a backlog item in this repo (before the 2eb72237 policy change) archived a dated per-item file under `docs/history/backlog/completed/`. That directory now holds 318 such files (2026-08-16 through 2026-09-25) that duplicate the completed-plan history, inflate Layer 3, and fight the open-inbox consolidation rule (one work-type SOT, absorbed micros deleted). Consumer repos bootstrapped before the policy change still teach and run the per-item archive, so each one grows the same duplicate history.

**After (this plan).** A mechanical migration helper matches every completed item to a destination plan (or to this plan's own migrated-disposition section when no related completed plan exists), appends the one-bullet disposition, deletes the per-item file, and records the migration in the registry (migration notes on the item and destination rows; unregistered items gain new rows, collision-suffixed when needed). The completed inbox keeps only its README stating the empty-inbox policy. The five skills already teach fold-then-delete and stay clean under a verification sweep. Consumer repos reuse the same helper for their own migrate passes (external, Ship when).

**Matching example (mechanism, synthetic mini-corpus).** Completed item `2026-09-01-review-panel-hermeticity-dimension.md` tokenizes (date prefix stripped, hyphen split) to `review panel hermeticity dimension`; a completed plan named `2026-09-02-review-panel-hermeticity-dimension.md` shares all four tokens and wins the match. An item sharing fewer than two tokens with every completed plan is unmatched and self-hosts. Stop-word tokens are excluded before scoring, and score ties resolve deterministically (lexicographically smallest destination stem) with every tie line flagged in the mapping report for executor review. The real corpus matching is never applied blind: Task 2 writes a mapping report first, the executor reviews a sample, and wrong pairs are corrected through an overrides file before any apply.

**Edge cases.** An item completed with no implementing plan (quick fixes) self-hosts. An item whose related plan is only deferred (not completed) self-hosts, because destinations must be completed-plan records. An item already carrying a registry row (the P54 backfill wave) keeps its row's `src` and gains the migration note; an unregistered item gains a new noted row (collision-suffixed when its base identity exists); a destination plan's row gains the received-form note. No row's `src` cell is ever rewritten. Two completed items tokenizing identically both map to the same destination; each gets its own bullet, so no information is lost.

## Evaluation Criteria

**Quality dimensions:**
- correctness: after apply, the completed inbox holds zero dated item files; every deleted item has exactly one disposition bullet in its destination; `doc_registry_validator validate` exits 0; `deferred/` and `rejected/` are byte-identical to the pre-migration tree.
- maintainability: the helper is reusable for consumer repositories (its directory and registry paths arrive as flags; no repo-specific constants are hardcoded), and dry-run is the default so a bare invocation can never mutate.
- observability: the mapping report records, before any mutation, every item's disposition (matched destination or self-host), so the executor reviews the whole mapping before the first deletion.

**Done when:**
- all tasks checked; the unittest suite is green; the Validation Commands block is green on the migrated tree; `docs/history/backlog/completed/README.md` exists with the policy line; the stale-teaching sweep over `agents/skills/` reports zero hits.

**Ship when:**
- sibling CRM deployables and other playbook-bootstrapped repos run the same helper against their own inboxes and empty them (external, per-repo execution).
- company docs and bootstrap mirrors that still teach per-item archiving are synced to the fold-then-delete wording (external).
- the `backlog_completed_dir` retirement decision is made once external tooling stops reading the key (external follow-up; not this plan).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/migrate_backlog_completed.py` *(new)*

**Tests:**
- `scripts/test_migrate_backlog_completed.py` *(new)*

**Documentation:**
- `docs/history/backlog/completed/README.md` *(new)*
- `docs/history/backlog/completed/2026-*.md` (the migrated per-item corpus; every matched file is deleted by Task 3)
- `docs/plans/completed/<matched-plan>.md` (disposition bullets; the concrete set is matcher-derived at execution)
- `docs/maintenance/document-registry.md` (migration notes on item and destination rows; new rows for unregistered items and the README)
- `docs/plans/2026-09-25-backlog-completed-archive-policy.md` (this plan; the self-host disposition section)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/deferred/**` and `docs/history/backlog/rejected/**`; reason: frozen archives, origin step 2 and the doc-hierarchy revival rule.
- `docs/history/backlog/*.md` top-level open items; reason: the live inbox is not migration input.
- `scripts/plan_readiness.py`, `scripts/check_plan_origins_closed.py`, `scripts/check_backlog_claimed.py`; reason: parser and checker surface owned by the open plans-lifecycle/readiness-parser integrity plan.
- `agents/skills/**` except drift fixes the Task 5 sweep prescribes; reason: the policy wording landed in 2eb72237; this plan verifies, not rewrites.

## Design Invariants (CR Guard)

- `docs/history/backlog/deferred/` and `docs/history/backlog/rejected/` stay byte-untouched (origin step 2; doc-hierarchy treats them as permanent history).
- The `backlog_completed_dir` facts key stays in `.ai-playbook/facts.md` and in bootstrap teaching (tooling compatibility; retirement is an external follow-up).
- Skill texts keep the fold-then-delete teaching; no task rewords any skill back toward per-item archiving.
- Registry `src` cells of migrated rows stay unchanged (multiply-claimed-src gate); migration evidence lives in `audit` cells and in appended rows for unregistered items, never in `src` rewrites.
- The readiness-parser checker surface named out of scope above is not modified by this plan.

## Validation Commands

Pre-round gate record: `plan_readiness.py --pre-round` exit 0 over these bytes (2026-09-25); `check-no-em-dash.sh file` green over this plan; public hygiene scan exit 0; the Task 5 sweep pattern's positive control fires against its own control line (mechanism named beside that command). Record any failure class beside this line before round 1.

```bash
#!/usr/bin/env bash
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

# 1. helper unit suite
( cd scripts && python3 -m unittest test_migrate_backlog_completed ) || fail "unittest suite"

# 2. completed inbox holds zero dated item files (explicit zero assertion, not a bare grep)
leftover=$(find docs/history/backlog/completed -maxdepth 1 -name '[0-9][0-9][0-9][0-9]-*.md' | wc -l | tr -d ' ')
[ "$leftover" -eq 0 ] || fail "completed inbox still holds $leftover dated item files"

# 3. README policy line present
grep -qF 'must stay empty of dated item files' docs/history/backlog/completed/README.md || fail "README policy line missing"

# 4. registry table validates
python3 scripts/doc_registry_validator.py --root . validate >/dev/null 2>&1 || fail "doc_registry_validator validate"

# 5. no move-teaching left in the skills layer (rc split: 0 = match = fail, 1 = clean, >=2 = tool error)
PAT='move (this|the) (file|item) to .*backlog/completed'
# positive control: the pattern must match a known carrier line; the control deliberately
# embeds the searched phrase (self-reference is the mechanism, the sweep target agents/skills/
# never contains this plan's bytes)
printf 'move this file to docs/history/backlog/completed/x.md\n' | grep -qiE "$PAT" || fail "sweep pattern dead (positive control did not fire)"
grep -riE "$PAT" agents/skills/ > /tmp/mig_sweep_hits.txt 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then fail "stale move-teaching in agents/skills (see /tmp/mig_sweep_hits.txt)"; fi
if [ "$rc" -ge 2 ]; then fail "sweep tool error rc=$rc"; fi

# 6. em-dash scan over this plan's created files
bash scripts/check-no-em-dash.sh file docs/history/backlog/completed/README.md scripts/migrate_backlog_completed.py scripts/test_migrate_backlog_completed.py || fail "em-dash in created files"

# 7a. frozen archive dirs carry no uncommitted worktree damage
git diff --quiet HEAD -- docs/history/backlog/deferred docs/history/backlog/rejected
rc=$?
[ "$rc" -eq 0 ] || fail "frozen archive dirs changed or git error (rc=$rc)"
# 7b. no commit since this plan's authoring base touched the frozen archive dirs
base=$(git log --format=%H -- docs/plans/2026-09-25-backlog-completed-archive-policy.md | tail -1)
[ -n "$base" ] || fail "cannot resolve this plan's authoring base commit"
n=$(git log --oneline "$base..HEAD" -- docs/history/backlog/deferred docs/history/backlog/rejected | wc -l | tr -d ' ')
[ "$n" -eq 0 ] || fail "$n commit(s) touched frozen archive dirs since the plan base"
# 7c. frozen archive file counts unchanged (catches untracked additions and deletions)
df=$(find docs/history/backlog/deferred -type f | wc -l | tr -d ' ')
[ "$df" -eq 99 ] || fail "deferred/ file count changed: $df (expected 99)"
rf=$(find docs/history/backlog/rejected -type f | wc -l | tr -d ' ')
[ "$rf" -eq 1 ] || fail "rejected/ file count changed: $rf (expected 1)"

echo "VALIDATION OK"
```

### Task 1: Migration helper with unittest coverage (TDD)

Files:
- `scripts/test_migrate_backlog_completed.py` *(new)*
- `scripts/migrate_backlog_completed.py` *(new)*

CLI contract (pinned for tests and Task 2/3 use): `--plans-dir DIR`, `--backlog-completed-dir DIR`, `--registry FILE`, `--self-host FILE` (this plan's path), `--overrides FILE` (lines: `<item-stem> <destination-plan-relpath>`), `--report FILE` (dry-run mapping report), `--apply` (mutate; default is dry-run), `--date YYYY-MM-DD` (audit-note date; defaults to today). Exit 0 on success, 2 on usage error.

Matcher contract (pinned): date-prefix strip, hyphen tokenization, stop-word exclusion set {a, an, and, or, the, of, to, in, on, for, with}; score = shared-token count; a destination needs at least two shared tokens; ties resolve by lexicographically smallest destination stem; the report flags every tie line.

Apply contract (pinned): every mutation is paired with its write-gate license in the same run; item deletions are licensed by a noted item row (existing or newly appended), destination bullet appends are licensed by a note on the destination plan's registry row, and both notes carry the leading `user-approved <migration date>:` token in the empty-cell and pre-filled forms pinned in Assumptions; item-row notes name the destination they folded into, while destination-row notes use the received form naming what arrived: `user-approved <migration date>: migration audit - received <former-item-relpath> disposition (per-item file deleted)`; a destination with no registry row is backfilled first (new row: identity scheme with collision escalation, state completed, `archived` = migration date, received-form note), and edits to the self-host destination (this living top-level plan) need no license.

- [x] `MatcherTest#test_exact_stem_match`; given a fixture plans dir holding `2026-09-02-review-panel-hermeticity-dimension.md` and a completed item `2026-09-01-review-panel-hermeticity-dimension.md`, expects the matcher maps the item to that plan (all tokens shared). [class: REPOSITORY_TEST]
- [x] `MatcherTest#test_single_token_overlap_unmatched`; given an item stem sharing fewer than two tokens with every fixture plan, expects the item classified self-host. [class: REPOSITORY_TEST]
- [x] `MatcherTest#test_best_score_wins`; given one plan sharing three tokens and another sharing two, expects the three-token plan selected. [class: REPOSITORY_TEST]
- [x] `MatcherTest#test_tie_break_deterministic`; given two fixture plans sharing the same top score with an item, expects the lexicographically smallest destination stem selected and the tie flagged in the report. [class: REPOSITORY_TEST]
- [x] `MatcherTest#test_stop_words_excluded`; given an item stem `review-and` and a plan stem `review-and-fix`, expects no match: without the stop-word exclusion the shared pair {review, and} would reach the two-token threshold, with it only {review} remains and stays below it (discriminating both directions). [class: REPOSITORY_TEST]
- [x] `ApplyTest#test_missing_destination_fails`; given an overrides file naming a destination plan that does not exist in the fixture tree, expects `--apply` to exit non-zero before any mutation. [class: REPOSITORY_TEST]
- [x] `ApplyTest#test_unregistered_item_gets_row_note`; given a completed item with no registry row, expects `--apply` to append a new row (identity = filename minus date prefix, `src` = the item path, state completed) whose `audit` cell carries the full `user-approved <migration date>:` migration note, licensing the deletion; and given an item whose base identity already exists in the registry, expects the MMDD-suffixed identity, escalating to the directory tag when the date collides too, per the registry header's identity scheme. [class: REPOSITORY_TEST]
- [x] `ApplyTest#test_destination_row_noted`; given a destination plan whose registry row has an empty `audit` cell, expects `--apply` to write the received-form migration note (`user-approved <migration date>: migration audit - received <former-item-relpath> disposition (per-item file deleted)`) into that row's `audit` cell when it appends the disposition bullet, so the body edit is licensed at the done boundary; and given a pre-filled destination cell, expects the appended `; received <former-item-relpath> disposition (per-item file deleted)` form. [class: REPOSITORY_TEST]
- [x] `ApplyTest#test_rowless_destination_backfilled_and_licensed`; given a destination plan with no registry row, expects `--apply` to append the backfill row (identity scheme with collision escalation, state completed, `archived` = the migration date, received-form note) before appending the bullet; the test then pipes the changed paths as name-status lines to the real `python3 scripts/doc_registry_validator.py --root <fixture> check-writes --stdin` and asserts exit 0 (the validate-exit-0 oracle cannot see this defect class). [class: REPOSITORY_TEST]
- [x] `ApplyTest#test_apply_folds_bullet_and_deletes`; given a matched pair in a fixture tree, expects `--apply` appends exactly one bullet naming the former item path under `## Disposition of migrated backlog items` in the destination plan and deletes the item file; a second `--apply` run expects no change (idempotent no-op). [class: REPOSITORY_TEST]
- [x] `ApplyTest#test_self_host_section`; given an unmatched item, expects `--apply` appends its bullet to the `--self-host` file's migrated-disposition section and deletes the item file. [class: REPOSITORY_TEST]
- [x] `ApplyTest#test_registry_audit_note_src_unchanged`; given a fixture registry holding one row whose `src` names the item path with an empty `audit` cell and one row with existing audit content, expects `--apply` to replace the empty cell with `user-approved <migration date>: migration audit - disposition folded into <destination-plan-relpath>; per-item file deleted`, append `; migrated <migration date>: disposition folded into <destination-plan-relpath>; per-item file deleted` to the pre-filled cell, leave `src` and all other cells byte-identical, and leave rows without that src unchanged; the test then seeds the fixture's minimal `.ai-playbook/facts.md`, registers the fixture's completed-history files, and asserts `python3 scripts/doc_registry_validator.py --root <fixture> validate` exits 0 over the produced registry. [class: REPOSITORY_TEST]
- [x] `ApplyTest#test_frozen_dirs_untouched`; given a fixture tree with files under `deferred/` and `rejected/`, expects `--apply` never reads or modifies them (byte-compare). [class: REPOSITORY_TEST]
- [x] `ApplyTest#test_overrides_win`; given an overrides file naming `item-stem destination`, expects the override destination used instead of the matcher's choice. [class: REPOSITORY_TEST]
- [x] `ReportTest#test_dry_run_writes_report_and_mutates_nothing`; given a fixture tree, expects `--report` writes one line per item naming its disposition (matched destination or self-host) and the tree is byte-identical after the run. [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd scripts && python3 -m unittest test_migrate_backlog_completed )` (module missing = import error counts as RED). [class: REPOSITORY_TEST]
- [x] Implement `scripts/migrate_backlog_completed.py` (stdlib only; date-prefix stripping and hyphen tokenization shared by matcher and report; registry edited as text lines preserving byte layout of untouched rows). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: same command, suite green. [class: REPOSITORY_TEST]
- [x] Commit: `feat: add backlog-completed fold-then-delete migration helper` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Dry-run inventory and mapping manifest review

Files:
- none tracked; the report lives under `{tmp_dir}/backlog-completed-migration/` (ephemeral session artifact; the durable record is the dispositions themselves)

- [x] Run the dry-run over the real tree: `python3 scripts/migrate_backlog_completed.py --plans-dir docs/plans/completed --backlog-completed-dir docs/history/backlog/completed --registry docs/maintenance/document-registry.md --self-host docs/plans/2026-09-25-backlog-completed-archive-policy.md --report docs/tmp/backlog-completed-migration/mapping-report.md`; expect exit 0 and a report line for each of the 318 completed items. [class: IMPLEMENTATION_REQUIRED]
- [x] Review every tie-flagged report line plus a 10-item sample of unique matches by opening each named destination plan and confirming the same theme; correct wrong pairs through the overrides file; record final counts (matched, self-host) in the session log. [class: IMPLEMENTATION_REQUIRED]
- [x] Regenerate the mapping report after the overrides file is written, so the reviewed-and-corrected mapping (not the matcher's first pass) is what Task 3 applies. [class: REPOSITORY_TEST]
- [x] Interim gate (stage-scoped to artifacts that exist now): the report exists, every item line names exactly one destination, and no line references a `deferred/` or `rejected/` path. [class: REPOSITORY_TEST]

### Task 3: Apply the migration in month batches

Rollback: each batch is a single commit; a wrong batch reverts whole with `git revert <batch-commit>`, restoring the deleted items and their disposition bullets together; no narrower undo is prescribed.

Files:
- existing completed plans under `docs/plans/completed/` named by the Task 2 mapping report (disposition bullets appended; no new files created)
- `docs/maintenance/document-registry.md` (audit-cell notes)
- the dated per-item files under the completed inbox named by the Task 2 mapping report (all deleted by this task)

- [x] Apply the 2026-08 batch, then probe the registry: run `python3 scripts/doc_registry_validator.py --root . validate`; expect exit 0 with `src` cells unchanged, audit notes added on both the item and destination rows, and every produced note carrying the leading `user-approved <migration date>:` token. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the 2026-08 batch: `docs: migrate 2026-08 completed backlog to fold-then-delete dispositions` [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the 2026-09 batch the same way; expect the completed inbox to hold only files this plan created (none yet). [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the 2026-09 batch: `docs: migrate 2026-09 completed backlog to fold-then-delete dispositions` [class: IMPLEMENTATION_REQUIRED]

### Task 4: README policy note for the completed inbox

Files:
- `docs/history/backlog/completed/README.md` *(new)*

- [x] Create `docs/history/backlog/completed/README.md` stating: the directory exists for `backlog_completed_dir` tooling compatibility; it must stay empty of dated item files; completion folds disposition into the matching `{plans_completed_dir}` plan then deletes the item (pointer to `plans` **Plan Lifecycle**); mirrors the profile-microservice README convention named in the origin. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the README's registry row to `docs/maintenance/document-registry.md` (state completed, `src` naming the README path) with a `user-approved <migration date>:` audit note, so the new file is a registered completed-history record and its add passes the done-boundary `check-writes` gate. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: state empty-inbox policy in backlog completed README` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Skill-text and mirror verification sweep

- [x] Run the stale-teaching sweep (Validation Commands entry 5, pattern included) over `agents/skills/`; expect the positive control to fire and the sweep itself to find zero hits; on any hit, reword the hit to the fold-then-delete teaching and record the file and line in the session log. [class: REPOSITORY_TEST]
- [x] Confirm `bootstrap-ai-playbook` still creates `backlog/completed/` for the tooling key while teaching the empty-inbox policy (the 2eb72237 wording); no edit expected. [class: REPOSITORY_TEST]
- [x] Commit (only if a drift fix landed): `docs: fix residual move-teaching found by archive-policy sweep` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Final validation and closeout

- [x] Run the full Validation Commands block; expect every entry green on the migrated tree. [class: REPOSITORY_TEST]
- [x] Run the corpus origins scan `python3 scripts/check_plan_origins_closed.py`; expect exit 0 with roughly 80 unresolved-origin warnings (the 5 pre-existing plus about 75 migrated origins whose per-item files were deleted by design; r2 faithful-simulation estimate); record in the session log that this warn set is expected and the audit trail lives in the disposition bullets and registry audit notes. [class: REPOSITORY_TEST]
- [x] File the follow-up backlog item (receiving-review Backlog capture) teaching `check_plan_origins_closed.py` the fold-then-delete disposition, for example by consulting registry migration audit notes, so the migrated-origin warn noise is retired with the script's owning surface. [class: IMPLEMENTATION_REQUIRED]
- [x] On completion (done boundary), fold this origin item's disposition into this plan's archived record and delete the origin file per `plans` **Plan Lifecycle**; the self-host section becomes the permanent record for unmatched items. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-08-28-summarizer-cli-followups.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-08-28-telemetry-lock-symlink-toctou.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-08-28-validator-test-coverage-followups.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-08-29-v1-enum-reason-type-gates.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-08-29-v1-finding-message-and-duplicate-id.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-08-30-agterm-comma-splice-residue.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-08-30-source-kind-unhashable-crash.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-08-31-id-fixture-family-hardening.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-08-31-v1-redundant-null-keep-valid-fixtures.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-08-31-v1-required-field-tuple-null-semantics-split.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-01-private-dir-symlink-toctou.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-01-review-test-false-green-completeness-checklist.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-01-single-sot-for-cross-cutting-contract-rules.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-01-stale-snapshot-arm-parse-helper-dedup.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-01-strict-audit-summary-lag.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-04-summarizer-dirfd-flag-constant.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-04-summarizer-set-based-retry-delta.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-04-validator-sibling-version-check.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-05-cleanup-scope-preserve-preexisting-content.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-05-missing-parent-arm-path-predicate.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-05-summarizer-lag-arm-classes-witness.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-05-summarizer-read-path-ancestor-dirfd.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-05-vrs-exclusivity-message-oxford-and.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-06-chronic-reabsorption-masks-rebreak.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-06-dirfd-open-error-loses-path-context.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-06-done-run-start-probe-coverage.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-06-read-byte-buffer-ancestor-symlink-residual.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-06-vrs-unclosed-fence-warning-print-wording.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-07-plans-233-restatement-governance.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-07-plans-step14-meta-rule-grilling-duplication.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-07-summarizer-pinned-open-helper-dedup.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-08-plans-trunk-branch-confirmation.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-08-producer-template-freshness-contract.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-08-review-loop-rule4-stop-clause-anchor.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-08-validation-nomatch-rc2-hardening.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-09-plans-trailer-date-pointer-rewrite.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-09-runtime-hermeticity-witness-gaps.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-10-flexible-predecessor-lineage-precondition.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-11-doc-hierarchy-duplicated-deferred-tree-line.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-11-quota-probe-calibration-fallback.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-11-vrs-quotePath-pin-vs-worktree-entries-reuse.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-12-deferred-convention-em-dashes.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-12-quota-probe-write-flag-exception-scope.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-12-runtime-test-git-env-coverage.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-13-codex-deny-envelope-verification.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-14-budget-guard-deployed-hook-copies.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-14-budget-probe-codex-fail-open-diagnostics-collapse.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-14-budget-probe-vacuous-resourcewarning-witness.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-14-drift-witness-gitignored-corpus-fallback.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-14-maintenance-clear-procedure-stale-id-remedy.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-15-maintenance-authoring-lane-chaining-gap.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-15-maintenance-indefinite-operation.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-15-maintenance-paused-execution-resume.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-cross-surface-globish-brevity-policy.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-done-lock-one-shot-shell-handoff.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-finder-applescript-folder-reference-10006.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-graphify-skill-package-version-drift.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-learn-skill-usage-issue-backlog-capture.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-review-retention-and-safe-pruning.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-review-round-record-selection.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-scheduler-dispatch-fallback.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-successor-chaining-after-plan-completion.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-zcode-memory-files-external-rewrites.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-17-maintenance-darkness-detection-concurrent-done-race.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-18-authoring-lane-claim-check-gap.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-18-done-rearm-on-touch-mechanical-gate.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-18-done-sweep-gate-runner-codification.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-18-untracked-nested-git-dir-hygiene.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-19-b2p2-remaining-origin-item-closure.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-19-bootstrap-doc-hierarchy-greenfield-path-ordering.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-19-cache-breakpoint-overflow-token-cost.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-19-edit-failure-churn-read-discipline.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-19-host-caveat-durability-claim-scope.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-19-recycling-update-flip-refuted-delete-plus-create.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-19-selection-helper-suffix-shadowing.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-20-merge-session-content-fixture.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-20-quota-fire-at-straddle-midnight-and-paraphrase-freeze.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-20-waiting-capacity-reclaim-fence-exhausted-window-evidence.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-21-audit-review-agents-for-portability.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-21-automate-skill-version-drift-repair.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-21-done-review-thread-completion-gate.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-21-merge-dirt-regression-gate.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-21-successor-duty-primitive-absence-park-fallback.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-21-vendored-runtime-catalog-landing-gap.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-22-blueprint-payload-telemetry-paths-keep-literal-prefix.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-22-deferral-sweeps-must-cross-check-claimed-origins.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-22-dirt-gate-staged-deletion-edge.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-completed-provenance-convention-consolidation.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-d1-recert-drift-flag-instead-of-silent-skip.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-dfm-cr-f4-origins-gate-singular-form.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-dfm-cr-f5f6f8-gate-suite-under-constraints.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-dfm-cr-f7-receiving-review-tag-mapping.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-dfm-cr-f9-pricing-phrase-clarity.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-dfm-r6-gate-comment-misgrouping.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-dirt-gate-origin-disposition-unrecorded.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-doing-code-review-incomplete-literal-and-partial-recovery-status.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-p37-turn-usage-variant-b-precision.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-panel-profile-filename-date-calendar-validity.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-parallel-fleet-cap-four-children.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-plans-shared-body-forbidden-term-precheck.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-registry-archived-date-semantics.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-runtime-capabilities-zcode-frozen-region-hits.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-scheduler-execution-queue-and-durable-priority-directive.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-23-user-directed-dispatch-dedup-guard.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-24-scheduler-discharge-parked-intents-in-same-session.md: disposition folded into 2026-09-25-backlog-completed-archive-policy.md (2026-09-25); per-item file deleted.

(This section is empty at authoring time. Task 3 appends one bullet per unmatched migrated item here, and the section rides to `{plans_completed_dir}` when this plan completes, giving every deletion a durable disposition home.)

## Execution record (2026-09-25)

Executed in ad-hoc worktree `ai-playbook-exec-archivepol` off main 56a38ade. All six tasks completed. Counts: 318 items migrated (21 dated 2026-08, 297 dated 2026-09), 211 matcher/override destinations, 107 self-hosted into this plan's section; zero overrides needed (tie review by literal origins-mention confirmation plus title-theme inspection). Registry audit notes: 398 `user-approved 2026-09-25:` notes written (item and destination rows); identities collision-escalated per the header scheme.
Deviations and notes:
- Helper parser bug found and fixed during the 2026-09 batch: the row-parser's header-skip heuristic keyed on the word "identity" and skipped any row whose identity contains it (the rfc-design-create-mode-identity-header-wiring family), producing two spurious backfill rows; rows repaired in place on the original 219/344 rows, helper fixed to key on the literal header cell, unit suite re-run green.
- The full validation block printed VALIDATION OK exit 0; one run showed a trailing environmental `SEC_ERROR_PKCS11_DEVICE_ERROR` line emitted after script exit by the host shell (not a block entry; direct rerun rc=0).
- Origins scan: 116 unresolved-origin warnings (expected migrated-origin noise; plan estimated ~80, the difference is pre-existing unannotated rows), recorded as expected; follow-up backlog item filed at docs/history/backlog/2026-09-25-teach-origins-checker-fold-then-delete.md.
- Interim verification strengthened beyond the plan text: 97 of 211 matched items are literally named in their destination plan's bytes (origins/annotations), the remainder confirmed by title-theme inspection.

## Origin disposition

Origin docs/history/backlog/2026-09-25-backlog-completed-archive-policy.md: implemented in full by this plan (executed 2026-09-25); the backlog file is deleted per the plans-skill completion step rather than archived per-item.
