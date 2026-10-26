# Plan: Bind prompt-log commits to the intended branch ref

Backlog origin: `docs/history/backlog/2026-10-25-primary-log-branch-drift-at-commit.md`
Driving force: reliability + simplicity
Plan review record: the staging series `.ai-playbook/reviews/YYYY-MM-DD-plan-review-primary-log-branch-drift-at-commit-p870a6b6d-r*.md` (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 4.0h total, largest task 2.0h
Authoring claim: `docs/tmp/authoring-claims/2026-10-25-primary-log-branch-drift-at-commit.md` (session `01a1638f-189d-7b02-9cf8-0990eb6f3dfd`)

## Terms

- **Rolling prompt log:** either `docs/history/backlog/PLAN-PROMPTS.md` or `docs/history/backlog/EXEC-PROMPTS.md`.
- **Intended ref:** the branch selected by the existing caller rule after lock acquisition and before the final log read or edit; the writer carries its symbolic ref and starting OID through commit.
- **Ref-bound commit:** a commit whose captured symbolic `HEAD` and starting OID match the caller-selected ref and OID, then advances that captured ref through the existing compare-and-swap.
- **Owned log paths:** the exact rolling-log paths declared by the write operation before staging.
- **Primary-checkout log write:** a rolling-log commit made from the primary checkout under the primary done-lock boundary; it does not acquire the repo-wide merge lock.
- **Worktree log commit:** a rolling-log commit made on the worktree branch under the existing merge-lock guard.
- **Captured-tree landing:** the existing `done_run.sh` path that captures the staged tree and symbolic `HEAD`, then compare-and-swaps that captured branch ref.
- **Primary `land`:** the `land_squash.sh land` mode that mutates the primary index, worktree, and branch ref. It acquires the done lock before the merge lock, holds both through snapshot, landing, and recovery, then releases merge before done.
- **Ref-only `land-worktree`:** the `land_squash.sh land-worktree` mode that composes through a temporary index under the merge lock only, leaves the primary index and worktree untouched, and advances the primary ref with captured-OID CAS.

## Why

A prompt-log prune was prepared while the primary done and merge locks were held. Another session switched the shared checkout to a peer branch before a plain commit, so the commit landed on that peer branch. The change was recovered, but the lock contract does not pin the checkout's symbolic branch. The repository already uses a captured-tree compare-and-swap transaction for primary-checkout commits; the rolling-log path should preserve the caller-selected ref through that existing owner.

## Gist & Examples

Title: Bind prompt-log commits to the intended branch ref
TLDR: Check the caller-selected branch before changing the log, then bind the commit to it so a checkout switch cannot redirect the log write.
Before: A checkout branch switch between log preparation and commit can redirect a plain commit to a peer branch.
After: A prompt-log write changes the log only after its selected ref matches primary HEAD, then updates only that ref or takes recovery without changing another branch or worktree files.
Edge cases: Capture the intended ref and OID under the primary done lock before the final log read or edit; recover on mismatch before changing the log, then recheck before staging and CAS. Landing modes follow their Terms; worktree log commits use the merge lock only.

## Outcome

Use the existing captured-tree transaction for primary rolling-log commits. Each primary caller acquires or reuses the primary done lock before selecting the intended symbolic ref and starting OID and before the final log read or edit, then holds it through staging, CAS, and failure recovery. The caller verifies the selected pair matches primary `HEAD`; on mismatch, use existing recovery before changing a log or staging. The caller passes the pair to `done_run.sh`, which rechecks it before staging and through captured-tree CAS. Capture the tree only while the same symbolic `HEAD` and OID still match, then use the existing captured-HEAD compare-and-swap. Primary log writers do not acquire the repo-wide merge lock. The canonical Worktree-first contract in `agents/skills/execute-plan/SKILL.md` owns primary-checkout mutation serialization. Landing-mode lock ownership follows the `Primary land` and `Ref-only land-worktree` Terms. If ref-only `land-worktree` advances primary `HEAD` after a log writer selects ref/OID but before CAS, the writer refuses, cleans only its owned staged delta, preserves the landing and unrelated state, then reselects before retry. Worktree log commits remain merge-lock-only. Prove a primary log write completes while the worktree merge lock remains held, and prove primary `land` cannot snapshot or restore over a staged log delta. A worktree-placement freeze whose default target is not primary `HEAD` uses recovery naming the exact checkout alignment required; it stands down before plan-file work and resumes only after primary `HEAD` is moved to the default branch. Keep the transaction limited to declared owned log paths. Add the pre-registered machinery row and its sunset commitment; add no lock, validator, holder scan, temp-index route, or second transaction recipe.

Gate delta: add one blocking selected-ref mismatch refusal, backed by the true 2026-10-25 wrong-branch commit recorded in the backlog origin. Retire the existing repo-wide merge-lock acquisition refusal for primary log writers in the same change; keep those writes and primary `land` under the existing primary done lock, with `land` also taking merge second. Keep worktree `land-worktree` and worktree log commits under the merge lock only. The runner centralizes the existing pre-staged-owned-path refusal for both rolling-log paths, retiring only caller-specific duplicates. Keep the captured-tree staged-scope and capture-window fences that reject paths outside the declared owned set, including foreign paths staged after the early check. Expected catches are rare branch switches during a primary log write; a false-positive mismatch costs one recovery/reselection and leaves the log and refs unchanged. Review by 2027-01-25; if no additional true catch occurs by then, demote the mismatch refusal to warning-only and remove its registry entry in that reviewed change.

## Assumptions

- Each caller’s existing placement rule selects the intended branch after lock acquisition and before the final log read or edit; later symbolic-HEAD reads may only verify that selection, never replace it. For example, a primary-placement plans freeze uses its current branch while a worktree-placement freeze selects the default branch.
- The current plain log commit and `done_run` captured-tree commit path are distinct; rolling-log callers pass the selected ref and starting OID as preconditions, while ordinary commits keep their existing `HEAD` behavior.
- `captured_tree_landing` owns primary-checkout commits and preserves the captured index/worktree tree. For rolling-log calls it verifies that the caller-selected symbolic ref and starting OID equal primary `HEAD`, then uses the existing captured-HEAD tree and compare-and-swap path. Primary index/worktree mutation serialization follows the `Primary land` Term. Ref-only `land-worktree` can advance `HEAD` after selection; captured-OID CAS then refuses and existing pre-CAS cleanup and reselection apply. No temp-index route is used for rolling-log commits. `scripts/docs_branch_sync.sh` and the completed merge-landing plan are read-only evidence for the rejected unheld-ref temp-index alternative.
- A primary symbolic-HEAD mismatch is recovered before a caller reads or edits the log; an OID movement uses existing runner recovery before CAS. Landing lock ownership follows the Terms. Ref-only `land-worktree` can move the primary ref independently, and captured-OID CAS uses the existing cleanup and recovery boundary. Primary log writers do not take merge. The origin records why operator-lapse, stale earlier-check, global-lock, and separate-log-source alternatives do not close the incident; the Rule 42 alternatives appear in Gate delta.
- The known wrong-branch incident is the true catch motivating the blocking ref check. Further catches are expected to be rare shared-checkout branch switches during primary log writes. A false mismatch costs one recovery/reselection, performs no log edit or ref update, and preserves unrelated refs and worktree bytes; the 2027-01-25 review demotes and removes the check if the interval contains no additional true catch.

Decision points requiring a grill: none remain.
Scope extensions (grilled): none proposed.
Sources inspected: the backlog origin; `PLAN-PROMPTS.md` Standing rules and Write boundary; `EXEC-PROMPTS.md`; `plans` Final Step and freeze writer; the investigate append path; maintenance prune and freeze duties; primary-checkout write duties in `done`; the completed merge-landing grouping plan Task 2; `scripts/done_run.sh`; `scripts/docs_branch_sync.sh`; and `scripts/test_done_run_wrapper.py`.

## Standing constraints

- Primary log writes hold the primary done lock through same-turn commit and recovery, but do not acquire the repo-wide merge lock; worktree log commits retain the merge-lock guard.
- For primary-checkout log writes, select the intended symbolic ref and starting OID after lock acquisition and before staging; pass them unchanged through tree capture and the captured-HEAD compare-and-swap. Worktree log commits retain their current selected-branch route under the merge-lock guard.
- Stage only exact owned log paths; refuse pre-staged owned-path deltas per the current write contract.
- Keep unrelated refs, staged bytes, and worktree files unchanged. In primary rolling-log mode, refuse before staging if either rolling-log path already has a staged delta. Once staging begins, one runner-owned cleanup path unstages and verifies only this writer’s declared owned delta on every refusal before captured-ref CAS succeeds, including refusals before captured-tree landing. Disarm cleanup immediately after CAS success; later ledger or post-commit-hook errors report that the landed commit stands and do not roll back. If pre-CAS cleanup cannot be verified, report blocked recovery; the two-path pre-stage guard blocks either later primary log writer. Ordinary non-log `done_run` failure behavior remains unchanged. Landing lock ownership follows the `Primary land` and `Ref-only land-worktree` Terms. If ref-only `land-worktree` advances `HEAD` after primary log ref selection, captured-OID CAS refuses and owned-delta cleanup preserves the landing. Worktree-local branch and log behavior is unchanged. A concurrent worktree log commit continues to use its merge lock and must land only its own selected branch while the primary log writer lands only the primary selected ref.
- Reuse existing compare-and-swap and recovery behavior; add no lock, validator, or ceremony. The new mismatch refusal is registered with its dated demotion/removal commitment; primary log merge-lock contention is removed in the same change.

## Evaluation Criteria

**Quality dimensions:**
- Ref binding: the commit target is the caller-selected symbolic ref and OID when they match primary `HEAD`; plans freeze keeps its primary-placement current-branch and worktree-placement default-branch rules, and recovers before authoring when they do not match.
- Preservation: landing lock ownership follows the Terms. Ref-only `land-worktree` may move `HEAD` independently; captured-OID CAS refuses, cleans only the writer-owned delta, preserves the landing, and requires reselection. A mismatch refuses before tree capture without changing unrelated refs or index/worktree bytes. A concurrent worktree log commit changes only its selected ref and leaves the peer worktree unchanged.
- Scope: only rolling-log writes change; ordinary `done_run` commits keep their existing behavior.

**Done when:**
- A regression proves a primary-checkout mismatch refuses before staging or commit without changing the existing worktree-local log path.
- Every primary rolling-log refusal before successful captured-ref CAS, including a ref move caused by `land-worktree` and refusals before captured-tree landing, restores only this writer’s owned delta and leaves unrelated refs, index bytes, and worktree files unchanged; the landing remains standing and retry selects the new tip. Primary `land` cannot overlap a log write in the primary checkout because both hold the done lock. If cleanup cannot be verified, either primary log writer refuses before staging when either rolling-log path has residue. A ledger-append or post-commit-hook error after CAS leaves the landed commit standing and cleanup disarmed. Ordinary non-log `done_run` behavior and worktree log placement remain unchanged. A default-branch freeze mismatch names the required checkout alignment and resumes only after that state change.
- The rolling-log contract uses selected-ref preconditions and captured-tree CAS. Primary log writes use the done lock; landing modes follow the Terms and Task 2 mode-specific tests.

**Ship when:** None; this is a local reliability correction.

## Review Scope

**Explicit must-fix:** any design that lets a primary caller read or edit a log before its selected ref/OID matches primary `HEAD`, stages or commits to a peer ref, allows a primary `land` that can snapshot, mutate, or restore the primary checkout while a log writer holds the done lock, uses an unsafe lock order, or releases locks in the wrong order, a `land-worktree` ref move that lacks the captured-OID CAS refusal, omits owned-delta cleanup on a pre-CAS refusal, rolls back after successful CAS, changes ordinary non-log failure behavior, lets either rolling-log residue pass the existing pre-stage refusal, changes unrelated state, removes primary index/worktree done-lock serialization, lets a primary/worktree concurrency case cross refs or worktree bytes or lets the primary writer wait for the worktree merge lock, adds a refusal beyond the selected-ref mismatch and existing owned-path checks without the planned same-change retirement, or changes worktree placement.

**Implementation:**
- `scripts/done_run.sh` (Task 1)
- `scripts/test_done_run_wrapper.py` (Task 1)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 2)
- `docs/history/backlog/EXEC-PROMPTS.md` (Task 2)
- `agents/skills/investigate/SKILL.md` (Task 2)
- `agents/skills/maintenance/SKILL.md` (Task 2)
- `agents/skills/plans/SKILL.md` (Task 2)
- `agents/skills/execute-plan/worktree-first.md` (Task 2)
- `agents/skills/execute-plan/SKILL.md` (Task 2)
- `agents/skills/jira-workflow/SKILL.md` (Task 2)
- `agents/skills/doing-code-review/SKILL.md` (Task 2)
- `agents/skills/github-pr-workflow/SKILL.md` (Task 2)
- `agents/skills/update-stacked-branches/SKILL.md` (Task 2)
- `scripts/machinery_registry.json` (Task 2)
- `scripts/land_squash.sh` (Task 2)
- `scripts/test_land_squash.py` (Task 2)
- `scripts/done_sweep_gates_lib.py` (Task 2)
- `scripts/test_done_sweep_gates_lib.py` (Task 2)
- `agents/skills/maintenance/zcode.md` (Task 2)
- `agents/skills/maintenance/template-execution.md` (Task 2)

