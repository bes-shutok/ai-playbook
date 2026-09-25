# Plan: Merge/landing serialization lock + worktree closeout hardening

Backlog origins (grouping "Grouping candidates for the lock plan"): `docs/history/backlog/2026-09-20-default-branch-merge-serialization-lock.md`; `docs/history/backlog/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md`; `docs/history/backlog/2026-09-20-closeout-migration-robustness-residues.md`. Python test conventions: `projects/.ai-playbook/python_guidelines.md`. Review artifacts: `docs/reviews/2026-09-20-plan-review-merge-landing-lock-grouping-r<N>.md` (prefix reference; round count not enumerated).

## Terms

- **Merge landing lock ("merge lock")**: the new per-repository exclusive lock in `scripts/done-lock.sh` (merge-* command family) held across a child's landing critical section. Distinct from the done lock: separate lock root, session file, and env exports; a holder may hold both at once.
- **Landing critical section**: for an execution child, the final gates plus the squash commit onto the default branch plus branch deletion; for an authoring child, the copy of its changed files into the checkout that holds the default branch plus the one pathspec-scoped commit there plus the landed-bytes verification.
- **Self-landing**: an authoring child's own final step that lands its files onto the default branch from its ad-hoc worktree, without a merge.
- **Checkout that holds the default branch**: the working checkout whose checked-out branch is the repository default branch (here `main`). When no checkout holds it (primary checkout on a peer branch), the landing uses the temp-index equivalent defined in Task 2 and never switches any checkout's branch.
- **Certification digest**: the `source_digest` of a plan's latest `source_kind: "plan"` review sidecar, as consumed by `scripts/plan_readiness.py` and `scripts/docs_branch_plan_guard.py`.
- **Joint-state riding (superseded)**: the pre-worktree model where an authoring child committed on whatever branch the shared checkout held so its commits rode that branch's final squash merge. This plan supersedes it for authoring children with worktree isolation plus self-landing under the merge lock.

## Assumptions

