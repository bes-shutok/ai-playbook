# Plan: Teach the Prompt-Log Stale Check the Deleted-Origin Served Class

Backlog origin: docs/history/backlog/2026-10-20-served-origin-deletion-leaves-prompt-entries-live.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-23-plan-review-prompt-log-stale-check-deleted-origin-served-r*.md
Execution budget: 2h total, largest task 1h
Classification: [class: fix-class] validator classification repair with fixtures
Authoring claim: docs/tmp/authoring-claims/2026-10-20-served-origin-deletion-leaves-prompt-entries-live.md (session zcode-automation-1f6ae856-1944)

## Terms

- **Rolling prompt log:** One of the two tracked files `docs/history/backlog/PLAN-PROMPTS.md` and `docs/history/backlog/EXEC-PROMPTS.md`, each holding ready-to-dispatch entries that list their backlog origins.
- **Origin:** A backlog row path listed under an entry's `Origins:` block.
- **Stale check:** The default mode of `scripts/check_prompt_log_origins.py`, which classifies every origin of every entry and exits 1 when an entry's origins are all served.
- **Served:** The classification for an origin whose work is complete, so it no longer keeps its entry dispatchable.
- **Live:** The classification for an origin that still carries open work, which keeps its entry dispatchable.
- **Deferred:** The classification for an origin that sits in the `deferred/` directory (an archive directory outside the served pair); it is still-actionable and never serves an entry.
- **Covered-row rule:** The repository guideline that a completing change deletes the backlog row outright instead of leaving a status stub.
- **Deletion commit:** The most recent commit reachable from HEAD that removed an origin path from the tree, found with `git log --diff-filter=D -1 --format=%H -- <path>`; because the walk is HEAD-rooted, every commit it returns is an ancestor of HEAD by construction.
- **Archive directory:** One of the served archive state directories `completed/` and `rejected/` under the backlog directory; an origin resolving into either by basename is served with the resolved path as detail. The `deferred/` directory is a further archive directory carrying the opposite, never-serves class.
- **Day-one STALE set:** The entries that read live today and exit 1 as STALE once this change lands, inventoried in validation and pruned later by the monitor sweep.
- **Monitor sweep:** The maintenance monitor's periodic stale read over the rolling prompt logs, which prunes each stale entry with a receipt.
- **STALE (verdict):** An entry whose every origin is served; the stale check exits 1 for any stale entry.
- **Landing closeout:** The end-of-run step of an authoring or execution run that runs the checker's fail-closed modes before a landing.
- **Prune receipt:** The `PLAN-PROMPTS-PRUNE:` or `EXEC-PROMPTS-PRUNE:` line a prune writes naming the removed slug and its witness.
- **Collateral discovery:** The `--collateral-served` mode of the checker, a read-only listing of entries served inside a landing's `base..HEAD` window.
- **Sibling log:** For either rolling prompt log, the other one; the checker's `--prune-audit` mode already enumerates both in one invocation.
- **Rider sentence:** The sentence in the authoring blueprint (`agents/skills/maintenance/template-authoring.md`) that tells a landing to run collateral discovery and prune what it lists.

## Why

Since the covered-row rule took effect, the normal shape of a served origin is an absent path with no archive twin, and the stale check reads exactly that shape as live. A served entry therefore stays dispatchable until a person notices, which invites a duplicate authoring or ad-hoc run.

## Gist & Examples

TLDR: The stale check classifies an origin deleted by a reachable commit as served, and collateral discovery sweeps both rolling logs, so served entries get their receipted prune instead of sitting dispatchable, for code-quality.

**Before:** The EXEC-PROMPTS entry `done-valid-document-removal-row-coverage` stayed listed as live for two days after commit `887d890b8` deleted its only origin; the default stale check exited 0 and one monitor prune sweep passed over it, while `--collateral-served --base 887d890b8~1` listed it correctly. (Historical state: that entry was hand-pruned with its receipt on 2026-10-20, so the example cannot replay at HEAD.)

**After:** Running the stale check over a log holding an entry whose every origin is a covered-row deletion prints a `SERVED:` line naming the deletion commit and a `STALE:` verdict line, so the next monitor sweep prunes it with its receipt; the plan's Task 1 fixtures demonstrate exactly this on a temporary git repository.

**Example:** An entry whose origins are one deleted row and one row still present with `Status: open` prints one `SERVED` line and one `LIVE` line and is not stale, because a mixed entry still carries unlanded work.

