- **Filed:** 2026-09-30
- **Status:** open
- **Workflow:** done (learn Step 1.8)
- **Priority:** medium
- **Origin class:** self-serving
- **Driving force:** automation
- **Class:** fix-class

# p102 post-landing reconciliation review residuals (6 items)

Residuals captured at the execute-plan run of docs/history/plans/2026-09-30-execute-plan-post-landing-primary-checkout-reconciliation.md (whole-plan review: ready=yes, 0 blocking; Task 1 and Task 2 intermediate reviews: clean/1 blocking fixed). Each item below is independently actionable; split on pickup if needed.

1. Record the delivered `synced`-row grammar (`synced <checkout> <path>`) as a post-landing contract errata for the p102 plan's Task 2 output-format bullet (the plan's own fixture case demands the path-bearing form). Driving force: automation (the row text is the machine surface later sessions grep; contract and carrier must not drift).
2. Map a failed single-path restore in scripts/reconcile_post_landing.py to a `block <checkout> <path> restore-refused` row and continue the run, reserving exit 2 for pre-flight tool failures (witnessed: an untracked file at a landing-deleted path aborts the whole run as exit 2; the file survives, but one debris shape stops reconciliation instead of degrading to a named block). Driving force: automation (the reconcile loop should degrade to recorded named blocks it can resume from).
3. Add a mixed-reset wholesale-residue fixture (worktree at ancestor blob, index at post-tip blob) to scripts/test_reconcile_post_landing.py asserting the worktree-only restore leaves the index untouched; the arm is implemented but had no fixture. Driving force: automation (the fixture suite is the carrier's paying witness; an unprobed arm is the r1 dead-arm defect's shape).
4. Add CHERRY_PICK_HEAD and the sequencer heads to midflight_witness's marker list in scripts/reconcile_post_landing.py (defense-in-depth: a conflicted cherry-pick currently escapes the midflight guard and is only caught by the classification's byte-state fallthrough). Driving force: correctness (a witness must not depend on byte-state fallthrough to stay safe).
5. Route rev_parse_verify's subprocess through the same hermetic env the git() helper builds in scripts/reconcile_post_landing.py. Driving force: correctness (one git invocation path, one environment contract).
6. Execute-plan task Evidence lists pin the em-dash/hygiene checks on the production file only while each task also edits the plan document itself; consider pinning those gates on the plan file too in the execute-plan skill's evidence conventions (both files verified clean in this run; hardening, not a defect). Driving force: reliability (plan files are prose artifacts the same gates apply to).
7. FIXED 2026-09-30 (same session): scripts/reconcile_post_landing.py resolves --post-tip for reads but string-compares refs/heads/<base> against the raw argument in the tip guard, so an abbreviated --post-tip always degrades to newer-landing blocks; resolve the argument (or compare resolved SHAs) and note the contract requires full SHAs today. Driving force: automation (the guard must compare resolved identities, not argument spellings). Disposition: resolve_invocation_or_exit2 now rewrites the invocation's tip fields to the resolved full shas, regression test test_abbreviated_tip_args_resolve_not_false_blocked added; contract unchanged (unresolvable args still exit 2, zero writes).
