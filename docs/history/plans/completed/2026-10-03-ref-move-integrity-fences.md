# Plan: Base-branch ref-move integrity fences (CAS enforcement, backward-move refusal, landed-receipt audit)

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-03-cas-enforce-base-branch-ref-moves.md`
- `docs/history/backlog/2026-10-03-empty-diff-landing-tip.md`

Driving force: reliability (fence-class work riding one same-night witnessed event, the 2026-10-03 03:16:41 through 03:18:05 landing window on this repository's main: the base branch moved forward to `acbc8fbb` at 03:17:22 and BACKWARD to `3a5a1400` at 03:18:05 between two landing sessions of one plan; the rollback-then-re-land sequence left the message-bearing tip `91a50b20` carrying an empty first-parent diff, and the prior morning's `a85aafdf` is the same empty-tip shape; both trees were verified byte-identical so nothing was lost, and both artifacts are the ref-layer relocation of the clobber loss class this plan fences).

Plan review record: the staging series docs/reviews/2026-10-03-plan-review-ref-move-integrity-fences-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A base-branch ref move can no longer silently discard content or carry a lying receipt: every landing-tail ref move is a compare-and-swap whose old value is resolved at move time and whose direction is verified fast-forward, a landing commit that carries nothing against its parent is refused at creation, any non-fast-forward step in the base reflog's recent window and any landing-phrased commit with an empty first-parent diff is a named audit row the landing record must reconcile, and the landing record carries the landed commit's diffstat so an empty tip is visible at closeout rather than discoverable by audit.

- `scripts/landing_parentage_gate.py` pre-swap gains the creation-time empty-diff leg: a landing commit whose tree is identical to its parent's tree is refused (exit 1, the refusal naming both commits), so an empty-diff landing tip cannot be created through the sanctioned tail; the script's legacy exit semantics 0/1/2 are preserved per its queued migration row.
- New `scripts/base_reflog_audit.py` (born under the script outcome contract) with two subcommands: `reflog-window` reports every non-fast-forward step in the base reflog between the newest entry and the since-sha anchor, and `landed-receipt` reports every landing-phrased base-branch commit whose first-parent diff is empty; every `landed-receipt` row names the repair path (a corrective commit naming the content-bearing sha, never an amend).
- The execute-plan landing critical section upgrades the CAS contract from prose to the enforced form, adds the unconditional fast-forward verification before the move, makes the empty-diff refusal a stop-for-adjudication refusal (keep the branch and worktree, record the already-landed content commit as the receipt of record, end the landing; no automatic restart, because a restart reproduces the same tree-identical commit), adds the diffstat receipt to the landing record, and wires both audit subcommands into the post-landing completion duty beside the reconcile receipt; a rollback inside a landing window is a recorded operation naming both tips and the reason (the maintenance blueprint's severed-ancestry lane and its inverse-compare-and-swap rollback is the sanctioned shape).
- The maintenance execution blueprint's final-merge paragraph mirrors the same receipts in delegate form (payload literals plus a pointer to the execute-plan landing critical section, which owns the semantics), and each wired region carries a removal-detecting pins needle (the record-only contract-table row is the one inserted region without one).

Gate delta: three priced additions, no removals. (1) The pre-swap empty-diff leg, priced on its cited completed-integrity-failure witness `91a50b20`, a landing message over an empty first-parent diff produced by the same-night rollback-then-re-land (the class-default alternatives are each impossible: add the sanctioned exit, because a tree-equal landing commit is exactly the witnessed harm and no gate looked at it; remove the false positive, because a no-op landing is never legitimate, the content's own commit is the receipt of record; simplify the flow, because the simplified flow is the tree-equality receipt alone and it shipped the empty tip). (2) The base-branch audit script, priced on the same window's backward step (`acbc8fbb` to `3a5a1400`) and the two empty-tip witnesses (`91a50b20`, `a85aafdf`): the window probe and the receipt sweep are the complements the creation-time refusal cannot be, because the witnessed backward move happened outside any sanctioned tail and only the reflog sees it. (3) The skill-text upgrade of the CAS contract to the enforced form plus the overlay mirror and pins rows, priced on the same witnesses: the contract prose existed before the event and did not stop it, so the delta is the enforced invocation and the direction check, not more prose.

## Terms

- **Compare-and-swap ref move**: the base-branch update through the two-value form `git update-ref refs/heads/<base-branch> <new-tip> <old-tip>`; both values are resolved via `git rev-parse` at move time, and a failed old-value check (non-zero update-ref exit) aborts the landing keeping the branch.
- **Backward move**: a base-branch ref update whose new tip is not a descendant of its old tip (`git merge-base --is-ancestor <old-tip> <new-tip>` exits 1); a rollback of the base branch is a deliberate, operator-visible, recorded operation, never a step inside a landing; the maintenance execution blueprint's severed-ancestry lane inverse-compare-and-swap rollback is that recorded operation's sanctioned shape.
- **Stop-for-adjudication refusal**: the empty-diff leg's disposition class: the landing ends with the branch and worktree kept and the receipt of record named, and no automatic restart happens (a restart reproduces the same tree-identical commit); the class is excluded from the deferred-landing path's restart clause and from every generic exit-1 routing that restarts.
- **Landing-phrased commit**: a base-branch commit whose subject line matches `^[A-Za-z0-9-]+: (land|archive) `; the phrasing family the receipt audit checks.
- **Empty-diff landing tip**: a base-branch commit whose first-parent diff is empty while its message claims a landing or archive; the message-bearing tip is what records, search, and diff-keyed tooling read, so it carries nothing to verify.
- **Reflog window**: the base branch's reflog values from the newest entry down to and including the anchor value (the since-sha, the pre-landing tip); consecutive values (v(i+1), v(i)) pair into the moves the window audits, and the move that created the anchor is itself audited.
- **Base-branch audit**: `scripts/base_reflog_audit.py`, the new two-subcommand probe (`reflog-window`, `landed-receipt`), born under the script outcome contract.
- **Landing record**: the run's recorded landing receipts (tree-equality, parentage, reconcile, and now diffstat, audit rows, and rollback documentation) that the execute-plan closeout receipt duty already owns; this plan extends its contents, it does not create a new store.
- **Script outcome contract**: `scripts/OUTCOME_CONTRACT.md`; the audit script emits the final `OUTCOME:` line and exits 0 pass / 1 fail / 2 indeterminate / 3 tool error; the parentage gate keeps its legacy 0/1/2 semantics until its queued migration row lands.

## Assumptions

1. Sibling coordination, two plans: `docs/history/plans/completed/2026-10-02-revert-set-clobber-and-reviews-home.md` executed and landed 2026-10-03 09:23 through 09:24 (exec landing `0339b558`, archive `9df5bf74`; its pins rows and skill insertions are on main, and this plan's Task 3 pins append after them), and `docs/history/plans/completed/2026-10-02-evidence-integrity-fences.md` is landed and pending execution (its Task 3 wires `check-head` before the CAS move in the same landing critical section and a `reflog-scan` beside the reconcile receipt). All three plans' insertions are adjacent-additive sentences keyed to stable anchor fragments, and each execution rebases onto whatever has landed; no insertion rewrites or moves another plan's sentences. Two recorded interplays: an amend-shaped reflog step satisfies this plan's backward-move definition, so it surfaces in both this plan's reflog-window and the evidence-integrity sibling's reflog-scan, and this plan's rollback-documentation reconciliation governs reflog-window rows while the sibling's allow-sha suppression never extends to them; and the inserted CAS sentence's resolve-at-move-time wording is self-standing and cites no named rule owned by the unexecuted sibling.
2. The witness window's backward step was the recorded repair of a landing-gate bypass; this plan fences the shape (record plus audit) and does not relitigate that repair, and no ack or suppression machinery is created for audit rows: reflog-window rows reconcile only against the landing record's own rollback documentation, and landed-receipt rows only by corrective-commit naming or citation recorded in the same record.
3. The parentage gate's queued migration row (`docs/history/backlog/2026-10-03-outcome-contract-migration-landing-parentage-gate.md`) stays queued: this plan preserves the script's legacy 0/1/2 semantics and adds no `OUTCOME:` line to it.
4. The audit script is born under the outcome contract and its contract table row lands with it in Task 2; the row's status value `conformant at birth (this plan)` is a deliberate third status class beside the table's existing `migrated (this plan)` and `queued`, and Task 2's register-prose amendment defines it.
5. The execution lane is closed at authoring time (operator directive, 2026-10-02); execution resumes under the operator's standing one-by-one discipline.
6. The origin's message-consistency arm (the landed diff must be consistent with the message's claims) is not modeled: the fence covers the witnessed empty-tip class only, and this narrowing is recorded here so the Task 5 coverage flip is not an over-claim.

Decision points requiring a grill: probe anchor semantics - resolved by the origin's own expected-state text (the audit flags any non-fast-forward step in the window, so the move that created the anchor is itself audited); source: docs/history/backlog/2026-10-03-cas-enforce-base-branch-ref-moves.md, read 2026-10-03; affected sections: Task 2 checklist items; outcome-contract applicability - resolved by the landed contract governing new decision scripts while the parentage gate keeps legacy semantics until its own migration row lands; source: scripts/OUTCOME_CONTRACT.md and docs/history/backlog/2026-10-03-outcome-contract-migration-landing-parentage-gate.md, read 2026-10-03; affected sections: Task 1 and Task 2 checklist items; remaining points - none remain (the frozen PLAN-PROMPTS entry fixes the arm scope, the two-sibling coordination, and the authoring-only lane; receipts recorded in docs/history/backlog/PLAN-PROMPTS.md on 2026-10-03)

## Gist & Examples

A landing must move the base branch forward and carry its own content. Before moving the branch, the tail proves the move goes forward; the move itself names the value it expects to replace, so a racing lane cannot pull the ground out from under it. A commit that claims it landed or archived something must show a diff. If a landing window ever moves the branch backward, the audit names the step and the landing record must say why. Repair is always a new commit that names the real receipt, never an amend.

## Evaluation Criteria

- Replaying each witness shape in a scratch repository trips exactly one named fence: a tree-identical landing commit is refused by pre-swap; a backward reflog step inside the window is a named row; a landing-phrased empty-diff commit is a named row; content landings and forward moves pass clean.
- The pins suite fails exactly three pins after Task 3's pin append and before the Task 4 insertions exist (the two execute-plan needles and the blueprint needle) and none after; the RED and GREEN runs are recorded in execution evidence.
- Existing gate behavior is unchanged where it should be: parentage refusals keep precedence over the empty-diff leg, and the parentage gate's existing selftests stay green.
- The audit script's every exit path ends with the contract's `OUTCOME:` line, and its indeterminate and tool-error paths stop the caller instead of passing.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/landing_parentage_gate.py` *(modified; pre-swap gains the empty-diff refusal leg, legacy exit semantics preserved)*
- `scripts/base_reflog_audit.py` *(new; the two-subcommand base-branch audit under the outcome contract)*
- `agents/skills/execute-plan/SKILL.md` *(modified; enforced CAS form, fast-forward verification, empty-diff routing, post-landing audit duty)*
- `agents/skills/maintenance/prompt-templates.md` *(modified; delegate-form mirror in the final-merge paragraph)*
- `scripts/check_maintenance_pins.sh` *(modified; six new pins before the final fail block)*
- `scripts/OUTCOME_CONTRACT.md` *(modified; contract table row for the new script)*
- `docs/history/backlog/2026-10-03-cas-enforce-base-branch-ref-moves.md` *(modified; Task 5 origin closure flip)*
- `docs/history/backlog/2026-10-03-empty-diff-landing-tip.md` *(modified; Task 5 origin closure flip)*

