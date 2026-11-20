# Backlog: gate-removal manifest-gone refusal interpolates None on the derived lookup path

- **Filed:** 2026-11-08, execution review r1 (design+contract echo) of docs/history/plans/completed/branch-only-closeout-gate-report-retention-completed
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding (Low, non-blocking, deferred)
- **Class:** fix-class
- **Driving force:** quality
- **Body:** scripts/worktree_closeout_migrate.py cmd_gate_removal (~:4733-4740) prints "the migration manifest at {explicit_manifest} is gone at recording time", but explicit_manifest is None when the manifest resolved through the derived plan-slug path; the captured _receipt_explicit flag is discarded instead of discriminating the message. Cosmetic, single-threaded CLI, fail-closed holds. Remedy: branch on _receipt_explicit or interpolate explicit_manifest or "the derived plan-slug directory". Related docstring-accuracy polish from the same round (recorded_at audit-only wording; has_receipt_section null-divergence invariant; consuming-arm attribution in the consult docstrings) folded here for a single follow-up edit.
