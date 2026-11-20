# Backlog: archive-ceremony arm Phase 3 advisories

Driving force: code-quality

Origin: Phase 3 review panel of the archive-rider-sweep-ordering execution run
(branch 2026-11-08-archive-rider-sweep-ordering, base 4d67cbb62). Both lenses
returned zero blocking findings; these are the recorded valid unfixed findings
(backlog capture before Phase 3 exit). Witness records:
`docs/tmp/execute-plan/archive-rider-sweep-ordering/phase3-lens-tests-scope.log.md`
and `phase3-lens-correctness.log.md` (session copies, gitignored).

- A1 (`scripts/test_done_run_wrapper.py` blocker-posture witness): chmod 0o000
  without the try/finally restore its lib-level twin applies
  (`scripts/test_done_sweep_gates_lib.py` blocker witness). Fix: mirror the
  twin's try/finally next time the class is touched.
- A3 (`scripts/done_sweep_gates_lib.py` `_segment_archive_findings`): the
  `"archive-ceremony gate failed: "` prefix literal is duplicated from the
  gate's failure composition. Drift degrades findings-bearing failures to the
  could-not-evaluate posture (fail-safe, never a false clean). Fix: share one
  named constant when the file is next touched.
- A4 (`scripts/done_sweep_gates_lib.py` arm entry point): derivation rows are
  derived twice (classification pass + gate-internal re-derivation under the
  pinned span). Perf-only; fix: derive once and thread rows through when the
  entry point is next touched.
- A2 (record-only, no action): plan-text imprecision in the covering plan
  (`FixtureMixin.run_finalize` naming; report line composition home). Recorded
  in the lens log for the plan record's accuracy.