**Tests:**
- `scripts/test_landing_parentage_gate.py` *(modified; empty-diff leg, precedence, and pass-path tests)*
- `scripts/test_base_reflog_audit.py` *(new; row, clean, indeterminate, and tool-error paths for both subcommands)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/reverse_squash_guard.py`; reason: the sibling plan `docs/history/plans/completed/2026-10-02-revert-set-clobber-and-reviews-home.md` landed its check-landed mode on 2026-10-03 (exec `0339b558`); this plan adds no mode to it (Assumption 1 coordination).
- `scripts/done-lock.sh` and `scripts/reconcile_post_landing.py`; reason: the audit duty invokes beside the reconcile receipt as its own script family member; neither script's code changes (Gate delta restraint).
- `docs/history/plans/completed/2026-10-02-evidence-integrity-fences.md`; reason: the amend-shape sibling is cited for coordination, not edited here.

Reviewers are asked to weight, with findings classed accordingly: the machinery pricing of the three additions against the machinery delta doctrine (docs/history/plans/completed/2026-09-29-plans-machinery-delta-doctrine.md), each arm named to a same-night witness; the probe mechanics (the reflog pair-walking grammar, the anchor-inclusive stop given the witnessed backward step created the anchor value, the indeterminate path, the first-parent root-commit edge); Assumption 1's two-sibling adjacency claim against the siblings' actual task text, where any collision beyond adjacent-additive sentences is a blocking finding; the outcome-contract conformance of the new script and the parentage gate's preserved legacy semantics; insertion anchor stability (each named anchor fragment exists exactly once on the current tree and the inserted sentences carry the pin needles verbatim); and scope discipline (no survey-arm adoption, no ack machinery, no new stores; the repair path is the corrective commit).

## Validation Commands

```
python3 scripts/test_landing_parentage_gate.py
python3 scripts/test_base_reflog_audit.py
bash scripts/check_maintenance_pins.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-10-03-ref-move-integrity-fences.md
python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-10-03-ref-move-integrity-fences.md
python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies
bash scripts/check-no-em-dash.sh added-lines --base <merge-base of the run branch with main>
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

