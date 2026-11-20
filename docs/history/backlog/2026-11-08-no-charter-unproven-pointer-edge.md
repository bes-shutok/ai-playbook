# Backlog: no-charter retained shape with unresolvable merge base prints the unproven-content pointer on a content-proven branch

- **Filed:** 2026-11-08, execution review r1 (correctness lens, solo) of docs/history/plans/completed/self-heal-closeout-workaround-must-preserve-landed-tree
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding (Low, non-blocking, deferred)
- **Class:** fix-class
- **Driving force:** correctness
- **Body:** when the transfer writer records no start commit because the merge base is unresolvable (mid-run destination root amend), the no-charter arm's retained disposition routes through the legacy changed-path scope and can print the report-only unproven-content pointer as a false cause claim on a branch its own chain proved carries zero run commits. Report-only blast radius; the printed route still resolves the branch correctly. Candidate remedy: a known-boundary note beside the arm's evidence chain or a reason-keyed exclusion narrowing the predicate; the plan clause "always content-proven through its own identity row" over-claims this edge.
