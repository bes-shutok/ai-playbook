# Backlog: the matched-plus-unmatched distinct-slug receipt-deletion scenario has no dedicated fixture

- **Cluster:** docs/history/backlog/completed/2026-10-28-pending-receipt-removal-warning-promotion.md (the same receipt-repair surface: the covering plan's one-for-one reconciliation landed in b6b0f7e21)
- **Filed:** 2026-10-31, focused plan-review round r1 over the pending-receipt-removal-audit-promotion completion pass (finding F2, reviewer session zcode-exec-20261031-praudit)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** execution-run finding
- **Class:** test-coverage

## Problem

The plan's criterion "given a matching committed deletion plus an unrelated deletion, expect only the matching occurrence reconciled, the unmatched receipt named in the audit output, and the audit rerun to fail" is verified structurally (reconciliation keys on full-line identity with a Counter multiplicity budget, `scripts/check_prompt_log_origins.py` one-for-one arms) and by the identical-lines x2 multiplicity test, but no fixture exercises the exact matched-plus-unmatched shape with two distinct receipt slugs. Existing repair-class fixtures use single-line, identical-x2 (dup), and same-slug-two-variants (amb) shapes only.

## Expected

A dedicated fixture in `scripts/test_check_prompt_log_origins.py`: one committed deletion plus an unrelated committed deletion of a different receipt line, one pending restoration: assert exactly one occurrence reconciled, the unmatched line named in the audit output, and the post-repair rerun failing.