**Edge cases:** An origin path that never existed in history (a typo or a fabricated path) has no deletion commit and stays live, keeping the checker's protection against fabricated origins. A deletion only reachable from an unmerged branch is invisible to the HEAD-rooted lookup, so the origin stays live; this is the accepted shape of the never-existed protection and needs no reachability gate of its own. A row that resolves into the deferred archive directory keeps its deferred class even when an older copy was once deleted at the top level, and a row resolving into a served archive directory keeps the archive detail. A log checked outside a git repository, or a git plumbing failure on the lookup (nonzero exit, timeout, missing binary), yields no deletion evidence and the origin stays live. The status and archive-directory served classes are unchanged and still win before the deletion lookup runs. A deletion commit witnesses removal, not completion: a wrong-reason deletion (a conflict-resolution drop, a delete-and-re-add move into another subdirectory) is an accepted residual mitigated by the SERVED line naming the commit for audit; the arm is additionally gated on HEAD-tree absence, so a path deleted and later re-added in history, and currently only working-tree-deleted, stays live; by symmetry, a row deleted at HEAD and re-added only as an uncommitted working-tree file reads served, because HEAD is authoritative for the deletion class and the uncommitted re-add is dirt until committed.

## Outcome

The stale check and collateral discovery recognise the deletion-shaped served state the covered-row rule produces.

- A deleted origin classifies served with its deletion commit named, so the monitor survey and the landing closeout see the stale entry.
- Collateral discovery enumerates both rolling logs in one invocation, matching the prune audit, so a landing's sweep covers EXEC-PROMPTS entries too.
- A never-existed origin path still classifies live, so the fail-closed typo protection is preserved.

Gate delta: No new refusal class, hard gate, fence, protocol layer, schema field, flag, mode, or dispatch pause; collateral discovery's served predicate is unchanged (the arm lives at the check_log layer, never in the shared classifier), while its enumeration widens per Task 2 with the sibling line's log name field priced in the Assumptions. The change narrows the stale check's classification (a false live becomes served) and mechanically grows its exit-1 surface: entries that today read live exit 1 as STALE once this lands, each one taking a receipted prune through the normal monitor duty with a receipt form the prune audit accepts; the day-one STALE set is inventoried in validation, and its prunes are deferred to that standing duty rather than executed inside this change. The checker's docstring classification list gains one served line and loses the "absent file that resolves nowhere" live wording it replaces. Revert path: revert of the two task commits; the revert does not restore entries the monitor duty already pruned under the class, whose recovery goes through their prune receipts plus the day-one inventory recorded in the execution record.

## Assumptions

