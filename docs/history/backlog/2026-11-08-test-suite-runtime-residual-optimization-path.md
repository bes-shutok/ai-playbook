# Test-suite runtime residual optimization path

- **Filed:** 2026-11-08
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** performance follow-up
- **Driving force:** efficiency
- **Origin:** `docs/history/plans/completed/2026-11-07-test-suite-runtime-reduction-follow-up.md`, Task 3

The follow-up execution preserved the accepted 44.10% result and recorded useful measurements, but no candidate passed the predeclared selection rule. The feature note gives concrete next steps without assigning them to a durable dispatch record: attribute subprocess cost in the dominant `test_done_run_wrapper.py` path, include the second-longest `test_worktree_closeout_migrate.py`, account for long-lived test controllers/process trees before repeating bounded parallel trials under measured lower contention, and only consider Go/Rust after a comparable profile attributes at least 5% of serial time to Python-specific work. The current feature note explicitly says this is not proof that the remaining target gap is irreducible.

## Suggested work

Create a bounded follow-up plan that first profiles the two named suites with retained raw samples and child-process attribution, then establishes a process-tree survey that accounts for long-lived test controllers and their descendants before repeating bounded parallel trials with matched controls under measured lower contention. Keep complete failure accounting, resource limits, and isolation checks. Treat same-interpreter reuse as rejected unless the observed environment restoration defect is fixed and the candidate also passes the same repeated matched-control selection rule. Treat a language prototype as conditional on a comparable measurement meeting the existing 5% threshold; define representative semantic-parity cases and build/maintenance costs before any port. Run a final complete-suite comparison only if a candidate meets the existing selection rule and the run is separately authorized.

Do not claim the parallel path or a language switch is effective from the current evidence: the parallel median gain did not exceed its run-to-run range, the controller overlap was unassigned, and Python-specific aggregate cost was not isolated. Do not infer that all further reduction harms coverage or reliability; the report says that condition remains unestablished.
