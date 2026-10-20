# gate-removal task 2 review residues (deferred)

Cluster: gate-removal-closeout-accounting
Cluster: docs/history/backlog/2026-10-21-guard-signal-gates-authorized-action-lesson.md
Status: open
Origin: plan 2026-10-19-gate-removal-closeout-accounting Task 2 tier-M review (non-blocking findings deferred at the light boundary, 2026-10-21).

- N1: scripts/done_run.sh cmd_setup's fail-open sweep report greps only `OUTCOME|remove|registration|branch-report` lines, so chain-skipped retained branches (dirty, post-landing, live session, no twin) never reach the setup report by name or OID (plan item "Setup and execute-plan closeout report every retained branch name" is partial).
- N3: hermetic-env residue in fixtures the Task 2 diff did not touch (test_worktree_closeout_migrate.py ~2501, ~798-808, ~1572/1584, ~3804/3816) and the kill_capture wrapper (~4181) which, unlike the mid-check wrapper, does not inject _hermetic_git_env.
- N4: _parse_branch_disposition re-splits reasons on `"; "` and mis-parses if reason text ever contains `"; "` or `reasons=`; current reasons never do, failure degrades to None.
- N5: the drain-time `registration: drained` line reprints the enumeration-time disposition/OID; reporting-only staleness since the drain never touches the ref.
- Plan-row wording: the plan's operator-closeout checklist row still says "without force"; Task 2 review ruled the executable form is `git worktree remove --force` plus the inventory precondition (see lesson 158). Reconcile the wording if the row text is ever mined for guidance.
- Optional pin: the unresolved-recorded-branch and non-git-target branch-only skip shapes are live-probed but carry no automated fixtures.

## Task 3 tier-M review notes (deferred 2026-10-21, 0 blocking)

- `_gate_refusal_text` reuse in the warn arm carries a refusal-specific name/docstring while rendering the never-absolute form the warn arm needs; rename or split if the helper grows arms.
- The warn arm's test relies on argparse last-wins for the double `--worktree` operand (established neighboring-test pattern); an explicit two-operand shape would be sturdier if the tests are ever restructured.
- Warning-before-verdict ordering on failing runs is harmless today; revisit only if warning output ever becomes machine-consumed.

## Task 4 tier-M review notes (deferred 2026-10-21, 0 blocking)

- The help pin counts the token over whole stdout; a future help line mentioning the literal token would fail it spuriously. Scope it to the usage line if the pin ever breaks.
- Dispatch coverage rests on the subprocess-CLI tests only (no in-process main dispatch witness); mutation check confirms they catch a dispatch regression.

## Phase 3 fresh-adversarial panel notes (deferred 2026-10-21, 1 blocking fixed at 1af769c59, rest non-blocking)

Full findings per lens live in the run lane logs (docs/tmp, untracked); the durable residues:

- Risk F2 (the blocking, FIXED 1af769c59): worktree mode printed the `--force` removal command with OUTCOME: pass even on failed guards; retained dispositions with a failed guard now hold the removal (held line, exit 1) and the sweep maps that shape on on-disk candidates to the same operator-controlled retained verdict. Narrowing accepted: a stale registration on a guard-failed branch parks as `gate-removal fail` instead of draining (conservative, non-destructive).
- Correctness F1: the ancestry-accounted pass message claims "single live worktree binds it; migrated artifacts verified", both false in branch-only mode (zero linked worktrees by construction) and unpinned elsewhere; reporting-text only.
- Testing F1/F3/F5/F6/F8: defensive arms of the new accounting untested (on-disk refusal in _remove_candidate, the not-a-registered-worktree identity refusal, git-failure branches, malformed disposition lines, the mixed missing-plus-refused remedy print); the mid-check mock pattern can reach them.
- Testing F2: the unresolved-recorded-branch and non-git-target skip shapes still carry no fixtures (supersedes the Optional pin bullet above).
- Testing F4: the content-scope post-landing arm (prod ~1596) is disjunctively asserted and currently unexercised.
- Testing F9/F10: tautological assertIsNotNone closer at test ~4683; the plain `python3 -m unittest scripts.test_...` form fails at import (scripts not importable; use the discover form) - pre-existing at base.
- Risk F1/F6: gate worktree-removal is dirt-blind (base-inherited; the step-4 inventory is the new protection; warning-only dirt visibility is the bounded ask) and GIT_* env inheritance is unscrubbed in gate git subprocesses (fails safe across repos).
- Risk F3/F4/F7/F9/F10: `OUTCOME: pass` covers both delete-eligible and must-not-delete branch states (the branch-disposition line is the field of record); `git update-ref -d` with an empty/all-zeros expected OID deletes silently (done step 7 should demand the proven OID); destination history is HEAD of whatever --target names (the trust boundary, plan-defined); a same-named tag can shadow the branch at proven-OID capture (downstream guards fail safe); date-stripped slug collisions share one manifest dir with records[-1] authoritative (fail-safe refusal on identity mismatch).
- Design F1-F13 and contract-docs F1-F6: mostly rendering/docstring residues (doubled refusal lines, four renderers plus the inverse parser, the thrice-copied primary-checkout recipe, derived-manifest lookup implemented twice, dead _remove_candidate arms, stale "plan stem" help text vs the Task 1 slug, module docstring's stale migrate-remedy claim, missing retained-branch reporting duty twin in done/SKILL.md, done step (3) sketch omitting required --plan/--target operands, sweep docstring splice naming branch-report lines wrong). The plan "without force" wording and done_run.sh N1 grep were re-witnessed by multiple lenses.
