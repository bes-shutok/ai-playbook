# Plan: Done closeout lock-span and output-cost reduction

Backlog origins (scope of record):
- docs/history/backlog/2026-10-10-done-merge-lock-hold-span.md
- docs/history/backlog/2026-10-10-done-closeout-residual-cost.md

Driving force: efficiency + simplicity
Plan review record: the staging series docs/history/reviews/2026-10-11-plan-review-done-closeout-lock-span-and-output-cost-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 6.0h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-done-closeout-lock-span-and-output-cost.md (session interactive-operator-20261011-continue-authoring)

## Terms

- merge lock: the repository-keyed exclusive lock family (`merge-*` commands of `scripts/done-lock.sh`) serializing shared-checkout critical sections; canonical semantics live in that script's usage text.
- done lock: the per-worktree exclusive lock serializing one checkout's done run end to end (done Step 0); untouched by this plan.
- lock matrix: the two-family lock design home, docs/history/plans/completed/2026-09-20-merge-landing-lock-grouping.md, whose critical-section span rule this plan amends.
- critical section: the span a merge lock hold covers. Today the done skill's Step 2 span covers worktree migration plus docs-branch sync plus read-only verification plus the agent-side release dance; the matrix's intent is seconds-to-a-minute mutation spans.
- runner-owned span: the adjudicated Task 1 shape - the mutating runner (docs-branch sync runner, witness append, closeout migration) acquires and releases the merge lock inside its own process with a bounded wait, with no agent-turn gaps and no lock exports surviving into chat context.
- cycle-10: the 2026-10-10 done-run cycle whose closeout is this plan's witnessed incident (both origin rows).
- confused-deputy guard: the release subcommands' refusal to source the session fence file, so a release credential must be holder-only knowledge (the env token, or the from-holder arm's ancestry relation).
- sync runner: `scripts/docs_branch_sync.sh`, the canonical docs-branch archive backend (its own `docs-branch-sync.lock` flock stays untouched).
- witness append: the sync runner's `--append-witness` subcommand, which commit-trees a lesson-scope-audit witness onto the docs ref.
- closeout migration: `scripts/worktree_closeout_migrate.py migrate`, the ad-hoc-worktree-to-primary transfer of gitignored run artifacts; its `sweep` sibling already acquires the merge lock internally (the Task 1 precedent; the sweep's try-once posture stays unchanged).
- sweep-gates runner: `scripts/done_sweep_gates.sh` plus `scripts/done_sweep_gates_lib.py`, the done closeout's deterministic gate phases (pre-docs, pre-commit).
- bounded report: a gate report message reduced to a count plus at most 10 sample lines, with the full enumeration written to a file; gate verdict semantics unchanged.
- done-session directory: `{tmp_dir}/done-session/` under the facts-resolved tmp root, resolved at run time from the gate context; the run-scoped home for markers, manifests, and (new) full gate-report listings.
- from-holder arm: the Task 3 metadata-sourced release form (`--from-holder` on the release subcommands of both lock families): no env token required; the release gates on the recorded holder being an explicitly pinned, verifiably alive, non-degenerate process and the calling shell descending from it, then removes through the existing compare-and-swap.
- holder identity: the acquire-time recorded `holder_pid` plus its process start identity (`holder_identity` in the lock meta) that `holder_state` in `scripts/done-lock.sh` already verifies.
- session fence: the `<repo>/.ai-playbook/done-lock.session` / `.ai-playbook/merge-lock.session` file written at acquire for status and fence; it stays status-only in this plan (the from-holder arm never sources it as a credential).
- module dispatch: the skill-text structure the maintenance skill's size refactor landed (agents/skills/maintenance/SKILL.md router plus per-concern module files); Tasks 4 and 5 apply the same shape to done and learn.
- router: a SKILL.md that keeps frontmatter, scope, configuration, the ordered step list with one-paragraph load-on-dispatch pointers, Rules, and Integration Points, while step bodies live in module files beside it.
- clean path: a done or learn run that executes steps once in order with no failures; the reader shape Tasks 4 and 5 optimize, verified by the rehearsal's read-set outcome.

## Why

The 2026-10-10 cycle-10 done closeout held the repository merge lock for roughly five measured minutes (operator-experienced as about ten) against a seconds-scale sync mutation, and the whole closeout ran 35 to 40 minutes for minutes of mechanical work. The lock span includes agent inference gaps and a release dance whose chat-context token re-export failed twice on emission corruption before a hand-read from the lock's own metadata succeeded. Independently, the sweep-gates phases printed a 2428-line foreign-exclusion enumeration and a 901-entry kept listing that the consuming agent then re-read into context, and both skills reload their full 723-line and 604-line texts every run. Each cost class has a witnessed incident row; the first reduction (cf43eec48) owned none of them.

## Gist & Examples

TLDR: the done closeout's merge-lock hold collapses to the sync's own runtime by moving lock acquisition into the mutating runners, gate reports become bounded summaries with file-backed full lists, lock release gains a metadata-sourced credential arm that ends the token re-typing dance, and the done and learn skills load step text at execution time instead of front-loading two full skill bodies - all four arms shrink closeout cost, named by the efficiency and simplicity forces.

Before: a done run in an ad-hoc worktree acquires the merge lock with a 40-line skill block, holds it across migration, sync, read-only verification, and two failed release attempts, re-typing `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN` between one-shot shells; the pre-docs phase prints thousands of report lines; the agent reads done (723 lines) plus learn (604 lines) before step work starts.

After: the sync runner (and the witness append, and the closeout migration) acquire the merge lock internally for their mutation and release in an always-run finally, so the skill carries no lock management and no lock exports ever enter chat context; a gate with 901 kept entries prints `kept=901; samples: ...; full list: <done-session>/gate-reports/<run>-pre-docs-docs-tmp-sweep-full.txt`; a release with lost exports succeeds via `release-repo --from-holder` when the recorded holder is an explicitly pinned, verifiably alive process and the calling shell descends from it; the done router dispatches `step-2-docs-sync.md` only when Step 2 is in flight.

## Outcome

A done closeout whose wall clock tracks its mechanical work: the merge lock is held only by the mutation that needs it, gate output is readable without flooding context, lock release never depends on re-typing a token from chat history, and skill text is loaded per step in flight.

- The repository merge lock is free within seconds of the sync mutation finishing, so peer landings, docs syncs, and sweeps never wait on inference gaps or release retries.
- Sweep-gate reports stay complete on disk and readable in the message: counts plus at most 10 samples inline, full enumerations in the run's done-session directory.
- A release with lost or corrupted exports succeeds through the from-holder arm under gates that keep the confused-deputy guard's force; the env-token path is unchanged, and the done skill's release text names the arm as the sanctioned lost-export remedy.
- The done and learn skills load one step's module text when that step runs; the routers stay the contract of record.

Gate delta: net machinery removal. Removed: the done skill's merge-lock management ceremony (the acquire block, the exports-retention duty, the every-exit-path release paragraph, and the release-retry behavior the chat-context token class invited - the token class dies for the sync path), and the unbounded gate-report listing emission. Added: internal bounded-wait acquisition inside two existing runners and the witness append (a relocation of the existing lock family to its mutation span - no new lock, no new lock family, satisfying the coordination policy's no-new-lock-family rule; the sweep's existing try-once span stays unchanged; the relocated contended-lock refusal replaces the skill-side bounded-wait refusal one-for-one), the `--from-holder` release credential arm (admission: incident docs/history/backlog/2026-10-10-done-closeout-residual-cost.md Evidence - two fail-loud release refusals rc 3 from emission-corrupted re-exports, 2026-10-10; expected frequency: every done or landing release; false-positive cost: none - the env path is unchanged and every refusal is fail-loud with a named arm; residual shared-pin risk named in the arm's usage text; sunset: review 2027-01), and the bounded-report emission shape (output channel only; no gate predicate, refusal class, or verdict input moves). The moved text lives again as module files: byte-neutral relocation, no new ceremony surface; no standing rehearsal script is committed - the Task 6 rehearsal runs once from a scratch location.

