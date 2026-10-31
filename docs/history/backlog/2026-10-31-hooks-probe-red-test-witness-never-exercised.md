# hooks_probe has no exercising test; its red-test witness obligation was discharged by re-class, not by coverage

Driving force: code-quality

Cluster: docs/history/plans/completed/2026-10-30-machinery-witness-ref-validation.md

The machinery-witness-ref-validation plan's criterion said the false `script:hooks_probe.py` witness would be repaired "by ensuring its cited test directly references and exercises the script stem". No tracked test exercises `scripts/hooks_probe.py` at HEAD, and fabricating a stem reference would recreate the false-witness dishonesty the plan removes, so the delivered repair re-classed the row to the registry's `user-decision` precedent shape (witness: registry note; commit on the run branch). The checkbox text and the delivered repair diverge; the coverage intent is not yet honored. Fix shape: write a genuinely exercising test for `scripts/hooks_probe.py` and restore the row to a real red-test witness. Residual from the 2026-10-31 execution (Phase 3 r1 correctness lens; adjudicated non-blocking).
