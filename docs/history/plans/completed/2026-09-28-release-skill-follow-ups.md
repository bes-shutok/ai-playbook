# Plan: Release-skill follow-ups (run-dir teardown, snapshot scope, lock relay, result-only pins, archived-plan citations)

Backlog origins:
- docs/history/backlog/2026-09-27-release-skill-code-review-deferred.md (anchor)
- docs/history/backlog/2026-09-27-release-skill-plan-stale-citations.md
- docs/history/backlog/2026-09-27-release-gate-result-only-scan.md

Driving force: code-quality + efficiency
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-release-skill-follow-ups-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Close the release-skill follow-up wave as one plan with a per-finding disposition against CURRENT bytes: the still-live defects land as fixes (authoring run dir never torn down, post-swap snapshot hash counting stray untracked files, unguarded set -e exits bypassing the authoring lock-export relay, a missing em-dash checker misdiagnosed as a policy hit, the missing selftest case for the destructive step-7 restore), the findings the landed result-only gate change already mooted are recorded as moot with evidence, the archived release-skill plan's four stale citations get their recorded successor-license edit, and the release skill's contract text gains the result-only scan semantics, the intermediate-squash-tree boundary, and the exclusion-list growth policy. After this plan lands, a release run cleans up after itself completely, a stray untracked file can no longer force a full re-release, and a locked authoring abort can no longer strand the done lock.

- Per-finding disposition table (origin finding: disposition):
  - code-review 1 (authoring run dir leftover): FIXED with the claim narrowed to the mechanism: the rewrite trap removes the dir at the rewrite's exit (the origin's own prescribed design; the groups file must survive until the rewrite consumes it, so the dir necessarily exists while the run is in flight and the report-only inventory still names it in-run), and the authoring step's own EXIT trap removes the dir on every non-zero exit of the authoring step (abort paths), so the only survivor at rest is a successful run whose rewrite has not yet exited (Task 1, Task 2, Task 3 wording).
  - code-review 2 (*.lock/gitlink hard-aborts): MOOTED, recorded: the landed result-only gate replaced the per-commit materialization loop; the result scan walks `git ls-tree -r` and skips 120000/160000 entries by design (the script's own comment), and no `.lock` literal exists in the script today (G2's pin proves it stays that way).
  - code-review 3 (snapshot hash covers untracked): FIXED (Task 2 scopes both snapshot sites to tracked changes).
  - code-review 4 (missing checker misdiagnosed): FIXED (Task 1 resolves the checker through a configurable path with an existence die arm).
  - code-review 5 (replace-mode keyed on any same-day heading): WONTFIX, recorded: the step-6 detection is live as flagged (publish membership restricts to unpushed CHANGELOG-touching commits but cannot distinguish a user-authored same-day section from release lineage without a marker convention); the replacement is recoverable via the backup ref per the origin's own note, and a marker convention is a design change out of this plan's scope.
  - code-review 6 (missing selftest case for the step-7 restore): FIXED (Task 5).
  - stale-citations 1-4 (archived plan citations and lineage): FIXED (Task 4, the recorded successor license for touching those archived bytes).
  - stale-citations addendum 5 (set -e exits bypass the lock-export relay): FIXED (Task 1).
  - stale-citations addendum 6 (release-draft tmpdir residue after abort): WONTFIX, recorded: the draft lives in TMPDIR outside every repo tree and the residue is harmless; prose churn for it is not warranted.
  - result-only boundary (intermediate squash trees unscanned): DOCUMENTED with the per-group scan arm explicitly deferred (Task 3).
  - result-only exclusion growth policy: DOCUMENTED as a deliberate-decision rule with the directory-level convention deferred until the list grows (Task 3).
  - result-only wording pin: FIXED (Task 3).

## Assumptions

