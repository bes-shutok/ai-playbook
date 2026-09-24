# Plan: docs-branch trap registration before the restore region (interrupt-window close)

Reference: docs/history/backlog/2026-09-04-docs-branch-trap-before-restore-region.md (scope of record; source: docs/reviews/2026-09-04-2026-09-03-docs-branch-temp-file-hygiene-code-review-r1.md, round r1, finding F5, Low, `security#temp-file-cleanup-window-before-trap-registration`)

## Terms

- **Step 2 script**: the large fenced bash block in `agents/skills/docs-branch/SKILL.md` (the one whose body defines `docs_branch_cleanup()`); the script that syncs shadow content to the `docs` branch.
- **Restore region**: the `if git show-ref --verify --quiet "refs/heads/${DOCS_BRANCH}"` block of the Step 2 script that restores branch-tracked shadow files missing on disk: its three temp-file pre-declarations, the `mktemp` calls filling them, the restore loop, the unstaging loop, plus the manual `rm -f` block and the `# DOCS_TMP_SWEEP_FILE is intentionally NOT removed here` comment that follow it.
- **The three temp files**: `DOCS_STAGED_DELETES_FILE`, `RESTORED_PATHS_FILE`, `DOCS_TMP_SWEEP_FILE`, the plain `mktemp` files created at the top of the restore region.
- **`docs_branch_cleanup` trap**: `trap docs_branch_cleanup EXIT INT TERM`; at plan-authoring time the function definition and registration sit immediately after the restore region (the predecessor plan moved them before the SHADOW_PATHS empty check); Task 2 moves both above the restore region.
- **Interrupt window**: the span between the first restore-region `mktemp` and the trap registration; a SIGINT/SIGTERM or a mid-region abort inside that span dies under the default signal disposition and leaks the three temp files.
- **mktemp shim / `PROBE_SIG_AT_MKTEMP`**: the exported `mktemp` shell function in the Validation Commands that redirects the script's temp-artifact creation into `$PROBE_TMP`; its env-gated trigger additionally SIGTERMs the script right after the Nth completed `mktemp` returns (used only by Probe 1b).

## Assumptions

- assume the fix targets only the embedded Step 2 script in `agents/skills/docs-branch/SKILL.md`; basis: the backlog item names the docs-branch embedded script, and `docs_branch_cleanup` appears in no other live artifact (only the backlog items and the archived predecessor plan mention it).
- assume the move variant of the suggested fix, moving the function definition and the trap registration together as one unit; basis: the backlog's suggested fix names the move, and bash resolves a trap handler by name when the trap fires; registering before defining would leave a signal arriving in between with no handler, so the definition must precede the registration for the early window to actually be covered.
- assume the split-move design: the `# DOCS_TMP_SWEEP_FILE is intentionally NOT removed here` comment stays attached to the manual `rm -f` block, and only the trap-ownership comment, function definition, and registration move; basis: that comment's "here" refers to the manual rm block's position, and it guards the use-after-delete regression class (r5) where `DOCS_TMP_SWEEP_FILE` gets manually removed despite being consumed downstream.
- assume behavioral verification via extracted-script fixture repos with the mktemp shim (no test framework exists for the embedded script); basis: repo has no bash test harness for skills, and user-level lesson #246 requires a probe, not an absence-grep.
- assume the interrupt-window probe uses a deterministic env-gated shim trigger instead of timing-based signal delivery; basis: the restore region's three plain `mktemp` calls are the Step 2 script's first three `mktemp` invocations (the candidates preamble block uses a `/tmp` file, not `mktemp`; verified at authoring time), so trigger-on-call-3 lands inside the region with no sleeps or races.

## Gist & Examples

In the Step 2 script the three temp files are created at the top of the restore region, but the `docs_branch_cleanup` function and its `trap ... EXIT INT TERM` registration sit only after that region (the predecessor plan moved them there from after the early exit, deliberately without touching the restore region). Any signal or abort between the first `mktemp` and the registration therefore dies under the default disposition and leaks all three files (contents are repo-relative path names, mode 0600: disk hygiene, not disclosure). This is the last unowned span of the temp-file lifecycle: every later path already cleans up via the manual `rm -f` block or the trap.

**Fix**: move the whole unit (the trap-ownership comment `# EXECUTE_PLAN_BACKUP, the worktree mktemp -d dirs, ...`, the `docs_branch_cleanup()` function definition, and the `trap docs_branch_cleanup EXIT INT TERM` registration) to immediately before the restore region (right after `docs_branch_is_explicit_delete()` and before the `# Add-only safety net:` comment block), extending the ownership comment to record the new coverage. The `# DOCS_TMP_SWEEP_FILE is intentionally NOT removed here` comment stays where it is, attached to the manual `rm -f` block. Nothing inside the restore region body changes; the manual `rm -f` block still removes only the first two files; `DOCS_TMP_SWEEP_FILE` is still consumed downstream (worktree sweep drop and staged deletion) and removed only by the trap.

