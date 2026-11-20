# Pricing record: the certification seal's sanctioned exits

The design priced here is the origin row's option (a)/(b): widen the
first-parent byte search in `resolve_landed_anchor`
(`scripts/corrections_record.py`) from the bounded first-parent window to
any HEAD-reachable commit, and add a recorded exit for legitimately
amended plans (a plan edit after certification declaring the amendment
and re-anchoring the seal, instead of costing a fresh review round). The
pinned ordering refusal (`the round-start commit postdates the
round-close commit`) is retained under the arm, sharing the
byte-resolved substitute vocabulary with the Task 1 diagnostics
messages, so a widened scan still refuses a moved anchor that postdates
its own close.

This record only prices the design; it implements nothing. The exits arm
stays unimplemented and routes through its own future promotion plan
under the machinery admission protocol.

Incident: docs/history/backlog/2026-11-09-plan-readiness-seal-breaks-on-rebase-and-post-review-plan-edits.md (the origin row), with development_lessons.md #449 (verify every seal anchor's existence at mint time) as the witnessed misdiagnosis class.

Expected catch frequency: every legitimate post-certification plan edit or rebase that orphans a seal anchor, roughly one per authoring lane week in the current corpus; the widened scan converts each into an automatic byte-identity rescue instead of a refused readiness gate and a manual forensic pass.

False-positive cost: a widened HEAD-reachable scan can bind a seal to unrelated commits carrying byte-identical plan text (a duplicate or reverted file), silently substituting an anchor the operator did not declare; the recorded-exit arm adds a new declaration surface authors can skip, degrading the seal to the exact-match digest rule. Mitigated by retaining the ordering refusal and the Task 1 substitution naming so every substitute is visible in the refusal text.

Sunset/review date: 2027-02-15 (re-derive the catch frequency from the friction-audit corpus then; if no second witness of the anchor-break class accumulates, the arm stays unimplemented and this record retires with the origin row).
