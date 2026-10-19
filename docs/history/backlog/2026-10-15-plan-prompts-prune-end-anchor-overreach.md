# Backlog: the PLAN-PROMPTS landing prune removed nine entries through a wrong end-anchor, and the prune audit stayed green

- **Filed:** 2026-10-15, discovered while building the corrective commit 9a7a71689
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** execution-run finding
- **Class:** fix-class

## Problem

The post-landing-reconciliation-enforcement landing (4818cc829, 2026-10-14) pruned its own dispatch entry with a section-removal step whose end anchor was `t.index('## codex-task-resource-cleanup-evidence-recovery')`, assuming the pruned entry was immediately followed by the codex entry. The log's actual order held nine more entries between the two headings, and the removal erased all of them: done-run-declared-deletion-path, execute-plan-closeout-cycle-and-filed-records, finite-string-state-values-need-enum-review-guidance, post-implementation-review-invariant-coverage, closeout-gate-review-series-expansion, framework-callback-readability-and-review-scope, configurable-artifact-paths-in-docs, execute-plan-sequential-trace-harness, and skill-monolith-module-extraction. Nine ready or frozen dispatch entries left the tracked log in a certified landing, and only the accidental later restoration (the stale-primary reversal of witness 7 in docs/history/plans/completed/2026-10-14-post-landing-reconciliation-enforcement.md, which committed the pre-landing bytes back) returned them to main.

## Why the prune audit did not catch it

`python3 scripts/check_prompt_log_origins.py --prune-audit --base 163ce04aa` ran before the rider commit and answered `OUTCOME: pass` with `0 removals across 0 log-touching commit(s)` while the working tree carried a PLAN-PROMPTS.md diff of roughly 216 deleted lines. The audit's log-touching-commit detection does not see the uncommitted worktree state the landing is about to commit, so a removal performed in the working tree before the rider commit is invisible to it; the audit's plan-file-witness rule never fires for entries removed without their witnesses.

## Expected

A landing's prune step removes exactly one entry (the entry whose prompt authored the plan being landed), every removal carries its receipt line, and the prune audit fails closed when the landing range removes log content without a matching receipt-plus-witness pair, including removals staged in the working tree before the audit runs.

## Fix shape

Two arms, to be planned separately: (1) the prune step's procedure of record anchors the section removal on the NEXT heading actually following the pruned entry in the log (read, do not assume adjacency), and names every removed slug it did not intend as a loud stop; (2) the prune audit extends its input to the landing range's staged or worktree bytes (not only committed history) so a pre-rider removal is counted and witness-checked like a landed one.

## New witness (2026-10-19, executor-landing-helper-routing-gap execution r1)

A landing rider pruned its own frozen entry with a correct next-heading end anchor, yet the range still removed the neighboring landing's receipt line sitting at the range's tail: the anchor pair bounded the entry, but receipts accumulate between entries and the delete never inventoried the range's contents. The execution review caught it (1 blocking), restored the line byte-identically; the prune audit stayed green because it counts entry removals, not foreign receipt-line removals. Fix arm (1) extends to: after computing the range, list its `PLAN-PROMPTS-PRUNE:`/`EXEC-PROMPTS-PRUNE:` lines and stop loudly on any slug this landing does not own. Priority re-affirmed high. Corpus witness: docs/maintenance/development_lessons.md #111.
