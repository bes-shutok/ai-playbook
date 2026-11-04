# Clobber-guard Phase 3 review residuals (execution of closeout-migrate-clobber-guard-restore-arms)

Status: covered (docs/history/plans/2026-11-04-closeout-clobber-guard-review-residual-trio.md)
Driving force: code-quality

Origin: execute-plan Phase 3 fresh-adversarial branch review r1 (2026-11-04, 5 workers, 13 raw findings, 7 staged Low non-blocking, 0 blocking; record .ai-playbook/reviews/2026-11-04-2026-11-02-closeout-migrate-clobber-guard-restore-arms-code-review-r1.md).

Cluster: docs/history/backlog/2026-11-04-clobber-guard-report-line-wording-residuals.md, docs/history/backlog/2026-11-04-gate-removal-prevented-attribution-pin-residuals.md

Consolidated unfixed residuals over scripts/worktree_closeout_migrate.py:

- R1 (staged F1): `_record_delivered_blob` docstring names a non-git target as the failed-probe case, but `git hash-object` succeeds outside a repo; the real absence trigger is a genuinely failed probe (unreadable/missing file). Documentation-only.
- R2 (staged F2, echo correctness+testing): the gate-removal prevented notes slice path lists at five with no remainder count; add "+N more" or a total, matching the sibling unattributed_missing note's count convention.
- R3 (overflow): delivered raw-bytes hash vs filtered index blob inverts the equality under byte-transforming clean filters/autocrlf; not reachable in this repo (no text attrs, autocrlf unset). Record the filter-free precondition at the comparison site.
- R4 (overflow): the `_peer_restage` interception hook matches both the staged-entry probe and `_head_blob`'s rev-parse; a walk reorder retargets the restage (pins still fail correctly, misleading failure mode only). Tighten the hook to the exact argv shape.
- R5 (staged F4 / backlogged F1 confirmation): the stamp-less prevented-row attribution fallback is unpinned in both directions; remedy folded with the shared-helper option in docs/history/backlog/2026-11-04-gate-removal-prevented-attribution-pin-residuals.md.
- R6 (staged F5): the module header's vintage-restore sentence lacks the delivered-blob qualification; one clause.
- R7 (staged F6): the resolver's destinations_error discard-all prose is not true for the new prevented_rows key; symmetric reset or corrected prose (pairs with backlogged F2).
- R8 (staged F7): the deletion arm's absence-only recheck can destroy delivered or unstaged bytes in a window wider than the plan's priced vintage-arm window (a peer action preserving index-absence; a pre-existing staged deletion on an owned path overwrites delivered bytes with HEAD). Reproduced end-to-end; the operator-decide teardown note is the current mitigation. Remedy options: consult the delivered map on the deletion arm, or record the widened residual with matching pricing in the plan's Assumptions successor.
- R9 (staged F8): wildcard-named unmerged paths (`*`, `[`, `?` in the name) make `git rev-parse :<rel>` exit 0 echoing the argument, short-circuiting before the ls-files -u discriminator; the merge is misattributed to the wrong report line (no destruction). Validate stdout is a 40-hex sha before trusting rc=0.
- R10 (overflow, design): the row-stamp `if blob: entry["delivered_blob"] = blob` policy lives in four copies at the capture sites; pass the entry dict into `_record_delivered_blob` and stamp inside it.
- R11 (overflow): guideline #10 instance — `len(records) == 1` recomputed per row in both attribution loops; folds with R5's shared-helper remedy.

## Ship when

- The next review round or follow-up pass over scripts/worktree_closeout_migrate.py's guard or gate-removal machinery picks these up; R8 deserves explicit disposition (fix or priced-residual recording) at the next touch of the deletion arm.
