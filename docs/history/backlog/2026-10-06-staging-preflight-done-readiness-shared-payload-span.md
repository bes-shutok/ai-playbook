# Backlog: the landed staging-preflight and done-readiness plans both prescribe replacing the same payload certification span; the second-executing plan hits a stale anchor

- **Filed:** 2026-10-06 (authoring session's post-landing cross-plan check, witnessed while surveying for the next cycle)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Cluster:** docs/history/backlog/2026-10-05-authoring-certification-staging-series-gate.md, docs/history/plans/completed/2026-10-09-primary-class-anchors-grammar-drift.md (two surfaces certified against a shared span; the later consumer refuses on drift), docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md (shares the done_sweep_gates surface; named kept-open outside that row's demotion program)

Cluster: docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md (shared surface: this row's stale-anchor verification greps target prompt-templates.md spans, which that row's changelog extraction and template split relocate; sequence the span reconciliation after the split lands)
- **Origin class:** witnessed defect (two landed plans, one shared file seam, no execution-order fence)
- **Class:** fix-class
- **Skill/step:** the plans lifecycle's landing closeout (duplicate-origin coverage gate) and the execute-plan preflight's anchor verification at execution time

- **Cluster:** docs/history/plans/completed/2026-10-12-pre-round-gate-dimension-parity.md (backlog-wide survey: readiness and preflight gate surface)
- **Cluster:** docs/history/backlog/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md (tracks this row's stale Cluster referent)
## Observed vs expected

Observed: two certified plans sit at the plans root and both prescribe replacing the same span in `agents/skills/maintenance/prompt-templates.md` (the payload certification sentence `record the residual findings in the plan), and the workflow is processed`, still present on main at count 1):

- `docs/history/plans/2026-10-06-authoring-staging-preflight-gates.md` Task 2 (landed `87e43962`, first-landed, owns the `2026-10-05-authoring-certification-staging-series-gate.md` origin coverage): replaces the span with the parenthetical certification-ordering-duty form.
- `docs/history/plans/2026-10-07-done-readiness-closeout-boundary.md` Task 2 (landed `9c62b368`, later, whose commit message already acknowledges "the sibling staging-series origin keeping the peer plan's earlier coverage first-landed-wins"): replaces the same span with the assembled-series full-gate form (`...); after the final round's staging records are assembled, run the full readiness gate...`).

Both replacements deliver the same duty (the full gate over the final bytes before the ready state is treated as reached); they differ in wording and in side effects (the peer form also rewrites the blueprint's certification-sentence shape and carries its own validation gate literal `record the residual findings in the plan); after the final round`). Whichever plan executes second fails its Task 2 anchor: the quoted span no longer exists, the executor's anchor verification refuses, and the plan needs a mid-execution correction round.

Expected: two landed plans whose prescriptions overlap on one shared-file seam carry an explicit ordering or amendment record, so the second executor never meets a stale anchor: either the later plan is amended before execution to re-anchor on the first plan's landed form (or to drop the duplicated item as already-covered), or the plans declare a strict execution dependency so the ordering is deterministic and the correction is pre-authored.

## Evidence

- `grep -c 'record the residual findings in the plan), and the workflow is processed' agents/skills/maintenance/prompt-templates.md` returns 1 on main `9c62b368` (span alive; both prescriptions executable today, but only the first).
- `grep -c 'certification-ordering duty' agents/skills/maintenance/prompt-templates.md` returns 0 (my plan's form not yet landed by execution; the two prescriptions have not collided yet).
- The peer's landing commit `9c62b368` message: "the sibling staging-series origin keeping the peer plan's earlier coverage first-landed-wins" (the origin-row coverage is settled; the file-seam overlap is not).
- Both plans passed their readiness gates over their own bytes; neither gate cross-checks sibling plans' prescriptions over the same span.

## Suspected root area and fix shape

The landing closeout's duplicate-origin coverage gate resolves ORIGIN ROW ownership (first-landed wins) but never compares the landed plans' PRESCRIPTIONS over shared files. Candidate arms: (a) the second-executing plan is amended at execution time through the normal anchor-failure path (the current behavior; costs a correction round); (b) the landing closeout gains a shared-span scan across sibling queued plans (new machinery, prices high); (c) the execution queue drains same-seam plans strictly in landing order with the amendment pre-authored (the queue's parked-dependency machinery may already carry this). Adjudicate at authoring; arm (a) with a filed execution-order note is the no-new-machinery default.

## Environment

This repository, main `9c62b368`, 2026-10-06. Both plan files verifiable at the plans root.

## Update 2026-10-06 (staging-preflight execution)

The staging-preflight plan executed first (landing 8773177e base family, branch 2026-10-06-authoring-staging-preflight): its Task 2 anchor was alive at execution time and landed the certification-ordering form, so the done-readiness plan's Task 2 quoted anchor is now stale exactly as predicted; its executor takes arm (a), the normal anchor-failure correction path.