## Assumptions

- assume Task 1 lands the runner-owned span (shape b) over skill-side fusion (shape a): the runner shape collapses the hold to the mutation runtime and removes the chat-context token surface for the whole sync path, while fusion only removes inference gaps; the sweep already runs the runner-owned form in production, and the lock matrix's seconds-scale critical-section intent is met either way; basis: the entry scope arm 1's explicit adjudication delegation, `scripts/worktree_closeout_migrate.py` sweep arm, and docs/history/plans/completed/2026-09-20-merge-landing-lock-grouping.md.
- assume the closeout migration (`migrate`) gains the same internal bounded-wait acquire as the sync runner even though the origin row names only the sync runner: dropping the skill-side lock without it would leave the ad-hoc-worktree migration an unlocked shared-checkout write, a regression against the lock matrix; the sweep's try-once helper is parameterized for label and wait rather than reused verbatim, so the migration hold reports under its own label and waits boundedly; basis: done SKILL.md Step 2's current acquire-once-per-run span covering migration plus sync.
- assume the bounded-report sample bound is 10: a mechanical reporting constant, not a gate input; basis: the origin's counts-plus-bounded-samples direction (docs/history/backlog/2026-10-10-done-closeout-residual-cost.md).
- assume the from-holder credential is the caller-ancestry relation gated on an explicitly pinned holder: the arm requires the acquire to have recorded `holder_pinned` (the pin env var was set) and refuses unpinned and degenerate holders (pid 1), because a pin to a shared supervisor would let every subtree process pass the walk; the adjudication against the origin's simpler meta-read shape: a meta-read token plus alive check lets an overthrown chat release a peer's live hold with one flag - the exact overthrown-chat scenario the confused-deputy guard's comment names - while the ancestry relation is the only holder-only relation that survives the one-shot shell exit, and the env path (whose token is likewise readable from meta.env by a determined process) requires deliberate theft and stays unchanged; the residual shared-pin risk is named in the arm's usage text and admission note; basis: `cmd_release`'s token match plus `steal_remove_if_unchanged` in scripts/done-lock.sh and the cycle-10 release-dance witness.
- assume the module splits re-aim every moved literal's consumers in the same change - pins rows via a generated inventory (grep the pins script for done/learn-targeting rows), and the machine consumers (suite assertions, span slicers, budget caps, machinery-registry rows, harness-policy surfaces, hygiene-scan globs) via the same generated sweep per touched task; basis: the pins suite's literal-span contract and the byte-consumer inventory from the r1 panel.
- assume the rehearsal checkout reuses the host's deployed runtime home read-only, and every agent-side lock invocation in the rehearsal pins `DONE_LOCK_SCRIPT` to the scratch checkout's repo-local copy so the changed script is what runs; the baseline gate run materializes the base revision's scripts in a second scratch tree, never the deployed home; basis: the done skill's lock-script resolution is deployed-home-first, so the rehearsal must pin the override explicitly.
- assume the origin's compact clean-path run-card alternative for the text-loading arm is rejected in favor of the router split: the router split is the landed precedent (the maintenance size refactor), moves bytes without growth, and serves learn's standalone invocation (the maintenance harvest duty) as well as the embedded one; basis: agents/skills/maintenance/SKILL.md's module dispatch and the learn skill's Integration Points.
- assume the span gaps between this run's migrate, sync, and witness spans are adjudicated as accepted with bounded recovery: each mutation stays serialized, the witness append gains protection it lacked, verification is read-only, and the residual case (a peer sweep's removal phase removing this run's ad-hoc worktree in the migrate-to-sync gap) fails loud mid-closeout with the sanctioned response of re-running the sync from the primary checkout; the sweep's own twin gate governs a migrated-but-unsynced worktree; basis: the lock matrix's per-mutation serialization intent and the r1 risk worker's premortem.