- assume the checkout that would receive a landing may currently sit on a non-default branch (peers switch it), so the landing mechanic must work without switching any checkout's branch; basis: observed repository state 2026-09-20 (primary checkout on a peer branch while `main` advanced) and origin-1's race list (first landing commit `65a528c3` orphaned by a peer branch switch in the shared checkout).
- assume no verbatim copy of the 2026-09-20 ad-hoc blueprint edits (reverted per origin-1's state note) exists to restore; Task 2 re-authors the rewrite using the standalone dispatch form as the semantic reference; basis: origin-1 state note.
- assume the scheduler state file gains no new fields for the lock: the lock's on-disk presence via `merge-status` is the observable the guards read; basis: maintenance SKILL.md State-file scoping note (joint-state safety comes from the done-lock and claim checks; the merge lock joins that family).
- assume Python tests run as `python3 scripts/test_<name>.py` from the repository root; basis: every `scripts/test_*.py` ends in `unittest.main()` and resolves its script under test relative to `__file__`.
- assume the default branch is `main`; basis: repository HEAD and branch listing at authoring time.
- transition residual (r1 F7, accepted): payloads frozen at dispatch time before this plan lands never acquire the merge lock, so the fixed race survives one transition window bounded by the lane horizons (at most one pre-lock child per kind); a contention race observed during the first post-landing landing cycles may be that residual rather than a lock defect, which keeps the Ship-when "no contention stand-down" observation interpretable.

Decision points requiring a grill: lock mechanism (extend `scripts/done-lock.sh` with a merge-* command family over a sibling script; MERGE_LOCK_ROOT default `~/.ai-playbook/locks/merge`, repo-keyed lock dir, `.ai-playbook/merge-lock.session` fence, `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN` exports, MERGE_LOCK_STALE_SECS default 600) - recommendation accepted under standing pre-authorization, dispatch prompt 2026-09-20, affects Gist and Task 1; guard awareness form (new `G3b (landing in flight)` arm with defer-not-stand-down semantics, fresh hold defers the lane's Step 5 dispatch creation via pending_dispatch retention, stale hold is crash evidence that blocks no one) - recommendation accepted under standing pre-authorization plus origin-1 "nor stands down needlessly" wording, affects Task 3; landing mechanics when the checkout holding the default branch is on another branch (one pathspec-scoped commit there when it holds the default branch, otherwise the temp-index equivalent: temp `GIT_INDEX_FILE`, `read-tree <default>`, `update-index --add` of the task's changed paths as they exist in the authoring worktree, no bytes copied into any checkout, `write-tree`, `commit-tree -p <default>`, `update-ref refs/heads/<default>`), never switching that checkout's branch - recommendation accepted under standing pre-authorization plus origin-1 design direction (one pathspec-scoped commit, critical section stays short), affects Task 2; origin-2 smoke fixture shape (synthetic two-worktree git fixture, fixture plan and sidecar dated 2026-01-01 so only the base sidecar contract applies, bootstrap block executed verbatim as extracted from the skill text at test runtime) - recommendation accepted under standing pre-authorization plus origin-2 completion-evidence section, affects Task 5.

## Gist & Examples

Two child kinds can land commits onto the repository default branch and nothing serializes them against each other. Execution children finish with their own squash merge (gates, commit, branch deletion). Authoring children are moving to ad-hoc-worktree isolation with a self-landing: after the done skill, one commit carrying only the task's files lands on the default branch, then the branch and worktree are deleted. The done lock serializes done sweeps, not landings; `G3 (joint state)` sees an in-progress merge/rebase or a held done lock, not a landing in flight.

**Before (today):** an authoring child copies its files into the checkout that holds the default branch and commits while an execution child is mid-landing: the execution's tree-identical gate (`git diff <branch> main` empty) can fail because the authoring commit moved `main` mid-gate; index and commit interleaving can sweep a peer's staged state; branch-deletion and worktree-removal race each other. Witnessed 2026-09-20: a landing's first commit (`65a528c3`) was orphaned by a peer branch switch in the shared checkout and had to be re-landed (`4ed86ce3`). Also today, the authoring blueprint still carries the superseded joint-state riding model (commit on the shared checkout's current branch, ride the execution's squash merge), while the standalone dispatch form already carries an unserialized self-landing; the reverted 2026-09-20 blueprint edits left the corpus internally inconsistent.

**After (this plan):** both child kinds acquire the merge lock (Task 1's `merge-wait-acquire`) before their landing critical section and stand down or retry on contention (bounded wait, then keep branch and worktree and report). The execution child holds the lock across its final gates, the squash commit, and branch deletion; the authoring child's worktree run prepares and verifies everything first, so its critical section is just copy, one pathspec-scoped commit (or the temp-index equivalent when no checkout holds the default branch), and a landed-bytes check. The authoring blueprint is rewritten to the worktree self-landing form in the same pass, and `G3b (landing in flight)` makes the scheduler turn aware: a fresh hold defers only the affected lane's dispatch creation (pending_dispatch retention), a stale hold is crash evidence, and the turn never stands down wholly because of a landing.

Example (execution child): the child reaches its final paragraph, runs `bash scripts/done-lock.sh merge-wait-acquire --label execution-final-merge --max-wait 300`, gets `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN` exports, runs the PII and hygiene gates and the tree-identical gate while holding, squashes onto `main`, deletes the branch, releases with `merge-release-repo`. An authoring landing trying to interleave waits up to 300 seconds, then proceeds after the release; a third actor's `merge-status` shows the holder during the hold.

**Bootstrap (origin 2):** the Linked-worktree bootstrap recipe already landed in execute-plan Step 0.4 (commit `e35d4fa8`): a linked worktree (`.git` is a file) copies the facts file and the reviews directory from the primary checkout and creates the gitignored directories before the Step 0.5 gate. What the origin still demands is its completion evidence: a smoke check that creates a fresh worktree and runs the bootstrap plus the readiness gate to exit 0 with no out-of-skill copying. Task 5 adds that smoke check, executing the skill's own fenced block verbatim (extracted at test runtime, so drift fails the test), plus a negative control proving the recipe is load-bearing.

**Closeout residues (origin 3):** four script residues and three guard residues, each with a failing-first test: `capture` crashes with a raw traceback on a dangling symlink inside the captured dirs; the migration manifest is written only after the full copy loop so a mid-loop exception orphans already-copied verified files from the audit record; the verify-error test patches the copy seam and so bypasses production copy semantics; `check-restored --plans-dir` is accepted but unused; an unreadable plan file makes the certified-plan guard fail closed by accident (traceback instead of a named skip-and-warn); a missing dedupe script skips silently while the guard warns loud when missing; and two stale prose spots (execute-plan's "never auto-prunes" rationale, docs-branch's sync failure-semantics enumeration omitting the certified-downgrade refusal).

Design invariants carried through every task: per-execution worktree isolation stays rejected (2026-09-19 stance, restated in maintenance SKILL.md); the scheduler state schema stays additive-only with no version bump; done-lock done-mode behavior stays byte-identical (its existing selftest keeps passing unmodified); the pins suite (`scripts/check_maintenance_pins.sh`) stays green and gains needles for the new invariants; child payloads stay self-contained (repository-relative literals only, no user-facts key resolution).

## Evaluation Criteria

**Quality dimensions:**
- correctness (lock): `bash scripts/done-lock.sh selftest` passes with the new merge-mode race, fence, independence, and stale-clean fixtures; contention between a simulated execution landing and a simulated authoring landing serializes (one holder at a time).
- compatibility (lock): the pre-existing done-mode selftest fixtures pass unmodified; done and merge locks are mutually independent (holding one never blocks acquiring the other).
- correctness (closeout and guard): every origin-3 residue has a test that fails before its fix and passes after (RED records kept in the review staging notes); no behavior change outside the named residues.
- docs accuracy: probes over the edited skill files pass only when the prose matches implemented behavior (absence probe for the superseded riding sentence and the "never auto-prunes" claim; presence probes for the lock duties, the G3b arm, and the sync failure-semantics enumeration).
- maintainability: one lock machinery (no duplicated lock-lifecycle script); pins cover each new invariant with a needle whose deletion breaks the suite.

**Done when:**
- all Validation Commands exit 0 on the implemented tree;
- `python3 scripts/plan_readiness.py docs/plans/2026-09-20-merge-landing-lock-grouping.md` exits 0 on the final bytes (certification gate).

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] the next scheduler-dispatched execution child and authoring child each complete a landing under the merge lock with no contention stand-down, observed via subsequent scheduler turns' state file and `merge-status`; evidence owner: the maintenance loop's state file and the children[] outcomes; closure condition: two clean landing cycles with no landing-class `turn_error`.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done-lock.sh`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/docs_branch_plan_guard.py`
- `scripts/worktree_closeout_migrate.py`
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/execute-plan/SKILL.md` *(partial freeze: in scope only for the Linked-worktree bootstrap block (if a Task 5 delta requires it) and the exit-path throwaway-script cleanup paragraph (Task 8); every other section is frozen; reject any finding that touches them)*

**Tests:**
- `scripts/test_worktree_closeout_migrate.py`
- `scripts/test_docs_branch_plan_guard.py`
- `scripts/test_execute_plan_worktree_bootstrap.py` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; frozen validator, unless the Task 5 smoke check exposes a defect in it (then plan-related)
- `scripts/quota_window_probe.py` and the budget-guard hooks; untouched by this plan
- `.ai-playbook/scheduler-state.json` schema; no fields change (assumption above)
- `agents/hooks/**`; untouched

## Validation Commands

```bash
set -u
FAIL=0
expect_ok() { if ! "$@"; then echo "VALIDATION FAIL: $*"; FAIL=1; fi; }
expect_grep() { test -f "$2" || { echo "VALIDATION FAIL: missing $2"; FAIL=1; return; }; if ! grep -qF "$1" "$2"; then echo "VALIDATION FAIL: missing [$1] in $2"; FAIL=1; fi; }
expect_no_grep() { test -f "$2" || { echo "VALIDATION FAIL: missing $2"; FAIL=1; return; }; if grep -qF "$1" "$2"; then echo "VALIDATION FAIL: forbidden [$1] present in $2"; FAIL=1; fi; }
expect_count() { test -f "$3" || { echo "VALIDATION FAIL: missing $3"; FAIL=1; return; }; n="$(grep -oF "$1" "$3" | wc -l | tr -d ' ')"; if [ "$n" != "$2" ]; then echo "VALIDATION FAIL: [$1] count $n != $2 in $3"; FAIL=1; fi; }
flatten() { tr '\n' ' ' < "$1" | tr -s ' '; }

# 1. Lock machinery (Task 1): syntax, full selftest incl. merge-mode fixtures.
bash -n scripts/done-lock.sh || { echo "VALIDATION FAIL: done-lock.sh syntax"; FAIL=1; }
expect_ok bash scripts/done-lock.sh selftest

# 2. Blueprint duties (Tasks 2 and 4): dedicated probes per obligation.
expect_count 'merge-wait-acquire' 2 agents/skills/maintenance/prompt-templates.md
flatten agents/skills/maintenance/prompt-templates.md | grep -qF 'git worktree add -b YYYY-MM-DD-authoring-<slug>' || { echo "VALIDATION FAIL: authoring blueprint lacks worktree isolation"; FAIL=1; }
flatten agents/skills/maintenance/prompt-templates.md | grep -qF 'merge-release-repo with the acquired exports' || { echo "VALIDATION FAIL: blueprints lack lock release duty"; FAIL=1; }
flatten agents/skills/maintenance/prompt-templates.md | grep -qF 'temp-index equivalent' || { echo "VALIDATION FAIL: authoring blueprint lacks temp-index landing arm"; FAIL=1; }
# Body-scoped absence (r1 F1): the superseded riding sentence must leave the fenced blueprint
# bodies; the dated deviation-list history entry may keep quoting it, so a whole-file sweep is wrong.
python3 - <<'PYEOF'
import re, sys
text = open('agents/skills/maintenance/prompt-templates.md', encoding='utf-8').read()
fence = chr(96) * 3
bodies = re.findall(r'^' + fence + r'\n(.*?)^' + fence + r'$', text, re.S | re.M)
needle = 'final squash merge as joint-state content'
hits = [i for i, body in enumerate(bodies) if needle in body]
if hits:
    print('VALIDATION FAIL: riding sentence still in fenced blueprint body(ies) %s' % hits)
    sys.exit(1)
print('riding literal absent from blueprint bodies: ok')
PYEOF
[ $? -ne 0 ] && { echo "VALIDATION FAIL: blueprint body absence check"; FAIL=1; }

# 3. Guard awareness (Task 3).
expect_grep 'G3b (landing in flight)' agents/skills/maintenance/SKILL.md
expect_grep 'merge-status' agents/skills/maintenance/SKILL.md
expect_grep 'merge-acquire' agents/skills/maintenance/zcode.md
expect_grep 'merge landing lock' agents/skills/maintenance/SKILL.md
# 3b. Living-surface riding-model supersession (r1 F3): the rewritten living sentences carry
# distinctive literals; each appears exactly once at its site.
expect_count 'lands via its own merge-lock-serialized self-landing' 1 agents/skills/maintenance/SKILL.md
expect_count 'self-landings under the merge landing lock' 1 agents/skills/maintenance/zcode.md

# 4. Pins suite (Task 4) incl. the new needles.
expect_ok bash scripts/check_maintenance_pins.sh

# 5. Closeout residues (Task 6): executable probe with placement and teardown.
repo="$(git rev-parse --show-toplevel)"
tmp="$(mktemp -d)"
mkdir -p "$tmp/revs"
: > "$tmp/revs/real.md"
ln -s "$tmp/revs/missing-target" "$tmp/revs/dangling.md"
probe_out="$(cd "$tmp" && python3 "$repo/scripts/worktree_closeout_migrate.py" capture --out base.json --dirs revs 2>&1)"; probe_rc=$?
if [ "$probe_rc" -ne 0 ]; then echo "VALIDATION FAIL: capture rc $probe_rc on dangling symlink"; FAIL=1; fi
case "$probe_out" in *'dangling symlink'*) ;; *) echo "VALIDATION FAIL: capture did not name the dangling symlink"; FAIL=1;; esac
grep -qF '"revs/real.md"' "$tmp/base.json" || { echo "VALIDATION FAIL: capture dropped the regular file"; FAIL=1; }
rm -rf "$tmp"

# 6. Guard residues (Task 7): exactly one --plans-dir (the guard subcommand), named skip literal.
expect_count '"--plans-dir"' 1 scripts/docs_branch_plan_guard.py
expect_grep 'unreadable plan file' scripts/docs_branch_plan_guard.py
expect_grep 'backlog duplicate-sweep script not found' agents/skills/docs-branch/SKILL.md

# 7. Python suites (Tasks 5, 6, 7).
expect_ok python3 scripts/test_worktree_closeout_migrate.py
expect_ok python3 scripts/test_docs_branch_plan_guard.py
expect_ok python3 scripts/test_execute_plan_worktree_bootstrap.py

# 8. Stale prose (Task 8).
expect_no_grep 'never auto-prunes' agents/skills/execute-plan/SKILL.md
expect_grep 'Failure semantics (sync):' agents/skills/docs-branch/SKILL.md
expect_grep 'certified-downgrade refusal (exit 1, before staging)' agents/skills/docs-branch/SKILL.md

# 9. Scans over the touched set.
expect_ok bash scripts/check-no-em-dash.sh touched
expect_ok bash scripts/scan-public-hygiene.sh

if [ "$FAIL" -ne 0 ]; then echo "VALIDATION: FAILED"; exit 1; fi
echo "VALIDATION: all green"
```

Authoring-time probe record (rules 19 and 337; refreshed in the review staging notes each round): probes 2 (both fragments), 5, 6-count, and 8 must be RED on today's tree and were executed at authoring time with observed failures recorded in `docs/tmp/plan-requirements-merge-landing-lock-grouping.md`; each flips GREEN exactly when its task lands.

### Task 1: Merge-lock command family in done-lock.sh

Files:
- `scripts/done-lock.sh`

- [x] `Selftest#merge_acquire_creates_lock_and_exports`; given a temp `MERGE_LOCK_ROOT` and a repo fixture, `merge-acquire` expects exit 0, a lock dir under the merge root keyed by the repo hash, `.ai-playbook/merge-lock.session` in the repo, and `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN` exports on stdout [class: REPOSITORY_TEST]
- [x] `Selftest#merge_second_acquire_held`; given an existing merge lock held by another holder token, a second `merge-acquire` expects exit 2 and leaves the first holder's lock intact [class: REPOSITORY_TEST]
- [x] `Selftest#merge_release_token_fenced`; given exports from `merge-acquire`, `merge-release` with a wrong token expects refusal and the lock surviving, and with the right token expects removal; `merge-release-repo` refuses when env is missing [class: REPOSITORY_TEST]
- [x] `Selftest#merge_and_done_locks_independent`; given a held merge lock, `acquire` (done mode) expects success, and given a held done lock, `merge-acquire` expects success [class: REPOSITORY_TEST]
- [x] `Selftest#merge_status_and_stale_clean`; given a held merge lock, `merge-status` expects the holder label; given a lock aged past `MERGE_LOCK_STALE_SECS` (override to a tiny value in the fixture), `merge-stale-clean` expects removal and `merge-status` expects free [class: REPOSITORY_TEST]
- [x] Run → expect RED: `bash scripts/done-lock.sh selftest` (merge fixtures fail: unknown command) [class: REPOSITORY_TEST]
- [x] Implement the merge mode by parameterizing the existing lock core (mode selects root env var, session-file name, export names; defaults per the Terms and Assumptions section: `MERGE_LOCK_ROOT` `~/.ai-playbook/locks/merge`, `.ai-playbook/merge-lock.session`, `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN`, `MERGE_LOCK_STALE_SECS` 600, `MERGE_LOCK_POLL_SECS` 30, dead-holder grace and incomplete thresholds mirroring the done defaults); commands: `merge-acquire`, `merge-wait-acquire`, `merge-release`, `merge-release-repo`, `merge-status`, `merge-stale-clean`; document them in the usage block; done-mode behavior and output stay byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/done-lock.sh selftest` (all fixtures, done and merge) [class: REPOSITORY_TEST]
- [x] Commit: `scripts: done-lock merge landing lock mode (serialized landings, independent of the done lock)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Child payloads acquire the lock (prompt-templates.md)

Files:
- `agents/skills/maintenance/prompt-templates.md`

- [x] Execution blueprint, final merge paragraph: insert the lock duty so the paragraph reads: acquire the merge landing lock first (`bash scripts/done-lock.sh merge-wait-acquire --label execution-final-merge --max-wait 300`; on timeout stand down keeping the branch and report), hold `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN` across the PII check + hygiene scan (exit 0 required, else release via `merge-release-repo with the acquired exports` and abort), the tree-identical gate and the gmail-author check, the squash commit onto main, and branch deletion; release after the branch is deleted; keep the existing worktree review-migration sentence and its position (after deletion, before worktree removal); keep "Finally squash merge to main" as the paragraph opener and the SUCCESSOR DISPATCH ordering intact (pins); the rewrite must not drop any existing gate of the paragraph (PII, hygiene, tree-identical, gmail-author) [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring blueprint: replace the joint-state riding sentences ("The current branch does not matter ... ride that branch's final squash merge as joint-state content." and the end-of-run stranding note) with the worktree self-landing form: run in an ad-hoc worktree created before any plan work (`git worktree add -b YYYY-MM-DD-authoring-<slug> <sibling-path> <default-branch>`, run's current date; copy the primary checkout's gitignored `.ai-playbook/facts.md` in first; decline the plans skill's Phase 0 branch creation; if creation fails, stand down without writing anything); after the done skill, acquire the merge lock (`merge-wait-acquire --label authoring-self-landing --max-wait 300`; on timeout keep the worktree and branch and report), copy exactly this task's changed files into the checkout that holds the default branch, make one pathspec-scoped commit there carrying only those files and never switching that checkout's branch (plain `git commit -- <paths>` when that checkout holds the default branch; otherwise the temp-index equivalent, in which NO bytes are copied into any checkout: the index operations run in the authoring worktree against its own paths (temp `GIT_INDEX_FILE` seeded by `read-tree <default>` there, `update-index --add` of the task's changed paths as they exist in the authoring worktree, `write-tree`, `commit-tree -p <default>`, `update-ref refs/heads/<default>`; r2 F3), verify the landed plan's sha256 matches the final review digest and release via `merge-release-repo with the acquired exports`, then delete the authoring branch and worktree; on any verification failure keep both and report the stranding [class: IMPLEMENTATION_REQUIRED]
- [x] Register both changes in the deviation list with dated entries (2026-09-20): the worktree self-landing rewrite (noting it re-lands the reverted ad-hoc edits in locked form and supersedes the joint-state riding model for authoring children) and the merge-lock landing duty for both payloads; note in each entry that the literals live in this file and the pins suite, per the file's registration discipline; each new entry PARAPHRASES the command literal `merge-wait-acquire` instead of quoting it (the successor-chaining entry's paraphrase precedent), so the exactly-2 count pin holds (r2 overflow) [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep the authoring blueprint for residual riding-model wording (grep noun phrase `joint-state` and `ride`): every hit that describes the authoring child's commit placement is rewritten to the self-landing form; the deviation-list historical entries that document the superseded model stay (they are history, clearly dated) [class: IMPLEMENTATION_REQUIRED]
- [x] No commit this task (Tasks 2, 3, 4 land as the one-pass commit in Task 4) [class: IMPLEMENTATION_REQUIRED]

### Task 3: Guards aware of the lock (SKILL.md + overlay)

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`

- [x] SKILL.md Step 2: add `G3b (landing in flight)` evaluated after `G3 (joint state)`: trips when the merge landing lock is held (observable: `bash scripts/done-lock.sh merge-status` reporting a holder); unlike `G3` it never stands the turn down: survey, guards, decisions, and the state write still run; its effect is confined to Step 5's final-slot precondition: when the hold is fresh (younger than `MERGE_LOCK_STALE_SECS`, default 600 seconds), the affected lane's dispatch creation defers with `pending_dispatch` retained per the existing Step 1 reader semantics and the reason `merge-lock-held` recorded in `decision_reason`; when the hold is at or past the stale threshold it is crash evidence: record `turn_error: merge-lock-stale`, name `merge-stale-clean` as the operator escape, and proceed with scheduling (a stale lock blocks no one); state the failure-cap interaction explicitly (r1 overflow): a persistently stale lock records `turn_error: merge-lock-stale` every turn, so three consecutive stale turns trip `G2` and stand the loop down with an alert until a human runs `merge-stale-clean` and clears the alert, which is intended crash-evidence behavior, not indefinite loop continuity [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md and zcode.md: rewrite the three living sentences that still teach the superseded riding model (r1 F3): SKILL.md's `G1a` bullet (the "its plan-document commits may land on whatever branch the shared checkout currently holds ... ride that execution's final squash merge as joint-state content" sentence) becomes the self-landing form containing the distinctive literal `lands via its own merge-lock-serialized self-landing`; SKILL.md's Step 3 tail ("There is no checkout-branch precondition for D2 ... ride that branch's final merge as joint-state content") is rewritten to the same model; zcode.md's lane-independence parenthetical in the "Child classification markers" bullet ("authoring children may run alongside an execution and commit on whatever branch the shared checkout holds") is extended with `self-landings under the merge landing lock`; dated Revisions and deviation-list history entries stay as history untouched [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Execution-lane concurrency stance: append one sentence stating that landing critical sections on the default branch are serialized by the merge landing lock as of 2026-09-20 (the accepted overlap shapes now include mutually exclusive landing critical sections) [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Invariants: add the bullet that landing critical sections are mutually exclusive under the merge lock and both child kinds stand down or retry on contention [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Revisions ledger: add the 2026-09-20 entry naming the merge-landing lock group (lock family, `G3b`, blueprint self-landing rewrite re-landing the reverted worktree-isolation edits in locked form, pins extension) [class: IMPLEMENTATION_REQUIRED]
- [x] Overlay `zcode.md`: add the merge landing lock to "Scheduling primitives" (command shapes `merge-acquire`/`merge-wait-acquire`/`merge-release-repo`/`merge-status`/`merge-stale-clean`, the `MERGE_LOCK_*` env exports, stale threshold 600 seconds, contention behavior: bounded wait then stand down keeping branch and worktree) and one line placed inside the lane-independence parenthetical of the "Child classification markers" bullet (the concrete anchor; zcode.md carries no G3 text of its own, r1 F6) stating that a held merge lock is a `G3b` defer condition, never a whole-turn stand-down [class: IMPLEMENTATION_REQUIRED]
- [x] No commit this task (one-pass commit in Task 4) [class: IMPLEMENTATION_REQUIRED]

### Task 4: Pins suite extension and the one-pass commit

Files:
- `scripts/check_maintenance_pins.sh`

- [x] Add needles in the suite's existing style: `merge-wait-acquire` appears exactly 2 times in prompt-templates.md (once per blueprint); the authoring blueprint contains the worktree-add fragment; SKILL.md contains `G3b (landing in flight)`; the overlay contains `merge-acquire`; the superseded riding sentence (`final squash merge as joint-state content`) is absent from the blueprint bodies via a body-scoped absence check in the suite's python block (the region-check style already used for the checkbox-regex pin, r2 F7; not the whole-file `expect_absent` helper, so the dated deviation-list history entry stays legal) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` (all pre-existing pins plus the new needles) [class: REPOSITORY_TEST]
- [x] Commit (the one-pass commit carrying Tasks 2, 3, and 4): `skills+scripts: merge-landing serialization lock across maintenance blueprints, G3b guard arm, overlay, pins` [class: IMPLEMENTATION_REQUIRED]

### Task 5: execute-plan worktree bootstrap smoke check (origin 2)

Files:
- `scripts/test_execute_plan_worktree_bootstrap.py` *(new)*

- [x] `WorktreeBootstrapTest#test_recipe_block_executes_verbatim_and_gate_exits_zero`; given a synthetic primary repo fixture (mktemp -d; git init with user config; initial commit carrying `.ai-playbook/facts.md` with the TOML keys, a minimal readiness-valid fixture plan `docs/plans/2026-01-01-fixture-plan.md` with title, Assumptions ending in the literal none-remain trailer, Gist & Examples, Evaluation Criteria, Review Scope, and Validation Commands sections, `.gitignore` covering the gitignored paths, and `docs/reviews/2026-01-01-plan-review-fixture-plan-r1.md` plus its `.stats.json` built as a COMPLETE version-1 sidecar (r2 F2: `plan_readiness.py` runs the full shared staging gate on the latest round and its required top-level fields are not date-fenced, so the `clean_sidecar` 4-field shape fails with 13 missing fields; the 2026-01-01 date exempts only the freshness, coverage, and record-kind fences): every required top-level field present - schema_version, source_kind `"plan"` (the `clean_sidecar` base carries `"code"`, rejected unconditionally, r1 F5), review_type, date `2026-01-01`, artifact_slug `fixture-plan`, round `r1`, panel_mode `"focused"` plus selection_reason (a `full` record demands all five worker rows), source_digest set to the fixture plan's sha256, escalation_reason, verdict `ready=yes`, zero-blocking counts, an empty `findings` array (gate-required; r3 F1), panel rows, deduplication_groups, discarded, severity_calibration, triage_outcomes, overflow, soften_watchlist, and the freshness fields - with a hierarchy-conformant fixture markdown (Metadata, Review Statistics with Panel/Counts/Deduplication/Discarded/Calibration/Triage, the four severity groups, and a Summary verdict line); a minimal pair of exactly this shape was validated clean through the shared gate during review) and a linked worktree of it (`git worktree add "$tmp/wt" -b run-branch`), when the test extracts the FIRST fenced bash block after the "Linked-worktree bootstrap" lead-in (the bootstrap recipe itself; a second fenced block, the closeout-baseline capture, follows in the same region and must not be picked, r1 F8) from `agents/skills/execute-plan/SKILL.md` at runtime and executes it verbatim in the worktree, then expects: `.ai-playbook/facts.md` present, the reviews sidecar pair present, `docs/tmp` present, and `PLAN_READINESS_VALIDATOR` pointing at the real repo's `scripts/plan_readiness.py` run from the worktree on the fixture plan exits 0; placement in mktemp -d with `rm -rf "$tmp"` teardown [class: REPOSITORY_TEST]
- [x] `WorktreeBootstrapTest#test_gate_fails_without_bootstrap`; given the same fixture without running the recipe, the readiness validator from the worktree expects non-zero exit with an environment failure (facts or reviews missing), proving the recipe is load-bearing [class: REPOSITORY_TEST]
- [x] Run → expect GREEN if the recipe and fixture already agree (r2 F4: today's block may already satisfy all four expected outcomes against a correctly built fixture, so no RED is forced here; when a check fails, record the failing outcome and fix it in its owner: the recipe, the fixture spec, or the skill text); `test_gate_fails_without_bootstrap` is the discriminating assertion that proves the recipe is load-bearing and passes at write time by design - it is a guard, not a fix-first RED [class: REPOSITORY_TEST]
- [x] Fix any delta the smoke exposes in the skill's bootstrap block or the fixture (for example the block's directory literals versus the facts TOML resolution sentence); keep the fix minimal and inside the frozen-scope carve-out for the bootstrap block [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_worktree_bootstrap.py` [class: REPOSITORY_TEST]
- [x] Commit: `scripts: execute-plan worktree bootstrap smoke check (origin completion evidence)` [class: IMPLEMENTATION_REQUIRED]

### Task 6: worktree_closeout_migrate.py robustness residues (origin 3, script)

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

- [x] In `scripts/test_worktree_closeout_migrate.py`'s existing `WorktreeCloseoutTest` class (r2 F7), add `WorktreeCloseoutTest#test_capture_warns_and_skips_dangling_symlink`; given a captured dir holding a regular file and a dangling symlink, `capture` expects exit 0, a stderr warning naming the dangling symlink, the regular file recorded in the baseline, and the dangling symlink recorded under a skipped list rather than crashing [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_migrate_skips_dangling_symlink_in_source`; given a source tree holding a dangling symlink among files to migrate, `migrate` expects no traceback, a manifest skip entry naming the dangling symlink with its reason, and the remaining files migrated normally [class: REPOSITORY_TEST]
- [x] `WorktreeCloseoutTest#test_unreadable_regular_file_still_fails_the_run`; given a source tree whose hash seam is patched to raise `PermissionError` on a regular file (monkeypatch `_sha256` on the loaded module, invoke `capture`/`migrate` in-process via `MODULE.main`; r2 F5: seam patching, never chmod, so runner identity cannot flip the fixture), neither command takes a dangling-symlink skip: the error propagates loudly (non-zero exit, no misleading skip entry), proving the containment is scoped to the dangling-symlink predicate (path is a symlink whose target is missing) and not to every OSError (r1 F4) [class: REPOSITORY_TEST]
- [x] Run → expect RED with per-test precision (r2 F4): `test_capture_warns_and_skips_dangling_symlink` fails today on the raw traceback; `test_migrate_skips_dangling_symlink_in_source` fails today on a manifest mismatch (today's code migrates the link instead of skipping it, no traceback); `test_unreadable_regular_file_still_fails_the_run` is a must-stay-GREEN regression guard (propagation is today's behavior; it pins the containment scope against a whole-OSError implementation) [class: REPOSITORY_TEST]
- [x] Implement named skip-and-warn for dangling symlinks on both the capture and migrate walks: the skip predicate is exactly the dangling-symlink shape (the walked path is a symlink and its target does not exist); every other OSError propagates loudly and unchanged; the warn line is `WARN: skipping dangling symlink: <path>`, the skip is recorded, and exit status behavior is otherwise unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] `WorktreeCloseoutTest#test_migrate_manifest_survives_midloop_exception`; given two files to migrate where the copy seam raises after the first verified copy, `migrate` expects non-zero exit and a manifest that already contains the first file's migrated entry plus an incomplete marker naming the failure, so no copied file is orphaned from the audit record [class: REPOSITORY_TEST]
- [x] Run → expect RED (manifest written only after the loop today) [class: REPOSITORY_TEST]
- [x] Implement manifest durability: accumulate the four sections in memory and write the manifest in a finally block; on a mid-loop exception append an `incomplete` marker entry naming the error before propagating the failure; the normal-path manifest shape is unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite `test_migrate_fails_without_moving_on_verify_error` to tamper the verify seam (patch `_verify_copy` to return False) with the copy path unpatched, and assert the exit code, the failed manifest entry, and that every source file still exists (copy-never-move asserted against real copy semantics) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/test_worktree_closeout_migrate.py` (full suite) [class: REPOSITORY_TEST]
- [x] Commit: `scripts: worktree closeout capture/migrate robustness (dangling symlinks, manifest durability, verify-seam test)` [class: IMPLEMENTATION_REQUIRED]

### Task 7: docs_branch_plan_guard.py residues (origin 3, guard)

Files:
- `scripts/docs_branch_plan_guard.py`
- `scripts/test_docs_branch_plan_guard.py`
- `agents/skills/docs-branch/SKILL.md`

- [x] In `scripts/test_docs_branch_plan_guard.py`'s existing `CertifiedPlanGuardTest` class (r2 F7), add `CertifiedPlanGuardTest#test_check_restored_rejects_plans_dir_flag`; given `check-restored --plans-dir <path> --reviews-dir <path> <file>`, `build_parser().parse_args` expects SystemExit (the unused argument is removed); update the existing check-restored test cases that still pass it [class: REPOSITORY_TEST]
- [x] `CertifiedPlanGuardTest#test_guard_warns_and_skips_unreadable_plan`; given a shared plan name whose bytes cannot be read (monkeypatch `sha256_file` to raise OSError), `guard` expects exit 0, a stderr line naming `unreadable plan file` with the path, and no refusal, so an unreadable file degrades to skip-and-warn instead of an accidental fail-closed traceback; same containment for `check-restored` [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_docs_branch_plan_guard.py` (both new tests fail today) [class: REPOSITORY_TEST]
- [x] Implement: remove `--plans-dir` from the check-restored subparser (the guard subcommand keeps its); wrap the per-file digest reads in `cmd_guard` and `cmd_check_restored` with OSError containment printing `WARN: unreadable plan file: <path>; sync proceeds without the digest check for it` and continuing [class: IMPLEMENTATION_REQUIRED]
- [x] docs-branch SKILL.md: drop `--plans-dir "$_plans_dir_ord"` from the check-restored invocation (the caller passes an argument the implementation never read) and add the missing-script warn parity to the dedupe block: when `$DEDUPE_SCRIPT` is absent, print `WARN: backlog duplicate-sweep script not found; sync proceeds without dedupe` to stderr (mirroring the certified-plan guard's missing-script warn) instead of skipping silently [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_docs_branch_plan_guard.py` [class: REPOSITORY_TEST]
- [x] Commit: `scripts+skills: docs-branch plan-guard residues (unused flag, unreadable-file skip, dedupe warn parity)` [class: IMPLEMENTATION_REQUIRED]

### Task 8: stale prose (origin 3, docs)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`

- [x] execute-plan SKILL.md exit-path throwaway-script cleanup paragraph: reword the stale rationale sentence (the one claiming docs-branch never auto-prunes) to current behavior: docs-branch is add-only outside `{tmp_dir}`, and its single sweep exception only drops a `{tmp_dir}` branch copy after the file is gone from disk, so throwaway scripts riding the `.md` logs still land on the docs branch and persist in its history until a later sweep, which is why the terminal-exit audit remains required; keep the rest of the paragraph intact [class: IMPLEMENTATION_REQUIRED]
- [x] docs-branch SKILL.md: add a sync failure-semantics enumeration paragraph immediately after the sync block's closing fence (the block whose tail carries the status-propagation comment), as a Markdown paragraph outside the executed fence (r2 F6), opening with the literal `Failure semantics (sync):` and enumerating: exit 1 abort paths (the hygiene gate and the certified-downgrade refusal (exit 1, before staging)), warn-and-continue paths (the guard script missing, the dedupe script missing or the sweep failing, the restored-plan witness warnings), each loud on stderr and consistent with the Certified-plan ordering Rules bullet; the existing witness-append Failure semantics line is scoped to Step 3 and stays as is [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skills: docs-branch sync failure semantics and execute-plan prune-prose accuracy` [class: IMPLEMENTATION_REQUIRED]

### Task 9: final validation sweep

Files: none (verification only)

- [x] Run the whole Validation Commands block from the repository root; expect exit 0 and the trailing `VALIDATION: all green` line; record any failure and fix in its owning task before re-running [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/plan_readiness.py docs/plans/2026-09-20-merge-landing-lock-grouping.md` after the final review digest binds; expect exit 0 (certification gate, re-run by the orchestrator after every fold) [class: REPOSITORY_TEST]

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-20-merge-lock-guard-wiring-residuals.md: disposition folded into 2026-09-20-merge-landing-lock-grouping.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-20-default-branch-merge-serialization-lock.md: disposition folded into 2026-09-20-merge-landing-lock-grouping.md (2026-09-25); per-item file deleted.
