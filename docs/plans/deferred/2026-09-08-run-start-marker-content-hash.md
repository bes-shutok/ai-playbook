# Plan: run-start marker records a repo-root digest instead of the raw path

Backlog origin: `docs/history/backlog/2026-09-07-run-start-marker-content-docs-branch-leak.md` (Security-class standalone direct fix).
Plan review: `docs/reviews/2026-09-08-plan-review-run-start-marker-content-hash-r*.md` (latest round is authoritative).

## Terms

- **Run-start marker**: the per-done-run file `{tmp_dir}/done-session/run-start-<UTCtimestamp>` written at `done` Step 0; its single content line anchors the done session window.
- **Session window**: the anchor-marker-timestamp-to-gate-time interval `done` Step 1.5 uses to decide which plans are this session's deliverables.
- **Content-match confirmation**: gate-time identity check that re-reads the marker and compares its recorded repo identity against the running repo, instead of trusting chat recall.
- **Shadow sync**: the `docs-branch` skill's add-only sync of gitignored docs/tmp paths onto the local orphan `docs` branch; `{tmp_dir}` paths present on disk are added or updated on the branch.

## Assumptions

- assume the remedy is backlog option 1: the marker's middle field becomes the SHA-256 hex digest of the trailing-slash-stripped resolved repo root; the raw path is never recorded; the epoch stays first, the PID stays last and is retained - the scope of record keeps the PID as an audit-only field (done Step 2.62 already declares it non-gate-time: "recorded for post-hoc audit rather than gate-time comparison"); basis: standing pre-authorization accepting the recommended remedy, task prompt, 2026-09-08. Option 2 (excluding markers from the shadow snapshot) is declined: it leaves the raw path in the marker content and needs a docs-branch carve-out plus explicit branch untracking, while option 1 fixes the content at the source.
- assume in-place migration of existing marker files preserves Step 1.5 anchoring for markers that recorded this repo, because content-match confirmation compares the recorded digest against the digest of the same (unchanged) repo root; a marker whose recorded middle field is another repo's raw root is re-stamped with the sha256 of ITS recorded root (not this repo's), so the foreign marker still fails this repo's content match and lands in conservative gating, while its raw path disappears from disk and the branch; basis: `done` Step 1.5 anchor and cross-repo clauses.
- assume `agents/skills/docs-branch/SKILL.md` needs no change: after the rewrite the marker content is non-sensitive, and the branch tip's leaked copies refresh automatically via the shadow sync's update-paths-present-on-disk rule during the execution session's `done`; the done skill executes from `~/.agents/skills/done/SKILL.md`, which is a symlink to this repo's `agents/skills/done/SKILL.md`, so the repo edit is the deployed edit; basis: docs-branch sync invariant ("Sync adds or updates paths present on disk only") and verified symlink `~/.agents/skills -> <repo>/agents/skills` (2026-09-08).
- assume the fix stops NEW leakage only: docs-branch history commits keep raw-path/PID blobs both from before this fix and from any done run in the execution session's Task 1-to-Task 2 window (that window's per-task done writes and syncs a raw-path marker with the still-old recipe), and any future `git push docs` would publish history, not just the tip; whether to rewrite docs-branch history (or recreate the branch) while it is still local-only is a separate human decision, out of scope here; basis: risk review r1 F2, r4 F3, and direct inspection of `refs/heads/docs`.
- assume vendored `done` copies in consumer repos keep the old raw-path recipe until their copy-sync redeploy lands, so their own docs branches need the same migration or the redeploy; that is outside this repo's execution scope and is recorded as a residual in the same human-decision bucket as the history rewrite; basis: risk review r2 F5 and done/SKILL.md's vendored-copy rationale.
- assume the digest is an identity token, not a secrecy mechanism: sha256 of a low-entropy path is dictionary-attackable, so the digest obscures rather than eliminates the recorded path; within the scope of record (plain digest, PID retained) this is accepted; basis: risk review r1 overflow.
- assume the Task 1 migration runs outside any done lock; run it only when no done run is in progress (the repo's done lock is free) so a concurrent raw-path write cannot survive past the migration. Between Task 1 and Task 2 the SKILL.md clauses still compare raw paths, so a done run in that window (for example from a peer session) sees digest markers as a mismatch and lands in conservative gating for that one run - a safe-direction degradation this plan accepts and names; basis: risk review r1/r2.

Decision points requiring a grill: marker remedy selection (option 1 digest vs option 2 shadow-snapshot exclusion) - resolved by standing pre-authorization accepting the recommended remedy, task prompt, 2026-09-08.

## Gist & Examples

**Before (today):** every `done` run writes `run-start-<ts>` whose content line is `<epoch> /Users/<you>/<repo> <pid>`. The Step 2.62 sweep never removes the newest previous-run marker, and the docs-branch shadow sync tracks `docs/tmp/done-session/` onto the local `docs` branch (verified: two live markers with raw paths and PIDs are tracked on `refs/heads/docs`). The repo is public and its guidelines forbid machine-specific absolute paths; any future `git push docs` publishes the home directory layout and PIDs.

**After (this plan):** the same trigger (a `done` run writing its Step 0 marker) produces `<epoch> <64-hex-digest> <pid>`, where the digest is `sha256` of the trailing-slash-stripped resolved repo root. Gate-time identity still works: Step 1.5 and Step 2.62 compare the recorded digest against the digest of the running repo, recomputed via the Step 0 recipe. A marker from a different repo still fails the match and lands in the conservative-gating branch, exactly as the raw-path comparison does today; a middle field that cannot be recomputed or does not match is a content mismatch and never anchors a window.

Example line for a repo rooted at `$REPO_TOP` (values illustrative):

```
Before: 1788825321 /Users/you/myrepo 3302
After:  1788825321 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08 3302
```

Edge cases motivating the design:

- Repo roots containing spaces: the old middle field could contain spaces (parsed positionally). The digest is a single 64-char token, so the three-field parse gets simpler, not harder; the field-order contract (epoch first, PID last, digest between) is unchanged.
- Pre-existing markers: deleting them would break Step 1.5 anchoring (conservative gating for one run - safe but degraded). Migrating them in place keeps epoch and PID and swaps only the middle field, so anchoring keeps working and the disk and branch copies stop carrying the raw path. A foreign-repo marker is re-stamped with the digest of its own recorded root: cross-repo discrimination is preserved and no raw-path marker survives under any classification.
- Task ordering makes the format change atomic for the gate: markers are migrated BEFORE the skill edit lands, and all skill edits (recipe + both confirmation clauses) land in ONE commit, so no done run executes a recipe/clause combination that disagrees with the marker format on disk.
- Hosts without a hash tool: the recipe fails loudly when the digest is missing or malformed instead of writing a degraded marker.
- Cross-tool portability: the recipe prefers `shasum -a 256` and falls back to `sha256sum`; both print the hex digest as the first whitespace-separated field, so one `awk '{print $1}'` serves both. (The fallback arm itself is not exercised on a sha256sum-only host in this plan; it is pinned by literal presence.)

## Evaluation Criteria

**Quality dimensions:**

- correctness: the Step 0 recipe yields a line matching `^[0-9]+ [0-9a-f]{64} [0-9]+$`; the digest equals `sha256` of the trailing-slash-stripped resolved repo root; Step 1.5 and Step 2.62 clauses pin digest comparison recomputed via the Step 0 recipe.
- security: no raw absolute repo-root path appears in the Step 0 spec, the recipe, the migrated marker files, or consequently the docs-branch tip after the next shadow sync; the plan stops new leakage, and the pre-fix docs-branch history blobs are recorded as a residual for a separate human decision; PID-only retention is per the scope of record.
- maintainability: the three reworded clauses stay mutually consistent (one computation, referenced from Step 0); no new script or file is introduced.
- portability: the hash step works on hosts with either `shasum` or `sha256sum`.

**Done when:**

- `agents/skills/done/SKILL.md` Step 0 spec and recipe prescribe the digest form; Step 1.5 and Step 2.62 clauses compare digests recomputed via the Step 0 recipe.
- The Validation Commands block exits 0 against the post-change tree, including migrated live markers under `docs/tmp/done-session/`.
- The block was demonstrated RED before the edits - recorded in the task evidence (see the evidence wording under Validation Commands).

**Ship when:**

- The next shadow sync (the execution session's `done`) refreshes the docs-branch tip copies; a human may then verify `git grep -E '^[0-9]+ /' refs/heads/docs -- docs/tmp/done-session/` finds nothing at the tip. Pushing the `docs` branch remains a human-owned decision and is not a plan task.
- The docs-branch history residual (raw-path/PID blobs, both pre-fix and any committed by Task 1-to-Task 2 window done runs) is dispositioned by a human decision (history rewrite, branch recreation, or accepted-while-local-only); this plan only records the residual.
- The vendored-copy residual (consumer repos' `done` copies still writing raw-path markers until their copy-sync redeploy) is dispositioned by the same human decision bucket; this plan only records the residual.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/done/SKILL.md` - Step 0 marker paragraph and Step 0 recipe block, the Step 1.5 marker-content confirmation clause, and the Step 2.62 `done-session/` sweep bullet. All other steps, clauses, and blocks in this file are frozen; reject any review finding that touches them (out-of-scope findings there become separate notes, not in-place fixes).

**Runtime data (migrated in place, gitignored; verified, not reviewed as code):**

- `docs/tmp/done-session/run-start-*` (existing marker files; epoch and PID preserved, middle field replaced by a digest - this repo's root for own markers, the marker's own recorded root for foreign markers)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/docs-branch/SKILL.md`; reason: under the digest remedy the shadow sync needs no carve-out and its invariants are untouched.
- docs-branch git history rewrite; reason: tip-level fix only; the history residual is recorded, and its disposition is a separate human decision (see Assumptions).
- `docs/tmp/done-session/plan-deliverables.txt`; reason: it records repo-relative paths only, no absolute path or PID.

## Validation Commands

Run the block by writing it to a temp file with a `#!/bin/bash` shebang and invoking `bash <file>` (UL#189 idiom; never paste the body into a zsh shell call - `shopt` does not exist in zsh). The block anchors itself to the repo root, so invocation cwd inside the repo does not matter (outside a git repo it fails loudly).

```bash
#!/bin/bash
set -u
REPO_TOP="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO_TOP" || exit 1
TMP_DIR="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' "$REPO_TOP/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
TMP_DIR="${TMP_DIR:-docs/tmp/}"
case "$TMP_DIR" in /*) ;; *) TMP_DIR="$REPO_TOP/$TMP_DIR";; esac
SKILL="agents/skills/done/SKILL.md"
test -f "$SKILL" || { echo "F0: missing $SKILL"; exit 1; }
grep -qF 'SHA-256 hex digest of the trailing-slash-stripped resolved `$REPO_TOP`' "$SKILL" \
  || { echo "F1: Step 0 digest spec missing"; exit 1; }
grep -qF 'REPO_HASH=' "$SKILL" || { echo "F2: recipe hash variable missing"; exit 1; }
grep -qF '(shasum -a 256 2>/dev/null || sha256sum)' "$SKILL" \
  || { echo "F2b: portable hash fallback missing"; exit 1; }
grep -qF "grep -qE '^[0-9a-f]{64}$'" "$SKILL" || { echo "F2c: digest hex-charset guard missing"; exit 1; }
if grep -qF '${REPO_TOP%/} $$' "$SKILL"; then echo "F3: raw-path recipe still present"; exit 1; fi
if grep -qF 'everything between them is the repo root' "$SKILL"; then echo "F6: old field-order spec still present"; exit 1; fi
if grep -qF 'recorded `$REPO_TOP`' "$SKILL"; then echo "F6b: old raw-path confirmation clause still present"; exit 1; fi
grep -qF 'recomputed via the Step 0 recipe' "$SKILL" \
  || { echo "F4: Step 1.5 digest-match clause missing"; exit 1; }
grep -qF 'recorded digest matching the SHA-256 hex digest of this repo' "$SKILL" \
  || { echo "F5: Step 2.62 digest-match clause missing"; exit 1; }
T="$(mktemp -d)" || exit 1
trap 'rm -rf "$T"' EXIT
printf '%s\n' "1788825321 $(printf '%s' /tmp/demo-repo | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}') 4242" > "$T/m"
grep -qE '^[0-9]+ [0-9a-f]{64} [0-9]+$' "$T/m" || { echo "F7: digest line format probe failed"; exit 1; }
shopt -s nullglob
found=0
for f in "${TMP_DIR%/}"/done-session/run-start-*; do
  found=1
  if grep -qE '^[0-9]+ [0-9a-f]{64} [0-9]+$' "$f"; then continue; fi
  if grep -qE '^[0-9]+ /' "$f"; then
    mid="$(awk '{mid=$2; for(i=3;i<NF;i++) mid=mid" "$i; print mid}' "$f")"
    if [ "$mid" = "${REPO_TOP%/}" ]; then echo "F9: unmigrated own marker $f"; else echo "F8: unmigrated marker (own or foreign): $f"; fi
    exit 1
  fi
  echo "F8: unmigrated marker format in $f"; exit 1
done
shopt -u nullglob
[ "$found" -eq 1 ] || { echo "F10: no run-start markers found under the resolved {tmp_dir}/done-session/"; exit 1; }
EXPECTED="$(printf '%s' "${REPO_TOP%/}" | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}')"
own_ok=0
shopt -s nullglob
for f in "${TMP_DIR%/}"/done-session/run-start-*; do
  if grep -qF " $EXPECTED " "$f"; then own_ok=1; break; fi
done
shopt -u nullglob
[ "$own_ok" -eq 1 ] || { echo "F11: no own marker carries this repo's recomputed digest"; exit 1; }
echo "VALIDATION OK"
```

Authoring-time evidence (recorded 2026-09-08): the block executed against the current tree exits at F1 (`F1: Step 0 digest spec missing`) because the block is fail-fast; the later arms were verified present-red by direct inspection instead - the F3/F6/F6b target texts exist in the current SKILL.md (the two-clause raw-path pattern occurs exactly twice, both Task 2 targets), and both live markers under `docs/tmp/done-session/` carry raw paths (old format), so the raw-marker arms fire against them when reached.

### Task 1: Migrate existing marker files in place (no commit)

Files:
- `docs/tmp/done-session/run-start-*` (runtime files; gitignored - nothing to commit)

- [ ] Verify no done run is in progress (the repo's done lock is free), then write this migration to a temp file with a `#!/bin/bash` shebang and run it as `bash <file>` (UL#189 idiom; never paste into a zsh shell call). It fails loudly outside a git repo, preserves epoch and PID, re-stamps own markers with this repo's digest, re-stamps foreign raw-path markers with the digest of their own recorded root (cross-repo discrimination preserved), and stops on a malformed marker:

```bash
#!/bin/bash
set -eu
REPO_TOP="$(git rev-parse --show-toplevel)" || { echo "migration: not inside a git repo" >&2; exit 1; }
TMP_DIR="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' "$REPO_TOP/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
TMP_DIR="${TMP_DIR:-$REPO_TOP/docs/tmp/}"
case "$TMP_DIR" in /*) ;; *) TMP_DIR="$REPO_TOP/$TMP_DIR";; esac
sha256_field() { printf '%s' "$1" | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}'; }
DIGEST="$(sha256_field "${REPO_TOP%/}")"
printf '%s' "$DIGEST" | grep -qE '^[0-9a-f]{64}$' || { echo "migration: sha256 tool missing or malformed digest" >&2; exit 1; }
shopt -s nullglob
migrated=0; restamped=0; already=0; aliased=0
for f in "${TMP_DIR%/}"/done-session/run-start-*; do
  line="$(cat "$f")"
  epoch="${line%% *}"; rest="${line#* }"; pid="${rest##* }"; mid="${rest% *}"
  if printf '%s' "$mid" | grep -qE '^[0-9a-f]{64}$'; then already=$((already + 1)); continue; fi
  if [ "$mid" = "${REPO_TOP%/}" ]; then
    new="$DIGEST"; migrated=$((migrated + 1))
  elif [ "${mid#/}" != "$mid" ]; then
    resolved="$(cd "$mid" 2>/dev/null && git rev-parse --show-toplevel)" || resolved=""
    if [ "$resolved" = "$REPO_TOP" ]; then
      new="$DIGEST"; migrated=$((migrated + 1)); aliased=$((aliased + 1))
    else
      new="$(sha256_field "${mid%/}")"; restamped=$((restamped + 1))
      echo "restamp foreign marker (console only, never copy into files under {tmp_dir}): $(basename "$f") root_sha256=$new"
    fi
  else
    echo "malformed marker (stop and report; the task returns blocked for user decision): $(basename "$f")" >&2; exit 1
  fi
  printf '%s %s %s\n' "$epoch" "$new" "$pid" > "$f.tmp" && mv "$f.tmp" "$f"
done
shopt -u nullglob
echo "migration done: migrated=$migrated aliased_own=$aliased restamped_foreign=$restamped already_digest=$already"
```

- [ ] Report the `migrated=`/`aliased_own=`/`restamped_foreign=`/`already_digest=` counts (the script's console output is safe to copy verbatim: it prints marker basenames and digests, never raw roots). `aliased_own` marks own-repo markers recorded under a path alias; the script resolved and re-stamped them with this repo's digest. A malformed-marker stop returns the task as blocked for user decision, not a skip
- [ ] Note in the task evidence: between this task and Task 2 the SKILL.md clauses still compare raw paths, so any done run in that window (including this execution session's own per-task done, which runs even when the tree is empty) writes a fresh raw-path marker; Task 2's re-migration step sweeps the disk copy. If execution is interrupted after this task, re-run this migration (it is idempotent) before any docs-branch-syncing done, and note that the raw blob that window's done already committed to docs-branch history is covered by the history residual (Ship when), not by the disk sweep

### Task 2: Rewrite the Step 0 spec/recipe and the Step 1.5/2.62 clauses in one commit

Files:
- `agents/skills/done/SKILL.md`

- [ ] Run the Validation Commands block against the current tree (bash temp-file idiom) and record the evidence: it exits at F1; separately verify by direct inspection that the F3/F6/F6b target texts are present pre-change (RED state)
- [ ] In the Step 0 marker paragraph, replace the two-sentence span (exact current text, `$REPO_TOP` is backticked in the source):

```text
The marker is content-bearing: its single line records the creation epoch, the trailing-slash-stripped resolved `$REPO_TOP`, and the writing shell PID, so gate-time identity can rely on content-match confirmation instead of chat recall alone. Field order in the marker line: the first field is the epoch, the last field is the PID, and everything between them is the repo root (repo roots containing spaces therefore parse unambiguously).
```

with exactly:

```text
The marker is content-bearing: its single line records the creation epoch, the SHA-256 hex digest of the trailing-slash-stripped resolved `$REPO_TOP`, and the writing shell PID, so gate-time identity can rely on content-match confirmation instead of chat recall alone. The raw repo-root path is never recorded. Field order in the marker line: the first field is the epoch, the last field is the PID, and everything between them is the digest (a single 64-character token, so the middle field parses unambiguously).
```

- [ ] In the Step 0 recipe block, insert a hash step with a fail-loud hex-charset guard before the `printf` and change the recorded middle field from the raw path to `$REPO_HASH`, so the block ends exactly:

```bash
REPO_HASH="$(printf '%s' "${REPO_TOP%/}" | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}')"
printf '%s' "$REPO_HASH" | grep -qE '^[0-9a-f]{64}$' || { echo "run-start marker: sha256 tool missing or malformed digest" >&2; exit 1; }
printf '%s\n' "$(date -u +%s) $REPO_HASH $$" > "$MARKER" && printf 'run-start marker: %s\n' "$MARKER"
```

- [ ] In the Step 1.5 gate paragraph, make these two exact replacements (`$REPO_TOP` is backticked in the source):

```text
BEFORE 1: (the recorded `$REPO_TOP` must equal this repo's resolved repo root)
AFTER 1:  (the recorded digest must equal the SHA-256 hex digest of this repo's resolved repo root, recomputed via the Step 0 recipe: sha256 of the trailing-slash-stripped resolved repo root, first hex field; a middle field that cannot be recomputed or does not match is a content mismatch and lands in the conservative-gating branch, never an anchor)
BEFORE 2: recorded content naming a different repository is a cross-repo done run
AFTER 2:  recorded content whose digest does not match this repo is a cross-repo done run
```

- [ ] In the Step 2.62 `done-session/` sweep bullet, make this exact replacement:

```text
BEFORE: a recorded `$REPO_TOP` matching this repo is the confirmable field
AFTER:  a recorded digest matching the SHA-256 hex digest of this repo's resolved repo root, computed as in Step 0, is the confirmable field
```

- [ ] Execute the new Step 0 recipe end-to-end against a scratch repo so no live marker is written: create a temp dir, `git init` it, write a scratch `.ai-playbook/facts.md` whose `tmp_dir` points inside the temp dir, run the recipe lines copied verbatim from the edited SKILL.md with `$REPO_TOP` pointed at the scratch repo, then verify the produced marker line matches `^[0-9]+ [0-9a-f]{64} [0-9]+$` and that the digest equals `sha256` of the scratch repo's trailing-slash-stripped root
- [ ] Re-run the Task 1 migration (it is idempotent: an already-digest middle field is counted as `already_digest` and skipped) to sweep any raw-path marker written by Task 1's per-task done or a peer done in the Task 1-to-Task 2 window
- [ ] Run → expect GREEN on the F1, F2, F2b, F2c, F3, F6, F6b, F4, F5 arms and the marker arms of the Validation Commands block (markers are all digest-format after the re-migration, so the block exits GREEN end to end: `VALIDATION OK`)
- [ ] Commit: `done: record repo-root digest instead of raw path in run-start marker content`

### Task 3: Final verification and report

Files:
- none (verification only)

- [ ] Run the full Validation Commands block once more → expect GREEN end to end (exit 0, `VALIDATION OK`)
- [ ] Run `bash -n` over the Validation Commands block and the Task 1 migration snippet; both must pass a syntax check
- [ ] Report: migrated markers keep their filenames (Step 1.5 anchoring intact), Task 1's migrated/re-stamped counts, and that the docs-branch tip refresh plus the history and vendored-copy residuals are covered by Ship when, not by this plan's tasks
