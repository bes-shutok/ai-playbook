# Plan: Backlog completed directory regrowth (fold-then-delete as the only terminal shape)

Backlog origin: docs/history/backlog/2026-11-08-backlog-completed-dir-regrowth.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-backlog-completed-dir-regrowth-r*.md and 2026-11-09-plan-review-backlog-completed-dir-regrowth-p978efcb1-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3.5h total, largest task 1.5h
Executed: yes (71ba50ce791ef2913f24c3d7a42d1b39b8860610)

Authoring claim: 2026-11-08-backlog-completed-dir-regrowth.md (session sess_c0be7d9e-eb6b-498d-b357-b8f8f984f87c)

## Terms

- completed/ directory: `docs/history/backlog/completed/`, the `backlog_completed_dir` tooling-compatibility home whose charter (`completed/README.md`) requires it to stay empty of dated item files.
- fold-then-delete: the repository guidelines' terminal shape for a covered backlog origin row: the disposition is folded onto the archived covering plan under `docs/history/plans/completed/`, then the row file is deleted in the same change.
- origins gate: `scripts/check_plan_origins_closed.py`, classifying each origin row (states: completed, rejected, closed, covered, open, unreadable, missing) in a strict archive mode (`run_plan_mode`, the landing gate) and a corpus warn mode (the maintenance survey).
- parking: landing flows moving a covered origin row into the completed/ directory instead of fold-then-delete; the gate classifies the row `completed` (in `PASS_STATES`), so parking is the cheap gate-accepted repair.
- licensing texts: the standing texts that license parking: development_lessons.md #104's rule wording, the root AGENTS.md witness-precedence clause, `agents/skills/doc-hierarchy/company-decisions.md`'s backlog lifecycle line, and the maintenance overlay's completed-home citation (`agents/skills/maintenance/zcode.md`).
- posture constant: the module-level flag in the origins gate selecting how a `completed` classification is treated in strict mode (warning today; refusing after a true catch).
- claimed-origin probe: `python3 scripts/check_backlog_claimed.py --slug <candidate stem>`; exit 1 names slugs claimed by a top-level plan; the sweep records them as skip rows and never deletes them.
- sweep receipt: the dated sweep record appended to `docs/history/backlog/completed/README.md`; the 2026-10-02 record there is the canonical form.
- completion-pass residual arm: the self-claimed skip rows the execution probe reports that stay behind during the sweep and are folded onto their covering plans and deleted by this plan's completion pass, except a row still claimed by another plan at completion time, which stays behind.
- parked-for-operator: the sweep-receipt outcome for a row the sweep cannot license for deletion (an unresolvable row, or a registered empty-audit row with no covering operator confirmation); it stays behind for operator disposition and is named in the Done-when's exception list, distinct from parking, the landing-flow channel this plan removes.

## Why

Covered backlog origin rows keep regrowing under the completed/ directory through routine landing flows because the origins gate classifies a parked row as a pass state and the licensing texts teach or license the home, although the directory's own charter requires it to stay empty and the repository guidelines prescribe fold-then-delete as the only terminal shape. The 2026-11-08 operator-directed history rewrite removed only that day's four instances; the channel stays open and parks again on the next landing.

## Gist & Examples

TLDR: makes fold-then-delete the only terminal shape for covered backlog origin rows, closing the parking channel the origins gate and four licensing texts kept open, as a code-quality repair.

