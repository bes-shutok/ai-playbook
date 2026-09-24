# Plan: docs-branch sync and worktree lifecycle safety

Backlog origins (scope of record, four items under `docs/history/backlog/`):
`2026-09-18-docs-branch-sync-reverts-certified-plan-bytes.md` (HIGH: fail-closed ordering fix required),
`2026-09-18-worktree-closeout-migrate-review-docs.md`,
`2026-09-18-overlapping-execution-children-worktree-isolation.md`,
`2026-09-19-docs-branch-sync-backlog-duplicate-sweep.md`.

## Terms

- **docs-branch sync**: the Step 2 script of `agents/skills/docs-branch/SKILL.md`; snapshots the shadow tree and commits it to the orphan `docs` branch through a temporary worktree.
- **Shadow tree**: the gitignored doc paths the sync preserves (`docs/reviews/`, `docs/tmp/`, plus repo-specific candidates); tracked doc paths under `docs/` ride along in the same snapshot.
- **Certified plan sidecar**: the `.stats.json` review sidecar under `{reviews_dir}` whose `source_kind` is `plan` and whose `artifact_slug` equals the plan's feature slug (the basename sans `.md` with the leading `YYYY-MM-DD-` prefix stripped, mirroring `feature_slug()` in `scripts/plan_readiness.py`); its `source_digest` (SHA-256 of the exact plan bytes, sometimes stored as a 16-hex prefix) is the certification digest.
- **Certified downgrade**: a sync write that would replace plan bytes matching the certification digest with bytes that do not; the failure class origin 1 records.
- **Ad-hoc worktree**: a secondary `git worktree` a run executes in, whose gitignored directories start empty and die with the worktree.
- **Main checkout**: the primary working checkout the worktree was created from; the corpus home review artifacts must reach.
- **Closeout baseline**: the per-run listing (path plus SHA-256) of `{reviews_dir}` and `{tmp_dir}` files captured at run start, so closeout can enumerate exactly what the run added or modified.
- **Fail-closed / warn-and-continue**: the two sync-gate postures. Fail-closed aborts the sync with a loud error; warn-and-continue prints a warning and proceeds. Postures are per-gate and never swapped.

## Assumptions

- assume `docs/plans/` and `docs/history/backlog/` are tracked on working branches while `docs/reviews/` and `docs/tmp/` are gitignored; basis: `.gitignore` lines `/docs/reviews` and `/docs/tmp/` plus `git ls-files docs/` output, checked 2026-09-19.
- assume a plan sidecar's `source_digest` is SHA-256 of the exact plan bytes and sidecars in the wild may carry it as a 16-hex prefix; basis: `compute_source_digest` in `scripts/validate_review_staging.py` (SHA-256, lowercase hex) and observed sidecars under `docs/reviews/`, 2026-09-19.
- assume the latest certified round for a plan is the sidecar with `source_kind: "plan"`, `artifact_slug` equal to the plan's feature slug (the basename sans `.md` with the leading `YYYY-MM-DD-` prefix stripped, mirroring `feature_slug()` in `scripts/plan_readiness.py`), highest `round` then latest `date`; basis: `feature_slug()` in `scripts/plan_readiness.py` and observed sidecars under `docs/reviews/`, verified 2026-09-19.
- assume script tests run under the repo test venv `$HOME/.agents/venvs/ai-playbook-test/bin/python` (pytest 9.1.1; the bare `python3 -m pytest` form fails on this host); basis: venv probe 2026-09-19, same resolution the hygiene-sweep plan pinned.
- assume peer sessions may hold the shared checkout dirty while execution runs; the executor re-verifies git state before staging and stages only this plan's files by explicit path; basis: repo guidelines and the peer-dirty state observed 2026-09-19.
- assume no `done`/`execute-plan` re-vendor is needed: skill edits land in the repo's `agents/skills/` copies, which the deployed runtime reads through the `~/.agents/skills` symlink; basis: the runtime registry sync model (repo canonical, home skills path is a symlink), checked 2026-09-19.

Decision points requiring a grill: origin-1 remedy: fail-closed sync-time refuse plus restore-leg warn (standing pre-authorization, authoring task prompt 2026-09-19; Gist, Tasks 1-2); origin-2 shape: migration script plus prose wiring, payload clause verified present and not edited (standing pre-authorization, 2026-09-19; Tasks 5-6); origin-3 disposition: keep executions sequential, record the evaluation (standing pre-authorization, 2026-09-19; Task 7); origin-4 shape: sweep script wired warn-and-continue (origin text, 2026-09-19; Tasks 3-4).

## Gist & Examples

Four changes in the docs-branch sync and worktree lifecycle family, one per origin:

1. **Certified-plan ordering guard (origin 1, HIGH)**. Trigger: a session whose on-disk plan bytes are an older shape runs `done`, whose Step 2 syncs the shadow tree. **Before (today)**: the add-only overlay copies the older bytes into the docs worktree and the sync commit replaces the branch copy, even when the branch held the exact certified shape; the next readiness gate on those bytes fails `sidecar source_digest is stale` and recovery needs per-commit blob archaeology (the 2026-09-18 incident). **After (this plan)**: before staging, a guard compares each top-level plan file present in both the incoming snapshot and the worktree against the plan's latest certified sidecar digest; when the write would overwrite certified bytes with non-certified bytes the sync aborts loudly (exit 1, no commit) naming the file, the certified digest, and the sidecar. The restore-fill leg gets a warn-only witness: a plan file restored from the branch whose bytes do not match the certification digest is recorded at restore time, so a later gate failure is explained by history.

