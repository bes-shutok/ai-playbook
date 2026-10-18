# Plan: Close the plan-authoring done-closeout gap: baseline establishment, the completion-claims boundary, and the execute-plan stranded-input pre-pass

Backlog origin: docs/history/backlog/2026-10-07-plan-authoring-done-closeout.md (the PLAN-PROMPTS entry `plan-authoring-done-closeout` carries the operator-confirmed prompt; the bypass and stranding witnesses are recorded in the row)
Driving force: reliability
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-plan-authoring-done-closeout-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 0.6h

## Terms

- Closeout baseline: the `closeout-baseline.json` the migration helper's `capture` subcommand writes at `{tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-baseline.json` from the worktree root, enumerating the facts-resolved gitignored artifact dirs; its sanctioned sibling `closeout-baseline-skip.json` (`{"skip": true, "reason": "capture failed", "fallback": "scoped-copy enumeration at closeout"}`) records a failed capture so the later closeout degrades to an explicit scoped copy.
- Both-absent refusal: the migration helper's standing refusal when neither record exists in a worktree: `migrate` cannot run, an implicit empty baseline is never inferred, and a blanket copy of the ignored root is never taken (scripts/worktree_closeout_migrate.py; preserved unchanged by this plan).
- Reference contract: the paragraph in agents/skills/execute-plan/SKILL.md binding the plans authoring worktree setup, the done Run-placement consult, and the maintenance child payloads to the Worktree-first standard, each carrying "only its payload-critical literals"; today that list scopes the closeout-baseline capture to "execution payload only", the contract text this plan amends.
- Completion-claims boundary: the Final Step rule that a plan-authoring session reports completion only after the `done` closeout has verified (the owned-files-clean preflight and the gate-removal invocation ending `OUTCOME: pass`, plus the closeout migration's verified transfer); a review certification (`ready=yes`) is review-readiness evidence, never completion evidence, and each sanctioned deferral reports the deferral itself, not completion.
- Stranded-input pre-pass: the execute-plan routing at the missing-plan remedy that, when the readiness gate reports the plan missing AND any record of the plan's expected review series is absent from the primary reviews home, runs the plans skill's Final Step handoff for the authoring worktree (its owned-files-clean preflight, its baseline migration, its gate-removal) at the gate failure, before the run proceeds past it; input satisfaction composes after it from the updated base (rebase the run branch onto it, or cherry-pick the landed plan commit from base history).
- Authoring Final Step handoff: the plans skill's "Final Step: Run `done`" section as applied to an existing authoring worktree (the closeout, preflight, gate-removal, and removal binding it already defines); the pre-pass routes to it by reference, never by restating its steps.
- Primary reviews home: the resolved `{reviews_dir}` at the primary checkout, the corpus home the Worktree-first standard's transfer-in copies from.
- Readiness gate: execute-plan's Step 0.5 plan readiness gate (the hard gate before any task implementation).

## Why

The plans skill explicitly requires `done` after a plan is saved, review-ready, and the execution handoff offered, and commit `eacdef38` (2026-10-07, plan-detail-boundary authoring) bypassed it anyway: the plan file landed while its ignored review records stayed only in the authoring worktree's reviews directory. When `done` was then invoked, the closeout could not transfer them: the authoring setup had established neither `closeout-baseline.json` nor `closeout-baseline-skip.json`, and the migration helper's both-absent refusal (the correct guard) stopped the transfer. The same gap stranded a 2026-10-09 execute-plan invocation: the plan existed only as an untracked file in its authoring worktree and its review series was absent from the primary home, so the missing-plan remedy's required plan-authoring commit and the Phase 0 input transfer both had nothing to consume, and the run correctly stopped before a claim or worktree existed. The instruction is explicit and was bypassed once and stranded once, so the gap is structural, not attentional: authoring setup never establishes the closeout evidence the later closeout consumes; no rule distinguishes "review certified" from "closeout verified" in the session's own reporting, so a session can report completion on `ready=yes` alone; and the missing-plan remedy assumes a completed closeout instead of routing through the one that never ran. The origin row records both witnesses in full (docs/history/backlog/2026-10-07-plan-authoring-done-closeout.md Evidence).

## Gist & Examples

TLDR: the plans skill's Phase 0 setup establishes the closeout baseline (or the sanctioned skip sibling) before any gate or plan-file write, the Final Step gains the completion-claims boundary, execute-plan's missing-plan remedy routes stranded inputs through that Final Step handoff at the gate failure, before the run proceeds past it, and suite witnesses pin the capture path, the refusals, and the routing.

Before: an authoring session commits the plan directly and reports completion on review certification alone; the later closeout refuses for want of a baseline; an executor asked to run the plan stops stranded with no recovery path.

After: the same authoring setup carries the evidence the closeout consumes, the Final Step names what completion evidence is (and what it is not), a deferral is reported as a deferral, and a stranded execute-plan request completes the authoring closeout first, then proceeds through the existing remedies.

Edge cases: a capture failure writes the skip sibling and fails this step loudly as the degraded arm (reported degraded, setup complete, never proceeding as if a baseline exists); an explicit user deferral ("not yet" / "wait" / "I'll commit myself") and the execute-plan first-task-ownership deferral are honored and reported as deferrals, never blocked and never reported as completion; when only the plan is missing while its review records already sit in the primary home, the pre-pass does not apply and the existing cherry-pick remedy runs unchanged (the pre-pass requires the series gap); a partial series gap routes through the pre-pass too, its closeout migration completing the partial transfer; a live authoring claim stands the pre-pass down for operator disposition instead of a takeover; a missing claim record or zero header-matching worktrees stops the pre-pass for operator disposition (never an inferred worktree); a legacy stranded worktree holding neither baseline record bottoms out at the migration helper's both-absent refusal: the pre-pass reports the refusal and stops for operator disposition, never improvising a copy; a skip sibling is never fabricated without a failed capture, and it never substitutes for a baseline at the migration helper; configured `plans_dir` and the confirmed base branch are untouched; the separate pre-removal worktree gate (docs/history/plans/completed/2026-10-07-worktree-removal-migration-gate.md, the fence's completed-plan home) stays at its own later lifecycle boundary.

