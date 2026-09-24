# Plan: docs-branch temp-file hygiene pass (trap registration ordering)

Reference: docs/history/backlog/2026-08-31-docs-branch-temp-file-hygiene.md (r6 finding F5, Low; residual of the r2 F2 fix)

## Terms

- **Step 2 script**: the large fenced bash block in `agents/skills/docs-branch/SKILL.md` (the one whose body defines `docs_branch_cleanup()`); the script that syncs shadow content to the `docs` branch.
- **SHADOW_PATHS empty check / early exit**: `if [ ${#SHADOW_PATHS[@]} -eq 0 ]; then exit 0; fi` in the Step 2 script.
- **The three temp files**: `DOCS_STAGED_DELETES_FILE`, `RESTORED_PATHS_FILE`, `DOCS_TMP_SWEEP_FILE`, i.e. the plain `mktemp` files created inside the `if git show-ref --verify --quiet refs/heads/${DOCS_BRANCH}` block.
- **`EXECUTE_PLAN_BACKUP`**: a `mktemp -d` backup of an active execute-plan session dir, created before the early exit.
- **`docs_branch_cleanup` trap**: `trap docs_branch_cleanup EXIT INT TERM`; at plan-authoring time registered after the early exit; Task 2 moved it before the early exit and before `EXECUTE_PLAN_BACKUP` creation.

## Assumptions

- assume the fix targets only the embedded Step 2 script in `agents/skills/docs-branch/SKILL.md`; basis: the backlog item names the docs-branch embedded script and no other artifact carries this logic.
- assume the trap-move variant of the suggested fix (not the create-files-later variant); basis: the three temp files and `EXECUTE_PLAN_BACKUP` must exist before the early exit, and the backlog's fix-risk triage rule forbids reordering the regression-prone restore region (r2 leak, r5 use-after-delete).
- assume behavioral verification via extracted-script fixture repos (no test framework exists for the embedded script); basis: repo has no bash test harness for skills, and user-level lesson #246 requires a probe, not an absence-grep.

## Gist & Examples

In the Step 2 script, the three temp files are created (inside the `git show-ref` block), two of them get manual `rm -f` after the restore block, but `DOCS_TMP_SWEEP_FILE` is deliberately kept: it is consumed later by the worktree sweep drop and staged-deletion step, and the `docs_branch_cleanup` trap removes it. The trap, however, is registered only after the SHADOW_PATHS empty check at plan-authoring time. Any run that hits

```
if [ ${#SHADOW_PATHS[@]} -eq 0 ]; then
  exit 0
fi
```

therefore leaks `DOCS_TMP_SWEEP_FILE` into the system temp directory (and `EXECUTE_PLAN_BACKUP` leaks in the variant where `docs/tmp/execute-plan/<slug>/manifest.md` exists but `docs/tmp/` is not gitignored, so it does not become a shadow path). Contents are repo-relative path names with 0600 modes (disk hygiene, not disclosure), but every early-exit run leaves litter.

**Fix**: move the `docs_branch_cleanup()` definition and its `trap ... EXIT INT TERM` registration from their position at plan-authoring time (after the early exit) to immediately after the `# DOCS_TMP_SWEEP_FILE is intentionally NOT removed here` comment block that closes the restore region (directly before the `SHADOW_PATHS=()` construction), before `EXECUTE_PLAN_BACKUP` is created and before the early exit. Everything the cleanup function touches is already `-n`-guarded, so registering it early is safe; the plain `exit 0` then flows through the trap (rc 0, no-op cleanup). This gives one owner for the whole temp-file lifecycle without touching the restore region that regressed in r2/r5.

**Example (before)**: fixture repo whose `docs` branch exists but is empty, no gitignored shadow content → script creates `DOCS_TMP_SWEEP_FILE`, hits the early exit, the system temp directory has 1 leftover file.
**Example (after)**: same fixture → no mktemp artifacts left in the temp directory after the run (observed as `leftovers=0` in `$PROBE_TMP` under the shim); exit code still 0; full-path sync runs unchanged.