2. **Backlog duplicate sweep (origin 4)**. Trigger: a backlog item is archived on the working branch (moved under `completed/` or `deferred/`, usually with a status update); the next sync overlays the archived copy but nothing removes the stale top-level copy. **Before**: the docs branch accumulates open-status duplicates next to their archived twins (202 strays removed by hand on 2026-09-19, 181 drifted). **After**: after the overlay, a sweep drops each top-level `{backlog_dir}/<name>.md` whose archived twin exists on the branch and differs from it in nothing but the `Status:` line; a deeper mismatch is surfaced and kept, never deleted. The sweep is warn-and-continue and idempotent.

3. **Worktree closeout migration (origin 2)**. Trigger: a plan run executes in an ad-hoc worktree and ends in a merge plus worktree removal. **Before**: the run's review staging docs, `.stats.json` sidecars, and session logs are gitignored, ride neither the branch commits nor the squash merge, and are destroyed with the worktree; the certification chain breaks retroactively in the main checkout. **After**: run start captures a closeout baseline (path plus SHA-256 of `{reviews_dir}` and `{tmp_dir}` files); closeout enumerates new and modified files against the baseline, copies each to the main checkout at the identical path, verifies each copy by checksum, renames on collision (`<name>.wt-<suffix>` before the extension, both copies kept), and records the migrated list in the run manifest. Worktree removal is allowed only after verified migration; an in-place run (checkout IS the main checkout) is a no-op.

4. **Execution-lane concurrency stance (origin 3)**. Trigger: the 2026-09-18 question of whether overlapping execution children are possible. **Before**: the sequential-executions rule and the removed 2026-09-15 worktree design are recorded as history without the collision rationale or the preconditions a future change must satisfy. **After**: the maintenance skill records the evaluated stance: executions stay sequential on the shared checkout; per-execution worktree isolation stays rejected, with the collision list (Phase 0 branch switches, staged-index races, the done lock, the document-registry archive commit, the merge) and the revisit preconditions written down, so the evaluation is durable and the item closes as evaluated.

Concrete effect: a stale shadow copy can no longer silently outrank a certified plan on the docs branch; an archived backlog item stops leaving open-status ghosts; a worktree run's evidence reaches the main checkout before the worktree dies.

## Design Invariants (CR Guard)

- **Posture split is load-bearing**: the certified-plan guard is fail-closed (a refusal aborts the sync before staging, exit 1); the backlog duplicate sweep is warn-and-continue (never aborts). No fold or fix may swap the postures.
- **The guard compares pristine bytes**: the certified-plan guard runs against the branch worktree BEFORE the shadow overlay copies incoming bytes over it; after `cp -Rp` the worktree no longer holds the branch's previous bytes and a downgrade is unobservable there (r1 F2).
- **A missing guard script is loud**: when the certified-plan guard script is absent at both resolution paths the sync prints a loud warning naming the skipped check and proceeds (consumer-repo compatibility), never a silent skip (r1 F7).
- **Add-only invariant preserved**: the sync's add-only rule keeps exactly one previous exception (`{tmp_dir}` sweep root) plus this plan's bounded duplicate removal. The dedupe removes only top-level backlog files whose archived twin exists on the branch and matches beyond the `Status:` line; it is not a new sweep root, and `{tmp_dir}` remains the one sweep-eligible root. Never widen either exception.
- **The live checkout stays read-only for `refs/heads/docs`**: both new sync gates operate on the temporary worktree copy or read bytes read-only; neither touches the live checkout's shadow files beyond what the existing script already does.
- **Copy, never move first** (origin 2): the worktree copy of every migrated artifact is the backup until the main-checkout copy's checksum verifies; a failed verification leaves both copies in place and reports.
- **No gate-time changes**: `scripts/plan_readiness.py` is untouched; the ordering fix lives at sync time, not in the gate's failure message (the origin's alternative leg is declined).
- **Payload texts are frozen**: the fenced child payloads in `agents/skills/maintenance/prompt-templates.md` are not edited; Task 6 only verifies the already-landed migration clause is present.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the guard refuses exactly the certified-downgrade shape and nothing else; upgrades (incoming bytes match the certification digest), sidecar-less plans, and `completed/` plans pass untouched; the dedupe removes only twin-matched top-level copies and surfaces deeper mismatches; each behavior has a dedicated test arm.
- test coverage: three new stdlib-only unittest suites run green under the repo test venv; every origin's acceptance behavior appears as at least one named test arm.
- simplicity: three small scripts, no new facts keys, no new runtime directories, no new scheduling state.
- maintainability: every wiring obligation has a dedicated validation pin that fails when the obligation is deleted; the edited skill's bash blocks pass `bash -n`.

**Done when:**
- the full Validation Commands block exits 0 on the executed tree.
- the three new test suites pass (RED first, then GREEN per task).
- each wiring pin hits its file, and the docs-branch blocks pass the syntax gate.

