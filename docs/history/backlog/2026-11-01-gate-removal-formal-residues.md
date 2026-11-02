# Gate-removal task 2 review deferred formal residues
Cluster: docs/history/backlog/2026-11-01-gate-removal-multi-record-gate-report-conjunction-test.md; docs/history/backlog/2026-11-01-gate-removal-note-newline-sanitization.md; docs/history/backlog/2026-11-01-gate-removal-record-index-bool-stamp-exclusion-untested.md; docs/history/backlog/2026-11-01-gate-removal-resolver-verified-destinations-derivation.md (same-day review family)

- **Filed:** 2026-11-01 during the gate-removal-task2-review-residues execution (Task 3 formal split)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** formal-hardening (parser, environment, pin, fixture, naming, and wording residues; no item demonstrates wrong behavior today)
- **Driving force:** code-quality
- **Source:** docs/history/backlog/2026-10-21-gate-removal-task2-review-deferred.md (the covered origin row; findings deferred 2026-10-21 at the plan 2026-10-19-gate-removal-closeout-accounting tier-M reviews and the Phase 3 fresh-adversarial panel), plus one docstring nit witnessed during this run's Task 2 intermediate review
- **Dedup probe:** searched open backlog filenames and Problem bodies for `gate-removal formal`, `hermetic-env`, `_parse_branch_disposition`, `drained`, and `help pin`; the nearest items are the covered origin row (this row's source) and `docs/history/backlog/2026-10-29-branch-skip-report-ref-and-line-integrity.md` (pre-gate skip-report OID forgery and tag shadow, a distinct security follow-up). No open item carries this inventory.

## Problem

The plan `docs/history/plans/2026-10-29-gate-removal-task2-review-residues.md` fixed the origin's two in-scope report defects (commit 25cef1315: ancestry evidence-only wording in `_gate_branch_closeout`; commit d17fd8f1f: retained-branch and skip-evidence relay in the setup output) and required, as an Outcome item, that the remaining formal-only residues live in a separate open record before the origin row closed. This row is that record. The origin's Risk F2 blocker was fixed at 1af769c59 and is not a residue.

Deferred findings, evidence preserved per line:

- N3 (environment): hermetic-env residue in fixtures the Task 2 diff did not touch (`scripts/test_worktree_closeout_migrate.py` around lines 2501, 798-808, 1572/1584, 3804/3816) and in the kill_capture wrapper (around 4181), which unlike the mid-check wrapper does not inject `_hermetic_git_env`.
- N4 (parser): `_parse_branch_disposition` re-splits reasons on `"; "` and mis-parses if reason text ever contains `"; "` or `reasons=`; current reasons never do and failure degrades to None.
- N5 (reporting staleness): the drain-time `registration: drained` line reprints the enumeration-time disposition/OID; reporting-only staleness since the drain never touches the ref.
- Plan-row wording: the completed plan's operator-closeout checklist row (`docs/history/plans/completed/2026-10-19-gate-removal-closeout-accounting.md`) still says "without force"; the review ruled the executable form is `git worktree remove --force` plus the inventory precondition (lesson 158). Reconcile the wording if the row text is ever mined for guidance.
- Skip-shape fixtures (Testing F2, supersedes the origin's Optional pin bullet): the unresolved-recorded-branch and non-git-target branch-only skip shapes are live-probed but carry no automated fixtures.
- Task 3 tier-M, naming: `_gate_refusal_text` reuse in the warn arm carries a refusal-specific name/docstring while rendering the never-absolute form the warn arm needs; rename or split if the helper grows arms.
- Task 3 tier-M, test shape: the warn arm's test relies on argparse last-wins for the double `--worktree` operand (established neighboring-test pattern); an explicit two-operand shape would be sturdier if the tests are ever restructured.
- Task 3 tier-M, ordering: warning-before-verdict ordering on failing runs is harmless today; revisit only if warning output ever becomes machine-consumed.
- Task 4 tier-M, pin: the help pin counts the token over whole stdout; a future help line mentioning the literal token would fail it spuriously. Scope it to the usage line if the pin ever breaks.
- Task 4 tier-M, coverage: dispatch coverage rests on the subprocess-CLI tests only (no in-process main dispatch witness); the mutation check confirms they catch a dispatch regression.
- Testing F1/F3/F5/F6/F8 (fixtures): defensive arms of the new accounting untested (on-disk refusal in `_remove_candidate`, the not-a-registered-worktree identity refusal, git-failure branches, malformed disposition lines, the mixed missing-plus-refused remedy print); the mid-check mock pattern can reach them.
- Testing F4 (fixture): the content-scope post-landing arm (prod around line 1596) is disjunctively asserted and currently unexercised.
- Testing F9/F10 (fixtures/infra): tautological assertIsNotNone closer at test around line 4683; the plain `python3 -m unittest scripts.test_...` form fails at import (scripts not importable; use the discover form), pre-existing at base.
- Risk F1/F6 (environment): gate worktree-removal is dirt-blind (base-inherited; the step-4 inventory is the protection; the bounded ask is warning-only dirt visibility), and GIT_* env inheritance is unscrubbed in gate git subprocesses (fails safe across repos).
- Risk F3 (semantics/wording): `OUTCOME: pass` covers both delete-eligible and must-not-delete branch states (the branch-disposition line is the field of record).
- Risk F4 (hardening): `git update-ref -d` with an empty/all-zeros expected OID deletes silently (the done step 7 should demand the proven OID).
- Risk F7 (documented trust boundary): destination history is HEAD of whatever `--target` names; plan-defined, recorded so a future hardening pass re-derives the boundary rather than inheriting it silently.
- Risk F9 (risk): a same-named tag can shadow the branch at proven-OID capture; downstream guards fail safe.
- Risk F10 (risk): date-stripped slug collisions share one manifest dir with records[-1] authoritative (fail-safe refusal on identity mismatch).
- Design F1-F13 and contract-docs F1-F6 (rendering/docstring residues, mostly): doubled refusal lines, four renderers plus the inverse parser, the thrice-copied primary-checkout recipe, derived-manifest lookup implemented twice, dead `_remove_candidate` arms, stale "plan stem" help text vs the Task 1 slug, the module docstring's stale migrate-remedy claim, the missing retained-branch reporting duty twin in done/SKILL.md, the done step (3) sketch omitting required `--plan`/`--target` operands, and the sweep docstring splice naming branch-report lines wrong.
- Task 2 intermediate review F1 (witnessed 2026-11-01, this run): the `_sweep_branch_tip_oid` docstring says "Never raises" while `_sweep_git` can raise `_SweepToolError` on git-launch OSError (`scripts/worktree_closeout_migrate.py` around lines 4818-4828 and 4026-4040); unreachable in practice, docstring precision only.

## Exact location

- `scripts/test_worktree_closeout_migrate.py`: hermetic-env fixtures around lines 2501, 798-808, 1572/1584, 3804/3816; kill_capture wrapper around 4181 (N3); warn-arm double `--worktree` test (Task 3 tier-M); defensive arms, post-landing arm around 1596, assertIsNotNone closer around 4683 (Testing F4/F9/F10 and F1/F3/F5/F6/F8).
- `scripts/worktree_closeout_migrate.py`: `_parse_branch_disposition` (N4); the drain-time `registration: drained` report line (N5); `_gate_refusal_text` warn arm (Task 3 tier-M); the help pin and dispatch tests (Task 4 tier-M); `_remove_candidate`, identity refusal, git-failure branches, remedy print (Testing F1/F3/F5/F6/F8); gate removal path and gate git subprocess env (Risk F1/F6); `OUTCOME` classification (Risk F3); `git update-ref -d` call (Risk F4); proven-OID capture (Risk F9); manifest dir derivation (Risk F10); renderers, primary-checkout recipe, derived-manifest lookup, help text, module docstring, sweep docstring splice (Design F1-F13); `_sweep_branch_tip_oid` docstring around lines 4818-4828 with `_sweep_git` around 4026-4040 (Task 2 intermediate review F1).
- `scripts/done_run.sh` and `agents/skills/done/SKILL.md`: retained-branch reporting duty twin and the done step (3) sketch operands (contract-docs F1-F6).
- `docs/history/plans/completed/2026-10-19-gate-removal-closeout-accounting.md`: operator-closeout checklist "without force" row (plan-row wording).

## Expected

- Environment: sweep-path fixtures and wrappers inject the hermetic git env uniformly, and the gate's GIT_* inheritance gets an explicit scrub-or-accept decision (N3, Risk F6).
- Parser and reports: disposition parsing handles or explicitly rejects adversarial reason text (N4); drain-time lines carry current state or are labeled enumeration-time (N5); `OUTCOME` semantics either split the pass states or keep the branch-disposition line as the documented field of record (Risk F3).
- Fixtures: every skip shape, defensive refusal arm, git-failure branch, and the post-landing arm has a focused test; no tautological closers; unittest invocations use the discover form (Testing F1-F10).
- Hardening: `git update-ref -d` demands the proven OID; proven-OID capture resolves the branch ref without tag shadow; slug-collision behavior stays documented (Risk F4, F9, F10).
- Naming and docs: `_gate_refusal_text` renamed or split when it grows arms; the help pin scoped to the usage line; stale help text, docstrings, the done/SKILL.md reporting twin, and the checklist wording reconciled (Design F1-F13, contract-docs F1-F6, plan-row wording, Task 3 tier-M naming, Task 2 intermediate review F1).

## Why not fixed now

The personal priority profile defers formal-hardening work, and none of these items demonstrates wrong behavior today: each fails safe, degrades to a report-only artifact, or is unreachable in practice. The certified plan's scope covered exactly the two in-scope report defects, and its Outcome and Review Scope required this separate open record before the origin row closed. The evidence is preserved verbatim in substance so a later plan can pick items up without re-running the 2026-10-21 reviews.

## Exec r1 additions (2026-11-01)

- docs#1 (Low): `_sweep_branch_report_line`'s docstring gloss "(the legacy skip shapes)" is now imprecise since branch-backed skips also emit `branch-report:` lines; docstring precision only.
- test#1 (Low): retained/accounted branch-report relay through cmd_setup is witnessed transitively (pre-existing accounted/retained assertions + the unchanged filter regex + the new skip-relay tests); no direct wrapper test. Add one when the surface is next touched.
