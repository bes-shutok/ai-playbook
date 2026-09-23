# Plan: Closure strays disposition routing

Backlog origin: none
Driving force: code-quality (primary), token-usage (secondary)

## Terms

- **Closure stray**: a backlog item whose implementation already landed on main while the item itself was never routed to the completed archive; while a stray exists, the open top-level backlog misrepresents repo reality and every survey re-reads a dead item.
- **Disposition line**: the item-level record, appended before the freeze move, naming the implementing plan and the landed commit that satisfies the item's requested change.
- **Freeze transition**: the lifecycle action that closes a document: archive move into a completed-history directory plus one ownership-registry row; the body is immutable after it (doc-ownership lifecycle, docs/plans/completed/2026-09-08-doc-ownership-lifecycle.md).
- **Ownership registry**: docs/maintenance/document-registry.md, the central Layer 2 file mapping document identity to state and archive location, validated by scripts/doc_registry_validator.py.
- **Identity collision**: two completed-history documents deriving the same registry identity from their filenames; resolved per the registry header scheme: a short MMDD date suffix is appended, and when the dates also collide (same base in two completed-history directories) a directory tag (plan/backlog) is appended too.

## Assumptions

- assume all six items' implementations carry landed evidence on main as of the 2026-09-24 authoring; basis: authoring-time verification against main a3424f3e (commits 7f708429, df664ad5, b73ac76f, 206a7f7b, 341961d1; DonePendingRecoveryTest 18/18 green; landed-text probes in agents/skills/maintenance/zcode.md, agents/skills/maintenance/SKILL.md, agents/skills/maintenance/prompt-templates.md, scripts/docs_branch_backlog_dedupe.py, scripts/check_maintenance_pins.sh).
- assume items 3, 5, and 6 route done even though their origin texts cite the authoring landing 430db0bd: the implementations landed via the execution commits b73ac76f (carve-out plan execution, drill 3/3) and 341961d1 (loop-quality-hygiene Tasks 7 and 8), and every requested clause has landed evidence; the Disposition lines name the execution commits; basis: git log -S probes on main plus the completed plans' task lists.
- assume the two identity collisions resolve per the registry header scheme: the loop-guard origin row takes `loop-guard-one-recorded-mutation-carve-out-0921-backlog` (same base and same 0921 date as the existing plan row, so the MMDD suffix and the directory tag both apply) and the sequential-landing origin row takes `sequential-landing-discipline-no-dispatch-before-squash-0921` (dates differ, backlog 0921 vs plan row 0922, so the MMDD suffix alone applies); basis: the docs/maintenance/document-registry.md header identity scheme; the validator hard-fails duplicate identities.
- assume the `archived` cell comes from each origin file's own date prefix (registry backfill rule), not the routing date; basis: registry header "Rows are backfilled: archived date from the filename date prefix" and the dirt-gate twin row (archived 2026-09-22 for a 2026-09-22 file).
- assume the registry audit notes cite this plan by its top-level path docs/plans/2026-09-24-closure-strays-disposition-routing.md; basis: the dirt-gate twin row's citation of the P54 plan by its then-top-level path (registry rows for dirt-gate-staged-deletion-edge and sequential-landing-discipline-no-dispatch-before-squash).
- assume item 4's routing inserts a clean `Status:` header line after the title even though the item's only Status mention sits inside its Driving-force paragraph; the prose mention stays untouched as historical text; basis: the other five items' header shape and the dedupe tool's `^Status:` line contract (scripts/docs_branch_backlog_dedupe.py STATUS_LINE_RE).
- assume item 1's plain registry identity `execute-plan-recover-stuck-done-pending-claims` latently collides with the on-disk but unregistered P53a completed-plan file docs/plans/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md: when the lifecycle migration backlog later registers that plan row, the registry header scheme's collision forms apply and the plan row takes the `execute-plan-recover-stuck-done-pending-claims-0924-plan` form; basis: the registry header identity scheme and the collided context-budget rows (`-0919-plan` / `-0918-backlog`) precedent; today the validator reports the plan file only as a warn-only unregistered completed-history file, so this plan's row is unique and hard-finding-free.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: route six already-executed backlog items into docs/history/backlog/completed/ with recorded Disposition lines and ownership-registry rows, because their implementations landed on main while the items were never archived, so the open backlog keeps misrepresenting repo reality.