**Ship when:**
- consumer repositories that resolve the deployed home copies of the three scripts receive the refreshed copies through the standing single-file copy path (the same deployment shape the repo already uses for its validators); operator-owned, outside this repository.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/docs_branch_plan_guard.py` *(new)*
- `scripts/docs_branch_backlog_dedupe.py` *(new)*
- `scripts/worktree_closeout_migrate.py` *(new)*
- `agents/skills/docs-branch/SKILL.md` (frozen except the Task 2 and Task 4 prescribed insertions and their Rules bullets)
- `agents/skills/execute-plan/SKILL.md` (frozen except the Step 0.4 capture insert and the Phase 5 migration subsection)
- `agents/skills/done/SKILL.md` (frozen except the Step 2 pointer sentence and the one Rules bullet)
- `agents/skills/maintenance/SKILL.md` (frozen except the stance subsection and the one Revisions line)

**Tests:**
- `scripts/test_docs_branch_plan_guard.py` *(new)*
- `scripts/test_docs_branch_backlog_dedupe.py` *(new)*
- `scripts/test_worktree_closeout_migrate.py` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: gate-time messaging is the declined alternative leg; the ordering fix is sync-time by task direction.
- `agents/skills/maintenance/zcode.md`; reason: runtime overlay owns scheduling primitives, not lane policy.
- `agents/skills/maintenance/prompt-templates.md`; reason: verify-only surface; its migration clause already landed 2026-09-19 (peer work), findings there ride plan-related extension only.
- deployed home copies under `~/.ai-playbook/scripts/`; reason: operational deploy targets of the standing copy path, not repository source.

## Validation Commands

```bash
# Interpreter: the repo test venv (bare python3 on this host has no pytest;
# authoring probe 2026-09-19). Override with TESTPY on other hosts.
TESTPY="${TESTPY:-$HOME/.agents/venvs/ai-playbook-test/bin/python}"
"$TESTPY" -m pytest scripts/test_docs_branch_plan_guard.py \
  scripts/test_docs_branch_backlog_dedupe.py \
  scripts/test_worktree_closeout_migrate.py -q

# Syntax gate: every fenced bash block in the edited skill parses standalone.
# The backtick literal is printf-built so this block carries no fence sequence
# (a literal triple backtick here would close the plan's own fenced block).
BT="$(printf '\140\140\140')"
awk -v bt="$BT" '$0 == bt "bash" {f=1;next} $0 == bt {f=0} f' agents/skills/docs-branch/SKILL.md > /tmp/docs-branch-blocks.$$.sh
if bash -n /tmp/docs-branch-blocks.$$.sh; then
  rm -f /tmp/docs-branch-blocks.$$.sh; echo "docs-branch blocks: syntax OK"
else
  rm -f /tmp/docs-branch-blocks.$$.sh; echo "FAIL: docs-branch bash block syntax"; exit 1
fi

# Wiring pins: one dedicated grep per structural obligation; each pin quotes a
# span from the task's prescribed text and fails when that obligation is deleted.
grep -qF 'docs_branch_plan_guard.py' agents/skills/docs-branch/SKILL.md || { echo "FAIL: guard script wiring absent"; exit 1; }
grep -qF 'Certified-plan ordering guard (fail-closed)' agents/skills/docs-branch/SKILL.md || { echo "FAIL: guard posture marker absent"; exit 1; }
grep -qF '|| exit 1' agents/skills/docs-branch/SKILL.md || { echo "FAIL: guard abort posture absent"; exit 1; }
grep -qF 'check-restored' agents/skills/docs-branch/SKILL.md || { echo "FAIL: restore-leg witness absent"; exit 1; }
grep -qF 'docs_branch_backlog_dedupe.py' agents/skills/docs-branch/SKILL.md || { echo "FAIL: dedupe wiring absent"; exit 1; }
grep -qF 'Backlog duplicate sweep (warn-and-continue)' agents/skills/docs-branch/SKILL.md || { echo "FAIL: dedupe posture marker absent"; exit 1; }
grep -qF 'closeout-baseline.json' agents/skills/execute-plan/SKILL.md || { echo "FAIL: Phase 0 baseline capture absent"; exit 1; }
grep -qF 'worktree_closeout_migrate.py' agents/skills/execute-plan/SKILL.md || { echo "FAIL: Phase 5 migration wiring absent"; exit 1; }
grep -qF 'do NOT remove the worktree' agents/skills/execute-plan/SKILL.md || { echo "FAIL: removal gate absent"; exit 1; }
grep -qF 'worktree_closeout_migrate.py migrate' agents/skills/done/SKILL.md || { echo "FAIL: done worktree pointer absent"; exit 1; }
grep -qF 'Ad-hoc worktree ordering' agents/skills/docs-branch/SKILL.md || { echo "FAIL: docs-branch ordering note absent"; exit 1; }
grep -qF 'proceeds without the ordering check' agents/skills/docs-branch/SKILL.md || { echo "FAIL: missing-guard loud warn absent"; exit 1; }
grep -qF 'docs/reviews/' agents/skills/maintenance/prompt-templates.md || { echo "FAIL: payload migration clause absent"; exit 1; }
grep -qF 'Execution-lane concurrency stance' agents/skills/maintenance/SKILL.md || { echo "FAIL: concurrency stance absent"; exit 1; }

# Fold-hardened obligation pins (r3 F2): each fold-hardened line gets its own
# dedicated pin so deleting it cannot stay green.
grep -qF 'if [ ! -f "{tmp_dir}/execute-plan/${PLAN_SLUG}/closeout-baseline.json" ]' agents/skills/execute-plan/SKILL.md || { echo "FAIL: capture re-entry guard absent"; exit 1; }
grep -qF 'GIT_DIR_P="$(cd "$(git rev-parse --git-dir)" && pwd)"' agents/skills/execute-plan/SKILL.md || { echo "FAIL: normalized git-path comparison absent"; exit 1; }