**Read-only evidence:**
- `docs/history/backlog/2026-10-25-primary-log-branch-drift-at-commit.md` (review-only)
- `docs/history/plans/completed/2026-09-20-merge-landing-lock-grouping.md` (review-only)
- `agents/skills/done/SKILL.md` (review-only)
- `agents/skills/maintenance/template-authoring.md` (review-only) - invokes plans authoring, does not write the rolling logs
- `scripts/docs_branch_sync.sh` (review-only) precedent

**Out of scope; reject unless plan-related:**
- Serializing all branch switches or adding a repository-wide lock.
- Changing squash composition, tree contents, or landing gates beyond primary `land` lock ownership; changing non-log `done_run` commits or rolling-log entry content and ordering.
- Changing the completion or dispatch behavior of maintenance plans and execution plans.

## Validation Commands

```bash
python3 scripts/test_done_run_wrapper.py
python3 scripts/test_land_squash.py
python3 scripts/test_done_sweep_gates_lib.py
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-25-primary-log-branch-drift-at-commit.md
bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-25-primary-log-branch-drift-at-commit.md
bash scripts/scan-public-hygiene.sh --files docs/history/plans/2026-10-25-primary-log-branch-drift-at-commit.md
bash scripts/check_maintenance_pins.sh
```

### Task 1: Add an explicit-ref transaction for rolling-log writes