**Before (today).** Six backlog items sit open at the top level of docs/history/backlog/ although everything they request is already on main. Concretely: docs/history/backlog/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md still reads `Status: open` and its 2026-09-22 Disposition annotation still says "certified, pending execution", while the status-match fix has been live in scripts/docs_branch_backlog_dedupe.py since commit 341961d1. A scheduler survey or a dedupe wave re-reads all six every time, and the registry has no rows recording where the work actually landed.

**After (this plan).** Each of the six is verified against main, gains a `Status: done (...)` line and a `Disposition:` line naming the implementing plan and the landed commit, is moved by `git mv` into docs/history/backlog/completed/, and gets exactly one ownership-registry row. The dedupe item's stale annotation is superseded by a final Disposition line citing Task 8 and commit 341961d1. The validator stays at zero hard findings and the top-level backlog shrinks by six.

**Hard evidence gate (residual split).** Disposition-only routing is licensed only by landed evidence. Before routing each item, the task re-verifies that item's evidence anchors on main. If any requested clause lacks landed evidence, that clause is NOT routed: split it into a fresh residual backlog item under docs/history/backlog/ recording the missing clause, and route only the covered part. Authoring verified all six covered (see Assumptions), so the expected outcome is 6/6 routed whole; the gate exists so an executor on moved main never routes on stale faith.

**Out of scope.** No implementation work of any kind. Registering the P53a and P54 plan rows (docs/plans/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md, docs/plans/completed/2026-09-24-p54-scheduler-loop-continuity-directives.md) stays with the lifecycle migration backlog: the validator reports them as warn-only unregistered completed-history files today, and this plan's scope is the six backlog items. The docs-branch sync and dedupe waves are downstream consumers and are not run here.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every Disposition line names the implementing plan path and a landed commit proven at routing time by `git merge-base --is-ancestor <sha> main`; any clause lacking evidence triggers the residual split instead of routing.
- completeness: 6/6 items archived with done Status and Disposition lines; 6/6 registry rows, one per pinned identity; the validator reports 0 hard findings.
- immutability: no completed-history body edits; the completed dirs gain only the six adds; the check-writes gate is green on every routing task.
- hygiene: the no-em-dash scan and the public-hygiene scan exit 0 over the changed set.

**Done when:**
- the whole Validation Commands block exits 0: validator validate (0 hard), the six per-item archive probes, the six identity count probes, DonePendingRecoveryTest green (18 tests), check-writes green, and the em-dash file scan over the changed docs.

**Ship when:**
- none; the docs-branch sync propagates the moves on its own cadence (external, prose only, no task).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Documentation (the six origin files, edited in place, then moved):**
- `docs/history/backlog/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md`
- `docs/history/backlog/2026-09-23-dirt-gate-origin-disposition-unrecorded.md`
- `docs/history/backlog/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md`
- `docs/history/backlog/2026-09-21-sequential-landing-discipline-no-dispatch-before-squash.md`
- `docs/history/backlog/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md`
- `docs/history/backlog/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md`
- `docs/maintenance/document-registry.md` (six row appends only)

**Tests:** none; this plan edits documentation state only. Item 1's implementing test (DonePendingRecoveryTest) is run as evidence and never modified.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it corrects a Disposition line's factual claim, fixes a registry row's cells, or records the residual split item the hard evidence gate produces. A residual split item lands under docs/history/backlog/ and joins the explicit must-fix set when created. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/**`; reason: completed-history bodies are immutable and no task edits them.
- `scripts/docs_branch_backlog_dedupe.py`; reason: the tool is item 5's landed subject; this plan records its disposition and never edits it.
- `agents/skills/maintenance/**` and `agents/skills/execute-plan/**`; reason: the landed loop disciplines are evidence only; no task edits them.
- `docs/history/backlog/2026-09-24-execute-plan-recovery-interruptions.md`; reason: a different item from the codex reconciliation lane; not one of the six.

## Validation Commands