- assume the snapshot scope fix is `git status --porcelain --untracked-files=no` at both the capture site and the persisted push script's re-assertion; basis: the defect is a stray untracked FILE failing the push re-assertion (origin finding 3), tracked modifications must keep failing it (the re-assertion's purpose), and `-uno` is exactly that line.
- assume the lock-export relay keeps stdout exactly-once on every path: die() and the script's success-path output each clear `lock_out` as they relay it, and a global EXIT trap relays only a still-non-empty `lock_out` (a set -e exit that never reached a relay); basis: the SCRIPT I/O CONTRACT comment pins "nothing else ever reaches stdout", so a relay that could double-print would break the calling shell's eval.
- assume the rewrite step derives the authoring run dir from the groups file's own directory (the authoring step writes the groups block inside its `release-authoring-*` temp dir and passes that path as argv), removing it in the trap only when the directory sits directly under the canonicalized temp root carrying the mktemp pattern's name; basis: the two steps are sibling processes (an export in one never reaches the other), so the file path is the only channel between them, and the pattern guard never removes an arbitrary caller-supplied directory.
- assume the archived plan file docs/history/plans/completed/2026-09-26-release-skill.md may be edited by exactly the four citation fixes because the PLAN-PROMPTS entry records this plan as that file's successor-item license; basis: the stale-citations origin's own text and the entry's orientation.
- assume mooted findings need no code change but DO need their recorded dispositions, because a future reader auditing the code-review origin against current bytes otherwise re-derives the mootness the hard way; basis: the origin's six findings predate the same-day result-only gate change that reshaped the script.

Decision points requiring a grill: snapshot scope = tracked changes only via --untracked-files=no over hashing untracked-modified entries; source: the origin's own failure witness is a stray untracked file and porcelain has no untracked-modified concept, 2026-09-28, Task 2; relay mechanism = die-clears-then-trap over trap-only relaying; source: the stdout eval-ability contract forbids a double relay, 2026-09-28, Task 1; per-group scan arm = deferred without implementation over building it now; source: no witness that an intermediate-tree blob ever leaked and the origin itself marks it optional, 2026-09-28, Task 3

## Gist & Examples

TLDR: the release tooling gets its last cleanup defects fixed (run dir torn down, snapshot ignoring stray untracked files, lock exports relayed on every exit, checker diagnosed by name), its contract text pinned to the result-only privacy scan with the documented intermediate-tree boundary, and its archived plan's stale citations repaired, while the findings the result-only gate already mooted are recorded as moot with evidence.

**Before (today).** The authoring step creates a `release-authoring-*` temp dir nobody removes, and the rewrite step's own inventory reports it as a leftover in the very same run. The post-swap snapshot hashes `git status --porcelain` including untracked paths, so an unrelated stray file appearing between the swap and the push aborts the push re-assertion and forces a full re-release. The authoring script's `set -euo pipefail` turns an unguarded `mv` or `git add` failure into a silent exit that skips die()'s lock-export relay, stranding the done lock. A missing `scripts/check-no-em-dash.sh` reports as an em-dash policy hit (exit 127 swallowed by `if !`). The selftest never exercises the step-7 whole-file rescan's destructive restore. And the archived plan still cites the dead `docs/plans/completed/` prefix, calls eight rounds the final lineage, and compresses the push design to "compare-and-swap push".

**After (this plan).** The rewrite step derives the authoring run dir from the groups file's own directory and its trap removes it, so the run leaves nothing behind. Both snapshot sites read `git status --porcelain --untracked-files=no`, so a stray untracked file no longer fails the push re-assertion while a modified tracked file still does. die() clears `lock_out` after relaying and a global EXIT trap relays whatever remains, so every post-acquisition exit path hands the lock exports to the calling shell exactly once. The checker resolves through `CHECK_NO_EM_DASH_SCRIPT` (default the repo-relative path) with an existence die arm naming the missing file. The selftest covers the step-7 restore branch, the stray-untracked push path, the run-dir teardown, the exactly-once relay on success and failure, and the missing-checker die arm whose abort also witnesses the authoring failure-exit run-dir removal. The archived plan carries `docs/history/plans/completed/`, the r1-r9 lineage, the docs-history registry scope, and the compare-and-swap-local-update-plus-verified-fast-forward-push wording. The skill's contract says the gate scans the published result, never the original commits, and documents the intermediate-squash-tree boundary with the per-group scan arm deferred.