- assume the deletion lookup runs `git log --diff-filter=D -1 --format=%H -- <origin path>` from the repository root; the walk is HEAD-rooted, so reachability holds by construction and no separate merge-base gate is added; basis: probed on 2026-10-23 against the witnessed origin, which resolves to `887d890b8`, while a never-existed path returns nothing.
- assume the deletion arm lives at the check_log layer, consulted only after `classify_origin` returns live, leaving the shared classifier and `collateral_served`'s head-side and base-side calls unchanged; basis: `classify_origin` has a second production consumer at the collateral mode's head-side call, and anchoring the arm on the classifier would flip that mode's documented no-coverage-deletion fence.
- assume the lookup path is the backlog directory's repo-root-relative path joined with the origin's basename, passed with the :(literal) pathspec magic, and the arm is gated on HEAD-tree absence; basis: the collateral mode's own origin_rel precedent and its cat-file absence probe; a differing-directory citation fixture discriminates this derivation.
- assume any git plumbing failure on the lookup (nonzero exit, timeout, missing binary) is treated as no deletion evidence and surfaces a one-line diagnostic on standard error, never an uncaught exception; basis: the checker's existing catch precedent for subprocess failures.
- assume the stale check resolves the repository root from the log path with `git rev-parse --show-toplevel` and treats a non-repository log directory as having no deletion evidence; basis: the existing stale-check fixtures write logs into plain temporary directories, and the collateral and prune-audit modes already resolve the repository the same way.
- assume the deletion class is consulted only after the top-level presence, status, archive-directory, and deferred lookups, in that order; basis: the existing `classify_origin` precedence keeps top-level presence and the served archive pair winning over the deferred lookup, and the deferred class must keep its never-serves semantics.
- assume the sibling-log enumeration for `--collateral-served` reuses the `SIBLING_LOG_RELS` mapping the prune audit reads, attributing sibling-originated lines with a log name field while the audited log's lines keep today's exact format; basis: that mapping is the checker's single owner of the two log paths.
- assume this plan changes one script, its test file, and one clause of the rider sentence; basis: the origin row's suggested fix names exactly those surfaces and rejects a new monitor duty.
- assume the simplest viable alternative, a hand-prune doctrine with no checker change, is rejected; basis: the recurrence is every covered-row deletion naming an open entry's origin, and one monitor sweep already missed the witnessed case.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the deleted-origin served and mixed-entry fixtures are red before the change and green after it; the never-existed, status, archive-directory, and deferred fixtures pin regression and are green before and after.
- Safety: a never-existed path and a non-ancestor deletion commit both stay live, and no existing fixture changes its expected verdict.
- Consistency: `--collateral-served` and `--prune-audit` enumerate the same log pair from the same mapping.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_prompt_log_origins.py` passes with the new fixtures present.
- `python3 scripts/check_prompt_log_origins.py --selftest` exits 0.
- The temporary-git-repository fixtures from Task 1 carry the real witness for the new served class: the deleted-served fixture prints the `SERVED:` line naming the deletion commit and exits 1 with the `STALE:` verdict.
- The live probe over both rolling logs at HEAD exits 0 when the day-one STALE set is empty and exits 1 otherwise; a nonzero exit is recorded as the inventoried day-one set (never pruned inside this change, per the validation comment), and is read as a regression only when an inventoried entry's SERVED detail names a deletion commit the entry's own prune history does not explain. The missing `|| exit` on the probe line is deliberate.
- The rider sentence names both rolling logs for the collateral sweep inside its existing sentence.

**Ship when:**
- None; the repository change is the complete deliverable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid).

**Production code:**
- `scripts/check_prompt_log_origins.py`

**Tests:**
- `scripts/test_check_prompt_log_origins.py`

**Documentation:**
- `agents/skills/maintenance/template-authoring.md` (the rider sentence's collateral clause only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/PLAN-PROMPTS.md` and `docs/history/backlog/EXEC-PROMPTS.md`; reason: the prune rule text already describes deletion-shaped evidence, and log entries are pruned by the monitor and landing duties, never by this change.
- `docs/history/backlog/2026-10-22-prune-audit-landing-token-never-resolves.md`; reason: a sibling row on the same checker about the prune audit's ledger-witness token class, not the stale check.
- `docs/history/backlog/2026-10-16-collateral-mixed-fixture-composition-pin.md`; reason: a collateral-mode fixture residual owned by its own row.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-23-prompt-log-stale-check-deleted-origin-served.md
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_prompt_log_origins.py || exit
python3 scripts/check_prompt_log_origins.py --selftest || exit
python3 scripts/check_prompt_log_origins.py docs/history/backlog/PLAN-PROMPTS.md; python3 scripts/check_prompt_log_origins.py docs/history/backlog/EXEC-PROMPTS.md
# Inventory the day-one STALE set surfaced by the new class; its prunes are deferred to the normal monitor duty (record the count in the execution record, never prune inside this change).
bash scripts/check-no-em-dash.sh || exit
REPO_ROOT="$(git rev-parse --show-toplevel)" || exit
(cd "$REPO_ROOT" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh") || exit
```

### Task 1: Classify a deleted origin as served with its deletion commit

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/check_prompt_log_origins.py`
- `scripts/test_check_prompt_log_origins.py`

Primary class anchors:
- `check_log` in `scripts/check_prompt_log_origins.py`

- [x] `check_log` delivers the deleted-origin served class at its own layer: given an origin for which `classify_origin` returned live (so the top-level, status, archive-directory, and deferred lookups all missed) whose resolved backlog-relative path has a reachable deletion commit and is absent from the HEAD tree, expects the classification served with a detail naming that commit. [class: IMPLEMENTATION_REQUIRED]
- [x] Isolation: the shared `classify_origin` and `collateral_served`'s head-side and base-side calls are unchanged by the arm. [class: IMPLEMENTATION_REQUIRED]
- [x] `check_log` delivers the served line and verdict: given a log entry whose only origin is such a deleted row, expects a `SERVED:` line carrying the deletion commit, a `STALE:` verdict line, and exit 1. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given an origin path with no history in the repository, or a log checked outside any git repository, expects the classification live and an unchanged `LIVE:` line. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a git plumbing failure on the lookup (nonzero exit, timeout, missing binary), expects no deletion evidence, a one-line stderr diagnostic, and the live class; never an uncaught exception. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given an entry with one deleted origin beside one present origin with `Status: open`, expects one `SERVED:` line, one `LIVE:` line, no `STALE:` line, and exit 0. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an origin that resolves into the deferred archive directory, or one served by status or by the completed or rejected archive directories, expects each existing fixture's verdict to be unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture shape: the Task 1 fixtures live in a temporary git repository, reusing or extracting the existing committed-deletion-capable helper shape (per-commit identity plumbing, the checker subprocess invoked from the suite cwd, two commits: the origin rows, then their deletion); the deleted-served fixture cites its origin from a differing directory so only the resolved-path derivation turns it green. [class: REPOSITORY_TEST]
- [x] Run -> expect RED: add the deleted-served, never-existed, mixed, deferred-intersection (a basename parked in the deferred directory beside a top-level deletion commit, expecting DEFERRED and exit 0), archive-intersection, and git-failure fixtures, and show the deleted-served fixture failing on today's live verdict. [class: REPOSITORY_TEST]
- [x] Git-failure fixture: a scratch git repository whose PATH shim lets the repository-root resolution succeed and makes the deletion lookup exit nonzero, expecting the live class, exit 0, and a one-line stderr diagnostic with a stable prefix naming the origin path and failure class; a PATH-stripped run covers the missing-binary leg under the same expectations, and the timeout leg is covered by the same exception-handling arm rather than by a sleeping shim. [class: REPOSITORY_TEST]
- [x] Write minimal implementation: the deletion lookup at the check_log layer after the live class, memoized per resolved path within one invocation, the resolved backlog-relative path passed with git's :(literal) pathspec flag, the HEAD-tree absence gate, and the repository root resolved from the log path. [class: IMPLEMENTATION_REQUIRED]
- [x] Write minimal implementation: git-failure handling with the stable-prefix stderr diagnostic plus a one-line per-invocation stdout summary (deletion-lookup failures: N), and the docstring classification list updated in place. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: the full test file and `--selftest` pass. [class: REPOSITORY_TEST]
- [x] Commit: `fix: classify deleted prompt-log origins as served` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Sweep both rolling logs in collateral discovery and name it in the rider

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/check_prompt_log_origins.py`
- `scripts/test_check_prompt_log_origins.py`
- `agents/skills/maintenance/template-authoring.md`

Primary class anchors:
- `collateral_served` in `scripts/check_prompt_log_origins.py`

- [x] `collateral_served` delivers the sibling-log sweep: given `--collateral-served --base <ref>` over either rolling log, expects `COLLATERAL-SERVED:` lines for qualifying entries of both logs in one invocation, sibling-originated lines attributed with a log name field while the audited log's lines keep today's exact format. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a sibling log absent from the tree, expects the invocation to list the audited log alone and exit 0 rather than fail. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the rider sentence in `agents/skills/maintenance/template-authoring.md`, expects its collateral clause to say the sweep covers both rolling logs, as an edit inside the existing sentence with no new sentence, step, or flag. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED for the sibling-sweep fixture: a fixture with a served EXEC-PROMPTS entry inside the range invoked through the PLAN-PROMPTS path lists nothing for the sibling today; the sibling-absent fixture (a tree holding only the audited log) passes before and after and guards the fail-open shape with exit 0 and no sibling error. [class: REPOSITORY_TEST]
- [x] Write minimal implementation: enumerate the sibling through the existing `SIBLING_LOG_RELS` mapping, mirroring the prune audit's enumeration. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: the collateral fixtures, the full test file, `--selftest`, and the em-dash and public hygiene scans pass. [class: REPOSITORY_TEST]
- [x] Commit: `fix: sweep both prompt logs in collateral discovery` [class: IMPLEMENTATION_REQUIRED]


## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-20-served-origin-deletion-leaves-prompt-entries-live.md` (Status: covered by this plan): deleted in the landing change per the covered-row rule; the delivered stale-check served class and the collateral sibling-log sweep are this plan's Tasks 1-2, review-certified through r3 (plan-review) and r2 (code review). Residual follow-up from execution: `docs/history/backlog/2026-10-24-collateral-served-nul-origin-uncaught-valueerror.md` (NUL-bearing origin tokens still crash `--collateral-served`, pre-existing, out of this plan's scope).
