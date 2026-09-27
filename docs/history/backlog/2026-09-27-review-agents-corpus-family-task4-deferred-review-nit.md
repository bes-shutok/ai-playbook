# Deferred review nit from review-agents corpus family Task 4 (drive-by capture)

Driving force: external + code-quality (Step 1.2b intermediate-review candidate on the corpus-family execution; deferred so the reviewed digest stays binding).

Status: open

- Low (floor-pin arithmetic): the corpus-family plan's declaration-test count pin `grep -c 'def test_.*_declared' ... -ge 11` is loose once Tasks 1-3 have landed (base 4 landed + 4 = 8 already passes; only 12 is the true post-Task-4 total), so mid-execution the pin would tolerate one missing Task 4 declaration test. All four exist and the final tree passes at 12. A future plan touching scripts/test_review_agent_doors.py should pin exact counts or tight floors instead of stale `-ge` bounds.