# Ordering chain (r1 F6 fold, r2 F2 marker fix, r3 F1 -e separator): the
# guard sits BEFORE the overlay line that would overwrite the worktree's
# branch copies; the dedupe sits AFTER the plan-archive move-detection
# block it mirrors. GUARD_LN keys on the guard CALL's unique --incoming-root
# argument, not the comment (the comment is shared with the earlier
# resolution block, which always sits before the overlay and would mask an
# inverted call). The pattern starts with -- so grep -F needs -e to stop
# option parsing; without it the command exits 2 on every tree. Line-order
# assertions, abort on any missing marker (fail-closed).
GUARD_LN="$(grep -nF -e '--incoming-root "$SHADOW_TMP"' agents/skills/docs-branch/SKILL.md | head -1 | cut -d: -f1)"
OVERLAY_LN="$(grep -nF 'cp -Rp "${SHADOW_TMP}/${src}" "${DOCS_WORKTREE}/${parent}/"' agents/skills/docs-branch/SKILL.md | head -1 | cut -d: -f1)"
ARCHIVE_LN="$(grep -n 'Plan-archive move detection' agents/skills/docs-branch/SKILL.md | head -1 | cut -d: -f1)"
DEDUPE_LN="$(grep -n 'docs_branch_backlog_dedupe.py' agents/skills/docs-branch/SKILL.md | head -1 | cut -d: -f1)"
if [ -z "$GUARD_LN" ] || [ -z "$OVERLAY_LN" ] || [ -z "$ARCHIVE_LN" ] || [ -z "$DEDUPE_LN" ]; then
  echo "FAIL: ordering-chain marker missing"; exit 1
fi
if [ "$GUARD_LN" -lt "$OVERLAY_LN" ] && [ "$ARCHIVE_LN" -lt "$DEDUPE_LN" ]; then
  echo "ordering chain OK"
else
  echo "FAIL: guard/overlay or archive/dedupe ordering inverted"; exit 1