## Outcome

- plans SKILL.md Phase 0 authoring setup establishes the closeout evidence before any gate or plan-file write: from the worktree root run `capture --out {tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-baseline.json` over the facts-resolved dirs; on capture failure write the skip sibling and fail this step loudly; the worktree setup is incomplete until one of the two records exists.
- plans SKILL.md Final Step carries the completion-claims boundary: completion is reported only after the done closeout verified; a review certification (`ready=yes`) is review-readiness evidence, never completion evidence; both sanctioned deferral paths report the deferral.
- execute-plan SKILL.md's missing-plan remedy gains the stranded-input pre-pass (plan missing AND a review-series gap routes through the plans Final Step handoff at the gate failure, before the run proceeds past it; claim-header-anchored worktree selection with the live-claim stand-down; input satisfaction composes from the updated base, by rebase or cherry-pick from base history; the records-present case unchanged), and the Reference contract's payload-literal list stops scoping the closeout-baseline capture to execution only.
- Suite witnesses pin the load-bearing spans: the capture/skip/refusal executable contract backing the setup duty, and the pre-pass routing literals in execute-plan; the pins checker carries presence pins beside the new skill text.

Gate delta (machinery admission): no new gate, validator, lock, ledger, or schema field lands; all three changes are prose duties and routing on lifecycle steps that already exist (Phase 0 setup, the Final Step's done invocation, the missing-plan remedy), enforced in-session like their sibling duties, with presence pins only. The prevented incident is the witnessed bypass (`eacdef38`) and the witnessed stranding (2026-10-09); expected catch frequency is the bypass-and-stranding class at roughly one per authoring-lane regression (two witnesses across the lane's first week); the false-positive cost is bounded by the sanctioned skip sibling and the deferral-reporting arms (an operator who says "not yet" is honored, not blocked); review trigger is the next touch of the closeout contract. The byte-budget gate stays green (additions are within the seeded caps; no ratchet deletion is triggered).

## Assumptions

