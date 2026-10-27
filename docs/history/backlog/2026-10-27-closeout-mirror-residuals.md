# Closeout boundary-mirror residuals from the execution review (non-blocking, fail-safe directions)

- Filed: 2026-10-27
- Status: open
- Priority: low
- Workflow: maintenance exec (consolidation pass candidates)
- Class: review residuals, all fail-safe (conservative staleness or bounded residue, no data loss)
- Origin class: closeout-migration-same-run-mirror-replace Phase 3 risk-floor panel
- Skill-step: scripts/worktree_closeout_migrate.py; agents/skills/execute-plan/SKILL.md Step 1.4; worktree-first.md transfer-out
- Cluster: docs/history/backlog/2026-10-27-closeout-replacement-failure-print-labels.md; docs/history/backlog/2026-10-27-execute-plan-skill-mirror-growth-unbalanced.md (same surface: the closeout-migration boundary-mirror family landed 2026-10-27; distinct defect classes: residuals/hardening, printer labels, text growth)

## Residuals

1. Consumer-side (migrate) post-install pre-record interrupt window: a KeyboardInterrupt between a receipt replacement's install and its manifest entry strands the `.repl-*.prior-tmp` sibling (prior bytes preserved in it) and writes an interrupted manifest without the replaced entry; the producer's append-before-install pattern (landed in boundary-mirror) would close it if mirrored to the consumer.
2. worktree-first.md step 5's per-record digest-verification route was not extended to the new `replaced` disposition; a replaced review record has no migrated entry, so the route's letter verifies none (migration's own verified+incoming_state digests still guard bytes).
3. cmd_boundary_mirror does not cross-check --worktree against the manifest's run_worktree identity line (hardening; divergence mirrors foreign bytes visibly at boundary time).
4. The refused-acquire skipped-row manifest write is deliberately lock-free (plan-prescribed; lost-update risk excluded by the execution claim); the acceptance is recorded here rather than in plan text.
5. Premortem residue: an un-timeout'd blocking source read (FIFO/stalled FS) inside the held repo-wide lock parks closeout migrations up to the 300s wait then conservative refusal; detection evidence and full recovery paths verified.