## Evaluation Criteria

**Quality dimensions:**
- correctness: an early-exit run (docs branch exists, `SHADOW_PATHS` resolves empty) leaves no mktemp artifacts in the temp directory (`leftovers=0` under the shim) and exits 0; probed RED today, GREEN after the fix.
- regression safety: a full-path sync run (gitignored shadow content present) still commits shadow content to the `docs` branch, leaves on-disk files in place, and leaves `leftovers=0` in `$PROBE_TMP`; `DOCS_TMP_SWEEP_FILE` consumption points downstream of the trap registration are not moved.
- maintainability: the trap registration region carries the trap-ownership comment pinned by grep (`cleanup covers the SHADOW_PATHS-empty early exit`), and the order-contract greps enforce that the registration precedes the early exit; `bash -n` clean on the extracted script.

**Done when:**
- Trap registration + function definition sit between the manual `rm -f` block and `EXECUTE_PLAN_BACKUP` creation in the Step 2 script (line-order probe passes).
- All four fixture probes (docs-branch-absent guard, early-exit leak, full-path smoke, hygiene-abort) pass with `leftovers=0` in `$PROBE_TMP`; the hygiene-abort probe additionally exits 1 with the docs-branch tip unchanged.

**Ship when:**
- Next real `done`-invoked docs-branch sync on this repo completes with no `mktemp` leftovers in `$TMPDIR` (human-owned observation; not a checklist item).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/docs-branch/SKILL.md` (Step 2 script region only; the rest of the file is frozen; reject findings touching prose, other steps, or other skills' files)

**Tests:**
- none (probe logic lives inline in Validation Commands; no test files are added)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by the explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- any other skill under `agents/skills/`; reason: this plan changes only the docs-branch Step 2 script
- `/tmp/docs-branch-facts.$$` handling in the Step 1 block; reason: pre-existing, unrelated to the temp-file lifecycle moved here

## Validation Commands

Probes run the REAL extracted Step 2 script in throwaway fixture repos. Because macOS `mktemp` ignores `$TMPDIR`, leak detection uses an exported `mktemp` shim that redirects the script's temp-artifact creation into a dedicated `$PROBE_TMP` directory; a leftover file in `$PROBE_TMP` after the run is the leak witness. Probed at authoring time (2026-09-03): the early-exit probe reports `rc=0 leftovers=1` against the unfixed script (the leaked `DOCS_TMP_SWEEP_FILE`) and `leftovers=0` with the trap moved; the docs-branch-absent first-run probe and the full-path smoke pass before and after. Post-review update (2026-09-04, r1 fixes F2-F4): Probe 1's fixture additionally commits an un-ignored `docs/tmp/execute-plan/slug/manifest.md` so the `EXECUTE_PLAN_BACKUP` leak variant is exercised before the early exit; the block cleans up after itself on failure paths via an EXIT trap; the block's own scratch files (extracted blocks, shim) live in a private per-run scratch directory rather than shared `/tmp` names, so concurrent runs cannot collide; fixture git calls run with `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null` and the sync.sh invocations strip a closed, exhaustively enumerated set of ambient variables: nine `env -u` GIT_* names (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_CONFIG_COUNT` — whose `GIT_CONFIG_KEY_*`/`GIT_CONFIG_VALUE_*` only take effect when COUNT is set — plus `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR`, `GIT_NAMESPACE`, `GIT_CEILING_DIRECTORIES`) and `REVIEWS_DIR`/`TMP_DIR`, alongside the two `/dev/null` config exports; any future GIT_* addition is an explicit delta to this list. The env-injection family (`GIT_CONFIG_COUNT` and dependents, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`) comes from lesson #5404; the repo-redirection trio (`GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE`) and the remaining names are this plan's own hermeticity additions. Post-review update (2026-09-04, r3 fixes F1-F4): the strip was extended from the config-only subset to the full family above (ending the per-variable GIT_* regeneration), and Probe 1 gained a docs-branch-unchanged witness (the early exit makes no docs-branch commit). Post-review update (2026-09-04, r5 fixes F1-F4): the sync.sh invocations additionally pin the two hygiene-gate ambient inputs `PUBLIC_HYGIENE_PATTERNS_FILE` and `CONFLUENCE_MIRROR_HYGIENE_SCRIPT` to `/dev/null` via inline `env` assignments (not `env -u`: both are resolved by the gate as `${VAR:-${HOME}/...}`, so a set variable beats the `${HOME}` fallback — which exists on this machine — and an inline assignment beats a host export, whereas `-u` would strip an exported pin and reactivate the fallbacks). Mechanism note (corrected in the r6 pass): `/dev/null` is a character device, so the gate's regular-file test fails on it and the deny-pattern scan is neutralized via the WARN path (no patterns file found in the fixture), not via `rg -f /dev/null`; the hygiene-script pin fails its `[ -x ]` test; either way the deterministic ABS_HOME_RG check stays active), and a fourth probe drives the hygiene gate's failing arm to witness the r4 `sync_rc` propagation (rc=1, leftovers=0, docs-branch tip unchanged).

```bash
set -u
DBRT="$(mktemp -d)"   # private per-run scratch dir (extraction files, shim)
FIX=""
PROBE_TMP=""
cleanup() {
  [ -n "${FIX:-}" ] && rm -rf "$FIX"
  [ -n "${PROBE_TMP:-}" ] && rm -rf "$PROBE_TMP"
  [ -n "${DBRT:-}" ] && rm -rf "$DBRT"
}
trap cleanup EXIT
# Fixture hermeticity: neutralize the user's global/system gitconfig so
# commit.gpgsign or global hooks cannot break the probes' git init/commit.
# The sync.sh invocations strip a closed, exhaustively enumerated set: nine
# env -u GIT_* names (GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE (repo
# redirection, this plan's addition), GIT_CONFIG_COUNT (GIT_CONFIG_KEY_*/
# GIT_CONFIG_VALUE_* only take effect when COUNT is set, so unsetting COUNT
# suffices; the env-injection family per lesson #5404), GIT_OBJECT_DIRECTORY,
# GIT_ALTERNATE_OBJECT_DIRECTORIES, GIT_COMMON_DIR, GIT_NAMESPACE,
# GIT_CEILING_DIRECTORIES) plus REVIEWS_DIR / TMP_DIR, and the two /dev/null
# config exports below; future GIT_* additions are explicit deltas to this list.
# Hygiene-gate ambient inputs are pinned per invocation (not env -u): the gate
# resolves PUBLIC_HYGIENE_PATTERNS_FILE and CONFLUENCE_MIRROR_HYGIENE_SCRIPT as
# ${VAR:-${HOME}/...}, so a set variable beats the ${HOME} fallback (which exists
# on this machine), and an inline env assignment beats a host export; -u would
# strip an exported pin and reactivate the fallbacks. /dev/null fails the gate's
# regular-file test (WARN path: no deny-pattern scan runs) and its [ -x ] test,
# while the always-on ABS_HOME_RG check stays active.
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
SKILL=agents/skills/docs-branch/SKILL.md
test -f "$SKILL" || { echo "FAIL: $SKILL missing"; exit 1; }

# dump_block <unique-marker-inside-block>: print the first bash fenced block containing the marker
dump_block() {
  awk -v pat="$1" '/^```bash$/{inb=1;buf="";next} inb&&/^```$/{if(index(buf,pat)){printf "%s",buf;exit} inb=0;next} inb{buf=buf $0 "\n"}' "$SKILL"
}
dump_block 'SHADOW_CANDIDATES=(' > "$DBRT/candidates.sh" || exit 1
dump_block 'docs_branch_cleanup()' > "$DBRT/step2.sh" || exit 1
grep -q 'SHADOW_CANDIDATES=(' "$DBRT/candidates.sh" || { echo "FAIL: candidates block not extracted"; exit 1; }
grep -q 'docs_branch_cleanup()' "$DBRT/step2.sh" || { echo "FAIL: step2 block not extracted"; exit 1; }
bash -n "$DBRT/candidates.sh" || { echo "FAIL: candidates block syntax"; exit 1; }
bash -n "$DBRT/step2.sh" || { echo "FAIL: step2 block syntax"; exit 1; }

# mktemp shim: redirect creation into $PROBE_TMP (macOS mktemp ignores TMPDIR).
cat > "$DBRT/shim.env" <<'SHIM'
mktemp() {
  _d=0; _t=""
  for _a in "$@"; do
    [ "$_a" = "-d" ] && _d=1 || _t=$_a
  done
  _stem=${_t##*/}
  [ -n "$_stem" ] || _stem="tmp.XXXXXXXXXX"
  _xs=0
  while :; do
    case "$_stem" in
      *X) _xs=$((_xs + 1)); _stem="${_stem%X}" ;;
      *) break ;;
    esac
  done
  [ "$_xs" -gt 0 ] || _xs=10
  _n=0
  while :; do
    _r=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c "$_xs")
    _path="$PROBE_TMP/${_stem}${_r}"
    if [ "$_d" -eq 1 ]; then
      mkdir "$_path" 2>/dev/null && chmod 700 "$_path" && break
    else
      ( set -o noclobber; : > "$_path" ) 2>/dev/null && chmod 600 "$_path" && break
    fi
    _n=$((_n + 1)); [ "$_n" -lt 20 ] || return 1
  done
  printf '%s\n' "$_path"
}
export -f mktemp
SHIM
bash -n "$DBRT/shim.env" || { echo "FAIL: shim syntax"; exit 1; }
command -v rg >/dev/null 2>&1 || { echo "FAIL: rg (ripgrep) is required on PATH for the hygiene-gate probes"; exit 1; }