```bash
# V1: registry integrity; expects exit 0 with 0 hard findings (45 warn-only findings at authoring are tolerated)
python3 scripts/doc_registry_validator.py validate || { echo "V1 registry validate FAILED"; exit 1; }

# V2: per-item archive state; archived present, top-level gone, done Status, Disposition line
for f in \
  2026-09-24-execute-plan-recover-stuck-done-pending-claims \
  2026-09-23-dirt-gate-origin-disposition-unrecorded \
  2026-09-21-loop-guard-one-recorded-mutation-carve-out \
  2026-09-21-sequential-landing-discipline-no-dispatch-before-squash \
  2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover \
  2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers
do
  test -f "docs/history/backlog/completed/$f.md" || { echo "V2 missing archived: $f"; exit 1; }
  test ! -e "docs/history/backlog/$f.md" || { echo "V2 still top-level: $f"; exit 1; }
  grep -q "^Status: done" "docs/history/backlog/completed/$f.md" || { echo "V2 no done Status: $f"; exit 1; }
  grep -q "^Disposition:" "docs/history/backlog/completed/$f.md" || { echo "V2 no Disposition: $f"; exit 1; }
done

# V3: registry rows exactly once per pinned identity (fixed-string cell match)
for ident in \
  execute-plan-recover-stuck-done-pending-claims \
  dirt-gate-origin-disposition-unrecorded \
  loop-guard-one-recorded-mutation-carve-out-0921-backlog \
  sequential-landing-discipline-no-dispatch-before-squash-0921 \
  dedupe-cannot-distinguish-reopen-from-stale-leftover \
  maintenance-primitive-emission-suppression-and-resume-carriers
do
  n=$(grep -cF "| $ident |" docs/maintenance/document-registry.md)
  test "$n" -eq 1 || { echo "V3 rows for $ident: $n (want 1)"; exit 1; }
done

# V4: item 1's implementing test still green at routing time; expects tail line OK over 18 tests
PYTHONPATH=scripts python3 -m unittest test_execute_plan_runtime.DonePendingRecoveryTest 2>&1 | tail -1 | grep -qx "OK" || { echo "V4 DonePendingRecoveryTest not green"; exit 1; }

# V5: completed-path write gate over the working tree; renames licensed by the registered src rows
git -c core.quotePath=false status --porcelain | python3 scripts/doc_registry_validator.py check-writes --stdin || { echo "V5 check-writes FAILED"; exit 1; }

# V6: em-dash gate over the changed doc set
bash scripts/check-no-em-dash.sh file \
  docs/plans/2026-09-24-closure-strays-disposition-routing.md \
  docs/maintenance/document-registry.md \
  docs/history/backlog/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md \
  docs/history/backlog/completed/2026-09-23-dirt-gate-origin-disposition-unrecorded.md \
  docs/history/backlog/completed/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md \
  docs/history/backlog/completed/2026-09-21-sequential-landing-discipline-no-dispatch-before-squash.md \
  docs/history/backlog/completed/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md \
  docs/history/backlog/completed/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md \
  || { echo "V6 em-dash FAILED"; exit 1; }
```

Authoring-time execution note: V1, V4, and the V6 scan of the plan file itself were executed at authoring (V1 exit 0, 0 hard, 45 warns; V4 OK over 18 tests; V6 plan bytes clean). V2, V3, and V5 pass vacuously or trivially until the routing tasks create their targets; each routing task runs its own subset (V5 after the move, V3 fragment after the row append).

### Task 1: Routing baseline and hard evidence gate

Files:
- `docs/history/backlog/` (residual split item only when the gate fires)

- [x] Record the routing baseline: `git rev-parse HEAD`; keep the sha in the session log [class: REPOSITORY_TEST]
- [x] Re-verify the five landed commits on main: `git merge-base --is-ancestor 7f708429 main && git merge-base --is-ancestor df664ad5 main && git merge-base --is-ancestor b73ac76f main && git merge-base --is-ancestor 206a7f7b main && git merge-base --is-ancestor 341961d1 main && echo ALL_LANDED`; expects `ALL_LANDED` [class: REPOSITORY_TEST]
- [x] Re-run the plan's Validation Commands V4; expects `OK` over 18 tests [class: REPOSITORY_TEST]
- [x] HARD RULE sweep: for each of the six items, confirm every requested clause is covered by the per-task evidence probes of Tasks 2-7; if any clause lacks landed evidence, split that clause into a fresh residual backlog item under `docs/history/backlog/` naming the missing evidence, and route only the covered part in the item's task [class: REPOSITORY_TEST]
- [x] Commit (only when a split item was created): `docs: residual split from closure-strays evidence gate` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Route item 1, execute-plan-recover-stuck-done-pending-claims

