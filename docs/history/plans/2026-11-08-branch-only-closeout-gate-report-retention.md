# Plan: branch-only closeout terminal completion receipt

Backlog origin: docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-branch-only-closeout-gate-report-retention-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Executed: no
Language guidelines: projects/.ai-playbook/python_guidelines.md
Authoring claim: branch-only-closeout-gate-report-retention.md (session sess_13f5baac-fc0c-47a9-98b7-ee5ffb2c5b64)

## Terms

- branch-only closeout: a `worktree_closeout_migrate.py gate-removal` run in `--branch` mode that adjudicates a branch ref with no linked worktree (the worktree was already removed); nothing is removed and a pass authorizes the operator's branch removal.
- terminal completion receipt: the record this plan adds to the existing closeout migration manifest, written when a branch-only pass adjudicates the branch accounted, bound to the recorded branch, the one proven tip OID, the verdict, and a timestamp.
- migration manifest: `closeout-migration.json` under the facts-resolved `docs/tmp/execute-plan/<session-slug>/` home; the append-only per-session surface `_gate_branch_closeout` already reads through `_resolve_closeout_reference_state`.
- disposition verdicts: the `status` values `_gate_branch_closeout` returns: `ancestry-accounted`, `exact-tree-accounted` (the accounted shapes), `retained`, `unknown-ref`, `ref-changed`, `unbound`.
- retention window: the done-session gate-reports bounded home rule in `_prune_done_session_markers` (scripts/done_sweep_gates_lib.py): a report inside the window stays, one past it is removed, an unreadable mtime is kept.
- unknown-ref recovery: a later adjudication of a branch ref that no longer resolves; today it yields the `unknown-ref` disposition with no recorded completion witness.
- receipts section: the dedicated top-level `terminal_completion_receipts` list in the migration manifest JSON, the receipt's only home; none of the three current manifest readers (`_gate_branch_closeout`, `_closeout_reference_hold`, `_proof_family_session_decision`) parses it as a branch record, and a receipt is never appended to the `branch` list (an append there would be adjudicated as the latest branch record and would shift the run-attribution index binding).
- section marker: the presence of the `terminal_completion_receipts` key in a manifest; every branch-only adjudication stamps it (an empty list when no receipt entry is written), so its presence is the only signal telling a branch-only manifest from a worktree-completed one; a manifest without the key (worktree-completed, or branch-only-adjudicated before this plan: the legacy grandfathering) keeps today's retention.

## Why