**Edge cases.** A release run aborted inside the authoring step before lock acquisition relays nothing (the trap's guard is `lock_out` non-empty), exactly today's behavior for that path. A release run on a repo with an empty rewritten tip still dies at the existing empty-tree arm before any snapshot exists. The archived-plan edits are byte-level citation fixes whose behavioral claims were verified true by the r10 worker, so no execution-side text changes meaning.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every post-acquisition exit from the authoring step relays the lock exports exactly once; the push re-assertion ignores untracked paths and still catches tracked modifications; the run dir is removed on the rewrite trap's every path.
- consistency: the disposition table above matches the current bytes (mooted findings cite the evidence that moots them); the skill contract, its Configuration table, and the script variables agree on names.
- compatibility: the selftest suite passes with the new cases; the archived plan's behavioral claims are untouched (citation-only edits).

**Done when:**
- All six code-review findings, both stale-citation addendum items, and all three result-only items carry their dispositioned outcome in landed bytes.
- The selftest suite passes via the test venv including the five new cases.
- All Validation Commands below exit 0.

**Ship when:**
- None as a release gate; all criteria are repository-verifiable.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Tests:**
- `scripts/test_release_skill_selftest.py` *(the five new cases and any fixture adjustment they need; existing cases frozen)*

**Production code:**
- `scripts/release-authoring.sh` *(only: the EXIT-trap relay with die()'s clear, the failure-path run-dir removal with run_tmp initialized, the checker resolution and its two call sites)*
- `scripts/release-rewrite.sh` *(only: the trap's run-dir removal and the two snapshot sites)*
- `agents/skills/release/SKILL.md` *(only: the result-only wording at its three surfaces, the boundary and exclusion-policy paragraphs, the Configuration table row, the summary cleanup wording, the boundary and exclusion-policy paragraphs, the Configuration table row, the summary cleanup wording, and the stale leftovers note whose never-cleaned claim the narrowed mechanism makes false; the note is reworded to that same narrowed mechanism in the summary-edit step below)*
- `docs/history/plans/completed/2026-09-26-release-skill.md` *(only the four citation fixes of Task 4; this plan is the recorded successor-item license)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done-lock.sh` and the lock implementation; reason: the relay fix is entirely inside the authoring script's exit paths.
- The hygiene scanner and its patterns file; reason: the exclusion growth policy is documented, not implemented; the existing exclusions stay as landed (measured at 22 entries at authoring time).

## Validation Commands

Stage note: the authoring-time records this plan requires are recorded here: the pre-round structural gate ran clean before round 1 (pre-round exit 0), the RED-today executions ran against current bytes with measured outcomes (G2's new literals absent from both scripts today; G3's skill wording pins absent today; G4's corrected citations absent from the archived plan today, whose dead prefix and r1-r8 lineage are present), and the mechanical audit (pinned spans once each, bash -n over this block) ran before round 1. The venv python resolves the test venv the selftest uses. Round 4 staged zero findings and verified the r3 folds (two partial residues folded in this pass: the stale exclusion count in the Out-of-scope note, and the explicit Task 3 step plus gate pins for the never-cleaned-note rewording, the G2 pin citation, the unnumbered gate-count words, and the explicit child-env in the checker case). The reconciliation record for the r2/r3 fold-defect triggers is docs/reviews/2026-09-28-plan-review-release-skill-follow-ups-reconciliation.md. Round 2 folded seven findings (the narrowed teardown mechanism with the authoring failure-exit cleanup, the canonical-groups_file derivation, the trap-state init, the three-surface count pin, the fifth selftest case, the full TMPDIR-shape guard, and the residue fixes). Round 3 folded seven more through a systematic consistency sweep: the five-case count on every surface, the canonicalized-temp-root guard comparison, the stale run-dir-export phrases on the Review Scope and Task 1 heading, the stale never-cleaned note added to the skill's edit whitelist, the count-free growth-policy wording, the run_tmp init, the extra G3/G4 pins, and the checker-case teardown witness. Round 1 folded five findings into these bytes: the run-dir handover now derives the directory from the groups file's own path inside the rewrite step (the steps are sibling processes, so the exported-variable design could never reach it), the relay mechanism clears `lock_out` at every relaying site so the success path relays exactly once, the code-review-5 disposition row moved from MOOTED to WONTFIX-recorded (the step-6 detection is live as flagged; recovery runs through the backup ref), Task 3 enumerates all three scan-wording surfaces, and G5 guards against a vacuous merge-base on a direct-to-main run.

```bash
# G1: the release selftest suite is green including the new cases.
"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_release_skill_selftest.py -q || { echo "G1 fail: selftest red"; exit 1; }

# G2: the script fixes are present at their pinned anchors.
grep -qF "authoring_run_dir" scripts/release-rewrite.sh || { echo "G2 fail: run-dir derivation missing"; exit 1; }
test "$(grep -cF -- '--untracked-files=no' scripts/release-rewrite.sh)" -eq 2 || { echo "G2 fail: snapshot scope not at both sites"; exit 1; }
grep -qE "^trap " scripts/release-authoring.sh || { echo "G2 fail: relay trap missing"; exit 1; }
grep -qF "CHECK_NO_EM_DASH_SCRIPT" scripts/release-authoring.sh || { echo "G2 fail: checker resolution missing"; exit 1; }
test "$(grep -cF '.lock' scripts/release-rewrite.sh)" -eq 0 || { echo "G2 fail: a .lock arm reappeared"; exit 1; }

# G3: the skill contract carries the result-only pins and the new key.
grep -qF "the published result" agents/skills/release/SKILL.md || { echo "G3 fail: result-only wording missing"; exit 1; }
test "$(grep -cF 'published result' agents/skills/release/SKILL.md)" -ge 3 || { echo "G3 fail: three-surface conversion incomplete"; exit 1; }
grep -qF "intermediate squash" agents/skills/release/SKILL.md || { echo "G3 fail: boundary wording missing"; exit 1; }
grep -qF "CHECK_NO_EM_DASH_SCRIPT" agents/skills/release/SKILL.md || { echo "G3 fail: configuration row missing"; exit 1; }

# G4: the archived plan carries the corrected citations.
grep -qF "docs/history/plans/completed/2026-09-03-reviewed-plan-readiness-gate.md" docs/history/plans/completed/2026-09-26-release-skill.md || { echo "G4 fail: dead prefix remains"; exit 1; }
test "$(grep -cF 'docs/plans/completed/' docs/history/plans/completed/2026-09-26-release-skill.md)" -eq 0 || { echo "G4 fail: dead prefix still cited"; exit 1; }
grep -qF "r1-r9" docs/history/plans/completed/2026-09-26-release-skill.md || { echo "G4 fail: lineage not updated"; exit 1; }
grep -qF "compare-and-swap local ref update" docs/history/plans/completed/2026-09-26-release-skill.md || { echo "G4 fail: push wording not corrected"; exit 1; }
test "$(grep -cF 'compare-and-swap push' docs/history/plans/completed/2026-09-26-release-skill.md)" -eq 0 || { echo "G4 fail: compressed push wording remains"; exit 1; }
grep -qF "its own failure exits" agents/skills/release/SKILL.md || { echo "G3 fail: narrowed cleanup wording missing"; exit 1; }

# G5: the run introduced no em dashes anywhere (the branch-run form; a
# direct-to-main invocation makes merge-base vacuous, so guard it).
test "$(git rev-parse HEAD)" != "$(git rev-parse main)" || { echo "G5 fail: run on the authoring branch, not main directly"; exit 1; }
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)"
```

### Task 1: release-authoring.sh relay, failure-path run-dir cleanup, checker resolution

Files:
- `scripts/release-authoring.sh`

- [ ] Make every post-acquisition exit relay the lock exports exactly once: die() clears `lock_out` immediately after its existing relay printf, the script's success-path output (the final `printf '%s\n' "$lock_out"`) clears `lock_out` as it prints it, and a global `trap` on EXIT captures `$?` at its start, relays a still-non-empty `lock_out` (with `run_tmp` initialized empty at the top beside `lock_out` so the trap never trips `set -u`) through the same stdout form, and on a non-zero exit also removes the step's own run dir (`rm -rf "$run_tmp"` guarded non-empty), so `set -e` exits on unguarded commands (the step-6 `mv`, the step-7 `git add`/`git commit` path) can no longer strand the done lock nor leak the run dir, while a successful run relays exactly once and leaves the groups file in place for the rewrite step [class: IMPLEMENTATION_REQUIRED]
- [ ] Resolve the em-dash checker through a variable with an existence die arm: `checker="${CHECK_NO_EM_DASH_SCRIPT:-scripts/check-no-em-dash.sh}"` validated once with a die naming the missing path, and switch both call sites (the step-5 whole-draft scan and the step-7 whole-file scan) to `bash "$checker"` so a missing checker is diagnosed as an environment failure, never as a policy hit; add the `CHECK_NO_EM_DASH_SCRIPT` key to the header Configuration comment block beside the existing keys [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G2's authoring-side pins → expect all found [class: REPOSITORY_TEST]
- [ ] Commit: `release: relay lock exports on every authoring exit and resolve the checker` [class: IMPLEMENTATION_REQUIRED]

### Task 2: release-rewrite.sh run-dir teardown and snapshot scope

Files:
- `scripts/release-rewrite.sh`

- [ ] Derive the authoring run dir at startup from the validated and normalized groups file's directory (`authoring_run_dir="$(dirname "$groups_file")"`, initialized empty beside the other trap-state vars), and in the EXIT cleanup trap remove it only when it sits directly under the CANONICALIZED temp root with the mktemp pattern's name: `tmpdir_root="$(cd "${TMPDIR:-/tmp}" 2>/dev/null && pwd)"` then `case "$authoring_run_dir" in "$tmpdir_root"/release-authoring-*) rm -rf "$authoring_run_dir" || true ;; esac`, so a trailing-slash TMPDIR cannot desynchronize the comparison from the canonicalized dirname so the groups file's producer directory is torn down with the step's own artifacts and no caller-supplied directory outside the TMPDIR mktemp shape is ever removed; the report-only inventory of step 4 still names the in-run dir before the trap fires, which the narrowed skill wording records [class: IMPLEMENTATION_REQUIRED]
- [ ] Change both snapshot sites (the post-swap capture and the persisted push script's re-assertion) from `git status --porcelain` to `git status --porcelain --untracked-files=no` so a stray untracked file between the swap and the push can no longer fail the re-assertion while a modified tracked file still does [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G2's rewrite-side pins → expect all found [class: REPOSITORY_TEST]
- [ ] Commit: `release: tear down the authoring run dir and scope the snapshot to tracked changes` [class: IMPLEMENTATION_REQUIRED]

### Task 3: release skill contract pins

Files:
- `agents/skills/release/SKILL.md`

- [ ] Pin the result-only semantics at all three scan-wording surfaces: the outcome line (the sentence carrying `scans every published blob and message`), the phase-3 wording (the sentence carrying `runs the privacy gate over every published blob and`), and the run-report item (the line carrying `The privacy-gate outcome: every published blob and message scanned and passed`) each state the gate scans the published result (the rewritten tip tree plus the groups file, materialized after the tree-identity gate), never the original commits, so a future edit cannot silently reintroduce per-commit scanning [class: IMPLEMENTATION_REQUIRED]
- [ ] Document the intermediate-squash-tree boundary and the two deferrals in the contract's privacy-gate section: a blob present in a group-end tree but absent from the final tree publishes inside that intermediate squash commit unscanned; the optional per-group scan arm is deferred until a witness shows it matters; the exclusion list grows only by deliberate one-line-reasoned decisions, with a directory-level convention deferred until the list grows substantially beyond its size at this plan's landing (the deliberate-decision rule is the operative control, not a count threshold) [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the `CHECK_NO_EM_DASH_SCRIPT` row to the Configuration table (repo-relative em-dash checker path resolved against the primary checkout; default `scripts/check-no-em-dash.sh`), reword the stale never-cleaned leftovers note to the same narrowed mechanism, and correct the summary's cleanup item to the narrowed mechanism: the authoring step removes its run dir on its own failure exits and the rewrite step's trap removes it at the rewrite's exit; the in-run report-only inventory still names the dir while the run is in flight [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G3's pins → expect all found [class: REPOSITORY_TEST]
- [ ] Commit: `release: pin result-only scan semantics, boundary, and checker configuration in the skill` [class: IMPLEMENTATION_REQUIRED]

### Task 4: archived plan citation fixes (successor license)

Files:
- `docs/history/plans/completed/2026-09-26-release-skill.md`

- [ ] Fix the four stale citations in the archived plan bytes: the three measured PII files and the doc-registry scope sentence move from the dead `docs/plans/completed/` prefix to `docs/history/plans/completed/` and the docs-history-based scope; the lineage metadata on the review-record line and in the design-history paragraph reads r1-r9 (nine review rounds) since the r9 folds are present in the bytes; the outcome's "compare-and-swap push" wording becomes the compare-and-swap local ref update followed by the verified plain fast-forward push; no behavioral sentence changes [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G4's pins → expect all found [class: REPOSITORY_TEST]
- [ ] Commit: `release: fix archived plan citations under the recorded successor license` [class: IMPLEMENTATION_REQUIRED]

### Task 5: selftest cases for the fixed behaviors

Files:
- `scripts/test_release_skill_selftest.py`

- [ ] Add five cases mirroring the fixes: the step-7 whole-file rescan's destructive restore branch (a changelog carrying an em dash after apply restores the pre-run state and aborts); a stray untracked file appearing between the swap and the push re-assertion no longer aborts the push while a tracked modification still does; the rewrite trap removes the authoring run dir derived from the groups file's directory (and leaves a directory outside the TMPDIR mktemp shape alone); the lock exports reach stdout exactly once on BOTH a faulted post-acquisition command and a successful run (the double-relay regression guard); a missing em-dash checker (the case sets CHECK_NO_EM_DASH_SCRIPT to a nonexistent path explicitly in the child env, never relying on the ambient value the harness may strip) dies naming the environment failure instead of reporting a policy hit, and that abort also witnesses the authoring failure-exit run-dir removal (the dir is gone after the run) [class: REPOSITORY_TEST]
- [ ] Run G1 → expect the full suite green including the five new cases [class: REPOSITORY_TEST]
- [ ] Commit: `test: cover release restore branch, snapshot scope, run-dir teardown, and lock relay` [class: IMPLEMENTATION_REQUIRED]

### Task 6: final validation

- [ ] Run the full Validation Commands block from the repo root → expect every gate green; record the output in the task log [class: REPOSITORY_TEST]

## Origins dispositions
- `docs/history/backlog/2026-09-27-release-skill-code-review-deferred.md` (anchor) - folded into this plan at execution (main dac7fcc1: run-dir teardown, snapshot scope, lock-export relay, checker resolution, step-7 restore selftest; mooted and wontfix findings recorded with evidence in the plan's disposition table); origin file deleted.
- `docs/history/backlog/2026-09-27-release-skill-plan-stale-citations.md` - folded into this plan at execution (main dac7fcc1, Task 4: the four stale citations in docs/history/plans/completed/2026-09-26-release-skill.md fixed under the recorded successor-item license); origin file deleted.
- `docs/history/backlog/2026-09-27-release-gate-result-only-scan.md` - folded into this plan at execution (main dac7fcc1, Task 3: result-only semantics pinned at all three skill surfaces, intermediate-squash-tree boundary and exclusion-growth policy documented with their deferrals; result-only wording pin fixed); origin file deleted.

## Disposition of migrated backlog items
- All three origin backlog items above were deliberately folded into this plan and deleted at execution (main dac7fcc1, archive commit). The mooted code-review finding 2 and the two WONTFIX dispositions (replace-mode keyed on a same-day heading; release-draft tmpdir residue) are recorded with their evidence in the plan's disposition table rather than re-filed.