Context surface: `## Terms`, `## Outcome`, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`
- `docs/history/backlog/PLAN-PROMPTS.md`
- `docs/history/backlog/EXEC-PROMPTS.md`

Primary class anchors:
- `captured_tree_landing` in `scripts/done_run.sh`

- [ ] Add the expected symbolic-ref and starting-OID pair for primary rolling-log writes. Callers select and check both under lock before the final log read or edit; reject a partial pair before staging with refs, index, and worktree unchanged. Worktree log commits and ordinary calls retain their existing paths. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `captured_tree_landing`, for the primary-checkout rolling-log path, require primary `HEAD` and the expected ref/OID pair to match before and after tree capture and after hooks; build the commit from that captured primary `HEAD` and use the existing captured-HEAD compare-and-swap. A mismatch uses existing recovery without a ref update. Preserve the worktree branch commit path. [class: IMPLEMENTATION_REQUIRED]
- [ ] Limit the captured-tree commit to declared owned log paths; an expected-ref or OID mismatch refuses without changing refs, primary index/worktree, or peer state. Before staging in primary rolling-log mode, refuse if either `docs/history/backlog/PLAN-PROMPTS.md` or `docs/history/backlog/EXEC-PROMPTS.md` already has a staged delta; leave the residue untouched. [class: IMPLEMENTATION_REQUIRED]
- [ ] Give primary rolling-log mode one cleanup owner for every refusal before captured-ref compare-and-swap succeeds, including gates before captured-tree landing. It unstages only this writer’s declared owned delta and verifies that delta is empty; unrelated staged and worktree bytes stay unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Disarm cleanup immediately after successful captured-ref compare-and-swap. A later ledger-append or post-commit-hook failure reports that the landed commit stands and never rolls it back. [class: IMPLEMENTATION_REQUIRED]
- [ ] If pre-CAS cleanup cannot be verified, report blocked recovery. Preserve ordinary non-log `done_run` failure handling. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep ordinary `done_run` commit and refusal behavior unchanged unless the caller selects the rolling-log path. [class: IMPLEMENTATION_REQUIRED]
- [ ] The fixture clears Git object/alternate/ceiling/namespace/shallow routing variables before invoking the runner. [class: REPOSITORY_TEST]
- [ ] Test caller selection, pre-read mismatch recovery, ordinary no-pair success/refusal and partial-pair refusal before staging with unchanged refs, index/worktree, and no rolling-log cleanup; also test captured primary `HEAD` as sole parent and selected-branch worktree placement. [class: REPOSITORY_TEST]
- [ ] Test rolling-log mode with a foreign staged path present before the early guard and with one inserted after that guard but before tree capture. Both cases refuse without commit or ref movement, preserve foreign staged bytes, and clean only the writer-owned delta; the early case refuses before `git add`. [class: REPOSITORY_TEST]
- [ ] Test each named done-lock consumer against an active primary log write in both lock orders; it waits or refuses before mutation, or the log writer waits without staging, then succeeds after checkout stability with unrelated refs and bytes unchanged. [class: REPOSITORY_TEST]
- [ ] Test overlap with a worktree writer paused after taking the merge lock but before ref update; the primary log write completes while the lock is held, then the worktree write completes, each advancing only its selected ref and preserving the peer index/worktree. [class: REPOSITORY_TEST]
- [ ] Test `land-worktree` moves primary `HEAD` between log ref selection and CAS; the writer refuses, cleans only its staged delta, preserves the landing and unrelated bytes, and reselects the new tip before retry. [class: REPOSITORY_TEST]
- [ ] Test representative pre-CAS refusals (pre-landing gate and post-hook CAS refusal) clean only the writer-owned delta and preserve unrelated state. [class: REPOSITORY_TEST]
- [ ] Test ledger-append failure after CAS: the ref stays advanced, the runner reports that the commit stands, and cleanup stays disarmed. [class: REPOSITORY_TEST]
- [ ] Simulate unverifiable cleanup for each rolling log; assert the initial writer reports blocked recovery, then both later writes refuse before `git add`. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: bind rolling-log commits to the intended ref` [class: IMPLEMENTATION_REQUIRED]

