# Backlog: budget probe, vacuous ResourceWarning witness for the deterministic HTTPError close

Status: open
Origin: execute-plan Phase 3 r5 review of docs/plans/2026-09-13-budget-gate-quota-fixes.md (testing lens, F1); deferred at the round cap (round 5 of 5; folding would mutate the digest and require a sixth round).

## Finding

`test_zcode_transport_never_follows_redirects` (scripts/test_quota_window_probe.py ~L341) wraps the probe call in `warnings.simplefilter("error", ResourceWarning)` + `gc.collect()` and its comment claims "deleting the close() fails here". Mutation-verified false on python3 3.14.7: with `exc.close()` removed, CPython converts the warning-as-error raised inside the HTTPError file object's `__del__` into an UNRAISABLE (printed as "Exception ignored ... ResourceWarning"), which never propagates to the `gc.collect()` call site; the test stays green. The redirect-blocking assertions in the same test are unaffected and discriminating; only this witness sub-mechanism is vacuous.

## Recipe

Replace the escalation with unraisable recording: patch `sys.unraisablehook` around the probe + `gc.collect()` window (a list-appending hook), then assert no recorded unraisable has `exc_type` ResourceWarning. The TemporaryDirectory cleanup sits outside that window, so its unrelated warning cannot false-positive. Keep the redirect-blocking assertions as-is.

## Verification bar

Mutation check: delete `exc.close()` from `urllib_transport`'s HTTPError branch -> the test must FAIL (the recorded unraisable assertion fires); restore -> green.