- The baseline path is the execute-plan run-dir convention `{tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-baseline.json` in authoring sessions too (PLAN_SLUG is the plan's canonical stem, fixed at Phase 0 per Task 1's slug rule: for a creation session it is the stem the dispatch entry and the claim file are keyed to, kept as the saved plan's filename stem, so capture, gate, and handoff resolve one run dir). Basis: the Final Step handoff, the done closeout, and the transfer-out contract all read exactly that literal (agents/skills/execute-plan/SKILL.md transfer-out paragraph); an authoring-specific path would fork the closeout contract this plan aligns with.
- The completion-claims boundary lives inside the Final Step section rather than a new section: the Final Step already owns the done invocation and its Skip-only-when list, so the rule attaches where the completion decision is made. Basis: the entry's "smallest enforceable completion boundary" and the section's existing skip arms (agents/skills/plans/SKILL.md, "Skip only when:").
- The pre-pass's second condition (review records absent from the primary reviews home) is what separates "stranded inputs" from the ordinary missing-plan case: the ordinary case (plan bytes on an unlanded branch, records already transferred) keeps the existing cherry-pick remedy unchanged. Basis: the 2026-10-09 witness had both absent (origin row Evidence), and the entry scopes the duty to a request "whose inputs are stranded in the authoring worktree".
- The pre-pass routes by instruction (run the plans skill's Final Step handoff for that worktree) and never copies the closeout steps into execute-plan: the Reference contract's own "update the consumers by reference, not by copying steps into them" rule governs. Basis: the contract paragraph in agents/skills/execute-plan/SKILL.md.
- The owned-files-clean preflight is named in the pre-pass only as part of the handoff it routes to (an authoring worktree may hold `wip:` checkpoint commits or uncommitted plan writes per D-10); the preflight's mechanics stay owned by the plans Final Step and the helper. Basis: the preflight already lives in the Final Step and the transfer-out (the wip-auto-checkpoint plan).
- Skill-text growth stays under the byte-budget caps; no deletion is triggered by the ratchet. Basis: `python3 scripts/skill_text_budget.py --check` green against the drafted text at authoring time.

Decision points requiring a grill: none remain (the entry fixes the rejected alternatives and the alignment targets; the baseline path, the boundary's home, and the pre-pass conditions are resolved above).

## Standing constraints

- Keep plans as authoring-policy owner, done as closeout caller, and execute-plan as the shared worktree-transfer contract; no lifecycle step is restated in a consumer body.
- Preserve the explicit user deferrals byte-identical: the Final Step's "not yet" / "wait" / "I'll commit myself" arm and the execute-plan first-task-ownership arm.
- Preserve configured `plans_dir`; never derive or hardcode it.
- scripts/worktree_closeout_migrate.py is byte-identical after this plan: the both-absent refusal is preserved, never weakened, and the `capture` subcommand is unchanged.
- The pre-pass never copies unrelated authoring-branch commits and never bypasses the confirmed base branch (the existing cherry-pick remedy's scope is unchanged where it applies).
- No machine-specific absolute paths in any edited file; no em-dashes in new lines; the hygiene scan stays green.
- Execution runs on a branch kept rebased onto current main at each fold. At each task start the executor re-verifies currency (pins suite exit 0 and no commit in `git log HEAD..main` touching this plan's anchor files) and on a red baseline, a vanished anchor, or a stale rebase stops and reports instead of proceeding; hand-reconciling PLAN-PROMPTS.md is never the repair.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the two skill texts carry the decided literals verbatim; the completion boundary names both deferral paths; the pre-pass requires both conditions and routes by reference to the plans Final Step handoff; the Reference contract's literal list matches the new payload split.
- regression safety: the two deferral arms are pinned byte-identical by the new Task 4 presence pins, the migration helper's capture-then-migrate acceptance and both-absent refusal stay witnessed by the cited existing WorktreeCloseoutTest fixtures, and the existing cherry-pick remedy keeps its pins-suite pin; `plans_dir` handling stays under the readiness gate's resolution; the pins suite, the hygiene scan, the em-dash added-lines scan, and the byte-budget gate pass.
- scope discipline: the change set is exactly the two SKILL.md files, the two test files, and the pins checker rows (plus this plan's landing riders).

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0.

**Ship when:**
- A plan-authoring session that skips `done` cannot report completion without contradicting the skill text, and an execute-plan request whose inputs are stranded in the authoring worktree recovers through the authoring closeout (when the worktree holds a baseline record or its sanctioned sibling) instead of stopping without a path, while a neither-record legacy worktree stops with the refusal named for operator disposition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code (skill text):**
- `agents/skills/plans/SKILL.md` (Task 1: the Phase 0 baseline establishment duty; Task 2: the Final Step completion-claims boundary)
- `agents/skills/execute-plan/SKILL.md` (Task 3: the stranded-input pre-pass at the missing-plan remedy; the Reference-contract literal list)

**Tests:**
- `scripts/test_execute_plan_worktree_bootstrap.py` (Task 4: the pre-pass routing span fixture)
- `scripts/test_worktree_closeout_migrate.py` (Task 4: the setup-capture, skip-sibling, and both-absent refusal pins)
- `scripts/check_maintenance_pins.sh` (Task 4: presence pins beside the new skill-text literals)

**Read-only (referenced, never edited):**
- `scripts/worktree_closeout_migrate.py` (the executable owner of capture, migrate, gate-removal, and the owned-files-clean preflight; byte-identical after this plan)
- `docs/history/plans/completed/2026-10-07-worktree-removal-migration-gate.md` (the pre-removal lifecycle fence's completed-plan home; untouched)
- `docs/history/plans/completed/2026-10-01-worktree-closeout-artifact-migration-and-residue.md` (the closeout migration contract of record)
- `agents/skills/done/SKILL.md` (the closeout caller; unchanged - the alignment reuses its existing transfer flow)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-07-plan-authoring-done-closeout.md (disposition: deleted in the execution landing rider, this plan the witness; the row's two witnesses, the eacdef38 closeout bypass and the 2026-10-09 stranding, are closed by Tasks 1-3 of this plan, verified by the execution review series 2026-10-11-plan-authoring-done-closeout-code-review-r1/r2, both validating hard with r2 verdict ready=yes)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## plan-authoring-done-closeout` (frozen under docs/tmp/authoring-claims/2026-10-10-plan-authoring-done-closeout.md; the authoring landing prunes it with the plans-root witness and the PLAN-PROMPTS-PRUNE receipt)

## Validation Commands

**Production:**
```bash
grep -qF 'the worktree setup is incomplete until one of the two records exists' agents/skills/plans/SKILL.md
   # exit 0: the Phase 0 establishment duty landed with its incompleteness boundary
grep -qF 'the saved filename stem, and the stem the readiness gate' agents/skills/plans/SKILL.md
   # exit 0: the capture slug rule landed (one stem across capture path, saved filename, gate, and handoff)
grep -qF 'and the closeout-evidence establishment duty above has produced one of its two records' agents/skills/plans/SKILL.md
   # exit 0: the adoption arm's completion sentence carries the establishment boundary
grep -qF 'that header match is the claim binding' agents/skills/execute-plan/SKILL.md
   # exit 0: the pre-pass worktree selection landed claim-header-anchored with its absence arms
grep -qF 'closeout-baseline-skip.json' agents/skills/plans/SKILL.md
   # exit 0: the sanctioned sibling is named where the capture duty lives
grep -qF 'is review-readiness evidence, never completion evidence' agents/skills/plans/SKILL.md
   # exit 0: the completion-claims boundary landed in the Final Step
grep -qF 'stranded-input pre-pass' agents/skills/execute-plan/SKILL.md
   # exit 0: the routing literal landed at the missing-plan remedy
grep -qF 'execution payload only, the closeout-baseline capture' agents/skills/execute-plan/SKILL.md; test $? -eq 1
   # exit 0: the old execution-only scoping of the capture is gone from the Reference contract
```

**Tests:**
```bash
python3 scripts/test_worktree_closeout_migrate.py   # exit 0, including the new production-shape setup-capture and skip-sibling inertness fixtures (capture-migrate acceptance and the both-absent refusal stay witnessed by the cited existing fixtures)
python3 scripts/test_execute_plan_worktree_bootstrap.py   # exit 0, including the new pre-pass routing span fixture
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )   # exit 0
python3 scripts/skill_text_budget.py --check   # exit 0, no cap breach, no ratchet debt
bash scripts/check-no-em-dash.sh added-lines --base <merge-base> -- agents/skills/plans/SKILL.md agents/skills/execute-plan/SKILL.md scripts/test_execute_plan_worktree_bootstrap.py scripts/test_worktree_closeout_migrate.py scripts/check_maintenance_pins.sh   # exit 0 on new lines only
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: the Phase 0 baseline establishment duty (plans SKILL.md)

Files:
- `agents/skills/plans/SKILL.md`

Primary class anchors:
- `Phase 0 authoring setup` in `agents/skills/plans/SKILL.md`, the worktree-setup paragraph ending "in before any gate or plan-file write" that sits before the already-provisioned recognition arm.

- [x] After the transfer-in sentence and before the already-provisioned recognition arm, add the closeout-evidence establishment duty as its own paragraph: the setup establishes the closeout baseline the Final Step's `done` closeout consumes, exactly per the execute-plan skill's bootstrap capture contract, whose block owns the invocation shape, the sibling body, and the guard semantics; the worktree setup is incomplete until one of the two records exists. [class: IMPLEMENTATION_REQUIRED]
- [x] The establishment paragraph's capture arm: from the worktree root run `capture --out {tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-baseline.json` over the facts-resolved dirs. [class: IMPLEMENTATION_REQUIRED]
- [x] The failure arm: on capture failure write the sibling `closeout-baseline-skip.json` per that block's failure arm and fail this step loudly as the degraded arm - the step is reported degraded, and because one of the two records now exists the setup is complete and the session proceeds (never as if a baseline exists), the closeout later degrading to the sanctioned scoped copy. [class: IMPLEMENTATION_REQUIRED]
- [x] The executable owner: scripts/worktree_closeout_migrate.py owns both records' semantics, and the establishment duty never fabricates a skip record without a failed capture nor infers an empty baseline. [class: IMPLEMENTATION_REQUIRED]
- [x] The establishment paragraph's slug rule: the plan slug in the capture path is fixed for every session shape - a creation session fixes the canonical plan slug before setup completes (the stem the dispatch entry and the authoring claim file are already keyed to, recorded in the claim) and keeps it as the saved plan's filename stem. [class: IMPLEMENTATION_REQUIRED]
- [x] The slug rule's resolution guarantee: the capture path's `PLAN_SLUG`, the saved filename stem, and the stem the readiness gate and the Final Step handoff later resolve are one and the same. [class: IMPLEMENTATION_REQUIRED]
- [x] The adoption-arm reconciliation: the already-provisioned recognition arm's completion sentence is amended to "treat the worktree setup as complete once the adoption check passes and the closeout-evidence establishment duty above has produced one of its two records", so the establishment duty runs identically on the adoption path. [class: IMPLEMENTATION_REQUIRED]
- [x] The reverse Integration Points record: the plans skill's Integration Points section ("With `execute-plan` skill") gains the record that execute-plan's missing-plan remedy routes stranded inputs through this skill's Final Step handoff (the stranded-input pre-pass), by reference. [class: IMPLEMENTATION_REQUIRED]

### Task 2: the Final Step completion-claims boundary (plans SKILL.md)

Files:
- `agents/skills/plans/SKILL.md`

Primary class anchors:
- `Final Step: Run done` in `agents/skills/plans/SKILL.md`, the section owning the `done` invocation, the removal preflight, and the Skip-only-when list this plan extends.

- [x] In the Final Step, add the completion-claims rule beside the Skip-only-when list: this session reports completion of the plan-creation work only after the `done` closeout has verified - the owned-files-clean preflight and the gate-removal invocation ending `OUTCOME: pass`, plus the closeout migration's verified transfer of the plan and review artifacts to their primary homes. [class: IMPLEMENTATION_REQUIRED]
- [x] The same rule names the degraded evidence and the hierarchy: in the skip-sibling degraded state the scoped-copy arm's per-file digest verification is the boundary's transfer evidence; a review certification (`ready=yes`) is review-readiness evidence, never completion evidence, and is never reported as completion. [class: IMPLEMENTATION_REQUIRED]
- [x] The same rule names the deferrals: each sanctioned deferral (the user saying "not yet" / "wait" / "I'll commit myself"; the execute-plan first-task-ownership fold) is honored and reported as the deferral it is, never as completion. [class: IMPLEMENTATION_REQUIRED]

### Task 3: the stranded-input pre-pass and the Reference-contract literal (execute-plan SKILL.md)

Files:
- `agents/skills/execute-plan/SKILL.md`

Primary class anchors:
- `Transfer-in implementation` in `agents/skills/execute-plan/SKILL.md`, the fence-resolution paragraph carrying the missing-plan remedy sentence ("When the readiness gate fails with the readiness validator's missing-plan error ...") this plan extends.
- `Reference contract` in `agents/skills/execute-plan/SKILL.md`, the payload-literal list paragraph ("...and, execution payload only, the closeout-baseline capture") this plan amends.

- [x] Extend the missing-plan remedy with the stranded-input pre-pass trigger: when the readiness gate reports the plan missing AND any record of the plan's expected review series (every round record plus its `.stats.json` sidecar) is absent from the primary reviews home, the plan-authoring closeout never ran or never completed, and the remedy routes through the plans skill's Final Step handoff for the authoring worktree. [class: IMPLEMENTATION_REQUIRED]
- [x] The routing runs at the gate failure, before the run proceeds past it, and takes the plans skill's own steps (its owned-files-clean preflight, its baseline migration, its gate-removal), run per that skill - never restated or improvised as a copy here. [class: IMPLEMENTATION_REQUIRED]
- [x] Worktree selection: enumerate `git worktree list` and select the single worktree whose plan file at the resolved plans dir carries the header literal `Authoring claim: <claim path> (session <session id>)` naming this claim record - that header match is the claim binding, and branch-name or directory-name similarity alone never selects. [class: IMPLEMENTATION_REQUIRED]
- [x] Selection absence arms: when the claim record is absent, no worktree matches, or more than one worktree matches, the pre-pass reports the unresolvable selection and stops for operator disposition, never selecting an inferred worktree; a worktree whose plan file already dropped the header at its certification commit is a zero-match case by design and bottoms at the same disposition. [class: IMPLEMENTATION_REQUIRED]
- [x] Takeover guard: run the claim duty's fresh-foreign-claim refusal first (the AUTHORING CLAIM paragraph in agents/skills/maintenance/template-authoring.md, the plans skill's Phase 0 procedure of record), and on a fresh (live) claim stand down for operator disposition instead of closing out; a raced second closeout reports and stops. [class: IMPLEMENTATION_REQUIRED]
- [x] Post-handoff composition: after the handoff, the missing-plan input is satisfied from the updated base - rebase the run branch onto it so the landed plan arrives, or cherry-pick the landed plan commit from base history - and the authoring branch's deletion defers while a consuming run still needs it; when every record of the review series is already present in the primary home, the pre-pass does not apply and the existing remedy runs unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the Reference contract's payload-literal list: the closeout-baseline capture is no longer "execution payload only" - the plans authoring setup now carries the same capture per its Phase 0 establishment duty - keeping the paragraph's by-reference rule and every other literal intact. [class: IMPLEMENTATION_REQUIRED]

### Task 4: witnesses and presence pins

Files:
- `scripts/test_execute_plan_worktree_bootstrap.py`
- `scripts/test_worktree_closeout_migrate.py`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `WorktreeBootstrapTest` in `scripts/test_execute_plan_worktree_bootstrap.py`, the suite class the routing span fixture joins (new methods join the existing class and naming style; the module main block stays last).
- `WorktreeCloseoutTest` in `scripts/test_worktree_closeout_migrate.py`, the suite class the setup-capture, skip-sibling, and both-absent refusal fixtures join (the module main block stays last).
- `pin` in `scripts/check_maintenance_pins.sh`, the helper whose rows gain the three presence pins beside the new skill-text literals.

- [x] In `scripts/test_execute_plan_worktree_bootstrap.py`, add a test method asserting the execute-plan SKILL.md missing-plan remedy region carries the pre-pass routing literals (both conditions plus the plans Final Step handoff reference) and that the Reference contract no longer scopes the closeout-baseline capture to execution payload only; skill-text drift fails the test. [class: REPOSITORY_TEST]
- [x] In `scripts/test_worktree_closeout_migrate.py`, add the two genuinely new fixtures the Phase 0 duty relies on: the production-shape setup-capture (capture with `--out` inside the facts-resolved tmp run dir, then `migrate` accepts that baseline) and the skip-sibling inertness pin (a written `closeout-baseline-skip.json` never substitutes for a baseline at the helper - the refusal stands, naming the implicit-empty-baseline message). [class: REPOSITORY_TEST]
- [x] Cite `test_migrate_copies_new_and_modified_with_checksum_verify` (capture-then-migrate acceptance) and `test_migrate_missing_baseline_fails_loud` (the both-absent refusal with nothing copied) as the already-landed witnesses for those two contract points. [class: REPOSITORY_TEST]
- [x] In `scripts/check_maintenance_pins.sh`, add presence pins beside the new literals: the plans Phase 0 incompleteness boundary literal, the plans completion-claims literal, and the execute-plan stranded-input pre-pass literal. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the two deferral-arm pins byte-identical: the plans Final Step literal `The user explicitly says "not yet" / "wait" / "I'll commit myself"; honor that and stop.` and the first-task-ownership literal from the plans Final Step Skip-only-when list in agents/skills/plans/SKILL.md ("say so and let `execute-plan` own the first commit") - pin rows are re-derived from the file bytes, never from this plan's quotation. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full `## Validation Commands` block green on the executed tree and record the outputs in the execution manifest. [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-07-plan-authoring-done-closeout.md: deliberately folded into this completed plan (its two witnesses are the plan's Why section and the landed Tasks 1-3) and the per-item file deleted in the execution landing rider; this plan is the witness.