fi
```

### Task 1: Certified-plan digest guard script (origin 1, HIGH)

Files:
- `scripts/test_docs_branch_plan_guard.py` *(new)*
- `scripts/docs_branch_plan_guard.py` *(new)*

Style: stdlib-only `unittest`, fixtures built in `tempfile.TemporaryDirectory`, mirroring `scripts/test_check_lesson_scope.py` (load the script module by path with `importlib.util`; no repo-state dependence).

- [x] `CertifiedPlanGuardTest#test_guard_refuses_certified_downgrade`; given a branch-root plan copy whose digest matches the plan's latest certified sidecar (`source_kind: "plan"`, `artifact_slug` equal to the plan's feature slug) and an incoming-root copy with different bytes, expects exit non-zero, output naming the plan path, the certified digest, and the sidecar filename [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_guard_allows_certified_upgrade`; given a branch copy whose bytes do not match the certification digest and an incoming copy whose bytes do, expects exit 0 with an upgrade info line naming the plan [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_guard_warns_when_neither_side_matches`; given branch and incoming copies that both differ from the certification digest, expects exit 0 with a warn line naming the plan and the certified digest [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_guard_silent_without_sidecar`; given a plan present in both roots and no sidecar under the reviews dir, expects exit 0 with no refusal [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_guard_ignores_completed_subdir`; given a plan copy only under the plans dir's `completed/` subdirectory, expects it never considered (no refusal regardless of bytes) [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_guard_prefix_digest_sidecar`; given a sidecar whose `source_digest` is the first 16 hex chars of the full digest, expects the downgrade still refused [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_guard_latest_round_wins`; given sidecars r1 (older digest) and r3 (current digest) for one plan, expects the r3 digest treated as certified: an incoming copy matching r1 but not r3 is refused [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_guard_feature_slug_lookup`; given a plan `2026-09-19-<feature>.md` and a sidecar whose `artifact_slug` is `<feature>` (date prefix stripped, the `feature_slug()` shape in `scripts/plan_readiness.py`), expects the lookup to find the sidecar and a downgrade to be refused [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_guard_mixed_round_forms`; given one sidecar with round `"r9"` (string form) and a newer one with round `10` (integer form), expects the integer-10 sidecar treated as latest (string comparison would misorder `"r10" < "r9"` and mixed-type comparison would raise); a downgrade against the integer-10 digest is refused [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_check_restored_warns_on_mismatch`; given a restored plan file whose digest differs from the certification digest, `check-restored` expects exit 0 with a warn line naming the file [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_check_restored_silent_on_match_or_missing_sidecar`; given a restored file matching the certification digest, and separately a restored file with no sidecar, expects exit 0 with no warning [class: REPOSITORY_TEST]
- [x] Run → expect RED: `"$TESTPY" -m pytest scripts/test_docs_branch_plan_guard.py -q` (collection error: the module does not exist yet) [class: REPOSITORY_TEST]
- [x] Implement `scripts/docs_branch_plan_guard.py`: subcommand `guard` with `--incoming-root`, `--branch-root`, `--plans-dir`, `--reviews-dir`; subcommand `check-restored` with `--reviews-dir`, `--plans-dir`, and file arguments. The sidecar lookup keys on the plan's feature slug (basename sans `.md` with the leading `YYYY-MM-DD-` prefix stripped), mirroring `feature_slug()` in `scripts/plan_readiness.py`. Latest-round selection normalizes the round to an integer (strip a leading `r`/`R`, then `int()`), treating a non-numeric round as oldest and breaking ties by date, so string `"r9"` and integer `10` forms compare correctly and never raise. Digest match is prefix-tolerant in one direction: the byte digest equals the sidecar digest or starts with it. Refusal collects every certified-downgrade row, prints them, and exits 1; upgrade/warn lines exit 0; `check-restored` always exits 0 [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `"$TESTPY" -m pytest scripts/test_docs_branch_plan_guard.py -q` (all eleven arms pass; the other two suites do not exist yet and are not run at this task point) [class: REPOSITORY_TEST]
- [x] Deploy the refreshed copy for consumer repos: `cp scripts/docs_branch_plan_guard.py ~/.ai-playbook/scripts/docs_branch_plan_guard.py` [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: certified-plan digest guard for docs-branch sync` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Wire the guard into the docs-branch sync (origin 1)

Files:
- `agents/skills/docs-branch/SKILL.md`

Three insertions into the Step 2 script, in this order:

- [x] Insert the shared resolution block immediately after the cleanup-trap registration (`trap docs_branch_cleanup EXIT INT TERM`) and before the add-only restore section, so both later insertions can use its variables [class: IMPLEMENTATION_REQUIRED]

```bash
# Certified-plan ordering guard (fail-closed): the sync must never commit a
# plan file's older bytes over the newer certified shape the branch holds.
# The certification digest comes from the plan's latest review sidecar.
_ORD_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
_plans_dir_ord="docs/plans"
_reviews_dir_ord="${REVIEWS_DIR:-docs/reviews}"
if [ -f .ai-playbook/facts.md ]; then
  _pd_cfg=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^plans_dir[[:space:]]*=/{gsub(/^plans_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)
  [ -n "$_pd_cfg" ] && _plans_dir_ord="$_pd_cfg"
  _rd_cfg=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^reviews_dir[[:space:]]*=/{gsub(/^reviews_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)
  [ -n "$_rd_cfg" ] && _reviews_dir_ord="$_rd_cfg"
fi
PLAN_GUARD_SCRIPT="${DOCS_BRANCH_PLAN_GUARD_SCRIPT:-${_ORD_TOP}/scripts/docs_branch_plan_guard.py}"
[ -f "$PLAN_GUARD_SCRIPT" ] || PLAN_GUARD_SCRIPT="${HOME}/.ai-playbook/scripts/docs_branch_plan_guard.py"
```

- [x] Insert the guard call immediately after the worktree creation block (the conditional that runs `git worktree add` or creates the orphan branch) and BEFORE the shadow overlay loop, so the guard compares the worktree's pristine branch bytes against the incoming snapshot before `cp -Rp` overwrites them; a refusal aborts before any staging. Placed after the overlay the refuse condition is unreachable: the worktree no longer holds the branch's previous bytes, and every downgrade would degrade to warn-and-continue (r1 F2) [class: IMPLEMENTATION_REQUIRED]

```bash
# Certified-plan ordering guard (fail-closed): compares the worktree's
# PRISTINE branch bytes against the incoming snapshot BEFORE the overlay
# overwrites them; a certified downgrade aborts the sync before staging.
if [ -d "${DOCS_WORKTREE}/${_plans_dir_ord}" ]; then
  if [ -f "$PLAN_GUARD_SCRIPT" ]; then
    python3 "$PLAN_GUARD_SCRIPT" guard \
      --incoming-root "$SHADOW_TMP" \
      --branch-root "$DOCS_WORKTREE" \
      --plans-dir "$_plans_dir_ord" \
      --reviews-dir "$_reviews_dir_ord" || exit 1
  else
    echo "WARN: certified-plan guard script not found; sync proceeds without the ordering check" >&2
  fi
fi
```

- [x] Insert the restore-leg witness immediately after the restore section's unstaged-reset block (`if [ -s "$RESTORED_PATHS_FILE" ]`) and before `RESTORED_PATHS_FILE` is removed, so it can enumerate the restored paths [class: IMPLEMENTATION_REQUIRED]

```bash
# Restore-leg certified-digest witness (warn-and-continue): a plan file just
# restored from the branch whose bytes do not match the latest certified
# sidecar digest is recorded loudly at restore time; refusal remains the
# overlay guard's job above.
if [ -s "$RESTORED_PATHS_FILE" ] && [ -f "$PLAN_GUARD_SCRIPT" ]; then
  grep "^${_plans_dir_ord%/}/" "$RESTORED_PATHS_FILE" | while IFS= read -r _restored_plan; do
    python3 "$PLAN_GUARD_SCRIPT" check-restored \
      --reviews-dir "$_reviews_dir_ord" --plans-dir "$_plans_dir_ord" "$_restored_plan" || true
  done
fi
```

- [x] Add one Rules bullet after the existing add-only-sync bullet: the ordering-invariant sentence, verbatim: `Certified-plan ordering: the sync refuses (exit 1, before staging) any overlay write that would replace plan bytes matching the plan's latest certified sidecar digest with bytes that do not match it, and warns when a restore fills a plan file whose bytes do not match the certification digest; a certified downgrade is never committed, and the refusal names the plan, the certified digest, and the sidecar.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the syntax gate and the five guard wiring pins from Validation Commands (run only those six lines; the other suites and pins belong to later tasks and are not run at this task point) [class: REPOSITORY_TEST]
- [x] Commit: `feat: abort docs-branch sync on certified-plan downgrade` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Backlog duplicate sweep script (origin 4)

Files:
- `scripts/test_docs_branch_backlog_dedupe.py` *(new)*
- `scripts/docs_branch_backlog_dedupe.py` *(new)*

- [x] `BacklogDedupeTest#test_removes_top_level_when_archived_twin_identical`; given a worktree with `backlog/<name>.md` and an identical `backlog/completed/<name>.md`, expects the top-level copy removed and the archived twin untouched [class: REPOSITORY_TEST]
- [x] `BacklogDedupeTest#test_removes_when_twin_differs_only_in_status_line`; given the twins differing in exactly one `Status:` line, expects the top-level copy removed [class: REPOSITORY_TEST]
- [x] `BacklogDedupeTest#test_keeps_and_surfaces_on_body_mismatch`; given twins differing beyond the `Status:` line, expects the top-level copy kept, a warning naming the file, exit 0 [class: REPOSITORY_TEST]
- [x] `BacklogDedupeTest#test_no_twin_left_untouched`; given a top-level item with no archived twin, expects it untouched and no warning [class: REPOSITORY_TEST]
- [x] `BacklogDedupeTest#test_deferred_twin_same_rules`; given a `deferred/` twin, expects the same remove-or-surface rules as `completed/` [class: REPOSITORY_TEST]
- [x] `BacklogDedupeTest#test_idempotent_second_run_noop`; given the tree a first run already swept, expects a second run to change nothing and exit 0 [class: REPOSITORY_TEST]
- [x] `BacklogDedupeTest#test_always_warn_and_continue`; given a worktree where one twin mismatches and another matches, expects the matched copy removed, the mismatch surfaced, exit 0 [class: REPOSITORY_TEST]
- [x] Run → expect RED: `"$TESTPY" -m pytest scripts/test_docs_branch_backlog_dedupe.py -q` (collection error: module missing) [class: REPOSITORY_TEST]
- [x] Implement `scripts/docs_branch_backlog_dedupe.py`: `--worktree-root`, `--backlog-dir`; for every top-level `<name>.md` whose twin exists under `completed/` or `deferred/`, compare after dropping lines matching `^Status:`; equal-after-normalization removes the top-level copy, otherwise warn and keep; always exit 0 [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `"$TESTPY" -m pytest scripts/test_docs_branch_backlog_dedupe.py -q` (all seven arms pass) [class: REPOSITORY_TEST]
- [x] Deploy the refreshed copy: `cp scripts/docs_branch_backlog_dedupe.py ~/.ai-playbook/scripts/docs_branch_backlog_dedupe.py` [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: backlog duplicate sweep for docs-branch sync` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Wire the sweep into the docs-branch sync (origin 4)

Files:
- `agents/skills/docs-branch/SKILL.md`

- [x] Insert the sweep block immediately after the plan-archive move-detection block and before the doc-hierarchy rogue-dir detection block [class: IMPLEMENTATION_REQUIRED]

```bash
# Backlog duplicate sweep (warn-and-continue): drop a stale top-level
# {backlog_dir}/<name>.md copy when its archived twin under completed/ or
# deferred/ exists on the branch and matches beyond the Status line;
# surface (never delete) on a deeper mismatch. Bounded: this removes
# duplicates of archived items only and never widens the sweep-root rule
# ({tmp_dir} stays the one sweep-eligible root).
_backlog_dir_cfg="docs/history/backlog"
if [ -f .ai-playbook/facts.md ]; then
  _bd_cfg=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^backlog_dir[[:space:]]*=/{gsub(/^backlog_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)
  [ -n "$_bd_cfg" ] && _backlog_dir_cfg="$_bd_cfg"
fi
DEDUPE_SCRIPT="${DOCS_BRANCH_DEDUPE_SCRIPT:-${_ORD_TOP}/scripts/docs_branch_backlog_dedupe.py}"
[ -f "$DEDUPE_SCRIPT" ] || DEDUPE_SCRIPT="${HOME}/.ai-playbook/scripts/docs_branch_backlog_dedupe.py"
if [ -f "$DEDUPE_SCRIPT" ] && [ -d "${DOCS_WORKTREE}/${_backlog_dir_cfg}" ]; then
  python3 "$DEDUPE_SCRIPT" --worktree-root "$DOCS_WORKTREE" --backlog-dir "$_backlog_dir_cfg" \
    || echo "WARN: backlog duplicate sweep failed; continuing (warn-and-continue)" >&2
fi
```

- [x] Add one Rules bullet after the tmp-sweep-exception bullet, verbatim: `Backlog duplicate sweep: after the overlay, the sync drops a top-level {backlog_dir} copy whose archived twin under completed/ or deferred/ exists on the branch and matches it beyond the Status: line; a deeper mismatch is surfaced and kept. Warn-and-continue always; never widen this to other roots.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the syntax gate plus the two dedupe wiring pins (scoped to this task's obligations) [class: REPOSITORY_TEST]
- [x] Commit: `feat: sweep stale top-level backlog duplicates on docs-branch sync` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Worktree closeout migration script (origin 2)

Files:
- `scripts/test_worktree_closeout_migrate.py` *(new)*
- `scripts/worktree_closeout_migrate.py` *(new)*

- [x] `WorktreeCloseoutTest#test_capture_records_hashes`; given a source tree with files under two configured dirs, `capture` expects a baseline file listing each path with its SHA-256 [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_migrate_copies_new_and_modified_with_checksum_verify`; given a baseline and a source with one new and one modified file, `migrate` expects both copied to the target at identical paths, byte-verified, and the migrated list written to the manifest [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_migrate_skips_identical_target`; given a target file byte-identical to the source, expects skip (no rename, no rewrite) and a skip note in the manifest [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_migrate_renames_on_collision`; given a target file that exists with different content, expects the incoming copy as `<stem>.wt-<suffix><ext>` beside it and both files present [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_migrate_preserves_symlinks`; given a source file that is a symlink, expects the copy to preserve the link rather than dereference the target into a second regular file [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_migrate_missing_baseline_fails_loud`; given a `--baseline` path that does not exist, expects non-zero exit with a loud message naming the missing baseline (never an implicit empty baseline, which would silently skip pre-existing artifacts) [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_migrate_fails_without_moving_on_verify_error`; given the copy step tampered (patched to write wrong bytes), expects non-zero exit, the source copy still present (copy never moves first), and a loud report [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_migrate_noop_when_source_equals_target`; given `--source` equal to `--target`, expects exit 0 with an in-place no-op note and nothing copied [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_manifest_records_migration`; given a successful migrate, expects the manifest to carry the migrated list with per-file verification status [class: REPOSITORY_TEST]
- [x] Run → expect RED: `"$TESTPY" -m pytest scripts/test_worktree_closeout_migrate.py -q` (collection error: module missing) [class: REPOSITORY_TEST]
- [x] Implement `scripts/worktree_closeout_migrate.py`: `capture` (`--out`, `--dirs`, default `docs/reviews docs/tmp`) writes the path-plus-SHA-256 listing; `migrate` (`--baseline`, `--source`, `--target`, `--manifest`, `--suffix`) enumerates new and modified files against the baseline, copies each with symlink-preserving `shutil` copy semantics (`follow_symlinks=False` for links; nothing assumes rename(2)), verifies each copy by re-read checksum, renames on collision to `<stem>.wt-<suffix><ext>`, appends the migrated/renamed/skipped lists to the manifest, and exits non-zero when any verification fails; a missing baseline file exits non-zero with a loud message naming the path (r2 F4) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `"$TESTPY" -m pytest scripts/test_worktree_closeout_migrate.py -q` (all nine arms pass) [class: REPOSITORY_TEST]
- [x] Deploy the refreshed copy: `cp scripts/worktree_closeout_migrate.py ~/.ai-playbook/scripts/worktree_closeout_migrate.py` [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: worktree closeout review-artifact migration tool` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Wire closeout migration into the run flows (origin 2)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`

- [x] In execute-plan Step 0.4 (session bootstrap), after the manifest-creation block, add the baseline-capture insert; resolve `{reviews_dir}` and `{tmp_dir}` from facts per using-skills Step 0 [class: IMPLEMENTATION_REQUIRED]

```bash
# Closeout baseline: record the pre-run file set of the gitignored artifact
# dirs so closeout can migrate exactly what this run added or modified.
# Capture ONCE per run (r2 F3): a resumed run keeps the original baseline so
# closeout also migrates artifacts created before the interruption.
# Two-tier script resolution mirrors the sync gates' pattern: repo-local
# first, then the deployed home copy (r1 F3).
CLOSEOUT_SCRIPT="${WORKTREE_CLOSEOUT_SCRIPT:-$(git rev-parse --show-toplevel)/scripts/worktree_closeout_migrate.py}"
[ -f "$CLOSEOUT_SCRIPT" ] || CLOSEOUT_SCRIPT="${HOME}/.ai-playbook/scripts/worktree_closeout_migrate.py"
if [ ! -f "{tmp_dir}/execute-plan/${PLAN_SLUG}/closeout-baseline.json" ]; then
  python3 "$CLOSEOUT_SCRIPT" capture \
    --out "{tmp_dir}/execute-plan/${PLAN_SLUG}/closeout-baseline.json" \
    --dirs "{reviews_dir}" "{tmp_dir}"
fi
```

- [x] In execute-plan Phase 5, immediately before the removal block, add the migration subsection: detect an ad-hoc worktree by resolving `git rev-parse --git-dir` and `git rev-parse --git-common-dir` to absolute paths (`cd ... && pwd`) and comparing (raw rev-parse output is relative at the repo root and absolute from subdirectories, so normalization is load-bearing, r1 F5 / r2 F4); when equal, the step is a documented no-op; when unequal, run the migration and gate removal on it [class: IMPLEMENTATION_REQUIRED]

```bash
# Ad-hoc-worktree closeout: migrate gitignored run artifacts to the main
# checkout BEFORE any worktree removal. Worktree removal is allowed only
# after verified migration; if the main checkout is mid-merge, mid-rebase,
# or done-locked, retry the migration and do not remove the worktree while
# blocked. Normalized path comparison (r1 F5, r2 F4 cwd fix): raw rev-parse
# output is relative at the repo root and absolute from subdirectories, so
# both paths are resolved through cd+pwd before comparing; equal in the
# main checkout, unequal in a linked worktree.
GIT_DIR_P="$(cd "$(git rev-parse --git-dir)" && pwd)"
GIT_COMMON_P="$(cd "$(git rev-parse --git-common-dir)" && pwd)"
if [ "$GIT_DIR_P" != "$GIT_COMMON_P" ]; then
  MAIN_ROOT="$(cd "$(dirname "$GIT_COMMON_P")" && pwd)"
  CLOSEOUT_SCRIPT="${WORKTREE_CLOSEOUT_SCRIPT:-$(git rev-parse --show-toplevel)/scripts/worktree_closeout_migrate.py}"
  [ -f "$CLOSEOUT_SCRIPT" ] || CLOSEOUT_SCRIPT="${HOME}/.ai-playbook/scripts/worktree_closeout_migrate.py"
  python3 "$CLOSEOUT_SCRIPT" migrate \
    --baseline "{tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-baseline.json" \
    --source "$(git rev-parse --show-toplevel)" \
    --target "$MAIN_ROOT" \
    --manifest "{tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-migration.json" \
    --suffix "<PLAN_SLUG>" || { echo "closeout migration failed; do NOT remove the worktree" >&2; exit 1; }
fi
```

- [x] In done Step 2 (the paragraph introducing the docs-branch invocation), add one pointer sentence: `When the session runs in an ad-hoc worktree, first migrate the run's review staging docs and session logs to the main checkout (the execute-plan Phase 5 migration, `worktree_closeout_migrate.py migrate`), before the docs-branch sync and in every case before the worktree is removed.` [class: IMPLEMENTATION_REQUIRED]
- [x] In done Rules, add one bullet: `Never remove an ad-hoc worktree before its run's gitignored review artifacts verify present in the main checkout; the docs-branch sync runs where the on-disk corpus is canonical (the main checkout after migration).` [class: IMPLEMENTATION_REQUIRED]
- [x] In docs-branch Rules (or the Step 2 notes), add the ordering note, verbatim: `Ad-hoc worktree ordering: run the sync in the main checkout after closeout migration, never from a worktree that is about to be removed; a sync from a stale worktree can commit doomed bytes and, through the fill-only restore, re-export them later.` [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the already-landed payload clause: `grep -qF 'docs/reviews/' agents/skills/maintenance/prompt-templates.md` (the worktree review-migration bullet and both payload sentences exist; no edit) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the six Task 6 wiring pins (scoped to this task's obligations; earlier pins stay green from their tasks) [class: REPOSITORY_TEST]
- [x] Commit: `feat: wire worktree closeout migration into execution and done flows` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Execution-lane concurrency stance (origin 3)

Files:
- `agents/skills/maintenance/SKILL.md`

Peer-dirty file as of authoring (2026-09-19): re-read the current bytes before editing; anchor both insertions on the `## Invariants` and `## Revisions` headings, which the peer's plan does not touch.

- [x] Add a subsection immediately after the Invariants bullet list, titled `### Execution-lane concurrency stance (evaluated 2026-09-19)`, with exactly this content: overlapping execution children remain forbidden and per-execution worktree isolation remains rejected (the 2026-09-15 removal stands); the collisions that force this are execute-plan Phase 0 branch setup and branch switches (a peer switch sweeps the other's uncommitted files), staged-index races during per-task commits, the done lock, the document-registry archive commit, and the final merge; a future change must first reinstate per-execution worktrees off a snapshot, rework what depends on the shared-checkout assumption (Phase 0 setup, done-lock scope, the archive commit, the merge order policy, the lane guards' discovery arm per worktree, and the state schema's single `progress_mark` per child), and decide the parallelism degree and merge-order policy; until then the two sanctioned overlap shapes stay as they are: one authoring child beside one execution child, and worktree runs only where an operator or plan prescribes them, which the closeout migration (this plan's Task 5) now makes survivable [class: IMPLEMENTATION_REQUIRED]
- [x] Append one Revisions line: `- 2026-09-19 (lane-model evaluation, user-directed proposal evaluated): recorded the concurrency stance above; no design change; the overlapping-executions evaluation closed with the collision list and revisit preconditions.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the stance wiring pin (`Execution-lane concurrency stance`) [class: REPOSITORY_TEST]
- [x] Commit: `docs: record execution-lane concurrency evaluation in maintenance skill` [class: IMPLEMENTATION_REQUIRED]

### Task 8: Final validation

Files:
- none new (validation and residual fixes only)

- [x] Run the full Validation Commands block → expect exit 0 (all three suites green, syntax gate clean, ordering chain OK, all sixteen wiring pins hit) [class: REPOSITORY_TEST]
- [x] Run the public hygiene scan and the no-em-dash scan over the touched paths → expect exit 0 both (`bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` from the repo root; `"${HOME}/.ai-playbook/scripts/check-no-em-dash.sh" touched`) [class: REPOSITORY_TEST]
- [x] Fix any residual the block surfaces, re-run the block to exit 0, and commit any fix: `chore: final validation for docs-branch sync and worktree lifecycle safety` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-18-docs-branch-sync-reverts-certified-plan-bytes.md: disposition folded into 2026-09-19-docs-branch-sync-and-worktree-lifecycle-safety.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-18-worktree-closeout-migrate-review-docs.md: disposition folded into 2026-09-19-docs-branch-sync-and-worktree-lifecycle-safety.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-19-docs-branch-sync-backlog-duplicate-sweep.md: disposition folded into 2026-09-19-docs-branch-sync-and-worktree-lifecycle-safety.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-15-drift-witness-docs-branch-sync-fallback.md: disposition folded into 2026-09-19-docs-branch-sync-and-worktree-lifecycle-safety.md (2026-09-25); per-item file deleted.