**Before (today):** a session finishing a plan whose origin row carries a covering-plan fold parks the row under `docs/history/backlog/completed/`; the origins gate reads state `completed` and passes the landing; 52 dated rows sit in the charter-empty directory (the 2026-10-02 sweep emptied it at 126 rows; the 2026-11-08 rewrite removed only that day's regrowth). Citations naming completed/ twins (lessons #111 and #207, the maintenance overlay) keep resolving while the files persist.

**After (this plan):** the origins gate treats a completed/ row as a warning-only posture defect ("archived against the fold-then-delete rule") and still exits 0 until promotion; a machinery registry row carries the incident, expected catch, false-positive cost, sunset, and promotion criteria; the licensing texts are aligned so the covering plan's completed twin is the only named durable citation home; the corpus is swept per the README recipe (census re-derived at execution, claimed-origin probe, fold-where-missing-and-licensed, delete, citation re-points, sweep receipt), leaving the directory empty of dated item files except the rows the Done-when's exception list excepts (the self-claimed residual arm folded and deleted by the completion pass, rows other live plans claim, and rows parked for operator disposition).

Edge cases: rows the claimed-origin probe reports as claimed are skipped, their disposal owned by the claiming plan's completion pass; a row whose fold is missing gets the fold appended only when the covering plan exists and the fold is licensed (no disposition invented for an unlicensed covering plan, per the 2026-10-02 recipe); the gate's `missing = straggler` fail-closed posture is unchanged; the release-side publish-scope checker for the same parking class belongs to the coordinated sibling row and is not built here.

## Outcome

Covered backlog rows can no longer park under the completed/ directory as a gate-accepted terminal state.

- The origins gate's completed-directory classification carries a warning-only posture defect with a registered promotion path, so parking is visible at every landing instead of silent.
- The directory holds no dated item files after the sweep except the rows the Done-when's exception list excepts (the self-claimed residual arm folded and deleted by the completion pass, rows other live plans claim, and rows parked for operator disposition), and the standing citations resolve to covering plans' completed twins.
- The licensing texts agree with fold-then-delete, so sessions are no longer taught the parking shape.

Gate delta: one warning-only emission added to the origins gate's strict verdict for a completed-directory row (posture constant, promoting to refusing only after a true catch), priced by the paying sibling removal this plan lands: the parking channel's gate license and its text licenses are removed, leaving fold-then-delete as the only terminal shape; the `missing = straggler` fail-closed posture is explicitly unchanged; no other refusal class, hard gate, fence, protocol layer, or schema field changes; one machinery registry entry row (kind `script`, the inventory's enforced vocabulary, admission fields named in Task 1) plus one removals row naming the parking channel's retirement. Ledger citation (authoring-time `gate_liveness_ledger.py show`): archive-ceremony catches=1 incidents=2; backlog-inbox catches=0 incidents=1 overrides=1.

## Assumptions

- assume the origin row's driving force `correctness` maps to the closed-taxonomy tag `code-quality`; basis: the taxonomy has no correctness tag and the defect class (a rule its own tooling contradicts) is the code-quality class.
- assume the `completed/README.md` 2026-10-02 record is the sweep recipe of record, with the census re-derived at execution and never taken from plan bytes; basis: the entry's scope arm 1 and the README's licensed sweep direction (operator direction 2026-10-01).
- assume rows the claimed-origin probe reports as claimed are skip rows whose disposal stays owned by the claiming plan's completion pass; basis: the 2026-10-02 receipt's skip rows.
- assume the sibling release-boundary arm stays owned by `docs/history/backlog/2026-11-08-release-publishes-charter-empty-dir-rows.md` (its covering plan authored and covered; execution still pending); basis: the Cluster lines on both rows (coordinated, not absorbed).
- assume `agents/skills/doc-hierarchy/SKILL.md`'s Backlog entry needs no edit; basis: the origin row's Evidence section ("the correct skill text exists and is contradicted, not absent").
- assume the fold-append set is large, not near empty: measured at r1 against the gate's own consult predicate, 11 of 52 rows are disposition-anchored, 0 registry-anchored, and about 38 have an identifiable covering plan lacking the disposition section; re-measured at r4 under the anchored-if-any tie-break as 12 anchored / 37 fold-missing / 3 skip; basis: the r1 and r4 reviews' corpus measurements (r1 F1, r4 F8), re-derived at execution from `_MIGRATED_DISPOSITIONS_HEADING_RE` boundary anchoring in `scripts/check_plan_origins_closed.py`.
- assume fold-appends onto archived covering plans are the licensed disposition-section body edit (the completion-pass class the plans lifecycle already sanctions on archived plans), not delta-round work: the delta-round discipline (development_lessons.md #102) binds plans under certification, and the 2026-10-02 sweep appended folds to archived plans as ordinary recipe steps; basis: the README recipe's fold-and-delete outcome rows.
- assume the self-claimed carve set is the skip rows the execution probe reports, measured three at r3: every dated row stem this plan's own text names reads as claimed by this plan once it sits at the plans root (measured at r2 and r3: the probe's CLAIMED lines all point at this plan), so the skip rows stay behind during the sweep and leave via this plan's completion pass after archiving dissolves the claims; the contract surfaces follow the probe receipt, never a byte-counted constant, so a claim set that differs at execution updates the residual arm, the receipt, the Done-when exception list, the Gist, the Outcome, and the Validation Commands record in the same sweep commit; basis: the r1, r2, and r3 probe measurements (r2 F1, r3 F4).
- assume the facts-values row named in the completion-pass residual arm is fold-resolvable despite carrying no Status witness: its covering plan `docs/history/plans/completed/2026-10-22-facts-values-safe-loading-and-audit.md` exists and its own `Backlog origin:` line names the row, and its disposition fold must carry the row's two deliberately-open arms (the owner-led local-facts audit and the preserved OAuth guidance) so the deletion loses no living pointer; basis: disk verification during the r1 fold and the r2 F5 measurement.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the warning-only arm emits the posture warning for a completed/ row in strict mode and still exits 0 until promotion; `missing`, `rejected`, `closed`, `covered`, `open`, and `unreadable` handling is verified unchanged outside the completed/ posture branch.
- completeness: the sweep receipt's outcome counts match the re-derived census file-for-file; no citation re-pointed by the sweep resolves to a deleted dated row.
- maintainability: the posture is one module constant consulted by the strict verdict loop, with promotion criteria living in the machinery registry row rather than code comments.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_plan_origins_closed.py -q` passes including the new posture tests.
- `ls docs/history/backlog/completed/2026-*` returns nothing except (a) the self-claimed rows named in the completion-pass residual arm, which this plan's completion pass folds onto their covering plans and deletes after archiving dissolves this plan's own probe claims, except a row still claimed by another plan at completion time, which stays behind, (b) any row another live plan claims, which stays behind with its disposal owned by that plan's completion pass, and (c) any row recorded as parked-for-operator in the sweep receipt, which stays behind for operator disposition; and `docs/history/backlog/completed/README.md` carries the new sweep receipt.
- the machinery registry carries the entry row (kind `script`, the inventory's enforced vocabulary) for the completed-directory posture and the paired removals row, and `python3 -I scripts/machinery_inventory.py --check` stays green (baseline: 151 entries, 23 removals).
- `rg -n "backlog/completed" docs/maintenance/development_lessons.md agents/skills/maintenance/zcode.md AGENTS.md agents/skills/doc-hierarchy/company-decisions.md` shows no forward-looking license of parking (historical witness prose and charter sweep records stay).

**Ship when:**
- none stated (repository-verifiable only; promotion to refusing is a later operator-visible decision gated on a first true catch and recorded in the machinery registry row).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_plan_origins_closed.py` (Task 1)
- `scripts/machinery_registry.json` (Task 1)

**Tests:**
- `scripts/test_check_plan_origins_closed.py` (Task 1)

**Docs:**
- `docs/history/backlog/completed/README.md` (Task 4) (sweep receipt; Task 5 follow-up records)
- `docs/history/backlog/completed/` (Task 2) (dated rows within, execution-derived census; deleted per the recipe)
- `docs/maintenance/development_lessons.md` (Task 2) (#111/#207 citation re-points)
- `docs/maintenance/development_lessons.md` (Task 4) (#104 rule wording)
- `agents/skills/maintenance/zcode.md` (Task 3) (completed-home citation re-point)
- `AGENTS.md` (Task 4) (witness-precedence clause)
- `agents/skills/doc-hierarchy/company-decisions.md` (Task 5) (backlog lifecycle line)
- `docs/history/plans/completed/` (Task 2) (covering plans receiving disposition folds; execution-derived set)
- `docs/maintenance/document-registry.md` (Task 2) (completed-src reconciliation; Task 5 residue re-points)
- `scripts/` standing-citation hits (Task 5) (execution-derived set; deliberately-historical mentions recorded; the machinery_registry.json path is owned by the Production code listing)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/release/SKILL.md` and the publish-scope checker; reason: the release-boundary arm of the same parking class is owned by the coordinated sibling row's landed plan.
- `agents/skills/doc-hierarchy/SKILL.md`; reason: already states the correct fold-then-delete rule (origin row Evidence); edit only if review finds drift.

## Validation Commands

Authoring-time record (rule 29 preamble, 2026-11-08): em-dash touched scan over the plan bytes PASS (0 substitutions); public-hygiene scan OUTCOME: pass; pre-round readiness gate OUTCOME: pass after two recorded pre-round repairs (Task 2 Files glob replaced with the existing directory; untagged Run/Commit checklist lines tagged), leaving one Files-coverage annotation warning fixed by splitting the lessons-corpus path per task; rule 22 mechanical audit PASS after the r1 fold (bash -n over the block re-run; the F4-pinned warning span occurs in Task 1's RED item following the F4 fold; the pre-fold audit claim naming that span was false and is corrected here); no forbidden-pattern sweep exists in the block, so no rule 19 RED-today execution applies; r1 recorded: full fresh-adversarial panel, verdict ready=no, 3 blocking (F1 sweep-append scale, F2 Done-when carve, F5 registry vocabulary), 5 non-blocking folded in the same batch; pinned commands over today's tree: pytest scripts/test_check_plan_origins_closed.py PASS (baseline suite green before the posture change), corpus scan exits 0 with parked-row warnings absent (rows classify completed today), the dated-rows ls is non-empty today (52) by design, post-Task-2 the ls exits 0 matching exactly the Done-when's exception set (the residual-arm skip rows plus any foreign-claimed row recorded with its owner plus any parked-for-operator row; re-derived at execution; measured three at r4, none foreign-claimed, none parked; execution 2026-11-09: probe self-claimed set is exactly `2026-10-21-facts-values-safe-loading-and-audit` (none foreign-claimed, none parked; census 52, 51 deleted, 1 skip)), no-match being the post-completion-pass condition on the residual arm once the other sets are empty, evaluated against the receipt. r3 recorded (2026-11-09, resumed authoring run after the stale-claim takeover of the r2 session's claim): fresh-adversarial focused panel over the r2 fold diff plus the blind probe, verdict ready=no, 3 blocking (F1 registry witness-ref re-point unowned, F2 document-registry check-writes collision, F3 the 2026-10-02 recipe's per-batch reconciliation arm dropped), 9 non-blocking folded in the same batch. r4 recorded (2026-11-09): fresh-adversarial certification-candidate panel with fold verification, verdict ready=no, 2 blocking (F1 the check-writes gate refuses the sweep write set and the fold remedy cleared the license before the gate read, F2 the Done-when disposal clause contradiction), 9 non-blocking folded with this record's correction; the r3 F5 sunset re-key and F6 removals-paths guidance land with this fold after r4 found the transcription gap.

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_plan_origins_closed.py -q
python3 scripts/check_plan_origins_closed.py --repo-root .
ls docs/history/backlog/completed/2026-*
```

### Task 1: Warning-only posture for the completed-directory origin state

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/check_plan_origins_closed.py`
- `scripts/test_check_plan_origins_closed.py`
- `scripts/machinery_registry.json`

Primary class anchors:
- `run_plan_mode` in `scripts/check_plan_origins_closed.py`
- `classify_origin` in `scripts/check_plan_origins_closed.py`

- [x] RED: strict-mode check over a plan whose origin row sits under the completed/ directory emits the exact posture warning span `archived against the fold-then-delete rule` naming the row and still exits 0 while the posture constant reads `warning`; given `missing` and `rejected` fixtures, expects today's behavior byte-identical [class: REPOSITORY_TEST]
- [x] Implement: module-level `COMPLETED_DIR_POSTURE = "warning"`; `run_plan_mode` routes a `completed` state through the posture warning instead of `PASS_STATES` membership, kept out of the fail set; corpus mode unchanged; a second test exercises the `refusing` posture routing `completed` into the fail set [class: IMPLEMENTATION_REQUIRED]
- [x] Pin corpus-mode non-regression with a test asserting a completed/ row under corpus mode stays resolved (no unresolved-origin warning for it) while the strict posture warning fires on the same fixture [class: REPOSITORY_TEST]
- [x] Registry: append one entry row in the enforced vocabulary, kind `script`, id `script:origins-completed-dir-posture`, `paths` left empty (the existing `script:check_plan_origins_closed.py` row owns that path), incident witnessed by this plan's tracked file (kept resolvable after the sweep) [class: IMPLEMENTATION_REQUIRED]
- [x] Registry: fill the entry row's `note` with the catch and cost admission fields: expected catch every parking attempt (the origin row's regrowth commits are the rate evidence); false-positive cost with the true bound `same-run adjacency (Task 1 lands, Task 2 sweeps immediately after); legacy twins are corpus-mode-only and stay silent` [class: IMPLEMENTATION_REQUIRED]
- [x] Registry: fill the entry row's `note` with the sunset and promotion fields: sunset review date written as the computed ISO date in the precedent form `review date: YYYY-MM-DD` (one quarter after Task 1's landing commit, the anchor), with the no-catch sunset at that review (if no true catch, remove the posture branch and move the row to the removals record); promotion criteria first true catch of a post-alignment parking attempt [class: IMPLEMENTATION_REQUIRED]
- [x] Registry: append the paired removals row in the same kind-vocabulary shape (no new kind), `paths` left empty (the script persists; the retirement is the behavior, not the file), naming the parking channel's retirement (fold-then-delete becomes the only terminal shape) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN (posture tests green; the full origins-gate suite green at this task point; later tasks add no failing checks) [class: REPOSITORY_TEST]
- [x] Commit: `feat: origins gate treats completed-dir rows as warning-only posture defects` [class: REPOSITORY_TEST]

### Task 2: Sweep the completed/ corpus to fold-then-delete

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `docs/history/backlog/completed/` dated rows within (execution-derived census; deleted per the recipe)
- `docs/history/backlog/completed/README.md` (sweep receipt appended in Task 4)
- `docs/history/plans/completed/` (covering plans receiving disposition folds; execution-derived set)
- `scripts/machinery_registry.json` (keep-row witness re-points)
- `docs/maintenance/document-registry.md` (completed-src registrations reconciled)

- [x] Re-derive the census at execution: list the dated item files under `docs/history/backlog/completed/` (near 52; never the plan-byte constant) and carry the count into the sweep receipt [class: IMPLEMENTATION_REQUIRED]
- [x] Run the claimed-origin probe in one bulk invocation over every census stem and record claimed slugs as skip rows excluded from deletion, their disposal owned by the claiming plan's completion pass [class: REPOSITORY_TEST]
- [x] On claim-set drift from the named surfaces (residual arm, receipt, Done-when, Gist, Outcome, Validation record, delete bullet), update them in the same sweep commit so the self-claimed names equal the probe's self-claimed set [class: REPOSITORY_TEST]
- [x] Resolve each unclaimed row's covering plan: Status witness, then any `Covered by:` line, then the archived twin's `Backlog origin:` line or plural origins declaration [class: REPOSITORY_TEST]
- [x] Verify the fold with the gate's consult predicate; with several named covering plans, treat the row as anchored-if-any, preferring the plan its disposition text designates [class: REPOSITORY_TEST]
- [x] Park unlicensable rows for operator (rows no ladder rung resolves that carry no probe claim, and registered empty-audit rows whose note has no covering operator confirmation), recording each in the receipt with its resolution or licensing witness and naming them in the Done-when's exception list so accounting stays total [class: IMPLEMENTATION_REQUIRED]
- [x] Immediately before the sweep commit: re-derive the directory listing and re-run the probe over the union of the census stems and every path deleted so far; fold or skip-record any arrival (an arrival resolving to no covering plan and carrying no claim is recorded as parked-for-operator) [class: REPOSITORY_TEST]
- [x] Assert no claim on a deleted path; on an assertion failure restore the deleted path from git, record it as a claimed skip row owned by the reporting claimer, and record the repair and the re-run outcome in the sweep receipt (the 2026-10-02 form's per-batch post-move discovery re-run) [class: REPOSITORY_TEST]
- [x] For each row whose covering plan lacks a gate-recognized fold (measured at r4: 37 of 52; 12 anchored, 3 skip), append the disposition to the covering plan as the licensed completion-pass body edit: a `## Disposition of migrated backlog items` section carrying a one-row disposition naming the row path and the covering relationship, or a matching row appended to the plan's existing section; never invent a disposition for an unlicensed covering plan [class: IMPLEMENTATION_REQUIRED]
- [x] Enumerate machinery-registry keep-row witness refs naming a deleted census row before the sweep commit (measured at r3: exactly one, `duty:clocked-order-verify-successor`) [class: IMPLEMENTATION_REQUIRED]
- [x] Re-point each enumerated ref (ref and note admission path) to the covering plan's completed twin (`docs/history/plans/completed/2026-10-18-clocked-order-successor-verification.md`) with the deletion, recording the re-points in the receipt [class: IMPLEMENTATION_REQUIRED]
- [x] Delete each dispositioned row file, leaving no dated item file behind except the receipt-recorded skip rows (the self-claimed residual arm and any foreign-claimed row with its owner) and any parked-for-operator row [class: IMPLEMENTATION_REQUIRED]
- [x] Carry the completion-pass residual arm into the receipt Task 4 appends: the self-claimed rows stay behind during the sweep (receipt-named; execution 2026-11-09 probe set: exactly `2026-10-21-facts-values-safe-loading-and-audit`, none foreign-claimed, none parked) [class: IMPLEMENTATION_REQUIRED]
- [x] A further claimed row likewise stays behind, recorded among the receipt's skip rows with its owner; it never joins the residual arm, its disposal staying with the claiming plan [class: IMPLEMENTATION_REQUIRED]
- [x] Before ending this task, stage every sweep change (deletions, fold-appends, registry re-points) and re-run the pre-commit probe; leave the changes staged, uncommitted, for Task 3's licensing gate [class: IMPLEMENTATION_REQUIRED]

### Task 3: License and land the sweep

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `docs/maintenance/document-registry.md` (licensing notes and register-and-note rows)
- `docs/history/backlog/completed/` dated rows (the Task 2 staged deletions land here)
- `docs/history/plans/completed/` (the Task 2 staged fold-appends land here)
- `scripts/machinery_registry.json` (the Task 2 staged re-points land here)

- [x] Licensing (a): verify each registered write-set row (measured at r3: 16 census rows, five empty audit cells) still names its path as `src`, notes in place through every gate read [class: IMPLEMENTATION_REQUIRED]
- [x] Licensing (b): mint dated `user-approved YYYY-MM-DD:` notes on each registered write-set row with an empty audit cell, citing the 2026-10-01 operator direction quoted in the completed/README sweep record ("integrate into completed plans, do not keep completed backlog separately") [class: IMPLEMENTATION_REQUIRED]
- [x] Licensing (b) fallback: a write-set row with no covering operator confirmation parks for operator instead of minting, recorded in the receipt with its licensing witness [class: IMPLEMENTATION_REQUIRED]
- [x] Licensing (c): add register-and-note rows only for unregistered write-set paths (sweep deletions, fold-append targets, the completion pass's future writes, which inherit these licenses); note existing rows for already-registered paths, never a second registration (a duplicate row multi-claims the src and stays gated) [class: IMPLEMENTATION_REQUIRED]
- [x] Licensing (d): with Task 2's changes staged, run `git -c core.quotePath=false diff --cached --name-status --no-renames | python3 scripts/doc_registry_validator.py check-writes --stdin`, expecting exit 0 with an `override:` line per written path; re-assert after any repair; a HARD line is a licensing failure blocking the commit [class: IMPLEMENTATION_REQUIRED]
- [x] Licensing (e): land the sweep with every license standing [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: sweep the backlog completed corpus to fold-then-delete` [class: REPOSITORY_TEST]
- [x] Follow-up commit, after the run's done-boundary gate read (the landing closeout or the completion pass's first arm) and named as pending in the receipt's licensing line with its owning commit: flip each completed src registration whose covering twin is unregistered to the twin, retire it when the twin is already registered by another identity, and clear the notes whose licensed writes landed; never before that done-boundary read [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: flip completed-src registrations to completed twins and clear override notes` [class: REPOSITORY_TEST]

### Task 4: Re-point standing citations and append the sweep receipt

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `docs/maintenance/development_lessons.md` (#111 and #207 citation re-points)
- `agents/skills/maintenance/zcode.md` (completed-home citation re-point)
- `docs/history/backlog/completed/README.md` (sweep receipt)

- [x] Re-point development_lessons.md #111's citation to `docs/history/plans/completed/2026-10-20-plan-prompts-prune-range-content-inventory.md` (the covering plan its row's Done line names), verifying the target exists before the edit, and reword the lesson's forward-looking "the new witness is appended there" directive to name the surviving witness home (or drop it to a historical witness statement), recording the reword in the receipt's citation re-points [class: IMPLEMENTATION_REQUIRED]
- [x] Re-point development_lessons.md #207's citation to `docs/history/plans/completed/2026-10-23-prune-audit-incommit-receipt-witness-arm.md` (the covering plan its row's covered-by line names), verifying the target exists before the edit [class: IMPLEMENTATION_REQUIRED]
- [x] Re-point the zcode.md MIXED-verdict bullet's completed-home citation (its two named rows are absent from the tree today) to the recorded owner `docs/history/plans/completed/2026-09-19-scheduler-ops-lanes-durability.md`, verified to exist before the edit [class: IMPLEMENTATION_REQUIRED]
- [x] Append the sweep receipt to `docs/history/backlog/completed/README.md` in the 2026-10-02 form: census, probe receipt with its per-batch post-move discovery re-runs, outcome counts file-for-file, citation re-points, licensing line (including the pending flip/clear follow-up and its owning commit), parked-for-operator outcomes from both triggers, and the completion-pass residual arm naming the self-claimed rows the probe reported and their disposal owner [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: re-point completed-corpus citations and record the sweep receipt` [class: REPOSITORY_TEST]

### Task 5: Align the licensing texts with fold-then-delete

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `docs/maintenance/development_lessons.md` (#104 rule wording)
- `AGENTS.md` (witness-precedence clause)
- `agents/skills/doc-hierarchy/company-decisions.md` (backlog lifecycle line)
- `docs/maintenance/document-registry.md` and `scripts/` standing-citation hits (Task 5 residue re-points; execution-derived set)
- `docs/history/backlog/completed/README.md` (sweep receipt follow-up records; second edit in this task's commit)

- [x] development_lessons.md #104: retitle the lesson (the title `Archive It Covered` is itself the parking license other texts cite; for example `... ; Fold It and Delete the Row`), keeping the 2026-10-19 witnesses as history with a one-line posture-flip note; check the maintenance pins suites for literals pinning the old title and reconcile beside their provenance comments in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] development_lessons.md #104: reword the rule so the served dispositions are the fold-and-delete shapes, `rejected/`, and a closed-status header; the completed/ archive stops being a named served disposition; the missing = straggler fail-closed sentence stays [class: IMPLEMENTATION_REQUIRED]
- [x] AGENTS.md: the witness-precedence clause names the covering plan's `docs/history/plans/completed/` twin as the durable citation home, dropping the backlog completed/ twin precedence [class: IMPLEMENTATION_REQUIRED]
- [x] company-decisions.md: the backlog subfolder bullet's archive-lifecycle sentence becomes the fold-then-delete form (fold onto the covering plan's completed twin, delete the row; the directory stays tooling-compatibility scaffolding) [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep for contradictory residue with `rg -n "backlog/completed" AGENTS.md agents/skills/ docs/maintenance/development_lessons.md docs/history/backlog/completed/README.md` and re-word any remaining forward-looking license of parking, keeping historical witnesses and charter sweep records [class: REPOSITORY_TEST]
- [x] Sweep the standing-citation fanout with `rg -n "backlog/completed/2026-" scripts/ docs/maintenance/ projects/ docs/history/plans/` (excluding the completed corpus, the plan-history twins, the rejected/ and deferred/ terminal-state archives, and this plan's own body) and re-point every surviving witness-style citation to the row's completed twin [class: REPOSITORY_TEST]
- [x] Record each deliberately-historical mention (docstring or comment prose, ledger evidence fields) in the sweep receipt, which receives its second edit in this task's commit; measured at r4: document-registry rows, machinery_registry.json notes, gate_liveness_ledger.json incident notes, the check_maintenance_pins.sh fixture lines, and script docstrings [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: align origin-row licensing texts with fold-then-delete` [class: REPOSITORY_TEST]

### Completion pass (after this plan lands and archives)

Files:
- `docs/history/backlog/completed/` residual rows (deleted per the recipe)
- `docs/history/plans/completed/2026-10-22-facts-values-safe-loading-and-audit.md` (completion-pass disposition fold)
- `docs/history/backlog/completed/README.md` (receipt follow-up records)
- `scripts/machinery_registry.json` (Task 1 witness re-point)

- [x] License the pass's own write set first, mirroring Task 2's shape: register-and-note each unregistered residual row path and each unregistered covering twin receiving a completion-pass fold-append (minted at the pass's execution date under the same recorded operator direction), assert `check-writes` exits 0 over the staged pass write set, then proceed; the pass's commit carries these registrations [class: IMPLEMENTATION_REQUIRED]
- [x] Dispose the residual arm: fold each residual row onto its covering plan first (the facts-values disposition naming its two deliberately-open arms verbatim); immediately before deleting, re-run the claimed-origin probe over the residual stems and the receipt's foreign-claimed skip rows: a row still carrying a claim from another plan stays behind, recorded in the receipt as a foreign-claimed skip row with its owner; a row whose claim dissolved resolves, folds onto its covering plan, and deletes with the remainder; a claimless row with no resolvable covering plan parks for operator; delete only the licensed unclaimed remainder once archiving dissolves this plan's probe claims, append the pass's licensing and outcome records to the receipt (including the note that the Task 1 witness ref dangles between the archive rename and the re-point, this pass being the sanctioned repairer of that red inventory state), and re-point the Task 1 registry row's witness ref to this plan's completed twin; then run the Task 2 follow-up arm if not yet landed [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: completion pass disposes the residual arm` [class: REPOSITORY_TEST]

## Residual findings (cap closure)

Dispositions for every staged finding of the cap round (r5, 2026-11-09); the round's three overflow candidates land their fixes in the same final batch. The review loop closed at its 5-round cap under the authoring payload's standing cap instruction ("at the cap finalize with the best available draft and record the residual findings in the plan"), this section being the record the instruction orders; no staged finding remains for a later round, and the reviewed r5 bytes are digest-pinned in the round's sidecar as the pre-fold witness.

- F1 (implementation#standing-gate-collision): folded - the licensing sequence rewritten: arms (b)/(c) scoped to the whole write set (notes on registered empty-audit rows, register-and-note only for unregistered paths, existing rows noted instead of duplicated), the gate read staged-span-pinned and re-asserted, the flip/clear follow-up re-homed after the done-boundary gate read with its own commit line.
- F2 (implementation#framework-contract-unverified): folded - the completion pass carries its own licensing arm (register-and-note + staged-span check-writes assert), a Files block, and a commit bullet.
- F3 (consistency#parked-bucket-membership-licensing-fallback-mismatch): folded - the parked bucket admits both triggers (unresolvable rows and unconfirmed empty-audit rows) across the Terms, Done-when class (c), the parked bullet, and the receipt enumeration.
- F4 (consistency#delete-bullet-exception-drops-foreign-claimed): folded - the delete bullet references the receipt's skip-row record and joins the drift-update surface list.
- F5 (security#stalled-claimer-orphan-no-fallback): folded - the completion-pass re-probe covers the receipt's foreign-claimed skip rows with dissolve/resolve/park branches.
- F6 (security#licensing-followup-unowned-untracked): folded - the receipt's licensing line names the pending follow-up and its owning commit.
- F7 (consistency#probe-equality-vs-arm-definition): folded - the equality demand scoped to the self-claimed set with foreign claims flowing to the receipt and Done-when.
- F8 (testing#coverage-claim-unchecked): folded - the fold-append sizing cites the r4 measurement (37 of 52).
- F9 (architecture#dual-surface-policy-parity): folded - the Terms and Done-when (a) carry the completion-time foreign-claim exception.
- F13 (security#witness-ref-dangling-archive-window): folded - the receipt records the dangling window and the completion pass as the sanctioned repairer.
- F14 (security#operator-confirmation-scope-unbounded): folded - arm (b) quotes the direction and states its coverage bound.
- F15 (consistency#review-scope-task-tag-missing-task-4-second-edit): folded - the Review Scope README entry carries both task tags.
- F16 (implementation#requirement-coverage): folded - Assumption 4 states the sibling's covered-pending-execution state.
- overflow F10 (architecture#dual-surface-policy-parity): folded - the parked parenthetical names the full resolution ladder.
- overflow F11 (architecture#dual-surface-policy-parity): folded - the sunset review date prescribes the ISO precedent form.
- overflow F12 (simplification#delete): folded - the dead post-promotion re-review field removed.
