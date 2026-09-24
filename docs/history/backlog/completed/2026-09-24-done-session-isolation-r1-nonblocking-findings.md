# Backlog: done-session-isolation execution r1 non-blocking findings

Origin: execute-plan run of docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md, intermediate reviews + plan re-cert, 2026-09-24
Status: closed

Disposition: 2026-09-25 (routed via docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md, Task 5): Discharged by docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md Tasks 1-3 (landed this run): F2/F3/F5/F9/F10/F11/F13 fixed in scripts/done_sweep_gates_lib.py + scripts/done_sweep_gates.sh with the F1 decoy pin and the wrapper suite green; F4/F7/F8/F12 landed as docstring and done-SKILL.md recipe truth; F13's bulk affordances (--claim-none, --foreign-review-from) are live and documented. F6 is record-only: the archived plan docs/plans/completed/2026-09-22-done-session-isolation-shared-checkout-ownership.md Assumption 1 sentence ("the four sibling origins ... archive as done") is inaccurate - the serialization-lock sibling is verify-only closed per that plan's r9 Low (measured inert) - and stays as-is under archived-plan immutability; this annotation is the correction of record.

Captured per the execute-plan exit rule (every valid unfixed finding needs a durable backlog item). All are non-blocking quality findings from the run's task reviews; none contradicts a plan gate.

- F1 (Low, test-discrimination): scripts/test_done_sweep_gates_lib.py test_load_run_manifest_matches_newest_marker does not discriminate marker binding from epoch selection (newest-marker record is also max-epoch); pin with an older-marker/higher-epoch decoy.
- F2 (Low, usage over-claim): scripts/done_sweep_gates_lib.py _usage lists write-manifest but scripts/done_sweep_gates.sh wrapper case-dispatch rejects it; either accept it in the wrapper or scope the usage line to the .py entry.
- F3 (Low, parse tolerance): RunManifest.from_dict accepts bools for created_epoch/pid (isinstance(True, int)); a corrupt `true` parses as 1.0 instead of degrading to None.
- F4 (Low, docstring accuracy): derive_review_staging_candidates docstring says candidates are "always filtered by the validator's own staging-path predicate" but manifest-owned existing paths are validated regardless of predicate (deliberate fail-closed reading); fix the docstring.
- F5 (Low, over-inclusion only): _adopted_chain_run_ids reads ancestor manifests without a repo-root content check; a foreign-root ancestor can only over-include into the OWNED (checked) set, never suppress a check; add the root check for symmetry.
- F6 (Low, plan prose): plan Assumption 1 still says "the four sibling origins ... archive as done" though the serialization-lock sibling is now verify-only closed (r9 Low, measured inert).
- F7 (Low, recipe robustness): done SKILL.md finalize recipe's `|| echo` tolerance masks non-zero lib errors as "nothing to finalize"; tighten when touching Step 6 next.

Phase 3 r2 additions (2026-09-24):

- F8 (Low, branch asymmetry): derive_review_staging_scope validates manifest-owned paths on is_file() alone while the fallback window arm applies the staging predicate; a misclaimed predicate-false path gets over-validated (fail-closed direction). Consider aligning the branches.
- F9 (Low, pre-existing parse posture): _porcelain_paths keeps literal quotes on quoted rename rows ("old" -> "new"), so a staged rename of a staging doc with quote-triggering names drops from the claim-or-foreign universe silently; pre-existing on main, now load-bearing for the fail-loud contract.
- F10 (Low, observability): a corrupt run-manifest-*.json is skipped by load_run_manifest, unreported by orphan detection, and finalize answers not-found; an undead run leaves no trace. Documented conservative stance; consider a corrupt-record report line.

Phase 3 r3 additions (2026-09-24):

- F11 (Low, conservative-inclusion gap): ledger stat-time OSErrors (dangling symlink, stat denied) fold Path.exists() to False, so such a ledger reads as absent/empty and the run's own commits classify foreign; suggest lstat-based error discrimination.
- F12 (Low, recipe override mismatch): done SKILL.md merge-lock acquire resolves DONE_LOCK_SCRIPT while the release re-derives MERGE_LOCK_SCRIPT (production defaults coincide; only the documented local-testing override diverges); align variable naming.

Field-use additions (2026-09-25, done run in a consumer repo):

- F13 (Low, operator affordance): `write-manifest`'s claim-or-foreign abort names every unclaimed staging candidate in one error string but offers no bulk way to answer it. In a repo whose reviews directory holds hundreds of prior-session staging docs, a run that owns none of them must pass one `--foreign-review` flag per path, which in practice means scripting a parse of the abort message back into arguments. Consider `--foreign-review-from <file>` (or a `--claim-none` / `--all-unclaimed-foreign` switch) so the common "this run owns no staging doc" case is answerable without re-parsing stderr.
- F2 witness (2026-09-25): confirmed in the field. The `done_sweep_gates.sh` wrapper rejects `write-manifest`, so the done Step 0 recipe's own `$LIB` resolution (which falls back to deriving the `.py` path from the wrapper default) is what makes the step work; invoking the documented wrapper subcommand fails.