Decision points requiring a grill: lock-span shape adjudication: runner-owned acquisition selected per the entry scope arm 1's explicit delegation to adjudicate and land one, source: PLAN-PROMPTS entry done-closeout-lock-span-and-output-cost scope arm 1 (frozen 0e66f685), 2026-10-11, affects Task 1; report sample bound: 10 fixed as an authoring constant per the origin's counts-plus-bounded-samples direction, source: docs/history/backlog/2026-10-10-done-closeout-residual-cost.md, 2026-10-11, affects Task 2; from-holder credential shape: ancestry-gated pinned holder over the origin's simpler meta-read shape, adjudicated in Assumptions, source: docs/history/backlog/2026-10-10-done-closeout-residual-cost.md arm (b) plus the confused-deputy guard's overthrown-chat comment in scripts/done-lock.sh, 2026-10-11, affects Task 3; text-loading shape: router split over the compact run card, adjudicated in Assumptions, source: docs/history/backlog/2026-10-10-done-closeout-residual-cost.md arm (c), 2026-10-11, affects Tasks 4 and 5

## Standing constraints

- Gate predicates are frozen: every sweep-gate keeps its verdict semantics, inputs, and failure classes; only the report emission channel and the release credential sourcing change.
- The lock families stay frozen: done-lock and merge-lock keying, TTLs, session fences, stale-clean escapes, dead-holder recovery, and compare-and-swap removal semantics are unchanged; no new lock family (the coordination policy's rule); the sweep's existing try-once acquire stays unchanged.
- Landing critical sections owned by other workflows (the worktree-complete squash landing, the sweep's release span) are untouched; `scripts/land_squash.sh` is read-only context for this plan.
- Any newly invoked helper resolves two-tier: repo-local `scripts/` copy first, deployed runtime home copy second, matching the closeout script convention.
- Skill text stays runtime-agnostic and names no personal paths; moved step bodies keep their section headings so Integration Point references survive the move.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the rehearsal closeout's merge-lock hold spans only the mutation runtime (measured and reported); every sweep-gate verdict on identical trees is identical between the base-revision baseline run and the post-change run.
- compatibility: the lock script's pre-existing selftest fixtures pass unmodified (the fixture count is asserted unchanged); the docs-branch focused suite passes with its new lock fixtures and its re-aimed skill-contract assertion.
- docs accuracy: probes over the edited skill text pass only when the prose matches implemented behavior (no merge-lock export-retention duty remains in the done skill; runner-owned span sentences match the code; the release text names the from-holder arm).
- staged loading: a clean closeout's read set is the router plus the in-flight step modules, evidenced from the rehearsal run log, and every router pointer carries the load-on-dispatch instruction.
- simplicity (net machinery): the removed skill-side lock ceremony and unbounded listings are verified absent by grep; no new refusal class exists beyond the relocated contended-lock refusal and the from-holder arm's admitted release refusals (foreign caller, dead holder, ambiguous identity, unpinned or degenerate holder, hostname mismatch, malformed meta).

**Done when:**
- The sync runner, witness append, and closeout migration each acquire and release the merge lock inside their own process, releasing on every exit path including mid-write failures.
- The sweep-gates runner emits bounded report messages and writes full enumerations under the done-session directory for both capped sites, with run-scoped filenames and a window prune arm.
- `release-repo --from-holder` and `merge-release-repo --from-holder` succeed for the recorded explicitly pinned, alive holder's own process tree and refuse a foreign caller, a dead holder, an ambiguous identity, an unpinned holder, a degenerate holder, a hostname mismatch, and a malformed meta, all fail-loud; the compare-and-swap refuses a stale generation.
- The done and learn routers dispatch per-step modules with load-on-dispatch pointers; every moved pins literal and machine-consumer assertion is re-aimed and the pins suite plus touched suites pass.
- The run-once rehearsal completes on the scratch checkout with the five observed outcomes recorded and all suites green.

**Ship when:**
- None; all work is local to this repository and its runtime home.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/docs_branch_sync.sh` (merge-lock acquisition around `sync` and the witness append, the hold-span trace line; all other functions frozen)
- `scripts/worktree_closeout_migrate.py` (the migrate subcommand's acquisition plus the shared acquire helper's label and wait parameterization; all other subcommands frozen)
- `scripts/done-lock.sh` (the release subcommand family plus the acquire meta write gaining the `holder_pinned` field, plus selftest; all acquire semantics otherwise frozen - keying, TTL, fence, stale-clean, dead-holder recovery, CAS unchanged; wait, status, stale, and orphaned commands frozen)
- `scripts/done_sweep_gates_lib.py` (the review-staging report emission site, the docs-tmp kept join site, and the shared bounded-emission helper; all gate classification logic frozen)
- `agents/skills/done/SKILL.md` (whole file: Step 0 lock-matrix paragraph, Step 2 rewrite, Step 6 release text, Rules lock row, blocked posture, router restructure)
- `agents/skills/done/step-*.md`, `agents/skills/done/sweep-gates-*.md` *(new)*
- `agents/skills/learn/SKILL.md` (whole file: router restructure)
- `agents/skills/learn/step-*.md` *(new)*
- `agents/skills/docs-branch/SKILL.md` (the invocation-sentence paragraph only; rest frozen)
- `scripts/check_maintenance_pins.sh` (re-aimed and retired rows only; all other rows frozen)
- `scripts/scan-public-hygiene.sh` (the GLOB_BODIES exemption inventory only; all other content frozen)

**Tests:**
- the touched surfaces' existing focused suites, extended in place (fixtures are execution-selected from repository evidence)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. The docs-branch skill and the two restructured skills carry their own doc updates in the explicit list; no other docs move.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh`; reason: the landing critical section is another workflow's lock span, frozen by standing constraint.
- `scripts/gate_liveness_ledger.json` as a plan deliverable; reason: no guard fires by plan design; ledger appends during execution follow the done skill's standing guard-liveness rule, not this plan.
- `agents/skills/maintenance/*` including the overlay's Merge landing lock paragraph; reason: it describes the lock family for scheduler lanes, which stays valid under runner-owned spans.
- The learn and done gate predicates (corpus gates, sweep-gate classifications); reason: standing constraint freezes them.

## Validation Commands

```bash
# Fail-closed block: every check aborts non-zero on miss or forbidden match.
set -u
REPO="$(git rev-parse --show-toplevel)"
FAIL=0
note() { printf 'VALIDATION: %s\n' "$1"; }
bail() { printf 'VALIDATION FAIL: %s\n' "$1"; FAIL=1; }
flatten() { tr '\n' ' ' < "$1" | tr -s ' '; }

# 1. Runner-owned spans: the sync runner carries the internal bounded-wait
#    acquire with its label and the hold-span trace; the done skill carries no
#    merge-lock management anywhere (existence-gated, fail-open-proof).
grep -qF 'merge-wait-acquire' "$REPO/scripts/docs_branch_sync.sh" \
  || bail "sync runner lacks internal merge-acquire"
grep -qF -- '--label docs-branch-sync' "$REPO/scripts/docs_branch_sync.sh" \
  || bail "sync runner acquire lacks its label"
grep -qF 'merge-lock: held' "$REPO/scripts/docs_branch_sync.sh" \
  || bail "sync runner lacks the hold-span trace line"
test -f "$REPO/agents/skills/done/SKILL.md" || bail "done router absent"
flatten "$REPO/agents/skills/done/SKILL.md" | grep -qF 'merge-wait-acquire' \
  && bail "done router still prescribes the skill-side merge-wait-acquire block"
test -f "$REPO/agents/skills/done/step-2-docs-sync.md" || bail "done Step 2 module absent"
flatten "$REPO/agents/skills/done/step-2-docs-sync.md" | grep -qF 'MERGE_LOCK_TOKEN' \
  && bail "done Step 2 module still retains lock exports in chat context"
flatten "$REPO/agents/skills/done/step-2-docs-sync.md" | grep -qiF 'runner-owned' \
  || bail "done Step 2 module does not name the runner-owned span shape"
flatten "$REPO/agents/skills/done/step-6-release.md" | grep -qF -- '--from-holder' \
  || bail "done release module does not name the from-holder arm"

# 2. Bounded reports: the emission helper exists, derives the home from the
#    gate context, caps samples at 10, and scopes filenames by run identity.
grep -qE 'SAMPLE_LIMIT *(=|:) *10\b' "$REPO/scripts/done_sweep_gates_lib.py" \
  || bail "bounded-report sample limit 10 not pinned in the gates lib"
grep -qF 'gate-reports' "$REPO/scripts/done_sweep_gates_lib.py" \
  || bail "full-list report home under done-session not named"
grep -qF 'done_session_dir' "$REPO/scripts/done_sweep_gates_lib.py" \
  || bail "report home does not derive from the gate context"

# 3. From-holder arm: flag documented, gates present, selftest green with
#    fixture count asserted, fixtures visible.
mkdir -p "$REPO/docs/tmp/done-session" || bail "cannot create the selftest log home"
bash "$REPO/scripts/done-lock.sh" selftest > "$REPO/docs/tmp/done-session/selftest.log" 2>&1 \
  || bail "lock script selftest failed"
grep -q 'from-holder' "$REPO/docs/tmp/done-session/selftest.log" \
  || bail "selftest carries no from-holder fixture"
grep -qF 'holder_pinned' "$REPO/scripts/done-lock.sh" \
  || bail "holder_pinned gate absent from the lock script"

# 4. Routers dispatch modules (both directions); moved pins re-aimed.
for m in $(grep -oE '(step|sweep-gates)-[a-z0-9-]+\.md' "$REPO/agents/skills/done/SKILL.md" | sort -u); do
  test -f "$REPO/agents/skills/done/$m" || bail "router names absent module: $m"
done
for m in $(grep -oE 'step-[a-z0-9-]+\.md' "$REPO/agents/skills/learn/SKILL.md" | sort -u); do
  test -f "$REPO/agents/skills/learn/$m" || bail "router names absent module: $m"
done
for m in "$REPO"/agents/skills/done/step-*.md "$REPO"/agents/skills/done/sweep-gates-*.md "$REPO"/agents/skills/learn/step-*.md; do
  base="$(basename "$m")"
  grep -qF "$base" "$REPO/agents/skills/done/SKILL.md" || grep -qF "$base" "$REPO/agents/skills/learn/SKILL.md" \
    || bail "module on disk not named by its router: $base"
done
for router in "$REPO/agents/skills/done/SKILL.md" "$REPO/agents/skills/learn/SKILL.md"; do
  grep -qF 'loads the named module' "$router" || bail "router lacks the load-on-dispatch instruction: $router"
done
bash "$REPO/scripts/check_maintenance_pins.sh" || bail "pins suite failed"

# 5. Machine consumers and hygiene inventory re-aimed.
python3 "$REPO/scripts/test_docs_branch_sync.py" || bail "docs-branch suite failed"
python3 "$REPO/scripts/test_worktree_closeout_migrate.py" || bail "migrate suite failed"
python3 "$REPO/scripts/test_done_sweep_gates_lib.py" || bail "sweep-gates lib suite failed"
python3 "$REPO/scripts/test_done_sweep_gates_wrapper.py" || bail "sweep-gates wrapper suite failed"
bash "$REPO/scripts/test_done_lock_holder_visibility.sh" || bail "holder-visibility suite failed"
grep -qF 'agents/skills/done/**' "$REPO/scripts/scan-public-hygiene.sh" \
  || bail "hygiene exemption inventory not widened to the done module tree"

# 6. Hygiene and em-dash policy over the touched set.
( cd "$REPO" && bash scripts/scan-public-hygiene.sh ) || bail "hygiene scan failed"
bash "$REPO/scripts/check-no-em-dash.sh" touched || bail "em-dash scan failed"

[ "$FAIL" -eq 0 ] && note "all validation gates passed" || exit 1
```

The run-once rehearsal (Task 6) executes outside this block from a scratch location and records its evidence lines in the round's execution records; `flatten` above is the wrap-tolerant flatten idiom with existence gates on every forbidden match so a missing file is a named failure, never a silent pass.

### Task 1: Runner-owned merge-lock spans for the sync, witness append, and closeout migration

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/docs_branch_sync.sh`
- `scripts/worktree_closeout_migrate.py` (migrate subcommand and the shared acquire helper only)
- `agents/skills/done/SKILL.md` (Step 2 region plus the Step 0 lock-matrix paragraph plus the Rules lock row and the blocked-posture text)
- `agents/skills/docs-branch/SKILL.md` (invocation-sentence paragraph)
- `scripts/check_maintenance_pins.sh` (the merge-lock row retirement or semantic rewrite only)

Primary class anchors:
- `sync` in `scripts/docs_branch_sync.sh`
- `append_witness` in `scripts/docs_branch_sync.sh`
- `main` in `scripts/worktree_closeout_migrate.py`, migrate subcommand dispatch

- [x] Add an internal merge-lock helper to the sync runner (two-tier done-lock script resolution, `merge-wait-acquire --label docs-branch-sync --max-wait 300` with the wait overridable by a `DOCS_SYNC_MERGE_MAX_WAIT` env defaulting to 300, exports parsed in-process, release in an always-run finally, one `merge-lock: held <N>s` stderr line at release) [class: IMPLEMENTATION_REQUIRED]
- [x] Hold the helper's lock across `sync(repo)`'s read-and-mutate body and across `append_witness()`'s mutation, so the hold is the runner's own runtime with no agent-turn gaps [class: IMPLEMENTATION_REQUIRED]
- [x] Contended-lock refusal: given a foreign-held merge lock that stays held past the bounded wait, expects the sync runner to fail loud with the holder evidence and leave the docs ref byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Always-run release with an acquire-happened witness: given a forced mid-sync failure after acquisition, expects the run's trace to contain the merge-acquire stage AND `merge-status` to report free immediately after the failing run [class: REPOSITORY_TEST]
- [x] Mirror the internal bounded-wait acquire for the migrate subcommand of `scripts/worktree_closeout_migrate.py` under its own label (`worktree-closeout-migrate`), parameterizing the sweep/migrate helper for caller-supplied label and wait so the sweep's try-once posture and label stay unchanged; contended-refusal and release-on-failure fixtures cover the migrate and witness arms (the migrate suite's existing blocker fixture is the pattern) [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture hermeticity: the touched suites' env builders pin `MERGE_LOCK_ROOT` / `MERGE_LOCK_POLL_SECS` into the fixture tmp tree and `DONE_LOCK_SCRIPT` at the repo-local copy (the migrate suite's lock-root fixture is the precedent), so no fixture reads or writes the host lock home, and the contended-refusal fixtures set `DOCS_SYNC_MERGE_MAX_WAIT=2` with `MERGE_LOCK_POLL_SECS=1` so the bounded-wait deadline is exercised in seconds, never at the 300 default [class: REPOSITORY_TEST]
- [x] Rewrite the done skill's Step 2: delete the merge-wait-acquire block, the exports-retention commentary, the every-exit-path release paragraph, and the release snippet; state the runner-owned spans (migration, sync, witness append) and move the post-sync verification text after the sync completes, outside any lock [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite the done skill's Rules-section lock row and the blocked-posture text to the runner-refusal posture (fail loud with holder evidence, then bounded retry, skip-with-report, or park-for-operator per the coordination policy) [class: IMPLEMENTATION_REQUIRED]
- [x] Update the done skill's Step 0 lock-matrix paragraph's span wording; record the span-gap adjudication (peer sweep removal in the migrate-to-sync gap fails loud, recovery re-runs the sync from the primary) [class: IMPLEMENTATION_REQUIRED]
- [x] Update the docs-branch skill's invocation sentence so it names the runner-owned span instead of the held-by-done wording; re-aim the docs-branch suite's pinned acquire sentence at the new runner-owned span sentence [class: IMPLEMENTATION_REQUIRED]
- [x] Retire or semantically rewrite the pins row freezing the removed acquire sentence ("done keeps the merge lock around migration and sync") in the same change [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the contended-lock, acquire-stage-witness, and always-run-release fixtures fail against today's runner (no internal acquire exists and no acquire stage is traced) [class: REPOSITORY_TEST]
- [x] Write minimal implementation, then Run → expect GREEN on the touched surfaces' focused suites including the new fixtures [class: REPOSITORY_TEST]
- [x] Commit: `feat: move the done closeout's merge-lock span into the sync and migration runners` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Bounded sweep-gate reports with run-scoped, file-backed full lists

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_sweep_gates_lib.py` (the two emission sites plus a shared bounded-emission helper; classification logic frozen)

Primary class anchors:
- `derive_review_staging_scope` in `scripts/done_sweep_gates_lib.py`
- `ReviewStagingScope` in `scripts/done_sweep_gates_lib.py`

- [x] Add the bounded-emission helper (message carries the count plus at most 10 sample lines and names the full-list file; the full enumeration is written under the gate context's done-session directory, `ctx.done_session_dir / "gate-reports"`, directory created on demand; the filename is scoped by run identity where the run manifest resolves one, falling back to the phase-gate name) and wire it at the review-staging report-line emission and the docs-tmp kept join [class: IMPLEMENTATION_REQUIRED]
- [x] Write-failure arm: on full-list write failure the helper degrades to today's unbounded inline emission plus one warning line naming the failed write path, never a gate failure [class: IMPLEMENTATION_REQUIRED]
- [x] Verdict parity and message shape: given the same staging tree with more than 10 reportable entries, expects the emitted message to carry a count, at most 10 sample lines, and the full-list file name (this shape assertion is the RED target against today's unbounded output), and the gate's pass-or-fail verdict to equal the frozen classification's expectation (green-today by design, documented as parity, not a RED target) [class: REPOSITORY_TEST]
- [x] Full-list fidelity: given a candidate set larger than the sample bound, expects the written full-list file to contain every entry the old inline emission would have printed, one per line; given a second run in the same checkout, expects its report file name to be distinct from the first run's [class: REPOSITORY_TEST]
- [x] Small-set shape: given 10 or fewer entries, expects the message to list them inline exactly as today (no behavior change at small scale) [class: REPOSITORY_TEST]
- [x] Write-failure degradation: given a staging tree with more than 10 reportable entries and the gate-reports parent made unwritable, expects the gate verdict to equal the unwritable-free run's verdict, the message to carry the full inline enumeration plus one warning line naming the failed write path, and the exit status to stay pass [class: REPOSITORY_TEST]
- [x] Retention: the done-session sweep's prune arm removes gate-reports files outside the current session window, mirroring the run-start marker rule [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the message-shape and full-list-fidelity fixtures fail against today's unbounded emission [class: REPOSITORY_TEST]
- [x] Write minimal implementation, then Run → expect GREEN on the gates lib suite [class: REPOSITORY_TEST]
- [x] Commit: `feat: bound sweep-gate report listings with file-backed full lists` [class: IMPLEMENTATION_REQUIRED]

### Task 3: From-holder release arm on both lock families

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done-lock.sh` (release, release-repo, merge-release, merge-release-repo flag handling, the acquire meta write gaining the `holder_pinned` field, plus selftest; all acquire semantics otherwise frozen - keying, TTL, fence, stale-clean, dead-holder recovery, CAS unchanged; wait, status, stale, and orphaned commands frozen)
- `agents/skills/done/SKILL.md` (the Step 6 release paragraph and the Step 0 exports note only)

Primary class anchors:
- `cmd_release` in `scripts/done-lock.sh`
- `holder_state` in `scripts/done-lock.sh`
- `session_fence_matches_lock` in `scripts/done-lock.sh`

- [x] Add `--from-holder` to the four release subcommands: no env token required; the arm resolves the repo-keyed lock dir and requires the meta to parse (token, numeric started epoch, holder pid, holder identity, hostname) [class: IMPLEMENTATION_REQUIRED]
- [x] The arm requires the acquire-time recorded `holder_pinned` flag (the pin env var was set at acquire; the usage text warns that pinning to a shared supervisor voids the arm's guard) and the recorded hostname to match the invoking host (the usage text names the rename false-positive and the fallback ladder) [class: IMPLEMENTATION_REQUIRED]
- [x] The arm requires `holder_state` to report alive with exact identity (dead routes to the orphaned arm; ambiguous refuses), refuses the degenerate holder (pid 1), and requires the calling shell's bounded parent-process walk to reach the recorded holder pid [class: IMPLEMENTATION_REQUIRED]
- [x] The arm removes through the existing compare-and-swap; every refusal is fail-loud naming the failed gate [class: IMPLEMENTATION_REQUIRED]
- [x] Wire the skill text: the done skill's Step 6 release paragraph and the Step 0 exports note name `--from-holder` as the sanctioned arm when exports are lost with the recorded holder verifiably alive, the env path staying the default [class: IMPLEMENTATION_REQUIRED]
- [x] Holder-path release: given exports lost between one-shot shells in the acquiring session's own process tree, expects `release-repo --from-holder` to release the still-alive pinned hold [class: REPOSITORY_TEST]
- [x] Refusal arms: foreign caller (a process tree not descending from the recorded holder), verified-dead holder (refused naming the orphaned recovery arm), reused-pid ambiguous identity, unpinned holder, degenerate holder (pid 1), foreign hostname in meta, malformed meta (missing or non-numeric started epoch or absent hostname) - each refused with a named gate and the lock intact [class: REPOSITORY_TEST]
- [x] Pin recording: given an acquire with the pin env var set, expects the meta to record `holder_pinned=1`; given an acquire without it, expects the meta to record it unset, so the recording itself is discriminatingly tested [class: REPOSITORY_TEST]
- [x] Generation race: after the gates read the meta, replace the lock generation (stale-clean plus re-acquire) and expect the old-generation from-holder to be unable to remove the newer generation [class: REPOSITORY_TEST]
- [x] Run → expect RED: the from-holder selftest fixtures fail before the flag exists [class: REPOSITORY_TEST]
- [x] Implement, then Run → expect GREEN on the lock script selftest with all pre-existing fixtures unmodified and the fixture count asserted unchanged [class: REPOSITORY_TEST]
- [x] Commit: `feat: add from-holder metadata-sourced release to the lock families` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Done skill module dispatch split

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/done/SKILL.md` (whole file; restructure)
- `agents/skills/done/step-*.md`, `agents/skills/done/sweep-gates-*.md` *(new)*
- `scripts/check_maintenance_pins.sh` (moved-literal rows only)
- `scripts/scan-public-hygiene.sh` (GLOB_BODIES exemption inventory only)

Primary class anchors:
- `Workflow continuity` in `agents/skills/done/SKILL.md`

- [x] Split the done skill body into per-concern module files beside the router (lock and manifest setup, learn and ledger, pre-docs sweep gates, docs sync, pre-commit stages, pre-commit sweep gates, commit, skills and facts, release, report), keeping frontmatter, scope ledger, invocation, configuration, workflow continuity, the ordered step dispatch list with one-paragraph load-on-dispatch pointers, Rules, and Integration Points in the router [class: IMPLEMENTATION_REQUIRED]
- [x] Every module keeps its section headings byte-identical, and the release and sweep-gates modules document the from-holder arm's gates and the full-list file location [class: IMPLEMENTATION_REQUIRED]
- [x] Generated pins inventory: grep the pins script for done-targeting rows and re-aim every row whose literal lands in a module (the rearm-on-touch pointer and its heading-order check, the dirt guard, the review-thread gate, the queue-drain taxonomy parity span, the reviews-home arm rows, the landing-cost rows, and every other row the sweep names), retiring or rewriting rows whose contract the plan deleted; run the pins suite green in-task [class: IMPLEMENTATION_REQUIRED]
- [x] Generated machine-consumer inventory: grep scripts/ for the done SKILL.md path and moved literals, and re-point every byte consumer in the same change (the lessons-recovery contract's anchor pairs, the sweep-gates lib's done-text span assertion, the skill-text budget caps and machinery-registry path rows, the harness-policy contract's surface list gaining the new modules); run each touched suite green in-task [class: IMPLEMENTATION_REQUIRED]
- [x] Widen the hygiene-scan exemption inventory from the single-file entries to the skill directories (`agents/skills/done/**`) with the scan run in-task, so the moved step bodies keep their earned exemption by a deliberate inventory row rather than an improvised per-file patch [class: IMPLEMENTATION_REQUIRED]
- [x] Dispatch parity: extract the module filenames named in the router and verify each exists and every module on disk is named by the router (both directions), with paragraph-lead resolution for bold leads like "Run placement", asserting every router pointer carries the load-on-dispatch instruction [class: REPOSITORY_TEST]
- [x] Reference parity: run the precedent's corpus sweep (grep agents/, scripts/, docs/maintenance/, README.md for done Step and heading citations) verifying each resolves to a router or module carrying the heading verbatim; fix stale gate-numbering citations found by the sweep in the same change [class: REPOSITORY_TEST]
- [x] Commit: `refactor: split the done skill into per-step modules behind a router` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Learn skill module dispatch split

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/learn/SKILL.md` (whole file; restructure)
- `agents/skills/learn/step-*.md` *(new)*
- `scripts/check_maintenance_pins.sh` (learn rows the generated sweep names, if any)

Primary class anchors:
- `Completion Checklist` in `agents/skills/learn/SKILL.md`

- [x] Split the learn skill body into concern-sized module files behind the same router shape as Task 4 (grouped at the top-level-step grain per the maintenance precedent: one extraction module carrying Step 1 and its 1.5 through 1.8 sub-step headings byte-identical inside, one placement module, one instruction-updates module carrying the size and corpus gates, one completion module; single-digit file count), keeping headings byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Generated consumer sweep: run the pins suite and the corpus citation sweep for learn Step and heading references (done consumers' Integration Points included), re-aiming any moved literal in the same change [class: REPOSITORY_TEST]
- [x] Dispatch parity: extract the module filenames named in the router and verify each exists and every module on disk is named by the router, both directions, and assert every router pointer carries the load-on-dispatch instruction [class: REPOSITORY_TEST]
- [x] Commit: `refactor: split the learn skill into per-step modules behind a router` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Run-once integration rehearsal

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none (the rehearsal runs once from a scratch location outside the committed tree; no standing script lands)

Primary class anchors:
- `main` in `scripts/docs_branch_sync.sh`, hold-span trace the rehearsal measures

- [x] Baseline materialization: clone the base revision's `scripts/` into a second scratch tree (or a second clone at the base commit with resolution forced to it) and seed two byte-identical trees (tar-snapshot restored between runs); the deployed runtime home is never the baseline [class: IMPLEMENTATION_REQUIRED]
- [x] Run the baseline gate phase on the baseline tree with `DONE_LOCK_SCRIPT` and every script-resolution override pinned to the baseline tree, recording the per-gate `OUTCOME:` lines verbatim into the rehearsal output [class: IMPLEMENTATION_REQUIRED]
- [x] Run the post-change closeout on the identical tree with the same overrides pinned to the landed tree and the holder pin env var set at the closeout's Step 0 acquire (so the hold is recorded pinned and the from-holder outcome is producible; record the pin evidence beside outcome 3), recording the per-gate `OUTCOME:` lines, and diff verdict-per-gate against the baseline [class: IMPLEMENTATION_REQUIRED]
- [x] Observed outcomes recorded as evidence lines in the rehearsal output: (1) the merge-lock hold span from the sync runner's `merge-lock: held <N>s` line is the sync's own runtime (seconds-scale, no inference-gap or release-retry span); (2) the sweep-gate reports are bounded with full-list files present under the scratch done-session directory; (3) a from-holder release succeeds from a fresh shell with no token env [class: REPOSITORY_TEST]
- [x] Observed outcomes recorded as evidence lines in the rehearsal output (continued): (4) the gate-verdict diff is empty; (5) the clean closeout's read set is the router plus the in-flight modules, evidenced from the run log [class: REPOSITORY_TEST]
- [x] Run the full battery: the lock script selftest, the holder-visibility suite, the sweep-gates lib and wrapper suites, the docs-branch and migrate suites, the pins suite, the hygiene scan, and the em-dash scan, all green [class: REPOSITORY_TEST]
