# Plan: landing-deleted-unclaimed-execution-ready-plan

- Date: 2026-10-11
- Execution budget: 2h (per directive D-8 this declares 2 full-panel review rounds)
- Change class: guard-widening inside two existing guard surfaces plus one additive pre-flight report leg; no new gate, validator, lock, ledger, or ceremony

## Terms

- Protected plans-root path: a path under the resolved plans roots and outside the completed/, deferred/, and rejected/ state directories; the class `claim_fence_protected` already scans (`scripts/reverse_squash_guard.py`).
- Claim-free window: the span after the authoring-claim teardown deletes the claim and before the plan is executed, archived, or rejected; a deletion in this window passes the fence silently today (the no-claim arm in `cmd_check_claim_fence` continues without a finding).
- Unclaimed-deletion warning leg *(new)*: the fence class that reports a protected deletion no live claim names and no sanction covers, printing a `claim-fence-warning:` line (the line carries the path and the deleting commit; a follow-on line names the sanctioned exits) while the guard's exit stays 0.
- Rejected-state sanction *(new)*: a same-commit rename whose post-side path sits under a rejected/ state directory with the deleted basename; it sanctions the deletion exactly like the completed-archive twin.
- Landing-boundary leg *(new)*: `cmd_check_landing`'s sanction-aware report, inside its existing stale-base branch, of every protected plans-root path present at the target tip and absent from the source tree whose same target-to-source scan carries no completed-archive or rejected-state twin; the fresh-base early return and the mode's exit semantics are unchanged.
- Arm-boundary matrix: at the landing boundary the checkable sanctions are the completed-archive twin and the rejected-state move (both tree-derivable from the target-to-source name-status records); the Plans-Deletion-Ack trailer is a sweep-fence-only arm because it lives in a commit message that does not exist pre-commit.
- Promotion: the registry-governed flip that turns the sweep-fence warning leg into a refusal after the first true catch, scoped to the sweep leg (the landing-boundary leg stays a naming enrichment inside the stale-base refusal, which is the boundary's fence); the flip is one commit updating the guard posture, the done-skill span sentence, the warning-literal pins, and the registry row together; review 2026-12.

## Why

A stale-base tree-commit landing carries absence as deletion: landing 617d5b0ee deleted the r5-certified, never-executed investigate-renewal-trigger plan from the plans root, and no gate in either session flagged it; the restore commit fdee5ce9e recovered the file byte-equal from the cycle-10 landing commit 8f42c3fcc, but detection was hand-inspection hours later (docs/history/backlog/2026-10-10-landing-deleted-unclaimed-execution-ready-plan.md). The fence of record predicates on a live claim naming the deleted path, and the authoring-claim teardown deletes the claim by design, so the execution-ready claim-free window is unfenced by construction.

## Gist & Examples

The fence keeps its claimed-deletion refusal byte-identical and gains a warning class beside it: a protected deletion with no naming claim and no sanction (completed-archive twin, rejected-state move, Plans-Deletion-Ack trailer) prints a warning whose first line carries the path and the deleting commit and whose follow-on line enumerates the sanctioned exits, and the guard still exits 0. The landing judge gains the same class inside its existing stale-base branch, sanction-aware: every protected path present at the target tip and absent from the source tree with no twin in the same target-to-source scan is reported naming the merge base; the witnessed incident shape (a foreign plan added to the base branch after the worktree forked) is exactly this predicate, and a landing archiving its own plan prints nothing for it because the same-scan twin sanctions it. The probe and the execute-plan wiring keep their existing contracts: the boundary's fence is the stale-base refusal that already fires, which this leg enriches with the claim-free naming; the entry's rehearsal demand ("refuses at the pre-flight") is satisfied by that pre-existing refusal, and the new leg lands warning-only beside it. At promotion, one flip turns the sweep-fence warning class into refusals with the same routing the claimed class uses (own-commit refusals fail, foreign-commit refusals report); the landing-boundary leg stays a naming line. Residual coverage, named: a land-mode invocation that skips the probe and the execute-plan judge carries no landing-boundary signal, and a fresh-based landing that deletes a foreign plan reaches neither boundary leg; the sweep-fence leg is the backstop over committed ranges at the next done run, and the tree-commit landing class from the incident remains outside both boundary surfaces.

## Outcome

The claim-free deletion class is fenced in warning posture at the sweep boundary (`check-claim-fence`) and named at the landing boundary (`check-landing`'s stale-base branch); the probe and the execute-plan wiring keep their existing contracts untouched. Gate delta: no new gate, ledger, or ceremony - both legs are predicates inside existing guard surfaces, and the promotion path is the pre-registered registry row. Machinery admission: incident = docs/history/backlog/2026-10-10-landing-deleted-unclaimed-execution-ready-plan.md; expected catch frequency = rare but data-destroying (any stale-base landing over a foreign unclaimed plan); false-positive cost = bounded, because landings that own their deletions already name twins, rejected moves, or acks, and the fence's live claim read (the primary checkout's claim directories at sweep time) can flap with a peer creating or deleting a claim mid-sweep - a flap is repaired by bounded retry or park-for-operator, never by editing the gate mid-lane; sunset = warning-only at landing, promotes on its first true catch, review 2026-12. Ledger kin row re-derived this run from `python3 scripts/gate_liveness_ledger.py show` (2026-10-11): `reverse-squash-guard: catches=1 incidents=2 overrides=1 time_lost_minutes=0`; the widened class starts its own registry row rather than inflating that row. Liveness-mark decision (entry arm c): claim-state fencing stays out of scope for the claim-free window - the authoring-claim teardown duty stays delete-on-teardown, and this widened fence is the complement; the disposition's durable carriers are this Outcome, the registry row's note, and the landing commit message, because the origin row is deleted at landing per the commit guidelines rather than kept as a covered stub.

## Assumptions

- `check-landing`'s existing wiring is untouched. Basis: the pins `check-landing base-freshness arm wired in execute-plan` and `check-landing wired in the blueprint` in `scripts/check_maintenance_pins.sh` hold before and after this plan.
- The refusal-block grammar (`claim-fence: <path> deleted while its claim is live`) is unchanged, so the done lib's `_claim_fence_refusal_blocks` parser needs no edit in warning posture; warning lines ride the gate's pass message unparsed, and any parser change belongs to the promotion edit. Basis: the contract-twin comment in `cmd_check_claim_fence`.
- `rejected` already sits in `PLANS_STATE_SUBDIRS` and the check-archive egress family already recognizes a rename into a rejected/ subdirectory, so the rejected-state sanction mirrors an existing state-directory shape rather than inventing one. Basis: `scripts/reverse_squash_guard.py` constants and module docstring.

Decision points requiring a grill: none remain.

## Standing constraints

- No new gate, validator, lock, ledger, or required ceremony; machinery admission is bound in the Outcome; deletion of ceremony is a first-class outcome and this plan adds none.
- The claimed-deletion refusal path is byte-preserved: same block format, same exits, same parser contract.
- Never push to origin; hygiene scan exit 0 before every commit; no em dashes; no machine-specific absolute paths in landed text; repo-relative paths only.

## Evaluation Criteria

1. An unclaimed protected deletion in a scanned range yields exit 0 with a `claim-fence-warning:` line naming the path and the deleting commit, and a follow-on line enumerating the sanctioned exits.
2. The same deletion with a same-commit archive twin, a Plans-Deletion-Ack trailer, or a same-commit rejected-state move yields the sanction line and no warning.
3. A live-claim deletion still refuses with the unchanged block format and exit 1.
4. `check-landing` over a stale base names a foreign target-tip-present, source-absent protected file with the merge base; a landing whose same scan carries the completed-archive twin prints no warning for it; a fresh base takes the unchanged early return.
5. Suites stay green: `test_reverse_squash_guard.py` (unittest), `test_done_sweep_gates_lib.py` (pytest via the venv invocation), `test_authoring_plans_liveness.py` (unittest); the pins suite's failure set stays exactly the named standing prompt-log pin; `machinery_inventory.py --check` keeps exactly its 18 pre-existing failures and the new entry adds none.

## Review Scope

- Category: guard-bearing code, its fixtures, and their registry and skill-text surfaces: scripts/reverse_squash_guard.py, scripts/test_reverse_squash_guard.py, scripts/test_done_sweep_gates_lib.py, scripts/check_maintenance_pins.sh, scripts/machinery_registry.json, agents/skills/done/SKILL.md. Single category (guard-bearing surfaces); every Files: path of every task is inventoried here.

## Validation Commands

- `python3 scripts/test_reverse_squash_guard.py` (unittest OK)
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_done_sweep_gates_lib.py -q` (pytest suite; fall back to `command -v python3` resolution per the completed plan 2026-09-30-review-staging-sidecar-kind-validation's precedent)
- `python3 scripts/test_authoring_plans_liveness.py` (unittest OK)
- `grep -c 'claim-fence-warning:' scripts/reverse_squash_guard.py` (expect 2 or more: one emit site per leg plus docstring mentions)
- `! grep -q 'no naming claim: passes silently' scripts/reverse_squash_guard.py` (the silent continue is gone; inverted-exit form)
- `bash scripts/check_maintenance_pins.sh` (exit 1 expected, standing red; the failure set must be exactly the one `PIN FAIL: prompt log has no all-served (stale) entry` line and nothing else)
- `python3 scripts/machinery_inventory.py --check` (exit 1 expected, standing red; the failure set must be exactly the 18 pre-existing failures recorded at certification - 1 unresolvable witness ref for script:skill_text_budget.py, 16 unregistered script file rows, 1 unregistered state field queued_execution - with the new `unclaimed-plan-deletion-fence` entry producing no failure of its own)
- `bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-11-landing-deleted-unclaimed-execution-ready-plan.md`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` (exit 0)

## Task 1: widen check-claim-fence with the unclaimed-deletion warning leg and the rejected-state sanction

Files: scripts/reverse_squash_guard.py, scripts/test_reverse_squash_guard.py, scripts/test_done_sweep_gates_lib.py, scripts/check_maintenance_pins.sh

Anchors:

- `cmd_check_claim_fence` in `scripts/reverse_squash_guard.py`
- `claim_fence_archive_twin` in `scripts/reverse_squash_guard.py`
- `ReverseSquashGuardClaimFenceTest` in `scripts/test_reverse_squash_guard.py`

- * [x] (code): In `cmd_check_claim_fence`, replace the silent no-claim continue with the warning class: when a protected deletion has no sanction and no naming claim, print `claim-fence-warning: unclaimed plans-root deletion: <path> (commit <sha>)` and a follow-on line enumerating the sanctioned exits - a same-commit archive twin, a same-commit rejected-state move, a `Plans-Deletion-Ack:` trailer, or standing down and restoring the file; the guard's pass line and exit 0 are unchanged.
- * [x] (code): Add `claim_fence_rejected_twin` mirroring `claim_fence_archive_twin`: an A, R, or C record in the same commit whose post-side path sits under a rejected/ state directory with the deleted basename yields the sanction line `ok: plans-root deletion sanctioned (same-commit rejected-state move at <twin path>): <deleted path>`; update the fence section comment's sanctioned-exit enumeration (the lines above `CLAIM_FENCE_TMP_DEFAULT`) to name the rejected-state move alongside the twin and the ack.
- * [x] (tests): In `ReverseSquashGuardClaimFenceTest`, add fixtures for the warning leg (unclaimed deletion, exit 0, warning line names path and commit, follow-on line names the exits), the rejected-state sanction (rename into rejected/ sanctions with no warning), and assertions that the existing twin and ack fixtures still produce their byte-identical sanction lines and contain no `claim-fence-warning:` line.
- * [x] (tests): Rename the three silent-pass claim-fence fixtures (`no_claim_passes_silently`, `absent_claim_dir_passes_silently`, `strict_subsequence_does_not_match`) to warning-bearing names and assert in each that the unclaimed deletion now produces the warning line with exit 0.
- * [x] (tests): In `scripts/test_done_sweep_gates_lib.py`, extend the plans-root-claim-fence gate fixture so a child exit 0 carrying warning lines passes with the warnings present in the gate message and nothing parsed as a refusal block.
- * [x] (pins): Add the pins suite's first claim-fence pins in `scripts/check_maintenance_pins.sh` - a new pin section beside the existing `check-landing` guard pins and before the suite's failure gate - carrying the `claim-fence-warning:` literal and the rejected-state sanction literal.

## Task 2: the landing-boundary leg in check-landing (sanction-aware, stale-branch placement)

Files: scripts/reverse_squash_guard.py, scripts/test_reverse_squash_guard.py, scripts/check_maintenance_pins.sh

Anchors:

- `cmd_check_landing` in `scripts/reverse_squash_guard.py`
- `ReverseSquashGuardTest` in `scripts/test_reverse_squash_guard.py`

- * [x] (code): In `cmd_check_landing`, inside the existing stale-base branch beside the deleted-path partition, add the landing-boundary leg: every protected plans-root path present at the target tip and absent from the source tree whose same target-to-source name-status scan carries no completed-archive twin and no rejected-state twin prints `claim-fence-warning: absent protected plan at the landing boundary: <path> (merge base <sha>)`; the fresh-base early return, the mode's exit semantics, and the execute-plan wiring are unchanged, and no `land_squash.sh` change is made (the probe relay was adjudicated out at review as a near-dead leg with a name-re-resolution race).
- * [x] (tests): Add the rehearsal fixture in `ReverseSquashGuardTest` pinned to the witnessed incident shape: a source branch forked before the foreign plan's addition to the base branch, the foreign plan absent from the source tree, produces the absent-plan warning naming the file and the merge base; a source branch that archives its own plan in the same landing produces the twin sanction silence for it; a fresh base takes the unchanged early return with no leg output.
- * [x] (pins): Add a presence pin for the `absent protected plan at the landing boundary` literal in the same new claim-fence pin section as Task 1.

## Task 3: machinery registry row, the done-skill span sentence, and the validation sweep

Files: scripts/machinery_registry.json, agents/skills/done/SKILL.md

Anchors:

- `entries` in `scripts/machinery_registry.json`
- `plans-root-claim-fence` in `agents/skills/done/SKILL.md`

- * [x] (docs): Add the machinery registry entry `unclaimed-plan-deletion-fence` (kind protocol, disposition keep, `paths: []` - the guard, landing-script, and pins-suite surfaces stay owned by their existing `script:` rows and are named in the note instead, per the `claim-if-concurrent` precedent): the note carries the admission facts from the Outcome (incident, catch frequency, false-positive cost including the claim-read flap repair posture, warning-only at landing, promotion on first true catch scoped to the sweep leg, review 2026-12), the residual-coverage sentence (boundary-unwared landings: probe- and judge-skipping tree-commit landings, fresh-based foreign deletions), the pre-registered removals commitment (the removals record cannot hold the row while the surfaces exist, so the commitment lives here per the anti-growth plan's convention), and the re-point-at-landing duty for the witness ref; `tests` names the three fixture sites (`ReverseSquashGuardClaimFenceTest`, the `ReverseSquashGuardTest` rehearsal fixture, the pytest gate fixture in `test_done_sweep_gates_lib.py`); `witness.class` is `incident` with `ref` = docs/history/backlog/2026-10-10-landing-deleted-unclaimed-execution-ready-plan.md, re-pointed to this plan's completed/ twin at landing (the `claim-if-concurrent` re-point convention).
- * [x] (docs): Extend the `plans-root-claim-fence` gate span in `agents/skills/done/SKILL.md` by one sentence naming the `claim-fence-warning:` class as a report-only line on an exit-0 child, with promotion governed by the registry row; no pin currently asserts that span, so no re-aim is owed, and the gate message's `sanction lines:` label carrying the warning lines is an accepted divergence.
- * [x] (tests): Run the full sweep and record the outcomes in the task commit message: the three suites (the pytest suite via its venv invocation), the pins suite with its failure set asserted to exactly the named standing prompt-log pin, `machinery_inventory.py --check` with its failure set asserted to exactly the 18 pre-existing failures and no new one, the em-dash check over this plan, and the hygiene scan.
