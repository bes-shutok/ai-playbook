# Backlog: quota-wall witness preamble committed-revision acceptance residual

- **Filed:** 2026-11-02 at the landing of docs/history/plans/2026-11-01-quota-doctrine-committed-rewrite-narrowing.md (origin row `2026-10-30-quota-doctrine-committed-rewrite-narrowing.md` closed at the archive; its open re-scope disposition was unexecutable against the origins-closure gate, which passes only closed/done/covered/rejected origins, so the residual's durable record moved to this fresh row - the standard landing-time residual capture; deviation recorded in the archived plan's Disposition section)
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Skill-step:** `scripts/test_quota_wall_doctrine.py` `test_witness_every_record_is_textually_unchanged_against_baseline_or_anchor` (the preamble two-revision acceptance block at the test's tail: preamble must equal the baseline preamble or the newest committed (HEAD) preamble)
- **Class:** fence-class
- **Cluster:** docs/history/backlog/completed/2026-10-30-quota-doctrine-committed-rewrite-narrowing.md (the record-class body of the origin concern; this row owns the preamble acceptance only)
- **Origin class:** self-serving
- **Driving force:** code-quality
- **Severity:** low

## Problem

The committed-revision acceptance the quota-doctrine plan re-anchored per record also exists for the directives file's preamble: the preamble must equal the baseline preamble, or the newest committed (HEAD) preamble when a sanctioned commit edited the preamble. That HEAD-anchored acceptance carries the same silent-erosion class the plan closed for record bodies: once any committed preamble rewrite lands, it becomes the permanent standard. The plan deliberately omitted the preamble arm (omit-extension at authoring; its Task 2 was supposed to leave the origin row open re-scoped to exactly this residual).

## Direction

Extend the record-anchor model to the preamble: anchor the preamble at the newest sanctioned revision (the named-constant mechanism extends naturally - a preamble-rewriting sanctioned landing joins the constant, or a preamble-specific anchor constant is added), so an unsanctioned committed preamble rewrite goes red instead of becoming the standard.