Files:
- `docs/history/backlog/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md`
- `docs/maintenance/document-registry.md`

- [x] Evidence probe: `git merge-base --is-ancestor 7f708429 main && echo LANDED`; expects `LANDED`; the subject names the P53a execution squash [class: REPOSITORY_TEST]
- [x] HARD RULE: the item's requested driver transition exists (DonePendingRecoveryTest green in Task 1 covers the three dispositions, exact claim identity, terminal evidence, duplicate receipts, working-tree preservation, readiness transitions); route whole [class: REPOSITORY_TEST]
- [x] Replace the `Status: open` line with `Status: done (executed via docs/plans/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md)` [class: IMPLEMENTATION_REQUIRED]
- [x] Append after the `Workflow: backlog` line exactly: `Disposition: 2026-09-24 (routed via docs/plans/2026-09-24-closure-strays-disposition-routing.md, Task 2): the driver recovery transition landed on main at 7f708429 (the P53a execution squash of 2026-09-24-exec-p53a-recover-done-pending-claims; plan archived at docs/plans/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md); DonePendingRecoveryTest covers the requeue, defer, and abort dispositions, exact claim identity, terminal evidence, duplicate receipts, working-tree preservation, and the readiness transitions, 18/18 green.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append to docs/maintenance/document-registry.md exactly: `| execute-plan-recover-stuck-done-pending-claims | no | completed | 2026-09-24 | executed | docs/history/backlog/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md |  |  | user-approved 2026-09-24: standing pre-authorization carried by the scheduling ask's unattended dispatch chain; routed done by docs/plans/2026-09-24-closure-strays-disposition-routing.md Task 2; implementation verified on main at 7f708429 (DonePendingRecoveryTest 18/18); the origin move licenses this row |` [class: IMPLEMENTATION_REQUIRED]
- [x] `git mv docs/history/backlog/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md docs/history/backlog/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run V5; expects exit 0 (the rename is licensed by the row appended above) [class: REPOSITORY_TEST]
- [x] Commit: `docs: route execute-plan-recover-stuck-done-pending-claims closure stray to completed` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Route item 2, dirt-gate-origin-disposition-unrecorded

Files:
- `docs/history/backlog/2026-09-23-dirt-gate-origin-disposition-unrecorded.md`
- `docs/maintenance/document-registry.md`

- [x] Evidence probe: `git merge-base --is-ancestor df664ad5 main && test -f docs/history/backlog/completed/2026-09-22-dirt-gate-staged-deletion-edge.md && grep -qF "dirt-gate-staged-deletion-edge" docs/maintenance/document-registry.md && echo TWIN_ROUTED`; expects `TWIN_ROUTED` (the P54 Task 8 routing of the twin is this item's implemented substance) [class: REPOSITORY_TEST]
- [x] HARD RULE: the item's suggested fix (move the twin with done Status plus registry row) is exactly what P54 Task 8 executed; route whole [class: REPOSITORY_TEST]
- [x] Replace the `Status: open` line with `Status: done (resolved via docs/plans/completed/2026-09-24-p54-scheduler-loop-continuity-directives.md, Task 8)` [class: IMPLEMENTATION_REQUIRED]
- [x] Append after the `Workflow: backlog` line exactly: `Disposition: 2026-09-24 (routed via docs/plans/2026-09-24-closure-strays-disposition-routing.md, Task 3): the requested routing was executed by P54 Task 8 on main at df664ad5: the twin 2026-09-22-dirt-gate-staged-deletion-edge moved to docs/history/backlog/completed/ with Status done (executed via the friction-audit plan's Task 4) and registry row dirt-gate-staged-deletion-edge; this item records that completion and routes itself closed.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append to docs/maintenance/document-registry.md exactly: `| dirt-gate-origin-disposition-unrecorded | no | completed | 2026-09-23 | executed | docs/history/backlog/completed/2026-09-23-dirt-gate-origin-disposition-unrecorded.md |  |  | user-approved 2026-09-24: standing pre-authorization carried by the scheduling ask's unattended dispatch chain; routed done by docs/plans/2026-09-24-closure-strays-disposition-routing.md Task 3; the twin's routing (P54 Task 8, main df664ad5) is the implemented substance; the origin move licenses this row |` [class: IMPLEMENTATION_REQUIRED]
- [x] `git mv docs/history/backlog/2026-09-23-dirt-gate-origin-disposition-unrecorded.md docs/history/backlog/completed/2026-09-23-dirt-gate-origin-disposition-unrecorded.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run V5; expects exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: route dirt-gate-origin-disposition-unrecorded closure stray to completed` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Route item 3, loop-guard-one-recorded-mutation-carve-out

Files:
- `docs/history/backlog/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md`
- `docs/maintenance/document-registry.md`

- [x] Evidence probes: `git merge-base --is-ancestor b73ac76f main && echo LANDED`; `grep -qF "One-recorded-mutation carve-out" agents/skills/maintenance/zcode.md`; `grep -qF "Operator override" agents/skills/maintenance/zcode.md`; `grep -qF "one-recorded-mutation carve-out pins" scripts/check_maintenance_pins.sh`; `grep -qF "pending_rearm" agents/skills/maintenance/zcode.md`; all expect success (carve-out, operator override, pins, and the dark-case mechanical carrier are landed text) [class: REPOSITORY_TEST]
- [x] HARD RULE: the item's four acceptance bullets are all covered (overlay carve-out and override; blueprint clauses via the pins suite and the rearm duty's pending_rearm payload-copy write; dark-case carrier; the execution commit subject records drill 3/3); route whole [class: REPOSITORY_TEST]
- [x] Replace the `Status: open` line with `Status: done (executed via docs/plans/completed/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md)` [class: IMPLEMENTATION_REQUIRED]
- [x] Append after the `Workflow: backlog` line exactly: `Disposition: 2026-09-24 (routed via docs/plans/2026-09-24-closure-strays-disposition-routing.md, Task 4): the carve-out plan executed on main at b73ac76f (drill 3/3; family authored at 430db0bd, review r6): the zcode.md dispatch-discipline section carries the one-recorded-mutation carve-out and the operator-override escape, the re-arm duty writes pending_rearm plus the parked payload copy as the dark-case mechanical carrier, and scripts/check_maintenance_pins.sh registers the carve-out pins; all four acceptance bullets landed.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append to docs/maintenance/document-registry.md exactly: `| loop-guard-one-recorded-mutation-carve-out-0921-backlog | no | completed | 2026-09-21 | executed | docs/history/backlog/completed/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md |  |  | user-approved 2026-09-24: standing pre-authorization carried by the scheduling ask's unattended dispatch chain; routed done by docs/plans/2026-09-24-closure-strays-disposition-routing.md Task 4; identity collided with the same-base plan row (same 0921 date) so the directory-tag form applies; implementation verified on main at b73ac76f; the origin move licenses this row |` [class: IMPLEMENTATION_REQUIRED]
- [x] `git mv docs/history/backlog/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md docs/history/backlog/completed/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run V5; expects exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: route loop-guard carve-out closure stray to completed` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Route item 4, sequential-landing-discipline-no-dispatch-before-squash