All are fail-closed suites; any non-zero exit blocks the task and the run. The pins suite is the wiring net: each wired region carries at least one `grep -qF` needle a reviewer can watch fail when the sentence carrying it is removed (the record-only contract-table row is the one inserted region without a needle).

Authoring-time record (the rule 29 pre-round execution): the rule 19 RED-today run of this block against the current tree observed `python3 scripts/test_landing_parentage_gate.py` exit 0 (vacuous for this plan's new tests, which Task 1 adds), `python3 scripts/test_base_reflog_audit.py` as the FIRST actually-failing gate (exit 2, the module is not created until Task 2), `bash scripts/check_maintenance_pins.sh` exit 0 (vacuous for this plan's six needles), `python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies` exit 0 (vacuous, no insertions yet), `bash scripts/check-no-em-dash.sh added-lines --base e9ecde9f` (the run branch's merge base with main at authoring time) exit 0, `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exit 0, and `bash -n` over this block exit 0 (the rule 22 mechanical audit also verified each of the six pin needles occurs exactly once in its owning prescribed snippet); the origins coverage arm exits 0 with no covering citer (the duplicate-origin exclusivity pass, this plan's expected pre-Task-5 state), and the readiness full mode's no-review-artifact reason is the tolerated pre-round class. The added-lines arm must bind the run branch's merge base, never the moving `main` tip: between authoring and landing, peer commits on main carry em-dash hits that are not this branch's lines and a main-tip base is a false RED.

