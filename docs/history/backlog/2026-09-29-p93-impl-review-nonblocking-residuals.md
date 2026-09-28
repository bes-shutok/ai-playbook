# p93 implementation review r1 non-blocking residuals

Origin class: consumer-company
Priority: low
Status: open

Five non-blocking findings from the p93 continuation-admission execution's r1 three-worker implementation review (landing 9ffee738). None blocked landing; recorded for a future polish pass.

1. `implementation#deferred-runtime-boundary-narrowing` (scripts/execute_plan_runtime.py ~1464): the new claim gate validates evidence runtime ids against eligible profiles only, so a CLI-validated `--runtime <deferred-id>` pair on a legacy manifest now refuses where the frozen stamp path previously proceeded. Fail-closed direction; launch would have refused later anyway. No test pins it.
2. `quality#payload-token-coercion` (scripts/execute_plan_runtime.py ~10158): the `recover-run-identity` payload `token` is accepted from any non-null JSON value via `str()` coercion while sibling fields are isinstance-strict.
3. `testing#vacuous-assertion` (scripts/test_execute_plan_runtime.py ~15872): `assertNotIn(..., {"claimed","launched","blocked"})` immediately after `assertEqual(..., "closed")` is vacuously true.
4. `quality#tokenization-semantics-widened` (scripts/execute_plan_runtime_codex.py ~383): the tolerant scan drops shlex quote-grouping/backslash-joining, so a shell-quoted multi-word resume id extracts truncated; failure direction is a missed join (conservative), inherent to the plan's Terms.
5. `testing#red-evidence-not-in-history` (commit 8abc37f4): RED runs are not separately witnessed in git history because tests and implementation share the plan-prescribed single task commit; compensated by the empirical RED reproduction in the review record.