Files:
- `docs/history/backlog/2026-09-21-sequential-landing-discipline-no-dispatch-before-squash.md`
- `docs/maintenance/document-registry.md`

- [x] Evidence probes: `git merge-base --is-ancestor 206a7f7b main && echo LANDED`; then all five clause probes expect success: `grep -qF "landing is not verified on main" agents/skills/maintenance/prompt-templates.md` (successor landing gate); `grep -qF "landing-gate resolution" agents/skills/maintenance/SKILL.md` (D1 pre-dispatch check); `grep -qF "the authoring lane dispatches only when zero outstanding unlanded runs" agents/skills/maintenance/SKILL.md` (authoring mirror); `grep -qF "caps the post-review, pre-landed state at one recorded run" agents/skills/maintenance/SKILL.md` (fleet rule); `grep -qF "teardown gated on the verified landing" agents/skills/maintenance/SKILL.md` (teardown gating) [class: REPOSITORY_TEST]
- [x] HARD RULE: all five requested clauses verified landed; route whole [class: REPOSITORY_TEST]
- [x] Pre-freeze em-dash repair (this file is still a living document before the move; after the move the repair would be a hard-gated completed-body edit): on the Driving-force line replace the em dash between "moves on" and "stranding work" with a colon plus a space, and on the D1 clause line replace the em dash between "work first" and "retry the squash" with a colon plus a space; expects both repaired so the whole-file V6 scan of this file goes green at Task 8 [class: IMPLEMENTATION_REQUIRED]
- [x] Insert after the title line exactly: `Status: done (executed via docs/plans/completed/2026-09-22-sequential-landing-discipline-no-dispatch-before-squash.md)` (the item has no Status header today; its mid-paragraph "Status: open." prose mention stays untouched as historical text) [class: IMPLEMENTATION_REQUIRED]
- [x] Insert on the next line exactly: `Disposition: 2026-09-24 (routed via docs/plans/2026-09-24-closure-strays-disposition-routing.md, Task 5): the namesake plan executed on main at 206a7f7b and all five requested clauses are landed: the successor-dispatch landing gate chain-nothing conjuncts (prompt-templates.md), the D1 pre-dispatch landing gate on both lanes with the landing read-back and landing-completion resolution (SKILL.md), the authoring mirror (authoring-lane D1 conjunct plus the self-landing landing-intent record duty), the fleet rule capping the post-review pre-landed state at one recorded run with zero outstanding unlanded runs per dispatch (SKILL.md invariants), and teardown gated on the verified landing.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append to docs/maintenance/document-registry.md exactly: `| sequential-landing-discipline-no-dispatch-before-squash-0921 | no | completed | 2026-09-21 | executed | docs/history/backlog/completed/2026-09-21-sequential-landing-discipline-no-dispatch-before-squash.md |  |  | user-approved 2026-09-24: standing pre-authorization carried by the scheduling ask's unattended dispatch chain; routed done by docs/plans/2026-09-24-closure-strays-disposition-routing.md Task 5; identity collided with the same-base plan row (differing dates 0921 vs 0922) so the MMDD-suffix form applies; implementation verified on main at 206a7f7b; the origin move licenses this row |` [class: IMPLEMENTATION_REQUIRED]
- [x] `git mv docs/history/backlog/2026-09-21-sequential-landing-discipline-no-dispatch-before-squash.md docs/history/backlog/completed/2026-09-21-sequential-landing-discipline-no-dispatch-before-squash.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run V5; expects exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: route sequential-landing-discipline closure stray to completed` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Route item 5, dedupe-cannot-distinguish-reopen-from-stale-leftover