**Interruption exit status (r1 F1 note)**: the cleanup trap is rc-preserving (`rc=$?` captured at handler entry), so a signal-interrupted restore-region run exits with the status current at interruption (0 at the probe's trigger point) rather than a distinctive signal status. That is the predecessor plan's inherited trap semantics, unchanged by this move; a caller distinguishing an interrupted sync from a successful one is out of scope.

**Example (before)**: fixture repo with an empty `docs` branch, the mktemp shim SIGTERMs the script right after the third `mktemp` returns (inside the restore region) → the run dies with rc=143 and leaves 3 files in `$PROBE_TMP` (probed RED at authoring time, 2026-09-05).
**Example (after)**: same fixture → the trap fires, removes all three files, and the run exits rc=0 with `leftovers=0` and the docs-branch tip unchanged (probed GREEN at authoring time against a patched copy carrying the Task 2 move).

## Evaluation Criteria

**Quality dimensions:**
- correctness: a SIGTERM landing inside the restore region (deterministic shim trigger after the third `mktemp`) exits via the cleanup trap with rc=0, `leftovers=0` in `$PROBE_TMP`, and the docs-branch tip unchanged; probed RED today, GREEN after the fix.
- regression safety: all four predecessor probes (early-exit leak, docs-branch-absent first run, full-path smoke, hygiene-abort with `sync_rc` propagation) pass unchanged; the manual `rm -f` block and `DOCS_TMP_SWEEP_FILE` consumption points do not move (full-chain order contract holds).
- maintainability: the moved trap-ownership comment states the interrupt-window coverage and is pinned by grep (`trap-covered from creation`); `bash -n` clean on the extracted script; the NOT-removed comment still anchors to the manual `rm -f` block.

**Done when:**
- The cleanup function definition and trap registration sit immediately before the restore region in the Step 2 script, with the registration preceding the region's first `mktemp` (full-chain order probe passes).
- All five fixture probes (interrupt-window, early-exit leak, docs-branch-absent, full-path smoke, hygiene-abort) pass with `leftovers=0` in `$PROBE_TMP`; the hygiene-abort probe additionally exits 1 with the docs-branch tip unchanged.

**Ship when:**
- A future real `done`-invoked docs-branch sync interrupted during the restore region leaves no `mktemp` litter in `$TMPDIR` (human-owned observation; not a checklist item).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/docs-branch/SKILL.md` (Step 2 script fenced block only: the moved unit, its insertion point, and the extended ownership comment. The restore region body is frozen; this plan's whole risk lesson is that editing it regressed reviews in r2/r5. All other content of the file (frontmatter, Core Concepts, Documentation paths, Steps 1/1.5, Recovery, Rules, Integration Points, and every other fenced block) is frozen; reject findings touching them.)

**Tests:**
- none (probe logic lives inline in Validation Commands; no test files are added)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by the explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- any other skill under `agents/skills/`; reason: this plan changes only the docs-branch Step 2 script
- `docs/plans/2026-09-05-plan-readiness-migration.md` and its review artifacts; reason: a parallel session's in-flight files, not this plan's work
- `/tmp/docs-branch-facts.$$` handling in the Step 1 preamble block; reason: pre-existing, unrelated to the trap lifecycle moved here

## Design Invariants (CR Guard)

- Preserve the predecessor plan's fix: the registration stays before the SHADOW_PATHS empty check and before `EXECUTE_PLAN_BACKUP` creation; this plan only moves it earlier (its order contract is a strict superset of the predecessor's chain).
- `DOCS_TMP_SWEEP_FILE` is never manually `rm -f`'d: it is consumed downstream (worktree sweep drop and staged deletion) and only the trap removes it; the manual `rm -f` block stays scoped to the first two files (the r5 use-after-delete class).
- The `# DOCS_TMP_SWEEP_FILE is intentionally NOT removed here` comment stays attached to the manual `rm -f` block; do not move it with the trap unit.
- Zero edits inside the restore region body; the moved unit is inserted before the `# Add-only safety net:` comment block, nothing is reordered inside the region (the r2 leak class).
- The probes' env-strip enumeration (`env -u` names and `/dev/null` pins) is closed; any addition is an explicit delta to the list, matching the predecessor plan's hermeticity contract.

## Validation Commands

Probes run the REAL extracted Step 2 script in throwaway fixture repos; leak/interrupt detection uses the exported mktemp shim redirecting artifact creation into `$PROBE_TMP` (macOS `mktemp` ignores `$TMPDIR`). Probed at authoring time (2026-09-05): against the unfixed tree the early-exit probe is green (`rc=0 leftovers=0`) and the block fails at the NEW probe printing `interrupt-window probe: rc=143 leftovers=3` followed by `FAIL: interrupted restore-region run must exit via the cleanup trap (got rc=143)`; the order-contract segment run standalone against the unfixed tree also fails (`fn=115 trap=131 mk=55 ...`, registration after the first mktemp). Against a patched copy of `SKILL.md` carrying exactly the Task 2 move, the full block prints `ALL CHECKS PASSED` (all five probes green, full chain `fn < trap < mk < rm < notrm < ebp < exit` holds, comment pin present). The `PROBE_SIG_AT_MKTEMP` trigger is env-gated: with the variable unset (every probe except 1b) the shim behaves exactly as the predecessor suite's shim. The env-strip enumeration and `/dev/null` hygiene pins carry over from the predecessor suite unchanged; it is a closed list, and any future GIT_* addition is an explicit delta. Run the block with a standard PATH grep (`/usr/bin/grep`, POSIX BRE); the mid-pattern `\[`/`\$` escapes in the order-contract patterns are intentional BRE, and a ugrep-style grep shadowing `grep` on PATH may not match them. The block additionally requires `rg` (ripgrep) on PATH for the hygiene-gate probes; the requirement is enforced fail-loud at extraction time, before any fixture runs.

```bash
set -u
DBRT="$(mktemp -d)"   # private per-run scratch dir (extraction files, shim, probe counter)
export DBRT           # shared with the shim's signal-trigger counter (Probe 1b)
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
# env -u GIT_* names (GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE, GIT_CONFIG_COUNT
# (GIT_CONFIG_KEY_*/GIT_CONFIG_VALUE_* only take effect when COUNT is set, so
# unsetting COUNT suffices), GIT_OBJECT_DIRECTORY, GIT_ALTERNATE_OBJECT_DIRECTORIES,
# GIT_COMMON_DIR, GIT_NAMESPACE, GIT_CEILING_DIRECTORIES) plus REVIEWS_DIR /
# TMP_DIR, and the two /dev/null config exports below; future GIT_* additions
# are explicit deltas to this list. Hygiene-gate ambient inputs are pinned per
# invocation (not env -u): the gate resolves PUBLIC_HYGIENE_PATTERNS_FILE and
# CONFLUENCE_MIRROR_HYGIENE_SCRIPT as ${VAR:-${HOME}/...}; /dev/null fails the
# gate's regular-file test (WARN path) and its [ -x ] test, while the always-on
# ABS_HOME_RG check stays active.
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
# Probe 1b trigger: when PROBE_SIG_AT_MKTEMP is set, count each COMPLETED mktemp
# in $DBRT/mkcount and, on the Nth call, send SIGTERM to the script right AFTER
# the path was returned; the signal lands mid-restore-region (that region's
# three plain mktemp calls are the script's first three).
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
  if [ -n "${PROBE_SIG_AT_MKTEMP:-}" ]; then
    printf 'x\n' >> "$DBRT/mkcount"
    _c=$(wc -l < "$DBRT/mkcount" | tr -d ' ')
    [ "$_c" = "$PROBE_SIG_AT_MKTEMP" ] && kill -TERM "$$"
  fi
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
DOC_BRANCH_AFTER=$(git -C "$FIX" rev-parse 'refs/heads/docs^{commit}' 2>/dev/null) || DOC_BRANCH_AFTER=""
rm -rf "$FIX" "$PROBE_TMP"
echo "early-exit probe: rc=$EARLY_RC leftovers=$EARLY_LEFT"
[ "$EARLY_RC" -eq 0 ] || { echo "FAIL: early-exit run must exit 0"; exit 1; }
[ "$EARLY_LEFT" -eq 0 ] || { echo "FAIL: early-exit run leaks $EARLY_LEFT temp file(s) into TMPDIR"; exit 1; }
[ "$DOC_BRANCH_AFTER" = "$DOC_BRANCH_BEFORE" ] || { echo "FAIL: early-exit run advanced the docs branch (before=$DOC_BRANCH_BEFORE after=$DOC_BRANCH_AFTER); early exit was not exercised"; exit 1; }

# Probe 1b: interrupt-window close (the behavioral witness for this plan's fix).
# Empty docs branch, no shadow content; the shim trigger SIGTERMs the script
# immediately after the third mktemp returns, i.e. inside the restore region
# right after its last temp-file creation. The trigger cannot reach deeper
# mid-region positions (the restore loop makes no mktemp calls); those are
# guarded by the full-chain order contract below, not by a behavioral probe.
# Before the fix the trap registers only after that region, so the default TERM
# disposition kills the run: rc=143, leftovers=3. After the fix the registration
# precedes the region, the trap fires and removes all three files: rc=0,
# leftovers=0, docs-branch tip unchanged.
make_fixture
PROBE_TMP=$(mktemp -d); export PROBE_TMP
: > "$DBRT/mkcount"
PROBE_SIG_AT_MKTEMP=3; export PROBE_SIG_AT_MKTEMP
INTR_BEFORE=$(git -C "$FIX" rev-parse 'refs/heads/docs^{commit}')
[ -n "$INTR_BEFORE" ] || { echo "FAIL: docs branch tip unresolvable before interrupt-window run"; exit 1; }
cat "$DBRT/candidates.sh" "$DBRT/step2.sh" > "$FIX/sync.sh"
( cd "$FIX" && . "$DBRT/shim.env" && env -u REVIEWS_DIR -u TMP_DIR -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_CONFIG_COUNT -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES -u GIT_COMMON_DIR -u GIT_NAMESPACE -u GIT_CEILING_DIRECTORIES PUBLIC_HYGIENE_PATTERNS_FILE=/dev/null CONFLUENCE_MIRROR_HYGIENE_SCRIPT=/dev/null bash sync.sh ) >/dev/null 2>&1
INTR_RC=$?
INTR_LEFT=$(ls -A "$PROBE_TMP" | wc -l | tr -d ' ')
INTR_AFTER=$(git -C "$FIX" rev-parse 'refs/heads/docs^{commit}' 2>/dev/null) || INTR_AFTER=""
unset PROBE_SIG_AT_MKTEMP
rm -rf "$FIX" "$PROBE_TMP"
echo "interrupt-window probe: rc=$INTR_RC leftovers=$INTR_LEFT"
[ "$INTR_RC" -eq 0 ] || { echo "FAIL: interrupted restore-region run must exit via the cleanup trap (got rc=$INTR_RC)"; exit 1; }
[ "$INTR_LEFT" -eq 0 ] || { echo "FAIL: interrupted restore-region run leaks $INTR_LEFT temp file(s)"; exit 1; }
[ "$INTR_AFTER" = "$INTR_BEFORE" ] || { echo "FAIL: interrupt-window run advanced the docs branch (before=$INTR_BEFORE after=$INTR_AFTER)"; exit 1; }

# Order contract (full chain): cleanup function definition < trap registration <
# first restore-region mktemp < manual rm block < NOT-removed comment <
# EXECUTE_PLAN_BACKUP creation < SHADOW_PATHS empty check.
fn_ln=$(grep -n '^docs_branch_cleanup() {$' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
trap_ln=$(grep -n '^trap docs_branch_cleanup EXIT INT TERM$' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
mk_first=$(grep -n 'DOCS_STAGED_DELETES_FILE=$(mktemp)' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
rm_manual=$(grep -n '\[ -f "$DOCS_STAGED_DELETES_FILE" \] && rm -f' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
notrm_ln=$(grep -n 'DOCS_TMP_SWEEP_FILE is intentionally NOT removed here' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
ebp_ln=$(grep -n '^EXECUTE_PLAN_BACKUP=""$' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
exit_ln=$(grep -n 'if \[ ${#SHADOW_PATHS\[@\]} -eq 0 \]; then' "$DBRT/step2.sh" | head -1 | cut -d: -f1)
[ -n "$fn_ln" ] && [ -n "$trap_ln" ] && [ -n "$mk_first" ] && [ -n "$rm_manual" ] && [ -n "$notrm_ln" ] && [ -n "$ebp_ln" ] && [ -n "$exit_ln" ]   || { echo "FAIL: order-contract anchors missing (if grep on PATH is not POSIX BRE - e.g. a ugrep-style shadow - the mid-pattern escapes match nothing; rerun with /usr/bin/grep)"; exit 1; }
[ "$fn_ln" -lt "$trap_ln" ] && [ "$trap_ln" -lt "$mk_first" ] && [ "$mk_first" -lt "$rm_manual" ] && [ "$rm_manual" -lt "$notrm_ln" ] && [ "$notrm_ln" -lt "$ebp_ln" ] && [ "$ebp_ln" -lt "$exit_ln" ]   || { echo "FAIL: cleanup definition + trap registration must precede the restore region's first mktemp; the manual rm block and NOT-removed comment stay between it and EXECUTE_PLAN_BACKUP before the SHADOW_PATHS empty check (fn=$fn_ln trap=$trap_ln mk=$mk_first rm=$rm_manual notrm=$notrm_ln ebp=$ebp_ln exit=$exit_ln)"; exit 1; }
grep -q 'trap-covered from creation' "$DBRT/step2.sh" \
  || { echo "FAIL: interrupt-window coverage comment missing"; exit 1; }

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
# the Step 2 hygiene gate without needing a patterns file). The sync_rc
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

### Task 1: RED: reproduce the interrupt-window leak with the fixture probe

Files:
- `agents/skills/docs-branch/SKILL.md` (read-only this task)

- [x] Run the Validation Commands block → expect the early-exit probe green (`early-exit probe: rc=0 leftovers=0`), then FAIL at the interrupt-window probe printing `interrupt-window probe: rc=143 leftovers=3` followed by `FAIL: interrupted restore-region run must exit via the cleanup trap (got rc=143)`; this is the RED witness that the window is open today (witness taken 2026-09-05 with the pre-fix tree; the block aborts there, before the order contract)
- [x] Record the probe output in the task log; do not modify any file in this task (the order-contract segment's own RED against the pre-fix tree was additionally witnessed at authoring time: `fn=115 trap=131 mk=55`, registration after the first mktemp)

### Task 2: GREEN: move the cleanup unit above the restore region

Files:
- `agents/skills/docs-branch/SKILL.md`

- [x] Cut the whole unit (the three comment lines from `# EXECUTE_PLAN_BACKUP, the worktree mktemp -d dirs, FILTERED_GITIGNORE, and` through `# covers every mktemp artifact of this script.`, the `docs_branch_cleanup()` function body, and the `trap docs_branch_cleanup EXIT INT TERM` registration line) from its current position immediately after the restore region's NOT-removed comment block
- [x] Paste the unit immediately before the line `# Add-only safety net: restore shadow files that exist on the docs branch but are` (i.e. after `docs_branch_is_explicit_delete()`'s closing brace and a blank line), with the unit's three comment lines replaced by, verbatim: `# EXECUTE_PLAN_BACKUP, the worktree mktemp -d dirs, FILTERED_GITIGNORE, and` / `# EXTRA_IGNORE_RULES are created below this line and are trap-owned; the trap` / `# covers every mktemp artifact of this script. It registers BEFORE the restore` / `# region so the region's three mktemp files are trap-covered from creation: a` / `# SIGINT/SIGTERM or mid-region abort can no longer leak them.`; keep the function body and the `trap` registration line byte-identical, and leave one blank line between the registration and the Add-only comment
- [x] Verify nothing else moved: the `# DOCS_TMP_SWEEP_FILE is intentionally NOT removed here` comment still directly follows the manual `rm -f` block; every line inside the restore region body (pre-declarations through the unstaging loop) is byte-identical; `bash -n` clean on the extracted Step 2 block
- [x] Trace the lifecycle in the task log: registration (new position, above the region) → the three temp files created inside the region, now trap-covered from creation → manual `rm -f` of the first two → `DOCS_TMP_SWEEP_FILE` consumed downstream (worktree sweep drop + staged deletion) and removed only by the trap → `EXECUTE_PLAN_BACKUP`, `SHADOW_TMP`, worktree dirs, `FILTERED_GITIGNORE`, `EXTRA_IGNORE_RULES` created below the registration, trap-owned; confirm the two regression classes are structurally closed: a signal in the window hits the registered trap (r2 leak class) and no consumption point reads a manually deleted file (r5 use-after-delete class)
- [x] Run → expect GREEN: the full Validation Commands block passes (`ALL CHECKS PASSED`: all five probes `leftovers=0`, interrupt-window probe `rc=0`, full order chain satisfied, comment pin present)
- [ ] Commit: `docs-branch: register cleanup trap before the restore region`

### Task 3: Final certification

Files:
- `agents/skills/docs-branch/SKILL.md` (only if a defect surfaced in Task 2; otherwise read-only)

- [x] Run → expect GREEN: full Validation Commands block passes from a clean shell (`bash -n` included)
- [x] `git status --short` shows no unintended files staged; parallel sessions share this checkout: any file this task did not create or edit (e.g. a peer session's plan or review artifacts) is NOT part of this plan and must not be committed
- [ ] Commit (only if Task 3 made edits): `docs-branch: trap-before-restore-region certification fixes`

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-04-docs-branch-trap-before-restore-region.md: disposition folded into 2026-09-05-docs-branch-trap-before-restore-region.md (2026-09-25); per-item file deleted.