Machinery admission: the witnessed wrong-ref commit justifies the new blocking selected-ref mismatch refusal; the pre-registered registry entry records the incident, rare expected catch frequency, one recovery/reselection false-positive cost, 2027-01-25 review, promotion basis (the existing true catch), and demotion/removal if no additional true catch occurs by review. The same change removes the primary log writer’s merge-lock acquisition refusal, balancing one added refusal with one retired refusal; landing modes follow their Terms and worktree log commits retain their merge-lock guard. The runner’s two-path residue guard relocates the existing staged-path refusal and removes duplicate checks; it adds no separate refusal.

### Task 2: Route primary-checkout rolling-log writes through the captured-HEAD write

Context surface: Task 1 and `## Standing constraints`; referenced, never restated. Primary contract anchor: `Write boundary` in `docs/history/backlog/PLAN-PROMPTS.md`; the exec log consumer is `docs/history/backlog/EXEC-PROMPTS.md`.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`
- `docs/history/backlog/EXEC-PROMPTS.md`
- `agents/skills/investigate/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/jira-workflow/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`
- `agents/skills/update-stacked-branches/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `scripts/machinery_registry.json`
- `scripts/land_squash.sh`
- `scripts/test_land_squash.py`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/template-execution.md`

Primary class anchors:
- `land` in `scripts/land_squash.sh`
- `captured_tree_landing` in `scripts/done_run.sh`

- [ ] Update the canonical Write boundary to require only the primary done lock for primary log writes, retiring their merge-lock acquisition refusal; keep the worktree branch-commit path under merge lock. Require primary callers to check selected ref/OID against `HEAD` under the done lock before the final log read or edit; on mismatch, recover before changing the log. [class: IMPLEMENTATION_REQUIRED]
- [ ] Move the existing pre-staged-owned-path refusal to the runner and cover both log paths, retiring only caller-specific duplicates. Preserve the captured-tree staged-scope and capture-window fences for foreign paths outside the declared owned set. Define cleanup for every pre-CAS refusal only; after successful CAS, later errors leave the commit standing. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update the plans Entry freeze, investigate append, and maintenance prune/freeze instructions to use the placement-specific canonical Write boundary. Preserve worktree branch commits; for a worktree-placement freeze targeting the default branch when primary `HEAD` differs, use recovery that names the required checkout alignment and resumes only after primary `HEAD` reaches the default branch. Do not retry unchanged state or duplicate the transaction recipe. [class: IMPLEMENTATION_REQUIRED]
- [ ] Define the landing-mode lock ownership in `agents/skills/execute-plan/worktree-first.md` using the `Primary land` and `Ref-only land-worktree` Terms, then link the rule from `agents/skills/execute-plan/SKILL.md`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Require primary `land` to verify both lock owners before snapshot; update its callers and maintenance landing recipes to follow the `Primary land` Term. Keep ref-only `land-worktree` and worktree log commits under merge only. Update done-sweep recovery guidance and its assertions to name this order. [class: IMPLEMENTATION_REQUIRED]
- [ ] Test both lock orders: with a primary log writer holding done after staging, primary `land` cannot snapshot or restore; while primary `land` holds done during snapshot/merge/recovery, a log writer cannot read or edit until checkout stability. After release, both preserve log, landing, unrelated refs, index, and worktree bytes. [class: REPOSITORY_TEST]
- [ ] Test the landing lock-mode matrix below, with each row's lock fixture and observable outcome. [class: REPOSITORY_TEST]

| Mode | Lock fixture | Expected outcome |
|---|---|---|
| Primary `land` | Valid matching merge lock; no done lock | Refuses specifically for missing done before snapshot; after clearing the wrapper marker, it stays absent before post-call status probes. |
| Ref-only `land-worktree` | Valid merge lock; done lock held | Advances only the selected ref and preserves primary index/worktree bytes. |
- [ ] Add the pre-registered `protocol:primary-log-ref-precondition` registry entry with the incident, catch frequency, false-positive cost, 2027-01-25 review, and promotion/demotion criteria in its note; its demotion commitment removes the row and makes the mismatch check warning-only if no additional true catch occurs by review. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update `agents/skills/maintenance/zcode.md` so primary monitor prune/freeze/investigate writes use done only and worktree branch commits use merge only. Update `agents/skills/maintenance/template-execution.md` so both landing modes follow their Terms. [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify primary plan-freeze, investigate append, and maintenance prune/freeze check selected ref before log read/edit, use captured-HEAD writes, and commit in the same turn. On mismatch, log bytes and checkout state remain unchanged. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: serialize primary land with rolling-log writes` [class: IMPLEMENTATION_REQUIRED]

Machinery admission: Task 2 registers the mismatch refusal and its pre-registered demotion/removal commitment, while retiring primary-log merge-lock contention. Moving the owned-path refusal into the runner removes caller duplicates without adding another refusal. No lock, validator, or ceremony is added; landing modes use the existing lock boundaries defined in Terms.

## Documentation Impact Assessment

The canonical rolling-log Write boundary uses the primary done lock for primary log writes. Landing lock ownership follows the Terms. Callers verify selected ref/OID before the final log read or edit; the runner checks both log paths before staging and restores the writer’s owned delta on every pre-CAS refusal. After CAS, later errors leave the landed commit standing and cleanup disarmed. The registry records the mismatch refusal and its dated removal commitment; ordinary failure behavior and worktree placement remain intact.
