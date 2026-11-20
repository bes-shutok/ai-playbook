# Backlog: unproven-content pointer exclusion duplicates the legacy-note literal instead of keying on legacy_evidence

- **Filed:** 2026-11-08, execution review r1 (design-simplicity + risk echo) of docs/history/plans/completed/self-heal-closeout-workaround-must-preserve-landed-tree
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding (Low, non-blocking, deferred; fix triage declined under zero-delta condition)
- **Class:** refactor-class
- **Driving force:** simplicity
- **Body:** in scripts/worktree_closeout_migrate.py `_gate_branch_closeout`, the pointer emission's exclusion compares each reason against a second hand-copied instance of the 137-char legacy changed-path-scope note (insertion site ~:5641, exclusion ~:5706); byte-equal today, and the negative canary test_legacy_evidence_retention_prints_no_pointer converts one-sided drift into RED. Candidate remedy: key the exclusion on `legacy_evidence is None` (the in-scope variable identifies the population precisely) and delete the duplicated literal; net bytes down, semantics unchanged.