make_fixture() {
  FIX=$(mktemp -d)
  git -C "$FIX" init -q -b main
  git -C "$FIX" config user.email probe@example.com
  git -C "$FIX" config user.name probe
  git -C "$FIX" commit -q --allow-empty -m init
  git -C "$FIX" checkout -q --orphan docs
  git -C "$FIX" commit -q --allow-empty -m docs-seed
  git -C "$FIX" checkout -q main
}

# Probe 1: early-exit leak (docs branch exists and is empty; no gitignored shadow
# content). The committed, un-ignored docs/tmp/execute-plan/slug/manifest.md makes
# EXECUTE_PLAN_BACKUP creation run before the early exit, so the probe also covers
# the backup-dir variant of the leak.
make_fixture
mkdir -p "$FIX/docs/tmp/execute-plan/slug"
echo plan > "$FIX/docs/tmp/execute-plan/slug/manifest.md"
git -C "$FIX" add docs/tmp && git -C "$FIX" commit -q -m execute-plan-session
PROBE_TMP=$(mktemp -d); export PROBE_TMP
DOC_BRANCH_BEFORE=$(git -C "$FIX" rev-parse 'refs/heads/docs^{commit}')
[ -n "$DOC_BRANCH_BEFORE" ] || { echo "FAIL: docs branch tip unresolvable before run"; exit 1; }
cat "$DBRT/candidates.sh" "$DBRT/step2.sh" > "$FIX/sync.sh"
( cd "$FIX" && . "$DBRT/shim.env" && env -u REVIEWS_DIR -u TMP_DIR -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_CONFIG_COUNT -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES -u GIT_COMMON_DIR -u GIT_NAMESPACE -u GIT_CEILING_DIRECTORIES PUBLIC_HYGIENE_PATTERNS_FILE=/dev/null CONFLUENCE_MIRROR_HYGIENE_SCRIPT=/dev/null bash sync.sh ) >/dev/null 2>&1
EARLY_RC=$?
EARLY_LEFT=$(ls -A "$PROBE_TMP" | wc -l | tr -d ' ')
# Positive early-exit witness: the early exit makes no docs-branch commit, so
# the tip must be unchanged (a vacuous full-path pass would advance it).
DOC_BRANCH_AFTER=$(git -C "$FIX" rev-parse 'refs/heads/docs^{commit}' 2>/dev/null) || DOC_BRANCH_AFTER=""
rm -rf "$FIX" "$PROBE_TMP"
echo "early-exit probe: rc=$EARLY_RC leftovers=$EARLY_LEFT"
[ "$EARLY_RC" -eq 0 ] || { echo "FAIL: early-exit run must exit 0"; exit 1; }
[ "$EARLY_LEFT" -eq 0 ] || { echo "FAIL: early-exit run leaks $EARLY_LEFT temp file(s) into TMPDIR"; exit 1; }
[ "$DOC_BRANCH_AFTER" = "$DOC_BRANCH_BEFORE" ] || { echo "FAIL: early-exit run advanced the docs branch (before=$DOC_BRANCH_BEFORE after=$DOC_BRANCH_AFTER); early exit was not exercised"; exit 1; }

