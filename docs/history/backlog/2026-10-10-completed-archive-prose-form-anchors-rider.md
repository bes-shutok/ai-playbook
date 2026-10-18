# Backlog: one prose-form anchors entry survives in the completed-plan archive, outside the open-plans-root scan scope

- **Filed:** 2026-10-10, rider of docs/history/plans/2026-10-09-primary-class-anchors-grammar-drift.md (found by the execution review loop's r2 blind probe)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (archived bytes, never re-validated unless resurrected; the open plans root is clean)
- **Origin class:** scan-scope residue of the anchors-grammar conversion
- **Class:** fix-class (one archived anchors entry conversion)
- **Skill/step:** `docs/history/plans/completed/2026-10-08-review-policy-scope-complexity-cap-checkpoints.md` (line ~219, the anchors bullet naming `select_record` and `_enumerate` in one entry)
- **Cluster:** docs/history/plans/completed/2026-10-09-primary-class-anchors-grammar-drift.md (the covering plan; same defect class, its Task 4 scoped the conversion to the open plans root)

## Observed vs expected

Observed, 2026-10-10, the execution review loop's repo-wide scan: the completed-plan archive carries exactly one remaining prose-form anchors entry — `- `select_record` and `_enumerate` in `scripts/review_record_selection.py`` — two backticked identifiers in one bullet, which the shared grammar `PRIMARY_CLASS_ANCHOR_ENTRY` refuses (the first token is not immediately followed by `` in ``). The entry predates the grammar's enforcement; Task 4's repository-scan checkbox scopes the rider-filing rule to the open plans root, so the completed archive fell outside the executed scan and no in-repo record witnessed that exclusion until this row.

Expected: the archived entry is either converted to the shared grammar form (two entries, one per identifier, each descriptive text after the comma) or consciously left with the exclusion recorded here — but never silently re-validated: the new pre-round gate refuses these bytes if the plan is resurrected or re-validated wholesale, so a resurrection run must fix the entry through that plan's own semantic plan-edit path. The archived plan's bytes are not edited by this rider.

Dedup probe: keyword search over docs/history/backlog/*.md for completed-archive, anchors, prose-form terms; the covering row (2026-10-09-primary-class-anchors-grammar-drift.md) is status covered and scoped its scan to the open root; no other row covers the completed archive's residue.