### Task 1: creation-time empty-diff leg in the parentage gate

Files:
- `scripts/landing_parentage_gate.py`
- `scripts/test_landing_parentage_gate.py`

Evidence:
- `python3 scripts/test_landing_parentage_gate.py`; covers the new refusal, its precedence under the parentage checks, the amended pass-path test, and the new leg's tool-failure arm

- [x] Extend `cmd_pre_swap` in `scripts/landing_parentage_gate.py`: after the parent-identity checks pass and before the ok line, run `git diff --quiet <parent> <new>` and on exit 0 print `refuse: landing commit <new> is tree-identical to its parent <parent> (empty-diff landing tip)` and return 1, and a diff exit other than 0 or 1 is a tool failure returning 2 (the gate's fail-closed convention); keep legacy exit semantics 0/1/2, add no `OUTCOME:` line, and update the module docstring's pre-swap description to name the third check [class: IMPLEMENTATION_REQUIRED]
- [x] `LandingParentageGateTest#test_pre_swap_refuses_tree_identical_commit`; given a scratch repo where the new commit's tree equals its parent's (built with `git commit-tree` reusing the parent tree), expects exit 1 and the `tree-identical to its parent` refusal line [class: REPOSITORY_TEST]
- [x] `LandingParentageGateTest#test_pre_swap_accepts_content_child`; given a scratch repo where the new commit carries real content against its parent, expects exit 0 and the ok line [class: REPOSITORY_TEST]
- [x] `LandingParentageGateTest#test_pre_swap_parentage_precedence`; given a tree-identical commit whose parent is NOT the pre-tip, expects exit 1 with the parent-mismatch refusal line, not the empty-diff line [class: REPOSITORY_TEST]
- [x] Amend the existing `test_pre_swap_child_of_pre_tip_passes` in `scripts/test_landing_parentage_gate.py`: its child commit is tree-identical to its parent (the exact shape the new leg refuses), so give the child real content (the builder the new `test_pre_swap_accepts_content_child` uses) and keep its exit-0 ok-line expectation [class: REPOSITORY_TEST]
- [x] `LandingParentageGateTest#test_pre_swap_diff_plumbing_tool_failure`; a diff exit other than 0 or 1 (a corrupted object between the two resolved commits; the child carries content, so the diff cannot short-circuit on equal tree shas) expects exit 2 and no refusal line [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/test_landing_parentage_gate.py` [class: REPOSITORY_TEST]

### Task 2: base-branch audit script under the outcome contract

Files:
- `scripts/base_reflog_audit.py` *(new)*
- `scripts/test_base_reflog_audit.py` *(new)*
- `scripts/OUTCOME_CONTRACT.md`

Evidence:
- `python3 scripts/test_base_reflog_audit.py`; covers both subcommands' row, clean, and indeterminate paths (anchor unreached for reflog-window; root commit for landed-receipt), the tool-error path of both subcommands (an unresolvable base branch), and the final `OUTCOME:` line on every exit

- [x] Create `scripts/base_reflog_audit.py` with subcommand `reflog-window --repo ROOT --base-branch NAME --since-sha SHA [--max-entries N, default 200]`: read the reflog via `git reflog show refs/heads/<NAME> --format=%H` (newest first, values v0..vk); audit consecutive pairs (v(i+1) to v(i)) with `git merge-base --is-ancestor v(i+1) v(i)`; each failing pair is one row `backward-move: <v(i+1)> -> <v(i)>`; walk newest-first and stop after auditing the first pair whose newer value v(i) equals the anchor (that pair is the move that created the anchor); when no pair's newer value equals the anchor, the anchor is reached only at the window's oldest entry, whose pair (the last one audited) carries it as the older value; if neither form is met within N entries, name the walked depth and exit 2 indeterminate; evidence rows print first, then the final `OUTCOME:` line; exit 0 pass when clean, 1 fail with any row, 3 tool error when the branch or its reflog does not resolve or `--since-sha` does not resolve [class: IMPLEMENTATION_REQUIRED]
- [x] Same script, subcommand `landed-receipt --repo ROOT --base-branch NAME [--max-commits N, default 100]`: walk `git log --first-parent --format=%H%x00%s -n <N> refs/heads/<NAME>`; a commit whose subject matches the landing-phrased family is checked with `git diff --quiet <sha>^ <sha>`, and an empty diff is one row `empty-receipt: <sha> <subject> (repair: a corrective commit naming the content-bearing sha, never an amend)`; a root commit inside the window is named and the run exits 2 indeterminate; exit 0 pass clean, 1 fail with rows, 3 tool error when plumbing fails [class: IMPLEMENTATION_REQUIRED]
- [x] Insert into `scripts/OUTCOME_CONTRACT.md`'s table, per the register's ranking (beside the `landing_parentage_gate.py` row), the row for `base_reflog_audit.py` with the operating-context assumptions (invoked inside the landing repository; the base branch resolves and carries at least one reflog entry; the walked reflog window is contiguous, since a gc or expiry gap inside the window can fabricate or mask a row and the script cannot detect the gap; `--since-sha` resolves else tool error; the anchor is reached within `--max-entries` else indeterminate; no base-branch root commit within `--max-commits` else indeterminate; subjects decodable as text) and status `conformant at birth (this plan)`, and extend the register prose by one sentence defining birth conformance (a born-conformant script is held to the migrated script's readings: the final `OUTCOME:` line, the four exit codes, and the declared assumptions), patching the adjacent scope sentence's quantifier to name both classes (the readings apply only to migrated and born-conformant scripts) [class: IMPLEMENTATION_REQUIRED]
- [x] `BaseReflogAuditTest#test_reflog_window_reports_backward_step`; witness-shaped scratch repo (two forward commits, then a non-fast-forward reset of the base branch to the older commit): expects exit 1, one `backward-move:` row naming both values, final line `OUTCOME: fail` [class: REPOSITORY_TEST]
- [x] `BaseReflogAuditTest#test_reflog_window_audits_move_that_created_anchor`; the landing-tail shape (anchor at v1): forward C1 to C2, reset the base branch to C1, commit C3, run with `--since-sha C1`: expects exit 1 and the `backward-move: <C2> -> <C1>` row (the move that created the anchor is the paying row) [class: REPOSITORY_TEST]
- [x] `BaseReflogAuditTest#test_reflog_window_clean_and_stops_at_anchor`; a forward-only window with the anchor at the oldest entry expects exit 0, no rows, `OUTCOME: pass`; and a second scratch where a backward step sits OLDER than the anchor expects exit 0 (the window stops at the anchor) [class: REPOSITORY_TEST]
- [x] `BaseReflogAuditTest#test_reflog_window_indeterminate_when_anchor_unreached`; a forward window longer than a small `--max-entries` with a `--since-sha` that resolves but never appears in the walked window (a side-branch tip in the same scratch repo): expects exit 2, `OUTCOME: indeterminate`, walked depth named [class: REPOSITORY_TEST]
- [x] `BaseReflogAuditTest#test_landed_receipt_reports_empty_tip`; a landing-phrased commit with an empty first-parent diff (built with `git commit-tree` reusing the parent tree and a `plans: land fixture` subject): expects exit 1 and one `empty-receipt:` row [class: REPOSITORY_TEST]
- [x] `BaseReflogAuditTest#test_landed_receipt_clean_and_non_landing_subjects`; a content-bearing `plans: land fixture` commit and an empty-diff commit with a non-landing subject: expects exit 0 and no rows [class: REPOSITORY_TEST]
- [x] `BaseReflogAuditTest#test_landed_receipt_root_commit_indeterminate`; a landing-phrased root commit inside the window: expects exit 2, `OUTCOME: indeterminate`, the root commit named [class: REPOSITORY_TEST]
- [x] `BaseReflogAuditTest#test_outcome_line_on_tool_error`; an unresolvable base branch exercised against BOTH subcommands: each expects exit 3 and final line `OUTCOME: tool_error` [class: REPOSITORY_TEST]
- [x] `test_base_reflog_audit.py` isolates git config hermetically in the style of `scripts/test_reverse_squash_guard.py`'s guard_env: `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` pointed at /dev/null and the ambient `GIT_*` family dropped, so scratch reflogs and fixture commits cannot inherit host config; the same two-variable pinning is applied to the `scripts/test_landing_parentage_gate.py` helpers the Task 1 tests join (its helpers drop the ambient `GIT_*` family but do not pin the config variables) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/test_base_reflog_audit.py` [class: REPOSITORY_TEST]

### Task 3: pins

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; the RED run this task prescribes (after item 1's append, before the Task 4 insertions) expects exactly three PIN FAIL lines (the two execute-plan needles and the blueprint needle; the gate and audit needles already hold from Tasks 1 and 2); the post-insertion GREEN run is recorded in Task 4's evidence

- [x] Append to `scripts/check_maintenance_pins.sh` before the final `[ "$fail" -eq 1 ] && exit 1` block, in the existing check-landing pin group's shape: `pin "pre-swap empty-diff leg present in the parentage gate" grep -qF 'tree-identical to its parent' "$repo/scripts/landing_parentage_gate.py"`; `pin "reflog-window subcommand present in the audit" grep -qF 'reflog-window' "$repo/scripts/base_reflog_audit.py"`; `pin "landed-receipt subcommand present in the audit" grep -qF 'landed-receipt' "$repo/scripts/base_reflog_audit.py"`; `pin "fast-forward verification wired in execute-plan" grep -qF 'merge-base --is-ancestor <old-tip> <new-tip>' "$E"`; `pin "reflog-window audit leg wired in execute-plan" grep -qF 'base_reflog_audit.py reflog-window --repo <primary-root>' "$E"`; `pin "base-branch receipts delegated in the blueprint" grep -qF 'scripts/base_reflog_audit.py' "$P"` [class: IMPLEMENTATION_REQUIRED]
- [x] RED-first: after item 1's append and BEFORE the Task 4 insertions, run `bash scripts/check_maintenance_pins.sh` and record exactly three PIN FAIL lines in the task evidence; the post-insertion GREEN run is owned by Task 4's closing item [class: REPOSITORY_TEST]

### Task 4: landing-tail wiring in execute-plan and the maintenance overlay

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies`; the shared-body forbidden-term gate over the skill insertions
- `bash scripts/check_maintenance_pins.sh`; the GREEN run proving every pin holds after the insertions
- a direct forbidden-term tuple scan over the three inserted sentences, recorded in the task evidence at execution

- [x] In the execute-plan landing critical section paragraph, insert immediately before the sentence beginning `Landing-op uniqueness rule:` the base-branch ref-move integrity sentence block (Terms-backed, verbatim, with each pinned literal kept unsplit on one physical line): the fast-forward verification before the ref move (`git merge-base --is-ancestor <old-tip> <new-tip>` exit 0 required; a backward move is a deliberate, operator-visible operation recorded in the landing record with both tips and the reason, never a silent landing step; the maintenance execution blueprint's severed-ancestry lane inverse-compare-and-swap rollback is that recorded operation's sanctioned shape), the two-value CAS form (`git update-ref refs/heads/<base-branch> <new-tip> <old-tip>`, both values resolved via `git rev-parse` at move time; a failed old-value check aborts the landing keeping the branch), and the pre-swap empty-diff refusal as a stop-for-adjudication refusal: keep the branch and worktree, record the content-bearing commit already on the base branch as the receipt of record, and end the landing, because an automatic restart reproduces the same tree-identical commit and the deferred-landing path's restart clause does not apply to this refusal (the repair for a message-bearing empty tip already in history is a corrective commit naming the content-bearing sha, never an amend) [class: IMPLEMENTATION_REQUIRED]
- [x] In the execute-plan closeout region, insert immediately before `Completion is verified, not assumed:` the post-landing audit duty paragraph (verbatim, with each pinned literal kept unsplit on one physical line): run `python3 scripts/base_reflog_audit.py reflog-window --repo <primary-root> --base-branch <base-branch> --since-sha <pre-tip>` (the same pre-tip value the reconcile invocation receives) and `python3 scripts/base_reflog_audit.py landed-receipt --repo <primary-root> --base-branch <base-branch>`; the landing record carries the landed commit's first-parent diffstat beside the tree-equality receipt, and every audit row is recorded and reconciled in that record: a reflog-window row reconciles against a rollback the record documents, where a backward step predating the landing is reconciled by documenting it in the current landing record with both tips and the investigated reason and a step with no discoverable reason stops the duty for operator disposition; a landed-receipt row reconciles by recording the row and naming its receipt: the corrective commit that names the content-bearing sha (created as a direct base-branch commit outside any landing tail, since the tail's own gates refuse it, with a subject outside the landing-phrased family so the repair never becomes a row itself), or, when the content already exists in history, the receipt-of-record sha; an existing receipt reconciles later occurrences of the same row, and of the corrective commit's own row should it have one, by citation, so no fresh commit is ever required for an already-repaired row (the two known rows on main today are the named initial rows: `a85aafdf` cites its corrective commit `3c05d17c`, and `91a50b20`, a no-loss row whose parent tree already carries its content, cites the receipt of record `3a5a1400`); and an unreconciled row, an `indeterminate`, or a `tool_error` outcome stops the completion duty for re-derivation per the script outcome contract [class: IMPLEMENTATION_REQUIRED]
- [x] In the maintenance execution blueprint's final-merge paragraph, insert immediately before `Worktree arm (the only arm` the delegate-form mirror sentence (verbatim): base-branch ref-move integrity receipts (the worktree-arm landing and the severed-ancestry diff-based landing, per the execute-plan landing critical section and the closeout audit duty, which own the semantics): the fast-forward verification before the ref move, the two-value CAS form, the pre-swap empty-diff refusal as a stop-for-adjudication refusal (excluded from the arm's generic exit-1 deferred-landing routing and from the parked-dependency unblock recipe's every-refusal blanket, since a restart reproduces the same tree-identical commit), and the post-landing completion duty's two `scripts/base_reflog_audit.py` subcommands (`reflog-window --since-sha <pre-tip>`, `landed-receipt`) with the landed commit's first-parent diffstat recorded beside the tree-equality receipt [class: IMPLEMENTATION_REQUIRED]
- [x] Run the shared-body gate, the direct forbidden-term tuple scan, and the pins suite's GREEN run; record all three clean runs in the task evidence [class: REPOSITORY_TEST]

### Task 5: completion pass

Files:
- none (verification and origin closure)

Evidence:
- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-03-ref-move-integrity-fences.md`; exit 0
- `python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-10-03-ref-move-integrity-fences.md`; exit 0

- [x] Mark both origin rows covered: flip `Status: open` to the covered form with the execution landing reference in `docs/history/backlog/2026-10-03-cas-enforce-base-branch-ref-moves.md` and `docs/history/backlog/2026-10-03-empty-diff-landing-tip.md`, then verify `python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-10-03-ref-move-integrity-fences.md` exits 0 [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full Validation Commands suite and record every exit code in the completion evidence; any failure blocks the closeout [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-03-cas-enforce-base-branch-ref-moves.md`: the ref-move integrity fences landed in the execute-plan landing section (fast-forward verification before the move, the two-value CAS form with both values resolved via `git rev-parse` at move time, the backward-move refusal as a recorded operator-visible operation) plus the after-the-fact probe (scripts/base_reflog_audit.py backward-move arm); execution evidence docs/reviews/2026-10-03-exec-review-ref-move-integrity-fences-r1.md.
- `docs/history/backlog/2026-10-03-empty-diff-landing-tip.md`: the empty-receipt arm landed in scripts/base_reflog_audit.py (message-bearing landing tip with an empty first-parent diff) and the pre-swap empty-diff refusal in the execute-plan landing section names the content-bearing commit as the receipt of record; both origins fold-deleted 2026-10-04 in the backlog-root fold pass.
