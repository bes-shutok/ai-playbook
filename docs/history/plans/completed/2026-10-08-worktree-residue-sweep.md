# Plan: worktree residue sweep (removal keyed on plans-completed membership)

Backlog origin: docs/history/backlog/2026-10-07-stale-worktree-branch-closeout-sweep.md
Driving force: automation
Plan review record: the staging series docs/history/reviews/2026-10-08-plan-review-worktree-residue-sweep-r*.md (the highest rN is the authoritative record; it binds the bytes of the fold it certifies)

Lineage: Plan 2 of the stale-worktree-closeout-sweep sequenced split (PLAN-PROMPTS entry stale-worktree-closeout-sweep). The cluster's other origin, docs/history/backlog/2026-10-05-authoring-worktree-migration-ordering-fence.md, was folded into Plan 1's landing 0035af90; the lineage survives at docs/history/plans/completed/2026-10-07-worktree-removal-migration-gate.md, whose Backlog origin line names the folded row. Plan 1 (the gate-removal pre-removal gate) landed 0035af90 and executed before this plan; this plan's removals reuse its primitive.

## Terms

- Residue: a registered git worktree of this repository (plus its checked-out branch) that outlived the landing of the plan it served, witnessed 2026-10-05 and 2026-10-07 (wt-ecc, wt-eprg, wt-rpps) and cleaned only by manual operator-directed audits.
- Plans-completed membership: the property that a plan basename exists as `docs/history/plans/completed/<basename>` in the primary checkout's HEAD tree. This is the removal key; patch-id or `git cherry` merge detection is banned (squash landings rewrite patch ids; witnessed: `git cherry` marked all ten authoring commits of the wt-rpps branch unmerged while the content sat landed in be06d88d).
- Primary checkout: the repository's main working copy (`git worktree list`'s first entry); the sweep's `--target` operand and the home of the facts-resolved reviews home the gate verifies against.
- Live-session evidence: any of a fresh execute-plan session manifest under the candidate worktree, a fresh execution or authoring claim naming the worktree or its plan, or a held done lock keyed to the candidate worktree; freshness bound is one cadence period (2 hours).
- Ad-hoc worktree shape: a registered worktree whose path sits in the same parent directory as the primary checkout and whose basename starts with the repository directory name followed by `-wt-` (for example `ai-playbook-wt-swcs`). Worktrees of other shapes (including tooling-managed trees under other roots, such as editor or agent-managed worktree directories) are out of scope and never enumerated.
- Survey: the maintenance scheduler turn's work-surface survey (agents/skills/maintenance/SKILL.md Step 1); named here because Decision point 1 rejects it as the sweep's home.
- Completed twin: the copy of the candidate's plan file at `docs/history/plans/completed/<basename>` in the target HEAD tree; the bytes of record for both membership and the gate operand.
- Authentic hold: the `--apply` precondition that the invoking run's own `DONE_LOCK_DIR`/`DONE_LOCK_TOKEN` exports match the target checkout's derived done-lock directory (the lock script's toplevel-digest form, with the lock root itself resolved through `DONE_LOCK_ROOT` exactly as the script resolves it) and its `meta.env` recorded token plus the record's `repo_root` equal to the target checkout root, the same authentic-env shape the landing helper's register row pins; directory presence alone never satisfies it, and a meta-less or mismatching directory is not-held.
- Stale registration: a worktree entry still listed by `git worktree list --porcelain` whose on-disk path is missing (git reports it prunable); it drains through a scoped administrative-dir removal gated by an enumeration-excluded non-destructive `git worktree prune --dry-run -v` and verified by the `git worktree list --porcelain` deregistration postcondition, never through `git worktree remove` or a destructive prune.
- Permanent-report class: a candidate disposition that re-reports on every run and never removes; the plan names two standing classes, the no-citations class (the gate's empty-owned-set refusal) and the cherry-pick class (Decision point 4), plus the contingent foreign-prunable deferral, which re-reports for as long as a foreign prunable registration survives.

## Why

Twice in one month an authoring or execution worktree outlived its plan's landing as a stranding cleaned only by a manual operator-directed audit (wt-ecc, wt-eprg, wt-rpps); the cluster's data-loss record is the twice-witnessed teardown series whose 2026-10-05 second witness destroyed review artifacts rebuilt only from session records (the dispatching entry's Urgency line and Plan 1's archive carry the record). The root cause has two halves: the in-session removal point read no migration gate (closed by Plan 1, the `gate-removal` subcommand of `scripts/worktree_closeout_migrate.py`, landed 0035af90), and no periodic mechanism ever revisits residue left by sessions that die before any closeout. This plan adds the second half: a mechanical sweep that removes a worktree plus its branch when, and only when, every removal precondition verifies, and reports everything it could not remove, never silently skipping.

## Outcome

Running the done skill's Step 0 in this repository drains ad-hoc worktree residue mechanically: each candidate is either removed with every precondition verified or reported with a named reason.

- A sweep can never destroy unmigrated artifacts: every removal reuses Plan 1's `gate-removal` verification over the completed twin's bytes and runs only on its `OUTCOME: pass`, no candidate without positively identified plans-completed membership is ever removed, and no branch carrying post-landing commits is ever force-deleted.
- Removals are doubly locked: `--apply` requires the invoking run's authentic hold of the target's done lock, and the sweep holds the repository merge lock across its releases so concurrent done runs serialize.
- Every skip is visible: dirty trees, unlanded plans, live sessions, stale registrations without verified membership, and permanent-report classes are named per candidate, never silently skipped.

Gate delta: one new refusal path (the `sweep` subcommand's six-arm pre-removal chain plus the authentic-hold done-lock refusal and the merge-lock refusal on `scripts/worktree_closeout_migrate.py`) and one done Step 0 recipe bullet; priced by the witnessed residue rows in the origin (wt-ecc, wt-eprg, wt-rpps strandings; the recorded 2026-10-05 teardown data loss); the paying sibling arms are Plan 1's reused `gate-removal` verification plus the new post-landing-activity arm; removals: none.

## Assumptions

- The sweep's home is the done skill's Step 0 recipe, not a nightly maintenance lane: the done run already holds the per-checkout lock discipline, runs multiple times a day across all lanes, and is the closeout family that owns worktree lifecycle; a nightly-only lane would leave residue up to 24 hours and widen the Survey (Decision point 1; rejected alternatives below).
- The sweep enumerates only the ad-hoc worktree shape defined in Terms; tooling-managed worktrees (Codex, editor) are peer-session state and never touched.
- A candidate with zero plan files at its plans root, a detached HEAD, zero or multiple dated plan files where removal requires exactly one twinned plan file, post-landing branch commits, or a stale registration without verified membership is reported, never removed; the stale registration drains under `--apply` through the scoped release of Terms after the drain chain verifies (arms 4 and 6 re-targeted to the branch's tree and target HEAD, plus arm 5's target-side witnesses; the clean-tree and local-manifest arms pass without evaluation because no on-disk tree exists to carry uncommitted state).
- `--apply` requires the invoking run's authentic hold of the target checkout's done lock, so free-running removals cannot happen outside a done run and a wrong holder or crash-leftover directory never satisfies the check.
- Plans whose header carries no review citations are a permanent-report class: the gate's empty-owned-set refusal names the skip reason and the candidate is re-reported on every run, never removed (accepted, named in Task 1).

Decision points requiring a grill: none remain: the dispatching entry's Plan 2 prompt is the confirmed design (operator-directed investigate pass with rejected alternatives recorded; Plan 1's primitive landed 0035af90 and executed, unblocking this arm); the home adjudication (done Step 0 over the nightly lane) resolves the entry's own either/or by residue latency and closeout-family ownership; basis: the origin row's remedy sentence, the sequenced split, and the witnessed residue list.

## Standing constraints

- All chat replies and committed prose in English; no em-dashes in committed files.
- Never push to origin; the hygiene scan runs before every commit.
- Every sha, path, and flag entering a precision-critical step is re-derived from disk, never quoted from context.
- The sweep never touches tooling-managed worktrees (peer-session state) and never removes without plans-completed membership plus a gate-removal pass.

## Gist & Examples

TLDR: a `sweep` subcommand on `scripts/worktree_closeout_migrate.py` plus a done Step 0 recipe arm drain landed-plan worktree residue mechanically, because sessions that die before any closeout otherwise strand worktrees until a manual audit (witnessed twice, with the recorded twice-witnessed teardown data-loss series beside them).

Example removal: `ai-playbook-wt-swcs` sits clean beside the primary, its dated plan file's basename has a completed twin in the target HEAD tree, no live-session evidence exists, the branch carries no post-landing commits, and the gate verifies the twin's owned records present: the sweep removes the worktree and its branch and prints `remove <path>`.
Example report: a candidate whose branch gained a commit after its twin landed prints `report <path>: post-landing commits on branch` and is never removed.

## Evaluation Criteria

- The unittest suite's sweep tests pass (`python3 scripts/test_worktree_closeout_migrate.py -k sweep`), covering every modeled arm, both outcome modes, the scoped stale release, and the lock checks.
- Every candidate resolution appears as exactly one verdict line using the pinned vocabulary (`remove <path>` or `report <path>: <reason>`), and every run ends with exactly one final `OUTCOME:` line from {pass, fail, tool_error}.
- Report mode never mutates: a no-`--apply` run on the live repository leaves `git worktree list` unchanged.
- `--apply` without an authentic hold exits 3 with `OUTCOME: tool_error` naming the requirement.

## Review Scope

**Explicit must-fix:** any path where a removal can destroy unmigrated artifacts, unclaimed post-landing work, or peer-session state.
**Production code:** `scripts/worktree_closeout_migrate.py` (the new sweep subcommand and its helpers).
**Tests:** `scripts/test_worktree_closeout_migrate.py` (new sweep tests); the contract surfaces `scripts/OUTCOME_CONTRACT.md` (register row) and `agents/skills/done/SKILL.md` (the Step 0 sweep arm).
**Plan-related extension:** work causally related to the sweep's surfaces is in scope for review, for example the gate-removal subcommand's own test fixtures in `scripts/test_worktree_closeout_migrate.py` and the done-lock script's acquire forms; reviewers flag unlisted-but-related paths rather than silently skipping them.
**Out of scope; reject unless plan-related:** tooling-managed worktrees under other roots (peer-session state); the PLAN-PROMPTS dispatch machinery; the plan-archival flow that populates `completed/`.

## Validation Commands

- `python3 scripts/test_worktree_closeout_migrate.py -k sweep -v` [class: IMPLEMENTATION_REQUIRED]
- `python3 scripts/worktree_closeout_migrate.py sweep --target <primary> --help` exits 0 and prints the sweep usage [class: IMPLEMENTATION_REQUIRED]
- `python3 scripts/worktree_closeout_migrate.py sweep --target <primary>` (report mode, no `--apply`) exits 0 with `OUTCOME: pass` on the live repository and prints a per-candidate verdict without removing anything [class: REPOSITORY_TEST]
- `python3 scripts/worktree_closeout_migrate.py sweep --target <primary> --apply` outside an authentic held done lock (no matching lock exports) exits 3 with `OUTCOME: tool_error` naming the lock requirement [class: IMPLEMENTATION_REQUIRED]
- `grep -c 'worktree-residue-sweep' scripts/OUTCOME_CONTRACT.md` returns at least 1 [class: IMPLEMENTATION_REQUIRED]
- `grep -c 'sweep' agents/skills/done/SKILL.md` returns at least 1 more after landing than the pre-landing baseline [class: IMPLEMENTATION_REQUIRED]

## Tasks

### Task 1: the sweep subcommand

Context surface: the plan's Terms, this task, and the Standing constraints.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`
- `scripts/OUTCOME_CONTRACT.md`

Evidence:
- `python3 scripts/test_worktree_closeout_migrate.py -k sweep -v`
- `python3 scripts/worktree_closeout_migrate.py sweep --target <primary> --help`
- the report-mode live run and the lock-refusal run from Validation Commands

- [ ] Add a `sweep` subcommand to `scripts/worktree_closeout_migrate.py` with operands `--target` (required, the primary checkout root) and `--apply` (flag, default off). When `--apply` is set, the run first verifies the invoking run's authentic hold per Terms and exits `OUTCOME: tool_error` naming the requirement before enumerating any candidate. Enumeration: `git worktree list --porcelain` in the target; keep only entries whose path differs from the target itself and match the ad-hoc worktree shape. [class: IMPLEMENTATION_REQUIRED]
- [ ] Per candidate, evaluate the gate chain in order and stop at the first failing arm, recording the reason: (1) ad-hoc shape; (2) on-disk presence: a registered entry whose path is missing on disk is a stale registration per Terms, except that a porcelain `locked` attribute on such an entry reports `locked registration` and stops the chain there, never scoped-removed while the operator's lock stands; for a stale registration the clean-tree arm (3) and the worktree-side manifest check pass without evaluation (no on-disk tree exists to carry uncommitted state or a live manifest), the branch resolves from the porcelain entry before arm 4 consumes it (a `detached` entry reports `stale detached registration` and stops the chain there), and the remaining arms re-target as: (4) membership enumerates the branch's tree with plain `git ls-tree <branch> docs/history/plans/` filtered on the `100644 blob` type column to entries matching the dated-`.md` shape at that level (the `completed/`, `deferred/`, `rejected/` subtree entries are excluded by the same filter) and requires exactly one such blob whose basename has a `HEAD:docs/history/plans/completed/<basename>` twin in the target; zero blobs reports `zero plan files on branch` and more than one reports `multiple plan files on branch`; (5) live-session evidence keeps its target-side witnesses (a fresh claim under the target's `execution-claims/` or `authoring-claims/` naming the candidate path or its plan slug, or a done-lock directory keyed to the candidate path within the freshness bound, its lock root resolved through `DONE_LOCK_ROOT` exactly as the script resolves it, each fails with the evidence named); (6) branch resolution plus post-landing activity: a detached HEAD candidate is reported, never removed, and every commit in `git -C <target> rev-list <branch> --not <target HEAD>` must carry a committer date at or before the completed twin's introduction commit (`git log --diff-filter=A --format=%ct -1 -- docs/history/plans/completed/<basename>` in the target); any newer commit fails with `post-landing commits on branch`. For an on-disk candidate, arm 3 is the clean-tree check (`git -C <worktree> status --porcelain` empty; untracked non-ignored files fail the arm) and arm 4 reads the candidate's own `docs/history/plans/` dated `.md` files (maxdepth 1, excluding the three subtrees) against the same exactly-one-twinned rule with the same named skips. [class: IMPLEMENTATION_REQUIRED]
- [ ] On arms 1 through 6 passing, run the existing gate-removal verification with the completed twin as the plan operand (read `git -C <target> cat-file blob HEAD:docs/history/plans/completed/<basename>` into a temp file under the target's facts-resolved tmp directory, removed after the gate run on every exit path, so membership and the gate key the same landed bytes; the candidate's own copy stays outside the trust boundary), target operand `--target`, worktree operand the candidate path in both kinds, and proceed only on its `OUTCOME: pass`; the gate runs before any release, stale registrations included (the gate verifies the records the branch's plans would have owned are present under the primary reviews home before the registration drains), and a stale registration ignores the gate's printed sanctioned-removal line because its release is the scoped administrative-dir removal of the removal bullet. A `fail` citing the empty owned set is the named permanent-report skip `no owned review citations`, any other `fail` or `tool_error` reports the candidate with the gate's printed evidence re-prefixed `gate: ` per line so no mid-stream `OUTCOME:` line reaches the sweep's stream, and never removes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Removal, only when `--apply` is set: first verify the invoking run's authentic hold of the target checkout's done lock per Terms and refuse with `OUTCOME: tool_error` naming the requirement when it does not hold; then hold the repository merge lock (one try-once `merge-acquire` invocation of the done-lock script before the first release, released after the last, so concurrent done runs serialize; a held or indeterminate acquire ends the run `OUTCOME: tool_error` before any removal, with the acquire's captured stderr re-prefixed `merge-lock: ` per line and its final OUTCOME line dropped so the sweep's single final line closes the run); an on-disk candidate releases through `git worktree remove --force <candidate>` followed by `git branch -D <branch>`; a stale registration releases only after a non-destructive `git worktree prune --dry-run -v` printed no prunable entry other than the candidate's own or another enumerated candidate's (the dry-run's `Removing worktrees/<id>` lines are matched against every enumerated candidate's admin-dir `gitdir` identity, so enumerated siblings drain in the same run without deferring each other; a remaining non-candidate entry defers the release with the named report `foreign prunable registration present` naming that sibling path, leaving the foreign registration in place and re-reported for as long as it survives per Terms); the release then proceeds through the scoped administrative-dir removal (locate `.git/worktrees/<id>` whose `gitdir` file names the candidate path, remove that admin dir), which is itself the deregistration, verified by the postcondition that `git worktree list --porcelain` no longer names the candidate and with no destructive prune running, then `git branch -D <branch>`; a stale registration never runs `git worktree remove`; a removal or release command failure (including a git-locked worktree refusal) reports the candidate with the command's output, enumeration continues for remaining candidates, and the run ends `OUTCOME: fail`. Without `--apply` the run is report-only. [class: IMPLEMENTATION_REQUIRED]
- [ ] Print one verdict line per candidate (`remove <path>` on removal, `report <path>: <reason>` on skip) and end with exactly one final `OUTCOME:` line per the outcome contract: `pass` when every enumerated candidate was removed or reported and no removal command failed, `fail` on any removal command failure, `tool_error` on enumeration failure, an unresolvable target, a lock that does not authentically hold under `--apply`, or usage violations remapped through the gate-removal parser override pattern. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the `sweep` register row to `scripts/OUTCOME_CONTRACT.md` (born-conformant, naming the worktree-residue-sweep plan in the born-conformant parenthetical per the gate-removal row's convention; modeled classes as above; `--help` stays a metadata exit). [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend `scripts/test_worktree_closeout_migrate.py` with sweep coverage: enumeration shape filter, each gate arm's skip reason (including the stale-registration arm in both modes and its re-targeted chain), plans-completed membership via a temporary fixture repository with a completed twin, live-session evidence skip, the post-landing-commits arm, report-only default (no removal without `--apply`), the authentic-hold refusal under `--apply` (missing, meta-less, token-mismatched, and repo_root-mismatched exports), removal on full pass for both candidate kinds (on-disk and stale registration), the scoped-release enumeration-excluded dry-run filter with the foreign-prunable deferral and the worktree-list postcondition, with a no-destructive-prune assertion on the stale-release path, and the locked-registration skip, the stale detached skip, the zero-blob and multiple-blob skip reasons, the `gate: ` evidence re-prefixing, and the final OUTCOME line vocabulary. [class: IMPLEMENTATION_REQUIRED]

### Task 2: the done Step 0 recipe arm

Context surface: the plan's Terms, this task, the Standing constraints, and the done skill's Step 0 lock matrix.

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -c 'sweep' agents/skills/done/SKILL.md` (baseline + 1 or more after the edit)
- the pins and hygiene scans over the edited file

- [ ] Add one bullet to `agents/skills/done/SKILL.md` Step 0, immediately after the per-worktree done lock acquisition item: run `python3 scripts/worktree_closeout_migrate.py sweep --target <primary checkout> --apply` from the project git root; the sweep itself requires the invoking run's authentic hold of the target's done lock and holds the repository merge lock across its releases (the same critical section the Step 2 migration uses); a done run placed outside the primary checkout never authentically holds the target's done lock, so its sweep exits tool_error before enumerating any candidate and is reported-and-continued by this bullet's fail-open tail; the sweep's verdict lines join the turn output; a `pass` or a run whose lines are all reports continues the closeout unchanged; a `fail` or `tool_error` sweep is reported in the session notes and never blocks the closeout (report-and-continue, the survey consults' fail-open posture). [class: IMPLEMENTATION_REQUIRED]

## Decision points

1. Sweep home: done Step 0 recipe (chosen) over the nightly maintenance lane (rejected: up to 24h residue latency and the survey's read-mostly posture; the done run is the closeout family's own boundary and runs multiple times daily) and over a landing-tail-only arm (rejected: the witnessed residue class is precisely sessions that never reach any closeout).
2. Removal key: plans-completed membership in the primary HEAD tree (chosen, pinned by the origin) over `git cherry`/patch-id merge detection (rejected: squash landings rewrite patch ids; witnessed false-unmerged on wt-rpps) and over branch-name slug matching (rejected: worktree and branch names do not reliably carry the plan slug).
3. Candidate scope: the ad-hoc worktree shape beside the primary checkout (chosen) over all registered worktrees (rejected: tooling-managed worktrees are peer-session state the loop never touches) and over worktree-less branches (rejected: no worktree-borne plan file to key membership from; branch-only residue keeps today's manual disposition).
4. Branch safety: the post-landing-activity arm keyed on committer dates against the twin's introduction commit (chosen) over patch-id equivalence (banned by the origin) and over refusing all branch deletions (rejected: it would leave the residue class unswept); a branch carrying a cherry-pick of the landing commit carries a newer committer date and is a permanent-report class alongside the no-citations class, fail-safe by design.

## Rejected alternatives

- Run the sweep only from the stranding session's own closeout (rejected: dead sessions never close out; the sweep must run from sessions that did).
- Remove on membership alone without the clean-tree, live-session, and post-landing arms (rejected: the post-landing closeout window has the plan already archived while the session still works; witnessed wt-rpps).
- Gate on the candidate's own plan-file bytes (rejected: the twin is the landed vintage; a stale worktree copy under-cites the owned record set).
- Release a stale registration through `git worktree remove` or an unscoped prune (rejected: the first exits non-zero on a missing path and the second sweeps foreign-root registrations; the scoped administrative-dir release touches exactly one entry).
- Default-on removal without `--apply` (rejected: a read-mode default keeps every first run observational).
- Silence skips (rejected: report-never-skip is the origin's pinned duty).
