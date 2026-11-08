# Plan: dispatch-admission outstanding-manifest recovery

Backlog origins (scope of record):
- docs/history/backlog/2026-11-05-dispatch-admission-outstanding-manifest-recovery.md
- docs/history/backlog/2026-11-04-dispatch-admission-candidate-side-conservatism.md

Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-dispatch-admission-outstanding-manifest-recovery-p4ac74b93-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 3h total, largest task 1.25h
Executed: yes (16e87ffe89687624d00ff8e476fc64e71073aad8)

Authoring claim: 2026-11-05-dispatch-admission-outstanding-manifest-recovery.md (session sess_aea7e776-fa40-4c32-82de-1b0addebe02b)

## Terms

- target-disjointness admission: the pre-dispatch consult (`scripts/dispatch_admission.py` `check_admission`) that refuses a candidate run whose owned-path set intersects an outstanding run's recorded set; the consult is global: a refusal blocks both lanes' dispatches.
- done-setup manifest: the run-owned JSON record at the facts-resolved done-session home (`docs/tmp/done-session/run-manifest-<run_id>.json`) carrying the `owned_paths`, `owned_plan_paths`, and `owned_review_paths` list fields, written by the done flow as today.
- execution claim: the live-run witness file (`docs/tmp/execution-claims/<plan-slug>.md` in the primary checkout) created by `scripts/execution_claim.sh` and deleted at terminal release; its `updated:` freshness defines the claim-live window.
- admission record: the claim-keyed JSON object this plan adds beside the execution claim in the primary checkout at the gateway's fixed relative path (`docs/tmp/execution-claims/<plan-slug>-admission.json`, never a facts-resolved temp directory), carrying exactly the three list fields `owned_paths`, `owned_plan_paths`, and `owned_review_paths`, so the consult's existing manifest reader reads it unchanged; it is never a `run-manifest-*.json` file, so the done-session classification surface never sees it.
- new-owner claim creation: a gateway claim create that starts a new run's ownership of a plan slug: a fresh create, a stale-foreign-claim takeover, or a dead-run conversion; it writes a fresh seed and replaces any prior admission record for that slug.
- refresh recreate: the gateway's refresh arm recreating a claim the same run lost to an unlink; it keeps an existing admission record and seeds only when none exists.
- claim retirement: a gateway path that ends a run's claim without a new owner taking it: release, sweep, and take-mode failure cleanup; each removes the admission record with the claim.
- owned-path set: the repository paths a run claims as its own edit surface.
- outstanding run: a run already in flight (or holding unlanded state) that a new candidate dispatch must be disjoint from.
- conservative verdict: the refusal taken when a run's owned-path set is missing, empty, or malformed; the run is treated as intersecting with the reason named.
- claim-live window: the interval from execution-claim take to the claim's retirement, during which the run is outstanding.
- monotone merge: a record update that only ever adds paths (a union with what the record already holds), so the record stays complete for everything the run has recorded so far.
- done boundary: a done-flow manifest write (the lib's `write-manifest` and `finalize-manifest` sub-commands) at which the run's owned lists merge into its admission record.
- first-blocker order: the consult's rule that the first refusing outstanding run in argv order decides the verdict reason.
- covering plan: the plan whose `Files:` lists the run executes and from which the admission record seeds.
- seed: the owned-path list derived from the covering plan's `Files:` lists by importing the consult's `owned_paths_from_plan`, its no-paths tool error read as an empty seed.
- candidate-side strictness: refusing a candidate whose `--candidate-manifest` derives an empty owned-path set, and refusing candidate or outstanding evidence whose parse would silently drop malformed items, instead of admitting on unprovable evidence.
- source-less residual: the outstanding runs that still present no record and keep the conservative verdict: runs whose claim predates this plan's landing, runs whose covering plan yields an empty seed, runs whose plan slug the deciding turn cannot resolve to a record, and authoring-lane runs (authoring claims never pass the gateway).

## Why

The dispatch admission consult treats an outstanding run with no done-setup manifest as intersecting, and the consult is global, so every live-but-manifest-less execution run freezes both lanes' dispatches. On the night of 2026-11-05 two full maintenance carriers produced zero picks against healthy mid-flight runs, and the freeze lasted until the peer landed. The candidate side has the mirror defect: a candidate manifest with empty or partially parseable owned-path fields is admitted vacuously on evidence that proves nothing.

## Gist & Examples

TLDR: keep a claim-keyed admission record readable for the whole claim-live window and refuse admission on empty or malformed evidence, so target-disjointness stays provable during active runs instead of freezing dispatch, for efficiency.

Before: an execution run takes its claim and works for hours; its done-setup manifest does not exist yet (or exists only in the run's own worktree, where the deciding turn does not look), so every dispatch admission consult over that run takes the conservative verdict and both lanes stand down. A candidate passing `--candidate-manifest` with all-empty owned-path fields exits 0 pass against a non-empty outstanding run, and non-string list items or non-list fields are dropped silently on both candidate and outstanding reads, so partially malformed evidence admits on a disjoint subset.

After: a new-owner claim creation writes an admission record seeded from the covering plan's `Files:` lists, each done boundary merges the run's owned lists into it, every claim retirement removes it, and the deciding turn passes a claim-live run's record to the consult by the plan slug it already holds, so the consult proves disjointness from a retrievable record. A covering plan with an empty seed warns and writes no record, leaving that run on the conservative verdict. A candidate manifest that derives an empty set refuses regardless of outstanding runs; malformed evidence refuses conservatively on both operands with the dropped evidence named. Between done boundaries, edits outside the run's `Files:` lists are not yet recorded, so the consult proves only what the record holds.

## Outcome

Make target-disjointness admission stay decidable for the whole life of an active run and honest about evidence quality.

- A live execution run claimed after landing presents a retrievable owned-path record to the consult, so a genuinely disjoint candidate dispatches instead of the whole lane freezing behind a missing-source verdict.
- The witnessed zero-pick window class from the missing-manifest cause cannot recur for runs claimed after landing whose covering plan yields a non-empty seed; the source-less residual keeps the conservative verdict.
- Admission on empty or malformed evidence is refused with the evidence named, on both the candidate and the outstanding operand.
- The conservative verdict's semantics and the outcome contract's existing classes are unchanged (its reach changes are priced in the Gate delta), exact intersection and the first-blocker order are unchanged, and a consult tool error (exit 3) resolves the lane to the existing D3 defer, never an unmodeled turn error.

Gate delta: adds the admission record (a run-scoped input artifact with seed, merge, and clear arms; an empty seed is a stderr warning, never a refusal) and grows the existing consult's conservative refusal surface by a candidate empty-set arm and malformed-evidence arms on both operands, inside the existing refusal and outcome classes; priced by (1) paying sibling: the existing missing-source conservative refusal's reach shrinks from every claim-live run to the source-less residual, its code and regression pin unchanged, the reach reduction recorded in the registry note; (2) the admission protocol's four fields for the new arms: incident = the 2026-11-04 candidate-side observations (the empty-set vacuous pass and the silent-subset second witness) and the 2026-11-05 zero-pick harvest windows, linked in the origins block; expected catch frequency = every consult over an operand presenting empty or malformed evidence; false-positive cost = a candidate legitimately presenting an empty set is refused naming the evidence and the lane takes the existing D3 defer; sunset/review = 2026-12-06 in the registry note. No new gate, validator, lock, ledger, outcome class, or consult-facing CLI surface (the merge arm takes the existing repo merge lock); the done-session classification surface is untouched; removed: none.

## Assumptions

- assume a retention record (seeded at new-owner claim creation, merged monotone at done boundaries, cleared at claim retirement) over deriving the set from claim plus plan plus worktree dirt at every consult; basis: the frozen PLAN-PROMPTS entry rejects a `Files:`-only derivation because an active worktree accumulates off-plan edits and rejects snapshots that can omit active changes, while a per-consult cross-checkout dirt scan is racy and expensive; the seed alone is that rejected derivation, the boundary merge is what makes the record a retention source, and the unrecorded between-boundary edits are the stated residual.
- assume the admission record lives beside the execution claim in the primary checkout keyed by plan slug, not inside the done-session `run-manifest-*.json` namespace; basis: that namespace's consumers (`classify_partial` newest-manifest classification, `_detect_interrupted_runs` advisories) assume records begin at done setup, so a claim-live record there would hard-refuse concurrent done setups; the gateway already resolves the primary claims directory, and the lib merge arm resolves the same primary through `_resolve_primary_checkout`, never the caller's cwd.
- assume the seeder, the record writer, and the merge arm live in `scripts/done_sweep_gates_lib.py`, the seeder importing `owned_paths_from_plan` from `scripts/dispatch_admission.py` (the lib's existing sibling-import pattern), with the gateway shelling to a lib entry point and the merge arm running inside the lib's existing `write-manifest` and `finalize-manifest` sub-commands, so `scripts/done_run.sh` is untouched; basis: the consult stays the one home of the `Files:` derivation, and the atomic temp-plus-replace writer prevents torn reads.
- assume every record mutation holds the existing repo merge lock and no new lock is added: seed, replace, and the release/sweep clears run inside the gateway's existing merge-lock hold; the merge arm reuses an inherited hold only after verifying the exported token and holder identity against the lock's meta record (the gateway's verification shape) and otherwise takes a try-once acquire through the lib's existing `_merge_lock_acquire` helper, re-checks under the lock that the execution claim exists and that its recorded `branch:` line names the boundary checkout's current branch (a claim without a branch line, or any mismatch, writes nothing and warns), and only then updates the existing record (never creates one) through atomic temp-plus-replace; the take-mode failure cleanup clears locklessly in its exit trap under its existing order guarantee (record removed before the claim, the owner check gating the removal); basis: the done flow calls the lib sub-commands outside the merge lock, so an unlocked read-union-replace could drop a successor's seed or resurrect a cleared record.
- assume a refused merge-lock acquire, a failed primary-checkout or slug resolution, or a failed record write at a done boundary warns on stderr naming the slug and never fails the done boundary; basis: the record keeps its monotone content, the next boundary retries, and the lag joins the stated between-boundary residual.
- assume an empty seed warns on stderr and writes no record instead of refusing the take; basis: the frozen PLAN-PROMPTS entry's machinery-admission line forbids a second blocker, and the existing missing-source verdict already covers that run conservatively.
- assume a fixed precedence: an unreadable, unparseable, or non-object input on either operand stays exit 3 `tool_error` first; then the candidate's malformed evidence (non-string items, non-list fields) refuses, then an empty candidate set refuses, both with exit 1 before the outstanding-run loop; then each outstanding run's malformed evidence is that run's conservative verdict at its loop position under the first-blocker order; basis: exit 3 on outstanding evidence would leave the deciding turn with no verdict, and the conservative refusal reuses the existing verdict vocabulary; the origin row's indeterminate option is not taken because the deciding turn needs a pass or fail verdict.
- assume the deciding turn chooses the operand by claim state: whenever the execution claim resolves at the slug it passes the admission record as `--outstanding-with-manifest <slug> <record path>` (the slug fills the RUN_ID slot as a display label, since no run id exists before done setup) and each done-session manifest whose `owned_plan_paths` name the covering plan, found in the done-session home of the run's worktree (resolved from the claim's `branch:` line through the worktree list) and of the primary checkout, as its own `--outstanding-with-manifest` operand under the same label, so refusal names whichever operand's paths intersect; when that worktree cannot be resolved the record goes alone and the unrecorded paths join the between-boundary residual; a claim-retired run with unlanded state keeps today's done-session manifest arm, and `--outstanding-without-manifest` stays for a claim-live run with no record or an unresolvable slug; basis: both sources hold, the record can lag a boundary whose merge was refused while the done-session manifest holds those paths, and the consult refuses on the union of the operands it is given.
- assume authoring-lane outstanding runs stay in the source-less residual; basis: authoring claims are session-written files that never pass the gateway, and extending seeding to them is a separate lifecycle.
- assume manifest-derived strings keep raw passthrough into verdict output lines; basis: the final `OUTCOME:` line is the contract surface, the trust model is same-user local records, and the repo's `_sanitize_manifest_error_value` precedent stays where corruption forging is a log-line risk; recorded as accepted residual, no code change.

Decision points requiring a grill: admission record in the primary claims home over a done-session-home record, per the orphan-misclassification collision in `classify_partial` and `_detect_interrupted_runs` (plan Assumptions); retention record over per-consult derivation snapshots, per the frozen entry's rejected alternatives (plan Assumptions); empty-seed warning over a claim-take refusal, per the frozen entry's no-second-blocker line (plan Assumptions); conservative refusals inside the existing outcome classes over a new indeterminate or tool-error class, per the deciding turn's verdict requirement (plan Assumptions); the existing repo merge lock for every record mutation over a new lock or lock-free writer disjointness, per the done flow's unlocked lib calls (plan Assumptions).

## Standing constraints

- The done-session classification machinery (`classify_partial`, `classify_run_boundary`, `_detect_interrupted_runs`) and the done wrapper script are frozen for this plan: no task edits them, and the admission record must never appear on their glob surfaces.
- Every gateway pin runs in a scratch `git init` repository under a mktemp parent with `EXECUTION_CLAIM_LOCK_HOME` pinned (the `test_execution_claim.py` setUp pattern); every lib pin runs under a temporary directory with `DONE_SWEEP_RUNTIME_HOME` and `DONE_SWEEP_USER_FACTS` pinned, and the locked-merge pin additionally pins the done-lock script and merge-lock root into the temporary directory with no ambient `MERGE_LOCK_DIR` or `MERGE_LOCK_TOKEN` exports, forcing refusals through controlled holder inputs rather than wall-clock aging; the done-isolation pin ports the `test_done_run_wrapper.py` scratch-repo pattern; no pin touches the real checkout.

## Evaluation Criteria

Quality dimensions:
- correctness: a consult over a claim-live outstanding run reads a non-empty admission record and admits a genuinely disjoint candidate (exit 0 `OUTCOME: pass`) and refuses an intersecting one naming the paths; a source-less run still refuses conservatively.
- evidence honesty: a candidate manifest with an empty derived set refuses regardless of outstanding runs; malformed evidence refuses conservatively on both operands naming the dropped evidence; unreadable and unparseable inputs stay `tool_error`.
- isolation safety: a foreign claim-live admission record never triggers a done-setup refusal or an interrupted-run advisory; the merge lands in the primary checkout's record from a linked worktree; every lifecycle pin runs hermetically.
- regression safety: existing pins regreen unchanged; every new refusal family member and every lifecycle path carries its own pin; the seeder imports the consult's plan derivation rather than copying it.
- simplicity: no new gate, validator, lock, ledger, outcome class, or consult-facing CLI surface; the diff adds one record artifact with one owned lifecycle and reuses the existing consult input contract.

Done when:
- `scripts/test_done_sweep_gates_lib.py` passes with the new pins for the empty-seed signal, record shape round-trip through the consult reader, monotone merge, merge-never-creates, the locked merge with its claim re-check, and primary-checkout resolution from a linked worktree.
- `scripts/test_execution_claim.py` passes with the new hermetic pins for new-owner seeding (fresh create, takeover, conversion), refresh recreate, the empty-seed warning, clearing on each claim retirement, and done-machinery isolation, and every existing pin regreens unchanged.
- `scripts/test_dispatch_admission.py` passes including the end-to-end gateway-take retrieval pin, the lagging-record two-operand witness, and the new refusal pins (empty candidate set with zero and with one outstanding run; candidate and outstanding malformed evidence, including a malformed run ahead of an intersecting one; a malformed candidate beside an unreadable outstanding input), with the source-less conservative verdict unchanged.
- `agents/skills/maintenance/decisions.md`, `agents/skills/maintenance/SKILL.md`, and `agents/skills/maintenance/scheduling.md` name the record operand and its precedence, keep the conservative wording for the source-less residual, and state the exit-3 defer treatment.
- The machinery registry's admission row note reflects the lifecycle move, the missing-source reach reduction, and the new arms' admission fields (incident links, catch frequency, false-positive cost, review date 2026-12-06).

Ship when:
- A maintenance carrier window runs a dispatch admission consult that admits a disjoint candidate against a live claim-bearing outstanding run (operational confirmation; observed from scheduler-state decision_reason lines, not a repository check).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (Task 1)
- `scripts/execution_claim.sh` (Task 2)
- `scripts/dispatch_admission.py` (Task 3)
- `agents/skills/maintenance/decisions.md` (Task 4)
- `agents/skills/maintenance/SKILL.md` (Task 4)
- `agents/skills/maintenance/scheduling.md` (Task 4)
- `scripts/machinery_registry.json` (Task 4)
- `scripts/check_maintenance_pins.sh` (Task 4)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (Task 1) *(new pins)*
- `scripts/test_execution_claim.py` (Task 2) *(new pins)*
- `scripts/test_dispatch_admission.py` (Task 2) *(new end-to-end pin; existing pins review-only)*
- `scripts/test_dispatch_admission.py` (Task 3) *(new pins)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh`; reason: the done-session classification surface is frozen for this plan (Standing constraints); the boundary merge lives in the lib sub-commands the done flow already calls.
- `scripts/quota_window_probe.py`; reason: the quota leg is a separate consult surface this plan does not touch.
- `scripts/check_prompt_log_origins.py`; reason: the prune audit reads plan-file witnesses, not admission inputs.
- Authoring-claim lifecycle surfaces; reason: authoring-lane runs stay in the source-less residual (plan Assumptions).
- Any redesign of the landing-completion resolution in `agents/skills/maintenance/decisions.md` beyond the consult-source wording; reason: the completion work is a downstream consumer of the consult, not part of its input contract.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execution_claim.py scripts/test_done_sweep_gates_lib.py scripts/test_dispatch_admission.py -q
bash scripts/check_maintenance_pins.sh
```

### Task 1: Admission-record home in the done-sweep lib

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `write_run_manifest` in `scripts/done_sweep_gates_lib.py`, the atomic write shape the record writer reuses
- `owned_paths_from_plan` in `scripts/dispatch_admission.py`, the derivation the seeder imports
- `_merge_lock_acquire` in `scripts/worktree_closeout_migrate.py`, the existing merge-lock helper the merge arm reuses

- [x] Seeder delegation: given a plan fixture with `Files:` lists and one without, expects the lib seeder to return the list `owned_paths_from_plan` yields for the first by importing it, and an empty seed for the second where that function raises its no-paths tool error, plus a delegation seam assertion patching the imported symbol at the seeder's binding site to return a sentinel list and observing the seeder track the patch, so a copied implementation fails the pin [class: IMPLEMENTATION_REQUIRED]
- [x] Record shape: expects the writer to emit a JSON object with exactly `owned_paths`, `owned_plan_paths`, and `owned_review_paths` through atomic temp-plus-replace, and `owned_paths_from_manifest` to read a written record back to the same non-empty set [class: IMPLEMENTATION_REQUIRED]
- [x] Monotone merge: given an existing record and a done boundary's owned lists, expects the record to become their union (never shrink); given no record, expects the merge to write nothing [class: IMPLEMENTATION_REQUIRED]
- [x] Locked merge: given a done boundary, expects the merge arm to hold the repo merge lock (a verified inherited hold or a try-once acquire), re-check under it that the execution claim exists and its recorded branch names the boundary checkout's branch, and write nothing otherwise; a refused acquire, unverifiable inherited hold, failed resolution, or failed write warns on stderr naming the slug and the boundary still succeeds [class: IMPLEMENTATION_REQUIRED]
- [x] Primary resolution: given a done boundary run from a linked worktree, expects the merge arm to resolve the record under the primary checkout's execution-claims directory (the gateway's fixed relative path) through `_resolve_primary_checkout` and the slug through the same artifact-slug derivation the gateway uses, updating the primary checkout's record and writing nothing under the worktree [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: hermetic lib pins for the empty-seed signal, record shape round-trip, monotone merge, merge-never-creates, the locked merge (verified hold, ownership re-check, warn-not-fail disposition, claim-gone and claim-foreign no-write arms), and primary resolution from a linked worktree, each failing against current code by design [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: add the admission-record seeder, writer, and merge arm` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Admission-record lifecycle in the claim gateway

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/execution_claim.sh`
- `scripts/test_execution_claim.py`
- `scripts/test_dispatch_admission.py`

Primary class anchors:
- `acquire_claim` in `scripts/execution_claim.sh`, the create-or-refuse state machine every new-owner path passes
- `cleanup_fresh_claim` in `scripts/execution_claim.sh`, the take-failure cleanup the clearing arm extends

- [x] New-owner seeding: given a fresh create, a stale-foreign-claim takeover, or a dead-run conversion, expects the record present at the claims home with the fresh seed once the invocation succeeds, any prior record for the slug replaced; one pin per path, asserting record state before and after [class: IMPLEMENTATION_REQUIRED]
- [x] Refresh recreate: given the same run recreating its unlinked claim, expects an existing record kept unchanged and a seed written only when no record exists [class: IMPLEMENTATION_REQUIRED]
- [x] Empty-seed warning: given a covering plan with an empty seed, expects the take to succeed with a stderr warning naming the plan and no record written; the existing pins, whose shared setUp plan has no `Files:` list, regreen unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Clearing: given each claim retirement (release, sweep, take-mode failure cleanup), expects the record absent after the invocation and intact while the claim stands, removed before the claim and only while the claim still names the retiring session; one pin per path [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (done machinery untouched): given a foreign claim-live admission record, expects a peer done-session setup in the same scratch repo to proceed with no orphan verdict and no interrupted-run advisory naming the live run [class: REPOSITORY_TEST]
- [x] Safety witness (lagging record): given a seed-only record and a done-session manifest holding extra paths, passed as two `--outstanding-with-manifest` operands under the same label, expects a candidate intersecting only the manifest's extra paths refused naming them [class: REPOSITORY_TEST]
- [x] End-to-end retrieval: given a hermetic gateway take over a fixture plan with a `Files:` list, expects a consult passing the record via `--outstanding-with-manifest` to admit a disjoint candidate and refuse an intersecting one naming the paths [class: REPOSITORY_TEST]
- [x] Run → expect RED: pins for the three new-owner paths, refresh recreate, the empty-seed warning, the three clearing paths, and end-to-end retrieval, each failing against current code by design; the two safety witnesses are green today and stay out of this list [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: keep a claim-keyed admission record live across the claim window` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Evidence-strict admission reads

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/dispatch_admission.py`
- `scripts/test_dispatch_admission.py`

Primary class anchors:
- `owned_paths_from_manifest` in `scripts/dispatch_admission.py`
- `check_admission` in `scripts/dispatch_admission.py`

- [x] Empty-set refusal: given a `--candidate-manifest` whose owned-path fields all derive empty lists, expects exit 1 `OUTCOME: fail` naming the candidate's empty-set reason before any outstanding-run loop runs; with one `--outstanding-without-manifest` run present, the missing-source reason is absent [class: IMPLEMENTATION_REQUIRED]
- [x] Partial-parse refusal, candidate side: given a candidate manifest carrying a non-string list item or a non-list owned-path field beside valid entries, expects exit 1 `OUTCOME: fail` naming the dropped evidence, replacing the silent-subset pass [class: IMPLEMENTATION_REQUIRED]
- [x] Partial-parse refusal, outstanding side: given an outstanding manifest or admission record carrying a non-string list item or a non-list owned-path field, expects that run's conservative verdict (exit 1) naming the dropped evidence at its loop position, never a verdict on the dropped subset and never exit 3; a malformed run ahead of an intersecting one decides with no intersecting-paths line [class: IMPLEMENTATION_REQUIRED]
- [x] Tool-error boundary unchanged: given an unreadable, unparseable, or non-object input on either operand, expects exit 3 `OUTCOME: tool_error` as today, checked before the malformed-evidence and empty-set arms; a malformed or empty candidate beside an unreadable outstanding input decides as the tool error [class: REPOSITORY_TEST]
- [x] Safety witness (plan-arm fail-closed preserved): given a `--plan` derivation that finds no owned paths, expects the existing fail-closed tool error unchanged [class: REPOSITORY_TEST]
- [x] Safety witness (consult semantics unchanged): given an outstanding run passed as `--outstanding-without-manifest`, expects the conservative verdict with the reason named, byte-identical to today's missing-source arm [class: REPOSITORY_TEST]
- [x] Run → expect RED: one pin per refusal family member (empty candidate set with zero and with one outstanding run; non-string item, candidate; non-list field, candidate; non-string item, outstanding; non-list field, outstanding; malformed outstanding run ahead of an intersecting one), each failing against current code by design [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: refuse admission on empty and malformed evidence on both operands` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Consult wording, registry note, and pin rows

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/scheduling.md`
- `scripts/machinery_registry.json`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `check_admission` in `scripts/dispatch_admission.py`

- [x] Consult wording, decisions.md: given the D1 landing gate and D2 mirror paragraphs, expects both rewritten in place to the operand choice by claim state (claim resolves: record plus each covering-plan done-session manifest from the run's worktree and the primary, same label; proven retirement: the manifest alone; source-less residual: `--outstanding-without-manifest`, conservative wording kept) [class: IMPLEMENTATION_REQUIRED]
- [x] Consult wording, SKILL.md and scheduling.md: given the SKILL.md fleet-cap bullet's consult operand enumeration (the pending_landing and surviving-note clause included) and the scheduling.md conservative-verdict clause, expects the superseded clauses rewritten in place to the same operand choice, net growth bounded to the record-operand sentence [class: IMPLEMENTATION_REQUIRED]
- [x] Consult tool-error treatment: given the consult wording across the three skill files, expects the exit-3 defer treatment stated (a consult tool error resolves the lane to the existing D3 defer) [class: IMPLEMENTATION_REQUIRED]
- [x] Registry note: given the machinery registry's existing admission entry, expects its note updated in the same change to describe the lifecycle move, the missing-source reach reduction, and the new arms' admission fields (incident links, catch frequency, false-positive cost, review date 2026-12-06), adding or removing no row [class: IMPLEMENTATION_REQUIRED]
- [x] Pins suite: given the pinned maintenance files touched by this task, expects `bash scripts/check_maintenance_pins.sh` to exit 0, with companion pin rows edited in `scripts/check_maintenance_pins.sh` in the same change when the suite demands them [class: REPOSITORY_TEST]
- [x] Commit: `docs: name the claim-live admission record in the consult wording` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

Series terminal state at the configured round cap: the loop exits through the cap-closure terminal shape with operator authorization recorded in this authoring session on 2026-11-07. Every r5 staged finding's outcome is listed below; the r5 record pair in the reviews staging home stays authoritative for verdicts, counts, and triage. These corrections were not panel-verified, a verification round exceeding the configured cap; the RED pins of Tasks 1 and 2 and the Task 4 wording rows bound the residual risk at execution, and the round's non-blocking residuals live in the backlog row docs/history/backlog/2026-11-07-dispatch-admission-plan-certification-residuals.md.

- F1 implementation#unresolved-operand-enumeration (Medium, was blocking): disposition: folded - the deciding turn finds done-session manifests by `owned_plan_paths` naming the covering plan in the run's worktree (resolved from the claim's branch through the worktree list) and the primary checkout's done-session homes, the record going alone when the worktree cannot be resolved; the Gist's lifecycle remark now says the manifest may exist only in the run's own worktree.
- F2 implementation#missing-identity-input (Medium, was blocking): disposition: folded - the merge arm's ownership re-check compares the claim's recorded branch with the boundary checkout's current branch, and a claim without a branch line or any mismatch writes nothing and warns.