Files:
- `docs/history/backlog/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md`
- `docs/maintenance/document-registry.md`

- [x] Evidence probes: `git merge-base --is-ancestor 341961d1 main && echo LANDED`; `grep -qF "status_value(item_text) == status_value(twin_text)" scripts/docs_branch_backlog_dedupe.py`; `test -f docs/plans/completed/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md`; all expect success [class: REPOSITORY_TEST]
- [x] HARD RULE: the item's suggested direction (Status agreement before removal, Status-only differences surface-and-keep) is the landed status_value comparison; route whole [class: REPOSITORY_TEST]
- [x] Replace the `Status: open` line with `Status: done (executed via docs/plans/completed/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md, Task 8)` [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the whole existing `Disposition: 2026-09-22 (annotated via docs/plans/2026-09-22-p36-scheduler-durability-audit.md, origin ledger)...` line exactly with: `Disposition: 2026-09-24 (routed via docs/plans/2026-09-24-closure-strays-disposition-routing.md, Task 6; supersedes the 2026-09-22 p36 origin-ledger annotation): the Status-match decision (a twin is removed only when normalized bodies AND Status values match, treating Status-only differences as surface-and-keep) landed on main at 341961d1 (loop-quality-hygiene Task 8, "Dedupe status-match fix and tests"): scripts/docs_branch_backlog_dedupe.py compares status_value() of both sides and keeps status-only twins.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append to docs/maintenance/document-registry.md exactly: `| dedupe-cannot-distinguish-reopen-from-stale-leftover | no | completed | 2026-09-20 | executed | docs/history/backlog/completed/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md |  |  | user-approved 2026-09-24: standing pre-authorization carried by the scheduling ask's unattended dispatch chain; routed done by docs/plans/2026-09-24-closure-strays-disposition-routing.md Task 6; implementation verified on main at 341961d1; the origin move licenses this row |` [class: IMPLEMENTATION_REQUIRED]
- [x] `git mv docs/history/backlog/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md docs/history/backlog/completed/2026-09-20-dedupe-cannot-distinguish-reopen-from-stale-leftover.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run V5; expects exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: route dedupe-reopen-vs-stale closure stray to completed` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Route item 6, maintenance-primitive-emission-suppression-and-resume-carriers

Files:
- `docs/history/backlog/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md`
- `docs/maintenance/document-registry.md`

- [x] Evidence probes: `git merge-base --is-ancestor 341961d1 main && echo LANDED`; `grep -qF "Emission-suppression witness and rule" agents/skills/maintenance/zcode.md`; `grep -qF "ZCODE_BUILTIN_PROVIDER_CONFIG_FILE" agents/skills/maintenance/zcode.md`; `grep -qiF "suppression" agents/skills/execute-plan/SKILL.md`; `grep -qiF "suppression" agents/skills/plans/SKILL.md`; all expect success (the discipline text, the env-complete recipe, and both budget-gate suppression notes) [class: REPOSITORY_TEST]
- [x] HARD RULE: fix directions 1-3 are landed and direction 4 is the carve-out item routed at Task 4; route whole [class: REPOSITORY_TEST]
- [x] Replace the `Status: open` line with `Status: done (executed via docs/plans/completed/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md, Task 7)` [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the whole existing `Disposition: 2026-09-22 (annotated via docs/plans/2026-09-22-p36-scheduler-durability-audit.md, origin ledger)...` line exactly with: `Disposition: 2026-09-24 (routed via docs/plans/2026-09-24-closure-strays-disposition-routing.md, Task 7; supersedes the 2026-09-22 p36 origin-ledger annotation): Task 7 "Emission-suppression discipline and headless resume recipe" landed on main at 341961d1: the zcode.md dispatch-discipline section carries the emission-suppression stand-down rule naming the 2026-09-20 witnesses, the launchd resume-carrier bullet exports ZCODE_BUILTIN_PROVIDER_CONFIG_FILE and its siblings in the job script, and both budget-gate pause protocols carry the suppression-risk note; direction 4 (the carve-out) is the sibling carve-out item's scope, routed done at Task 4 of this plan.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append to docs/maintenance/document-registry.md exactly: `| maintenance-primitive-emission-suppression-and-resume-carriers | no | completed | 2026-09-20 | executed | docs/history/backlog/completed/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md |  |  | user-approved 2026-09-24: standing pre-authorization carried by the scheduling ask's unattended dispatch chain; routed done by docs/plans/2026-09-24-closure-strays-disposition-routing.md Task 7; implementation verified on main at 341961d1; the origin move licenses this row |` [class: IMPLEMENTATION_REQUIRED]
- [x] `git mv docs/history/backlog/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md docs/history/backlog/completed/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run V5; expects exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: route emission-suppression closure stray to completed` [class: IMPLEMENTATION_REQUIRED]

### Task 8: Final validation sweep

Files: none (verification only)

- [x] Run the plan's whole Validation Commands block (V1 through V6) from the repo root; expects every gate exit 0 [class: REPOSITORY_TEST]
- [x] Run the public-hygiene scan anchored at the repo root: `PUBLIC_HYGIENE_REPO_ROOT="$(git rev-parse --show-toplevel)" bash scripts/scan-public-hygiene.sh`; expects exit 0 [class: REPOSITORY_TEST]
- [x] Confirm the top-level backlog no longer lists any of the six basenames: V2's top-level absence checks already cover this; re-run V2 alone and expect exit 0 [class: REPOSITORY_TEST]
