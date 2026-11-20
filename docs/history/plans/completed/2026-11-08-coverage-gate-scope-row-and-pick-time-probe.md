# Plan: Coverage-gate late and false refusals: pick-time probe and scope-row rule

Backlog origins (scope of record):
- docs/history/backlog/2026-11-08-authoring-pick-time-coverage-probe.md
- docs/history/backlog/2026-11-08-coverage-gate-deliberately-open-scope-row.md

Cluster: docs/history/backlog/2026-11-03-coverage-gate-directory-operand-self-conflict.md (the same gate's remaining false-conflict root, a directory-operand self-conflict; deliberately not consumed here, see Out of scope)

Required agent type: none (runtime-neutral)
Driving force: efficiency (primary), code-quality (secondary)
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-coverage-gate-scope-row-and-pick-time-probe-pbe300071-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 0.5h
Executed: yes (575cdf5e3fbf48ef65b447abbebe606542dee6b7)
Authoring claim: coverage-gate-scope-row-and-pick-time-probe.md (session sess_5e0f7280-6e25-4620-84fa-5a56169b6c92)

## Terms

- coverage gate (full name: duplicate-origin coverage gate): `scripts/check_plan_origins_closed.py --check-coverage`, the landing gate that scans active, deferred, completed, and rejected plans for other plans citing the declaring plan's origin basenames. This mode returns exit 0 clean, exit 1 conflict naming each citer and its state-specific remedy, and exit 3 tool error; it never returns exit 2 (that exit belongs to the corpus-scan and plan modes). The final `OUTCOME:` line is the routing input per `scripts/OUTCOME_CONTRACT.md`.
- scope-of-record block: the plan header's `Backlog origins (scope of record):` bulleted block; the coverage extractor parses the singular `Backlog origin:` line and bare `Origin:` header lines into the same coverage set, so every header citation shape is a coverage declaration.
- citer: another plan whose header cites one of the declaring plan's origin basenames. The gate's output can carry two conflict lines for one archived citer (the active-directory scan descends into the nested surfaces and prints the same path as `(active)` before its state-specific line), so citers are deduplicated by path and routed on the most specific reported state.
- deliberately-open row (also called a keep-open row; both names mean the same thing in this plan): a backlog row a plan names while its own dispositions record the row as staying open for separate work.
- pick-time coverage probe: the read-only pre-claim invocation of the coverage gate against a scratch declaring file carrying the picked origins, specified in Task 1.
- scratch declaring file: a minimal plan-shaped file whose header block lists exactly the probed origins, named `docs/tmp/coverage-probe-scratch-<session-id>.md` under the probing checkout's facts-resolved tmp directory; created before the probe, deleted after it, and the delete verifies the file's declaring content before unlinking so a parallel session's scratch is never removed.
- Cluster re-home: the development-lesson #427 remedy that moves a deliberately-open row's citation onto the citer's `Cluster:` line with a dated moved-here note, leaving the gate's code unchanged (the corrected header shape of the empty-diff completed plan is the precedent).
- empty-diff completed plan: `docs/history/plans/completed/2026-11-02-empty-diff-closeout-route.md`, whose `Cluster:` line carries the kept-open rationale and the dated moved-here note (moved here from the scope-of-record block, with the date and the backlog row cited), the corrected header shape the re-home mirrors.
- covering-origin arm: the closed routing table Task 2 adds to the collision disposition, giving each deduplicated citer the pick-time coverage probe reports exactly one disposition (skip, re-home and proceed, or remedy and skip).
- landing pre-check: the Task 2 step that, on the landing gate's exit 1, runs the development-lesson #427 citer read and the Cluster re-home ahead of the pre-landing gate clause's claim-deletion step and stranding report.
- collision disposition: the AUTHORING CLAIM gate's fresh-foreign-claim refusal, stale-foreign-claim takeover, and raced-pick continuation machinery in `agents/skills/maintenance/template-authoring.md`, extended by Task 2 with the covering-origin arm.
- authoring-time rule: the Task 3 rule in the plans skill's Origins block shape paragraph: a deliberately-open row is cited on the `Cluster:` line, never in the scope-of-record block nor as the singular `Backlog origin:` line when the plan's dispositions keep the row open.

## Why

The duplicate-origin coverage gate runs only before landing, so a header collision that existed on disk before the claim surfaces after full review spend, and a citer that merely mis-declares a keep-open row refuses an otherwise clean landing. Both costs were witnessed on 2026-11-08: a four-round certified authoring run was refused at landing and recovered only by an operator-directed self-heal re-home of the mis-declared row. The pick-time probe and the authoring-time rule close both costs at their sources.

## Gist & Examples

TLDR: a read-only pick-time coverage probe and an authoring-time Cluster: rule close the coverage gate's late and false refusals, for efficiency and code-quality.

Before: an authoring run picks an origin whose row a completed plan cites in its header; four review rounds are spent, the landing gate refuses naming the citer, and the run strands until an operator-directed recovery re-homes the row.

After: the same run probes the origin read-only before the claim create, sees the citer immediately, repairs a mis-declared completed citer through the sanctioned re-home carrier, and skips real coverage, so no review round is spent on a conflicted target and clean landings never strand on a mis-declared header.

## Outcome

Authoring runs detect covering citers before any claim or review spend, and plans declare deliberately-open rows in a shape the coverage gate cannot misread.

- A picked origin whose row another plan cites is surfaced at pick time with the citer named, before the claim create.
- A completed citer whose dispositions keep the row open is repaired through a sanctioned default-branch corpus-fix commit before the worktree exists, and the pick proceeds.
- Real competing coverage skips the target with the reason recorded, never a late refusal.
- The gate's code, operands, and refusal semantics are unchanged.

Gate delta: none (no new refusal class, hard gate, fence, protocol layer, schema field, or task pause condition; the probe reuses the existing gate CLI read-only through a scratch operand, the authoring-time rule and the corpus edits are skill-text and data changes, and no gate, validator, lock, ledger, or required ceremony is added)

## Assumptions

- Assume the coverage gate's coverage extractor parses the plural block, the singular `Backlog origin:` line, and bare `Origin:` header lines into one coverage set; basis: `extract_coverage_origin_basenames` in `scripts/check_plan_origins_closed.py`, and all three named corpus plans cite their rows through the singular line.
- Assume the three corpus rows are still open at the backlog top level with no completed or rejected archive twin; basis: disk reads at authoring time, re-derived by the executor before each edit.
- Assume the friction-audit message-class normalization landed in `scripts/friction_audit_quant.py` (the 1302/1308 provider codes and `_message_class` are present on disk); basis: disk read at authoring time, making fold-and-delete the likely corpus disposition pending the executor's acceptance re-derivation.
- Assume editing the three archived plans and folding one row needs no re-certification round; basis: the metadata-retrofit rule's next-natural-edit precedent and the empty-diff completed plan's post-archival header correction, both existing shapes.
- Growth-payment receipt: the operative-text additions cite development lesson #427's procedure by name instead of restating its decision rule, the two plans-skill pointers carry zero restated mechanics, and the residual unbalanced byte growth (the probe recipe and the closed disposition table) is accepted and recorded here as the review-time payment record.
- Probe carrier receipt: the prose scratch recipe stays instead of a `scripts/` helper because the origin row and the entry prompt mandate the existing gate CLI unchanged, and the recipe matches the template's inline-recipe precedent (the noclobber create); a `--probe-origin` read-only mode or a helper script is the recorded next step only if the scratch operand proves awkward in live use, mirroring the origin row's own escalation.
Decision points requiring a grill: probe placement = the pre-claim window of the AUTHORING CLAIM gate so every authoring invocation (operator payload walk, scheduler D2 dispatch, in-session run) crosses it exactly once, with both in-file restatements reconciled by pointer (source: entry scope arm 2 and single-homing over the body-side AUTHORING CLAIM paragraph as the procedure of record, with the payload-side duty and the compact stand-down mirror deferring by reference, 2026-11-08, affected sections: Tasks 1-3 / Review Scope); probe operand = the existing gate CLI with a session-unique scratch declaring file and no gate code change (source: origin row suggested-change section and the entry prompt's "using the existing gate CLI" with "keep the gate's code and refusal semantics unchanged", 2026-11-08, affected sections: Terms / Task 1 / Validation Commands); re-home carrier = the pick-time repair commits to the default branch through the primary checkout's ref-bound write transaction before the worktree exists, so the authoring branch inherits the fix and the landing gate sees it (source: r1 fold F2, the review workers' placement analysis and the witnessed #427 recovery shape, 2026-11-08, affected sections: Task 2); self-served re-home restricted to completed citers with deferred and rejected citers routed to skip-and-continue (source: r1 fold F5 and F10, the continuation-ownership preserve-and-route rule, 2026-11-08, affected sections: Task 2); corpus dispositions = re-home for runtime-scripts-home-reconcile-and-retire and codex-task-resource-cleanup (keep-open dispositions recorded on disk), fold-and-delete for friction-audit-quant-message-class-normalization (landed-code evidence), each with an executor re-derivation override that newer disk evidence triggers by recording the contradicting decision (source: entry scope arm 3 and the pinned disk reads in Task 5, 2026-11-08, affected sections: Task 5).

## Standing constraints

- Operative skill text cites incidents in at most one line; the dossier lives in the origin rows and development lessons #427 and #393, never in the edited rule text.
- The coverage gate's code and refusal semantics stay unchanged; a corpus or skill-text need that seems to require a gate change routes to the origin rows as a new backlog item instead.
- Every scripted invocation reads its outcome through the script's final `OUTCOME:` line per `scripts/OUTCOME_CONTRACT.md`; an exit that is neither the mode's pass nor its conflict exit is never read as pass or as conflict.
- Root discipline: pick-time probes and rehearsals run against the primary checkout with absolute paths; post-edit verifications run against the executing worktree; "verbatim" in this plan binds the scratch recipe shape, never the operand root.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the probe's scratch recipe parses (the gate reports the declared origins, never "no origins"), the exit-code routing matches the gate's outcome contract, and the covering-origin arm routes each deduplicated citer on its most specific reported state.
- maintainability: each arm has one home (probe and covering-origin arm in the AUTHORING CLAIM gate paragraph, with the payload-side duty and the compact mirror deferring by reference; the authoring-time rule in the plans skill's Origins block shape paragraph; the landing pre-check's mechanics home is the pre-landing duplicate-origin coverage gate clause in `agents/skills/maintenance/template-authoring.md`, ahead of that clause's claim-deletion step, whose plans-skill landing-closeout bullet is its one-sentence pointer), cross-referenced by name, never restated.
- minimality: no gate code change; the diff touches only the two skill files, the three archived plans, the one folded row, and the document-registry licensing rows.

**Done when:**
- The probe recipe, executed with its shape verbatim (roots per Standing constraints), reports exit 1 naming each archived citer at both reported states before Task 5's edits, and exit 0 with the line `coverage gate clean; no covering citer` for the two re-homed origins after them, probed from the executing worktree.
- The folded friction-audit row no longer resolves at the backlog top level and its disposition is recorded on the archived plan; no post-edit probe runs for that origin (a scratch declaring it exits 1 naming the archived completed plan by design).
- Each of the five skill-text landings passes its presence witness in Tasks 1-3 (RED before the edit, GREEN after).
- The document-registry gate licenses the corpus writes: `python3 scripts/doc_registry_validator.py validate` exits 0 and `check-writes` over Task 5's change set reports no unprotected immutable write (the added registry rows take the override path), the pre-review text-policy sweep (the em-dash added-lines gate `bash scripts/check-no-em-dash.sh added-lines --base <base-ref>` with the execution run's base commit as `<base-ref>`, public hygiene scan, pins suite over the touched pinned file) exits 0, and `python3 scripts/plan_readiness.py docs/history/plans/2026-11-08-coverage-gate-scope-row-and-pick-time-probe.md` (run from the executing worktree) exits 0 with `OUTCOME: pass` at execution start, before the first checkbox flip (later checkbox flips change the certified bytes until the execution-review record refreshes the sidecar digest).

**Ship when:**
- The next authoring pick over one of the three corpus origins runs the probe end-to-end in a live selection walk and proceeds or skips by the new disposition table without operator involvement.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- (none; this plan changes no production code)

**Docs and skill text:**
- `agents/skills/maintenance/template-authoring.md` (Task 1); also edited by Task 2
- `agents/skills/plans/SKILL.md` (Task 3)
- `docs/history/plans/completed/2026-10-28-runtime-scripts-home-reconcile-and-retire.md` (Task 5)
- `docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md` (Task 5)
- `docs/history/plans/completed/2026-10-25-friction-audit-quant-message-class-normalization.md` (Task 5)
- `docs/history/backlog/2026-10-09-friction-audit-quant-message-class-normalization.md` (Task 5); deleted by the fold
- `docs/maintenance/document-registry.md` (Task 5)

**Tests:**
- (none added; verification is the probe recipe itself plus the repository's standing suites listed under Validation Commands)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/check_plan_origins_closed.py`; reason: the entry prompt keeps the gate's code and refusal semantics unchanged, and the corpus edits clear the false citers at their source.
- `agents/skills/maintenance/decisions.md` and the scheduler D2 rule; reason: the probe fires inside the AUTHORING CLAIM duty every authoring invocation already passes through, so a second copy in D2 would drift.
- The backlog-completed-directory regrowth program; reason: a sibling entry owns the completed-backlog parking channel and its corpus sweep; coordinated, not absorbed.
- `docs/history/backlog/2026-11-03-coverage-gate-directory-operand-self-conflict.md` (the Cluster row); reason: a gate-side false-conflict root, out of scope because the gate's code stays unchanged.

## Validation Commands

```bash
# Pre-edit rehearsal (Task 4), from the primary checkout, absolute paths:
python3 <primary-root>/scripts/check_plan_origins_closed.py --check-coverage <primary-root>/docs/tmp/coverage-probe-scratch-<session-id>.md --repo-root <primary-root>
# Post-edit verification (Task 5), from the executing worktree root:
python3 scripts/check_plan_origins_closed.py --check-coverage <worktree-root>/docs/tmp/coverage-probe-scratch-<session-id>.md --repo-root .
# Registry licensing (Task 5), from the executing worktree root:
python3 scripts/doc_registry_validator.py validate
python3 scripts/doc_registry_validator.py check-writes --help  # then run check-writes over the Task 5 change set per its CLI
# Standing gates, from the executing worktree root:
bash scripts/check_maintenance_pins.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_plan_origins_closed.py -q
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base <base-ref>  # base-ref = the execution run's base commit
python3 scripts/plan_readiness.py docs/history/plans/2026-11-08-coverage-gate-scope-row-and-pick-time-probe.md
```

### Task 1: Pick-time coverage probe in the AUTHORING CLAIM gate

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/template-authoring.md`

- [x] In the body-side AUTHORING CLAIM gate paragraph of `agents/skills/maintenance/template-authoring.md`, the availability window immediately before the claim create carries the pick-time coverage probe, whose first step builds the session-unique scratch declaring file (a minimal plan header whose `Backlog origins (scope of record):` block lists exactly the picked origins) under the primary checkout's facts-resolved tmp directory [class: IMPLEMENTATION_REQUIRED]
- [x] The probe then runs `python3 <primary-root>/scripts/check_plan_origins_closed.py --check-coverage <scratch-abs-path> --repo-root <primary-root>` read-only, deduplicates the reported conflicts by citer path, routes each citer on its most specific reported state (a state-specific line beats the `(active)` mislabel the active-directory scan prints for the same archived file), and routes on the final `OUTCOME:` line [class: IMPLEMENTATION_REQUIRED]
- [x] The probe ends by deleting the scratch only after verifying its declaring content, so a parallel session's scratch is never removed [class: IMPLEMENTATION_REQUIRED]
- [x] Probe witness (exercised by Task 4's rehearsal): given a picked origin whose row a completed plan cites in its header, expects exit 1 with both reported lines for that citer (the `(active)` mislabel first, then the `(completed)` state line) before any claim write, with the scratch absent after the probe [class: REPOSITORY_TEST]
- [x] The payload-side AUTHORING CLAIM DUTY copy in the same file defers its pre-create window to the body paragraph by reference (one pointer clause mirroring its existing deletion-boundary deferral shape: the claim create runs through the body-side pick-time coverage probe window), and the PRE-WORK STAND-DOWN GATES compact mirror stays untouched (the probe is availability machinery, not a stand-down gate) [class: IMPLEMENTATION_REQUIRED]
- [x] Presence witness, failing before the edit and passing after, run from the executing worktree: `grep -c "pick-time coverage probe" agents/skills/maintenance/template-authoring.md` at least 2 (body paragraph and payload-duty pointer) [class: REPOSITORY_TEST]
- [x] Commit: `wip: pick-time coverage probe in the AUTHORING CLAIM gate` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Covering-origin arm and landing pre-check

Context surface: the plan's Terms, Task 1's probe, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/template-authoring.md`

- [x] The collision disposition in the body-side AUTHORING CLAIM gate paragraph gains the covering-origin arm, applied at probe time before the claim as a closed routing table over the deduplicated citers with arms (i) through (iv) below; no input outside the table is improvised at the mutation decision [class: IMPLEMENTATION_REQUIRED]
- [x] Arm (i): an active top-level citer, a deferred or rejected citer, or a citer whose dispositions are silent or ambiguous is real coverage or an ineligible surface; the target is skipped with the reason and citer recorded and the walk continued, never an autonomous header edit [class: IMPLEMENTATION_REQUIRED]
- [x] Arm (ii) basis: a completed citer whose dispositions keep the row open, established by the development-lesson #427 citer read with the quoted keep-open disposition lines and citer state recorded in the run report before deciding, takes the repair-and-proceed path [class: IMPLEMENTATION_REQUIRED]
- [x] Arm (ii) repair: the Cluster re-home with the dated moved-here note citing the authoring-time rule and the quoted basis is committed to the default branch in the primary checkout as one scoped corpus-fix commit through its ref-bound write transaction (merge/rebase checks and the done-lock boundary first, per the log-write discipline), before the ad-hoc worktree is created so the authoring branch inherits the fix [class: IMPLEMENTATION_REQUIRED]
- [x] Arm (ii) proceed: the probe is re-run from the primary root expecting the clean line before the claim; a later contradicting recorded decision restores the header shape through the origins lifecycle [class: IMPLEMENTATION_REQUIRED]
- [x] Arm (iii): a completed citer with real coverage takes the gate's printed remedy path and the target is skipped. Arm (iv): a final OUTCOME that is neither the mode's pass nor its conflict exit is re-derived from disk, and an unresolved re-derivation skips the target with the reason recorded, never read as pass or conflict [class: IMPLEMENTATION_REQUIRED]
- [x] Routing witness: given each routing input by name (active top-level citer; deferred citer; rejected citer; silent-or-ambiguous dispositions; completed keep-open citer; completed real-coverage citer; a probe OUTCOME that is neither pass nor conflict, exercised by an unreadable scratch producing the tool-error exit), expects the table's one disposition [class: IMPLEMENTATION_REQUIRED]
- [x] The landing pre-check lands in the same file's pre-landing duplicate-origin coverage gate clause (the sentence reading the gate's exit 1 as a refused landing), ahead of that clause's claim-deletion step: on an exit 1 naming a citer, the development-lesson #427 citer read runs first [class: IMPLEMENTATION_REQUIRED]
- [x] On a recorded keep-open disposition the landing pre-check commits the Cluster re-home to the default branch (primary checkout, ref-bound write transaction, before the landing critical section) and re-runs the primary-anchored gate expecting the clean line; only an unresolved read reaches the claim-deletion step and the stranding report (one-line lesson citation) [class: IMPLEMENTATION_REQUIRED]
- [x] Presence witnesses, failing before the edit and passing after, from the executing worktree: `grep -c "covering-origin arm"` and `grep -c "landing pre-check"` over `agents/skills/maintenance/template-authoring.md` each at least 1, with the first `landing pre-check` on the line of, and before, the literal `ensure this session's claim file is deleted` [class: REPOSITORY_TEST]
- [x] Commit: `wip: covering-origin arm and landing pre-check` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Plans-skill authoring-time rule and pointers

Context surface: the plan's Terms, Tasks 1-2, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`

- [x] In `agents/skills/plans/SKILL.md`, the Origins block shape paragraph carries the authoring-time rule: a deliberately-open row is cited on the plan's `Cluster:` line and never inside the scope-of-record block nor as the singular `Backlog origin:` line when the plan's dispositions keep the row open, with the coverage-extractor consequence named (all three header citation shapes parse into one coverage set) [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/plans/SKILL.md`, the Phase 0 Authoring claim bullet and the Plan Lifecycle landing closeout bullet each gain a one-line pointer naming the probe as part of the AUTHORING CLAIM procedure of record and the landing pre-check before a refusal stop report, referencing the template paragraph without restating it [class: IMPLEMENTATION_REQUIRED]
- [x] Presence witnesses, failing before the edit and passing after, from the executing worktree: `grep -c "deliberately-open row" agents/skills/plans/SKILL.md` at least 1, and the two pointer sentences pinned by `grep -q "pick-time coverage probe" agents/skills/plans/SKILL.md` and `grep -q "landing pre-check" agents/skills/plans/SKILL.md` [class: REPOSITORY_TEST]
- [x] Run `bash scripts/check_maintenance_pins.sh` and `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` from the executing worktree; expect exit 0 on both (the pins suite pins presence elements of the edited template paragraph; additions must not reword pinned lines) [class: REPOSITORY_TEST]
- [x] Commit: `wip: plans-skill authoring-time rule and pointers` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Probe rehearsal against the corpus origins (pre-edit behavioral proof)

Context surface: the plan's Terms, Task 1's recipe, and `## Standing constraints`.

Files:
- (none; read-only rehearsal against the primary checkout's plans directory)

Precondition: `git status --porcelain docs/history/plans docs/history/backlog` is empty in the primary checkout before the rehearsal; if a rehearsal output carries extra citer lines beyond the named archived plan (a parallel session's fresh plan), the extra lines are recorded and re-derived rather than treated as a rehearsal failure.

- [x] Build the scratch declaring file exactly per Task 1's recipe listing `docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md` and run the probe from the primary checkout with absolute paths; expect exit 1 with exactly two conflict lines naming `docs/history/plans/completed/2026-10-28-runtime-scripts-home-reconcile-and-retire.md` [class: REPOSITORY_TEST]
- [x] The first of those lines is labeled `(active)` and the second `(completed)` with its supersede-or-explicit-revival remedy; route on the second line, record the full output verbatim in the run record, and confirm the scratch is absent afterward [class: REPOSITORY_TEST]
- [x] Repeat for `docs/history/backlog/2026-10-13-codex-task-resource-cleanup.md` (expect the same two-line completed-citer shape) and for `docs/history/backlog/2026-10-09-friction-audit-quant-message-class-normalization.md` (expect the same shape); record all three rehearsal outputs in the run record (the session's run-record home under the gitignored reviews directory; its path is cited in the run summary; no commit is made for this task) [class: REPOSITORY_TEST]

### Task 5: Corpus corrections over the three named archived plans

Context surface: the plan's Terms, Task 3's rule shape, and `## Standing constraints`.

Files:
- `docs/history/plans/completed/2026-10-28-runtime-scripts-home-reconcile-and-retire.md`
- `docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md`
- `docs/history/plans/completed/2026-10-25-friction-audit-quant-message-class-normalization.md`
- `docs/history/backlog/2026-10-09-friction-audit-quant-message-class-normalization.md` *(deleted)*
- `docs/maintenance/document-registry.md`

(evidence-only read, no edit target: `scripts/friction_audit_quant.py`)

- [x] Re-derive each disposition from disk before editing; a newer recorded decision that contradicts this plan's authoring-time reading overrides it, with the contradicting evidence recorded in the run record and the affected disposition falling back to the row staying untouched and the deviation reported [class: IMPLEMENTATION_REQUIRED]
- [x] runtime-scripts-home-reconcile-and-retire: the `Backlog origin:` line becomes `Backlog origin: none` and the row moves to a `Cluster:` line with the dated moved-here note citing this plan and the authoring-time rule, mirroring the empty-diff completed plan's corrected header shape; its existing OPERATIONS_FOLLOW_UP disposition stays unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Re-home witness: given the post-edit header, expects a fresh worktree-rooted probe scratch for `docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md` to exit 0 with the line `coverage gate clean; no covering citer` and no `no origins` line [class: REPOSITORY_TEST]
- [x] codex-task-resource-cleanup: the same re-home shape for `docs/history/backlog/2026-10-13-codex-task-resource-cleanup.md`; witness: expects a fresh worktree-rooted probe to exit 0 with the same clean line [class: IMPLEMENTATION_REQUIRED]
- [x] friction-audit-quant-message-class-normalization code-evidence witness, before any edit: `grep -c "_message_class" scripts/friction_audit_quant.py` and a grep for the 1302 and 1308 literals both return at least 1 [class: REPOSITORY_TEST]
- [x] The normalization landed, so the completed friction-audit plan executes the origins lifecycle completion pass: a `## Disposition of migrated backlog items` fold recording the row as completed by the friction-audit-quant-message-class-normalization plan's own implementation lands on the archived plan and the row file is deleted [class: IMPLEMENTATION_REQUIRED]
- [x] Fold witness: given the post-edit tree, expects the row path absent at the backlog top level and the archived plan carrying the fold; no post-edit probe runs for this origin (a scratch declaring the deleted basename exits 1 naming the archived completed plan by design, the completed-state revival semantics, and that residue is accepted) [class: IMPLEMENTATION_REQUIRED]
- [x] Re-run the probe from the executing worktree for the two re-homed origins after the edits and record both outputs; expect exit 0 with the clean line on each [class: REPOSITORY_TEST]
- [x] Document-registry licensing: add registry rows for the two unregistered completed plans (state `completed` with the actual archive date and source path, each carrying a valid audit note so the licensed write takes the validator's override path) [class: IMPLEMENTATION_REQUIRED]
- [x] Add the `-origin` covered row recording the deleted friction-audit origin (the shape existing deleted-origin rows carry), and record the codex-task row's audit-note clearing as the standing follow-up the check-writes output names [class: IMPLEMENTATION_REQUIRED]
- [x] Registry witness: given this task's change set, expects `check-writes` to report no unprotected immutable write and `validate` to exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: re-home deliberately-open scope rows and fold the completed friction-audit row (coverage-gate corpus pass)` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- Origin row docs/history/backlog/2026-11-08-authoring-pick-time-coverage-probe.md: covered by this plan's execution landing 575cdf5e3 (the pick-time coverage probe in the AUTHORING CLAIM gate, Tasks 1-2); the row folds here and is deleted from the backlog top level in the same completion pass.
- Origin row docs/history/backlog/2026-11-08-coverage-gate-deliberately-open-scope-row.md: covered by this plan's execution landing 575cdf5e3 (the authoring-time Cluster: rule and the Task 5 corpus re-homes); the row folds here and is deleted in the same completion pass.