# Order contract (full chain, not pairwise): mktemp creation < restore-region comment
# block < trap registration < EXECUTE_PLAN_BACKUP creation < SHADOW_PATHS empty check.
mk_first=$(grep -n 'DOCS_STAGED_DELETES_FILE=$(mktemp)' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
rm_comment=$(grep -n 'DOCS_TMP_SWEEP_FILE is intentionally NOT removed here' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
trap_ln=$(grep -n '^trap docs_branch_cleanup EXIT INT TERM$' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
ebp_ln=$(grep -n '^EXECUTE_PLAN_BACKUP=""$' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
exit_ln=$(grep -n 'if \[ ${#SHADOW_PATHS\[@\]} -eq 0 \]; then' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
[ -n "$mk_first" ] && [ -n "$rm_comment" ] && [ -n "$trap_ln" ] && [ -n "$ebp_ln" ] && [ -n "$exit_ln" ]   || { echo "FAIL: order-contract anchors missing"; exit 1; }
[ "$mk_first" -lt "$rm_comment" ] && [ "$rm_comment" -lt "$trap_ln" ] && [ "$trap_ln" -lt "$ebp_ln" ] && [ "$ebp_ln" -lt "$exit_ln" ]   || { echo "FAIL: trap must sit between the restore-region rm block and EXECUTE_PLAN_BACKUP, before the SHADOW_PATHS empty check (mk=$mk_first rm=$rm_comment trap=$trap_ln ebp=$ebp_ln exit=$exit_ln)"; exit 1; }
grep -q 'cleanup covers the SHADOW_PATHS-empty early exit' "$DBRT/step2.sh" \
  || { echo "FAIL: trap-ownership comment missing"; exit 1; }

# Probe 2: docs-branch-absent first-run path (no docs branch; gitignored shadow
# content present, so the orphan-creation path runs end to end; regression guard
# that passes before AND after the fix).
FIX=$(mktemp -d)
git -C "$FIX" init -q -b main
git -C "$FIX" config user.email probe@example.com
git -C "$FIX" config user.name probe
printf 'docs/tmp/\n.ai-playbook/\n' > "$FIX/.gitignore"
mkdir -p "$FIX/docs/tmp" "$FIX/.ai-playbook"
echo scratch > "$FIX/docs/tmp/x.md"
echo facts > "$FIX/.ai-playbook/facts.md"
git -C "$FIX" add .gitignore && git -C "$FIX" commit -q -m gitignore
PROBE_TMP=$(mktemp -d); export PROBE_TMP
cat "$DBRT/candidates.sh" "$DBRT/step2.sh" > "$FIX/sync.sh"
( cd "$FIX" && . "$DBRT/shim.env" && env -u REVIEWS_DIR -u TMP_DIR -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_CONFIG_COUNT -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES -u GIT_COMMON_DIR -u GIT_NAMESPACE -u GIT_CEILING_DIRECTORIES PUBLIC_HYGIENE_PATTERNS_FILE=/dev/null CONFLUENCE_MIRROR_HYGIENE_SCRIPT=/dev/null bash sync.sh ) > "$FIX/out.log" 2>&1
NODOC_RC=$?
NODOC_OUT=""
git -C "$FIX" cat-file -e docs:docs/tmp/x.md 2>/dev/null && NODOC_OUT="$NODOC_OUT branch-has-x"
[ -f "$FIX/docs/tmp/x.md" ] && NODOC_OUT="$NODOC_OUT disk-kept"
NODOC_LEFT=$(ls -A "$PROBE_TMP" | wc -l | tr -d ' ')
rm -rf "$FIX" "$PROBE_TMP"
echo "docs-branch-absent probe: rc=$NODOC_RC$NODOC_OUT leftovers=$NODOC_LEFT"
[ "$NODOC_RC" -eq 0 ] || { echo "FAIL: docs-branch-absent run must exit 0"; exit 1; }
case "$NODOC_OUT" in
  *"branch-has-x"*"disk-kept"*) : ;;
  *) echo "FAIL: first-run sync must create the docs branch with shadow content and keep disk files"; exit 1 ;;
esac
[ "$NODOC_LEFT" -eq 0 ] || { echo "FAIL: docs-branch-absent run leaves $NODOC_LEFT temp artifact(s)"; exit 1; }

# Probe 3: full-path smoke (gitignored shadow content present; sync must commit it).
make_fixture
PROBE_TMP=$(mktemp -d); export PROBE_TMP
printf 'docs/tmp/\n.ai-playbook/\n' > "$FIX/.gitignore"
mkdir -p "$FIX/docs/tmp" "$FIX/.ai-playbook"
echo scratch > "$FIX/docs/tmp/x.md"
echo facts > "$FIX/.ai-playbook/facts.md"
git -C "$FIX" add .gitignore && git -C "$FIX" commit -q -m gitignore
cat "$DBRT/candidates.sh" "$DBRT/step2.sh" > "$FIX/sync.sh"
( cd "$FIX" && . "$DBRT/shim.env" && env -u REVIEWS_DIR -u TMP_DIR -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_CONFIG_COUNT -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES -u GIT_COMMON_DIR -u GIT_NAMESPACE -u GIT_CEILING_DIRECTORIES PUBLIC_HYGIENE_PATTERNS_FILE=/dev/null CONFLUENCE_MIRROR_HYGIENE_SCRIPT=/dev/null bash sync.sh ) > "$FIX/out.log" 2>&1
FULL_RC=$?
FULL_OUT=""
git -C "$FIX" cat-file -e docs:docs/tmp/x.md 2>/dev/null && FULL_OUT="$FULL_OUT branch-has-x"
[ -f "$FIX/docs/tmp/x.md" ] && FULL_OUT="$FULL_OUT disk-kept"
FULL_LEFT=$(ls -A "$PROBE_TMP" | wc -l | tr -d ' ')
rm -rf "$FIX" "$PROBE_TMP"
echo "full-path probe: rc=$FULL_RC$FULL_OUT leftovers=$FULL_LEFT"
[ "$FULL_RC" -eq 0 ] || { echo "FAIL: full-path sync must exit 0"; exit 1; }
case "$FULL_OUT" in
  *"branch-has-x"*"disk-kept"*) : ;;
  *) echo "FAIL: full-path sync must commit shadow content and keep disk files"; exit 1 ;;
esac
[ "$FULL_LEFT" -eq 0 ] || { echo "FAIL: full-path sync leaks $FULL_LEFT temp file(s) into TMPDIR"; exit 1; }

# Probe 4: hygiene-abort (Probe-3-shaped fixture, but .ai-playbook/facts.md
# carries an absolute home path, tripping the always-on ABS_HOME_RG check in
# the Step 2 hygiene gate without needing a patterns file). The r4 sync_rc
# propagation must surface the gate's exit 1: rc=1, trap-cleaned temps
# (leftovers=0), docs-branch tip unchanged (abort precedes any docs commit),
# and fixture disk files intact (abort must not delete shadow content).
make_fixture
PROBE_TMP=$(mktemp -d); export PROBE_TMP
printf 'docs/tmp/\n.ai-playbook/\n' > "$FIX/.gitignore"
mkdir -p "$FIX/docs/tmp" "$FIX/.ai-playbook"
echo scratch > "$FIX/docs/tmp/x.md"
printf 'home = /Users/leaker/x\n' > "$FIX/.ai-playbook/facts.md"
git -C "$FIX" add .gitignore && git -C "$FIX" commit -q -m gitignore
ABORT_BEFORE=$(git -C "$FIX" rev-parse 'refs/heads/docs^{commit}')
[ -n "$ABORT_BEFORE" ] || { echo "FAIL: docs branch tip unresolvable before hygiene-abort run"; exit 1; }
cat "$DBRT/candidates.sh" "$DBRT/step2.sh" > "$FIX/sync.sh"
( cd "$FIX" && . "$DBRT/shim.env" && env -u REVIEWS_DIR -u TMP_DIR -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_CONFIG_COUNT -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES -u GIT_COMMON_DIR -u GIT_NAMESPACE -u GIT_CEILING_DIRECTORIES PUBLIC_HYGIENE_PATTERNS_FILE=/dev/null CONFLUENCE_MIRROR_HYGIENE_SCRIPT=/dev/null bash sync.sh ) > "$FIX/out.log" 2>&1
ABORT_RC=$?
ABORT_AFTER=$(git -C "$FIX" rev-parse 'refs/heads/docs^{commit}' 2>/dev/null) || ABORT_AFTER=""
ABORT_TIP=tip-changed
[ "$ABORT_AFTER" = "$ABORT_BEFORE" ] && ABORT_TIP=tip-unchanged
ABORT_DISK=1
[ -f "$FIX/docs/tmp/x.md" ] && [ -f "$FIX/.ai-playbook/facts.md" ] || ABORT_DISK=0
ABORT_LEFT=$(ls -A "$PROBE_TMP" | wc -l | tr -d ' ')
grep -q 'absolute home paths' "$FIX/out.log" || { echo "FAIL: rc=1 not attributed to the ABS_HOME hygiene check"; exit 1; }
rm -rf "$FIX" "$PROBE_TMP"
echo "hygiene-abort probe: rc=$ABORT_RC leftovers=$ABORT_LEFT $ABORT_TIP"
[ "$ABORT_RC" -eq 1 ] || { echo "FAIL: hygiene-aborted sync must exit 1 (got rc=$ABORT_RC); sync_rc propagation broken"; exit 1; }
[ "$ABORT_LEFT" -eq 0 ] || { echo "FAIL: hygiene-aborted run leaves $ABORT_LEFT temp artifact(s)"; exit 1; }
[ "$ABORT_TIP" = tip-unchanged ] || { echo "FAIL: hygiene-aborted run advanced the docs branch (before=$ABORT_BEFORE after=$ABORT_AFTER); gate must abort before any docs commit"; exit 1; }
[ "$ABORT_DISK" -eq 1 ] || { echo "FAIL: hygiene abort deleted fixture shadow content on disk"; exit 1; }

echo "ALL CHECKS PASSED"
```

Note: the trap-ownership comment grep is a positive-presence pin on a distinctive multi-word span; it anchors the comment the fix task adds beside the moved registration. Run the block with a standard PATH grep (`/usr/bin/grep`, POSIX BRE); the mid-pattern `\[`/`\$` escapes in the order-contract patterns are intentional BRE, and a ugrep-style grep shadowing `grep` on PATH may not match them.

### Task 1: RED: reproduce the early-exit leak with the fixture probe

Files:
- `agents/skills/docs-branch/SKILL.md` (read-only this task)

- [x] Run the Validation Commands block → expect it to FAIL at the early-exit case, printing `early-exit probe: rc=0 leftovers=1` (the leaked `DOCS_TMP_SWEEP_FILE`) followed by `FAIL: early-exit run leaks 1 temp file(s) into TMPDIR`, this is the RED witness that the leak exists today (witness taken with the pre-amendment Probe 1 fixture; the amended fixture, which also seeds `docs/tmp/execute-plan/slug/manifest.md`, shows `leftovers=2` pre-fix: `DOCS_TMP_SWEEP_FILE` plus `EXECUTE_PLAN_BACKUP`)
- [x] Record the probe output in the task log; do not modify any file in this task

### Task 2: GREEN: register the cleanup trap before the early exit

Files:
- `agents/skills/docs-branch/SKILL.md`

- [x] Move the `docs_branch_cleanup()` function definition and the `trap docs_branch_cleanup EXIT INT TERM` registration from their current position (after the SHADOW_PATHS empty check) to immediately after the `# DOCS_TMP_SWEEP_FILE is intentionally NOT removed here` comment block that follows the restore block, directly before the `SHADOW_PATHS=()` construction and before `EXECUTE_PLAN_BACKUP` creation
- [x] Beside the trap registration, add the comment block (merged into one block in the r3 address pass from the two adjacent duplicate blocks, both grep anchors kept), verbatim as shipped in `agents/skills/docs-branch/SKILL.md` (r5 sync): `# DOCS_TMP_SWEEP_FILE is intentionally NOT removed here: DOCS_STAGED_DELETES_FILE` / `# and RESTORED_PATHS_FILE are consumed and rm'd in the restore block above, while` / `# DOCS_TMP_SWEEP_FILE is filled there but consumed later (worktree sweep drop and` / `# staged deletion), so only it survives to trap removal; cleanup covers the SHADOW_PATHS-empty early exit.` / `# EXECUTE_PLAN_BACKUP, the worktree mktemp -d dirs, FILTERED_GITIGNORE, and` / `# EXTRA_IGNORE_RULES are created below this line and are trap-owned; the trap` / `# covers every mktemp artifact of this script.`; do not move or edit any line of the restore block or the `DOCS_TMP_SWEEP_FILE` consumption points downstream
- [x] Trace the lifecycle in the task log: creation (show-ref block) → manual rm (first two files) → EXECUTE_PLAN_BACKUP → early exit → SHADOW_TMP/worktree mktemp -d → consumption of `DOCS_TMP_SWEEP_FILE` (sweep drop + staged deletion) → trap removal; confirm the invariant that the three mktemp files (`DOCS_STAGED_DELETES_FILE`, `RESTORED_PATHS_FILE`, `DOCS_TMP_SWEEP_FILE`) are created before the trap registration but are either manually rm'd above it (first two) or trap-removed at exit (`DOCS_TMP_SWEEP_FILE`, all `-n`-guarded in `docs_branch_cleanup`), that `EXECUTE_PLAN_BACKUP` is created after the registration, and that the trap sits before the early exit so nothing survives it; every consumption point still precedes process exit (`SHADOW_TMP` and the worktree dirs sit downstream of the moved trap and are covered by it at exit; `FILTERED_GITIGNORE` and `EXTRA_IGNORE_RULES` are created later still, below the registration, and — per the r4 trap-ownership extension — are now ALSO trap-owned: `docs_branch_cleanup` removes them on early-exit/failure paths, while the success path still manually rm's and unsets them)
- [x] Run → expect GREEN: the full Validation Commands block passes (`leftovers=0` on all four probes, full order chain satisfied)
- [x] Commit: `docs-branch: register cleanup trap before SHADOW_PATHS early exit`

### Task 3: Final certification

Files:
- `agents/skills/docs-branch/SKILL.md` (only if a defect surfaced in Task 2; otherwise read-only)

- [x] Run → expect GREEN: full Validation Commands block passes from a clean shell (`bash -n` included)
- [x] `git status --short` shows no unintended files staged; any modification to files outside the Review Scope (e.g. parallel-session changes to other skills) is NOT part of this plan and must not be committed
- [x] Commit (only if Task 3 made edits): `docs-branch: temp-file hygiene certification fixes` (condition false: Task 3 made no edits, certification green on the Task 2 commit)

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-08-31-docs-branch-temp-file-hygiene.md: disposition folded into 2026-09-03-docs-branch-temp-file-hygiene.md (2026-09-25); per-item file deleted.