A branch-only closeout pass authorizes the operator to remove the branch but records no durable completion anywhere, and the retention window prunes an aged report whose session manifest contributes nothing to the referenced set, which every branch-only manifest does (its recorded branch matches no registered worktree), so branch-only reports are pruned on age with no completion consult while unresolved recoveries can still need them, and no reader can prove a completed closeout terminal. Witnessed 2026-11-08: a branch-only closeout left a migrated report marked verified while its destination was absent and no recoverable bytes existed anywhere, and the gate retained the branch with no removal command (origin row; r11 finding implementation#missing-state-transition).

## Gist & Examples

TLDR: branch-only closeout passes stamp a terminal completion receipt into the existing migration manifest and the gate-report retention reader consumes it, so report pruning waits for proof of actual completion; code-quality, because a pruning decision must never guess between success and unresolved recovery.

Before (today): a run finishes its branch-only closeout with an `ancestry-accounted` disposition; the pass prints its authorization lines and exits 0; the manifest carries no completion record. The operator removes the branch. When the retention window later reaches the run's verified gate report, the reader cannot tell whether the branch closeout completed, and the witnessed incident class is the result: a verified report whose destination is gone and whose bytes survive nowhere, with the branch retained and no removal command.

After (this plan): the same pass appends one terminal completion receipt (recorded branch, proven tip OID, verdict, timestamp) into the manifest's `terminal_completion_receipts` section, and every other branch-only adjudication stamps that section present and empty. The retention window consults the section on manifests that carry it: an aged report prunes only when the section carries an entry whose branch equals the manifest's recorded branch and the branch ref no longer resolves; a stamped section with no matching entry, or a receipt whose branch ref still resolves, keeps the report for recovery (today such reports prune on window age with no completion consult). A manifest without the section (worktree-completed, or adjudicated before this plan) keeps today's unreferenced age pruning. The worktree-mode retention behaviors, the missing-destination refusal, and the bounded age pruning for unrelated reports are preserved unchanged.

Edge cases named: a receipt whose branch ref still resolves must not enable pruning (authorization is not completion); a manifest with no receipt must not change any existing worktree-mode retention behavior; a repeated branch-only pass must not duplicate the receipt; an unresolved `unknown-ref` attempt writes no receipt entry (it stamps the empty section, so its reports stay retained while the operator restores the ref and retries, the origin's Expected recovery exit).

## Outcome

Branch-only closeouts become distinguishable from unresolved recoveries by durable state that already exists, so gate reports are retained exactly while recovery can still need them.

- A branch-only pass leaves a machine-readable completion witness bound to the exact branch and the proven OID it verified.
- The retention window prunes a report of a section-carrying (branch-only-adjudicated) manifest only after that witness exists and the branch ref is confirmed gone.
- Unresolved branch-only attempts keep their verified reports and their retained branches through recovery, a deliberate change from today's prune-on-age-without-consult.

Gate delta: +1 manifest record population (the terminal completion receipt appended to the existing `closeout-migration.json`'s `terminal_completion_receipts` section on accounted branch-only passes, and the section stamped present and empty on every other branch-only adjudication) and +1 checked condition on the retention window's referenced-set arm (manifests carrying the section consult the receipt instead of contributing nothing to the referenced set); no new gate, validator, lock, ledger, or required ceremony, per the origin's machinery admission; the addition is priced by the origin's own simplification-first ordering (Task 1 must first prove no existing signal suffices before the receipt lands) and by the completed-integrity-failure witness above (the 2026-11-08 refusal and the r11 finding are recorded failures of the current shape); no refusal is removed and the three fix-class defaults are inapplicable: the sanctioned exits already exist (origin Problem records missing durable state, not a missing exit), there is no false positive to remove (origin Expected explicitly preserves the missing-destination refusal), and the simplify-the-flow alternative is this plan's own Task 1 (origin Suggested investigation: trace existing records for a reusable signal first); admission fields: expected catch frequency is every aged branch-only session report at its window boundary (a small population: branch-only closeouts are rare), the false-positive cost is a report retained longer while its closeout is unresolved (bounded by the operator resolving the closeout), and the admission review date is 2027-02-08 per the origin's Machinery admission; the missing-destination refusal and bounded age pruning are preserved unchanged.

## Assumptions

- assume the receipt lives in the existing closeout migration manifest under the dedicated top-level `terminal_completion_receipts` section (see Terms), never in the `branch` list; basis: the manifest is the surface `_gate_branch_closeout` already reads via `_resolve_closeout_reference_state`, but the `branch` list is adjudicated as branch records with `len(records) - 1` run-attribution stamping, the three current manifest readers parse only branch records or `records[0]`, and the origin's machinery admission rejects a second registry or ledger; the receipt append is the append-only discipline of that section, not a branch-row append.
- assume the reader-side terminal condition is: the receipts section carries an entry whose `branch` equals the manifest's recorded branch AND `_branch_ref_resolves` reports that branch gone; the receipt's `oid` is recorded for audit and is never compared on the reader side (the ref is gone when this leg reads), the resolution of the shape choice the r1 review requested; basis: the disposition `_gate_branch_closeout` returns binds branch and proven OID at pass time, and there is no live ref left to compare against.
- assume the retention reader resolves the branch ref through the existing `_branch_ref_resolves` helper on the sweep side; basis: the helper exists at scripts/done_sweep_gates_lib.py:4670 for exactly this target-and-branch resolution shape.
- assume the retention window's worktree-mode behaviors (missing-destination refusal, expired-destination reports-only pass, bounded age pruning for unrelated reports) are preserved; basis: origin Expected and the two named characterization tests in scripts/test_worktree_closeout_migrate.py (`test_missing_artifact_guard_holds_worktree_removal`, `test_expired_gate_report_destination_reports_only_and_passes`); the deliberate change is confined to manifests carrying the section marker (see Terms), which today do not exist; a branch-only manifest and a worktree-completed manifest are otherwise byte-indistinguishable to `_closeout_reference_hold` (one continue arm, no mode field), so the marker is the recorded discriminator design, chosen over a uniform keep arm (which flips the existing post-removal pins and retains ref-gone receipt-less reports forever) and over a receipts-only keep (which no real unresolved pass exercises); the existing pins `test_docs_tmp_sweep_retention_ends_after_worktree_removal` and `test_done_session_retention_unknown_ref_recovery_and_post_removal_prune` in scripts/test_done_sweep_gates_lib.py stay green because their fixtures never carry the section, and legacy branch-only manifests adjudicated before this plan keep today's prune.
- assume a stamped-section report retained after an `unknown-ref` adjudication exits through the origin's Expected recovery: the operator restores the ref and retries, an accounted pass writes the receipt, and the later branch removal makes the report prunable; basis: origin Expected ("preserve each verified referenced report while the operator resolves the ref and retries"), and the Gate delta prices the bounded false-positive cost.
- assume an unreadable or shape-unsupported manifest keeps today's warning arm (its verified destinations stay age-prunable), and only a readable manifest whose `terminal_completion_receipts` value is malformed (not a list, or an entry without a string `branch`) degrades to retention; basis: the read-error and shape-error arms at the top of the referenced-set loop in scripts/done_sweep_gates_lib.py already decide the unreadable case and are not this plan's scope.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: on a section-carrying manifest a prunable report requires receipt plus confirmed ref absence; every other state of that manifest retains the report (both failure directions covered by tests).
- compatibility: the two named characterization tests, the two existing post-removal sweep pins named in Assumptions, and both touched suites stay green with no semantics change on worktree-mode paths or on manifests without the section.
- simplicity: no second registry, ledger, or new gate; the receipt reuses the manifest and the helpers the gate already uses.

**Done when:**
- Both touched suites pass (the two test files named in Validation Commands).
- A branch-only pass with an accounted disposition writes exactly one receipt bound to branch, proven OID, verdict, and timestamp, named in the pass output.
- An unresolved branch-only attempt (unknown-ref) writes no receipt entry, stamps the section present and empty, and the retention window retains the run's reports.
- A receipt whose branch ref still resolves does not enable pruning.
- The missing-destination refusal and the expired-destination reports-only behavior are unchanged (characterization pins green).

**Ship when:**
- none stated (no deployed or cross-team condition; consumer repositories pick this up with the next vendored-asset sync of the scripts).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- scripts/worktree_closeout_migrate.py (Task 4)
- scripts/done_sweep_gates_lib.py (Task 4)

**Tests:**
- scripts/test_worktree_closeout_migrate.py (Task 2)
- scripts/test_done_sweep_gates_lib.py (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the worktree-mode migrate and gate-removal paths' existing semantics; reason: this plan changes only the branch-only pass's recording and the retention window's terminal leg, and origin scope arm (4) freezes the neighboring behaviors
- any second registry, ledger, or standalone completion store; reason: origin machinery admission rejects it

## Validation Commands

Validation preamble (authoring-time record; per-round `Round-start state for rN` lines are commit provenance, the certification wall of record is the seal file):
- authoring-time mechanical audit (rule 22): bash -n over the Validation Commands block: OK (2026-11-08T09:2xZ; no pinned-span pin-vs-text contract in this plan)
- em-dash touched scan over the plan bytes: OUTCOME: pass, 0 hits (authoring-time self-check)
- public hygiene scan: OUTCOME: pass (2026-11-08)
- readiness pre-round gate: PRE-ROUND OK structural checks clean, OUTCOME: pass (2026-11-08)

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py scripts/test_done_sweep_gates_lib.py -q || { echo "suites failed"; exit 1; }
bash scripts/check-no-em-dash.sh added-lines --base main || exit 1
bash scripts/scan-public-hygiene.sh || exit 1
```

### Task 1: Trace the branch-only terminal-state gap with live probes

Context surface: the plan's Terms, this task.

Files:
- scripts/worktree_closeout_migrate.py (probe-only evidence)
- scripts/done_sweep_gates_lib.py (probe-only evidence)

Primary class anchors:
- `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py`

- [ ] Probe the current pass shape [class: REPOSITORY_TEST]: given a scratch git fixture with a migration manifest bound to a local branch and a branch-only `gate-removal --branch` pass over an accounted disposition, expects exit 0, the authorization lines printed, and the manifest file byte-unchanged (no completion record written anywhere)
- [ ] Probe the unknown-ref shape [class: REPOSITORY_TEST]: given the same fixture with the branch ref deleted before a second branch-only pass, expects the `unknown-ref` disposition and no manifest mutation
- [ ] Confirm today's retention polarity by direct reading [class: REPOSITORY_TEST]: expects `_closeout_reference_hold` adds referenced destinations only when a registered worktree matches the recorded branch (a no-worktree-match manifest contributes nothing; the deferral comment names the shape), and `_prune_done_session_markers` prunes an aged report the referenced set does not cover; the retention side reads manifests directly and never invokes gate-removal
- [ ] Record the trace verdict in the task log [class: REPOSITORY_TEST]: the probes name the smallest existing-state candidate (if any) or confirm the receipt is the fallback the origin prescribes; the verdict is the Gate delta's Task-1 pricing evidence
- Fixtures run inside `mktemp -d` with explicit teardown; probes mutate no tracked file.

### Task 2: RED tests for the terminal completion receipt

Context surface: the plan's Terms, this task, and the Task 1 trace verdict.

Files:
- scripts/test_worktree_closeout_migrate.py *(tests added)*

Primary class anchors:
- `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py`

- [ ] RED: receipt on accounted pass [class: REPOSITORY_TEST]: given a branch-only pass over an accounted disposition (`ancestry-accounted` or `exact-tree-accounted`), expects the manifest's `terminal_completion_receipts` section gains exactly one terminal completion receipt carrying the recorded branch, the proven tip OID, the verdict, and a timestamp, and the pass output names the receipt (fails today: no record is written)
- [ ] RED: section stamped without receipt on unresolved attempts [class: REPOSITORY_TEST]: given branch-only passes over an `unknown-ref` and a `retained` disposition, expects the manifest carries the `terminal_completion_receipts` section present and empty, with no receipt entry appended (authorization is not completion; fails today on the stamp leg: no section is written)
- [ ] RED: no duplicate receipt on re-run [class: REPOSITORY_TEST]: given the accounted pass run twice, expects still exactly one receipt (green-at-RED via today's absence; must stay exact-count green after Task 4)
- [ ] Run → expect RED: the receipt and stamp tests fail on the missing record while the duplicate-receipt pin, the two named characterization tests, and the rest of the suite stay green [class: REPOSITORY_TEST]
- [ ] Commit: `test: red tests for branch-only closeout terminal receipt` [class: REPOSITORY_TEST]

### Task 3: RED tests for retention consumption

Context surface: the plan's Terms, this task.

Files:
- scripts/test_done_sweep_gates_lib.py *(tests added)*

Primary class anchors:
- `_closeout_reference_hold` in `scripts/done_sweep_gates_lib.py`
- `_prune_done_session_markers` in `scripts/done_sweep_gates_lib.py`
- `_branch_ref_resolves` in `scripts/done_sweep_gates_lib.py`

Today's measured polarity (verified at r1 against `_closeout_reference_hold`'s referenced-set loop and `_prune_done_session_markers`' `prune_within_hold`, where a report in the returned referenced set is retained and every other aged report prunes): a no-worktree-match session manifest contributes nothing to the referenced set, so its aged reports prune with no completion consult. Every fixture below is a no-worktree-match manifest; the section marker (see Terms) is the only byte that differs. Tests 1-3 and 5 are RED today for the reason each names; test 4 is the one green-at-RED pin.

- [ ] RED: prunable by receipt consult [class: REPOSITORY_TEST]: given a manifest whose section carries a hand-crafted receipt (an entry whose `branch` equals the manifest's recorded branch) whose branch ref no longer resolves, expects the aged report prunes AND the consulted justification is the receipt section (fails today on the discriminating leg: the report prunes today, but with no receipt consulted)
- [ ] RED: receipt with live ref retains [class: REPOSITORY_TEST]: given a manifest whose section carries a receipt whose branch ref still resolves, expects the report stays retained (fails today: the report prunes on age)
- [ ] RED: stamped empty section retains [class: REPOSITORY_TEST]: given a manifest whose section is present and empty, expects the report stays retained through recovery (fails today: the report prunes on age; the witness for Outcome bullet 3)
- [ ] Pin: no section keeps today's prune [class: REPOSITORY_TEST]: given a manifest without the `terminal_completion_receipts` key, expects today's aged prune (the worktree-completed and legacy-grandfather shape; green-at-RED, must stay green after Task 4 beside `test_docs_tmp_sweep_retention_ends_after_worktree_removal` and `test_done_session_retention_unknown_ref_recovery_and_post_removal_prune`)
- [ ] RED: malformed section retains [class: REPOSITORY_TEST]: given a readable manifest whose `terminal_completion_receipts` value is not a list, and separately one whose list holds an entry without a string `branch`, expects the report stays retained in both (fails today: the report prunes on age)
- [ ] Run → expect RED: tests 1-3 and 5 fail today on today's receipt-blind prune while test 4 and the existing suite (the unreferenced aged-pruning pin, the two named post-removal pins, and the worktree-mode holds) stay green [class: REPOSITORY_TEST]
- [ ] Commit: `test: red tests for retention terminal consumption` [class: REPOSITORY_TEST]

### Task 4: GREEN implementation of receipt and consumption

Context surface: the plan's Terms, Tasks 2 and 3.

Files:
- scripts/worktree_closeout_migrate.py
- scripts/done_sweep_gates_lib.py

Primary class anchors:
- `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py`
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`
- `_closeout_reference_hold` in `scripts/done_sweep_gates_lib.py`
- `_prune_done_session_markers` in `scripts/done_sweep_gates_lib.py`

- [ ] `cmd_gate_removal` delivers `terminal receipt recording`: given a branch-only pass whose disposition is accounted, expects one receipt appended into the manifest's `terminal_completion_receipts` section (never the `branch` list, so no branch record or attribution stamp shifts), idempotent on re-run (a repeated pass refreshes, never duplicates), with the proven OID captured at adjudication time [class: IMPLEMENTATION_REQUIRED]
- [ ] `cmd_gate_removal` delivers `section stamping`: given a branch-only pass whose disposition is not accounted, expects the section stamped present (empty when it holds no entry) and no entry appended [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given a manifest append or stamp failure, expects the branch-only pass fails closed (refusal with preservation, the authoring-strand arm's precedent) and never reports completion without the receipt on disk [class: IMPLEMENTATION_REQUIRED]
- [ ] `_closeout_reference_hold` delivers `terminal consumption`: given a no-worktree-match manifest carrying the section marker whose terminal condition holds (a section entry with branch equality and `_branch_ref_resolves` reporting the branch gone), expects it contributes nothing, so the aged report prunes; without the marker it likewise contributes nothing (today's prune, unchanged) [class: IMPLEMENTATION_REQUIRED]
- [ ] `_closeout_reference_hold` delivers `recovery retention`: given a marker-carrying manifest whose terminal condition does not hold, or whose section value is malformed, expects its verified destinations added to `referenced`, so `prune_within_hold` retains the report through recovery; the read-error and shape-error arms stay unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the new tests from Tasks 2 and 3 pass and both full suites pass (the interim RED of Tasks 2 and 3 flips here; no later task pends) [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `feat: branch-only closeout terminal completion receipt and retention consumption` [class: IMPLEMENTATION_REQUIRED]
