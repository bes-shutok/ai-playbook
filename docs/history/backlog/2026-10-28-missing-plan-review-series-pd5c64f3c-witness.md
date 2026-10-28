# Backlog: the machinery-registry-witness-home-convention plan's cited authoring review series exists nowhere on disk

- **Filed:** 2026-10-28 (witnessed during the 00:21 exec run's pick-2 teardown)
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** witnessed defect (pre-existing record loss surfaced by a gate refusal)
- **Class:** fence-class (reconstruct-or-witness report; no behavior change)
- **Skill/step:** the done closeout's gate-removal preflight (`scripts/worktree_closeout_migrate.py`) beside the record-durability checkpoint family (`agents/skills/execute-plan/SKILL.md`, in-session fallback)
- **Cluster:** docs/maintenance/development_lessons.md (the deciding-turn record-durability lesson, `##`-numbered in the corpus; see also the reviews-home copy-bridge lesson)

## Observed vs expected

Observed: the landed plan `docs/history/plans/completed/2026-10-24-machinery-registry-witness-home-convention.md` header cites `.ai-playbook/reviews/2026-10-24-plan-review-machinery-registry-witness-home-convention-pd5c64f3c-r*.md`, and the pick-2 teardown's gate-removal refused because that series has zero members. Two-command re-derivation (working-tree glob plus `git cat-file` probes at the tip) confirmed the series exists in no checkout, no worktree, and no reachable history: the loss predates the execution run (the series was never mirrored out of its authoring worktree before removal, the record-durability-checkpoint family's exact failure shape).

Expected: a plan's cited authoring review series is durably mirrored to the primary reviews home before its authoring worktree is removed; when a series is already lost, the discovering run records the witness note (never fabricates records) and a tracked disposition closes the dangling citation.

## Evidence

- gate-removal refusal at pick-2 teardown, 2026-10-28 ~01:0x local: zero members for the cited `pd5c64f3c` series.
- The landed plan header citation: `docs/history/plans/completed/2026-10-24-machinery-registry-witness-home-convention.md`.
- Fresh probes at the discovering run: filesystem glob and `git cat-file -e HEAD:<path>` both absent for every round of the series; the run's exec receipt (`.ai-playbook/reviews/2026-10-28-plan-review-machinery-registry-witness-home-convention-exec-r1.md`) carries the witness note and the removal proceeded on that recorded basis.

## Fix shape

One bounded ad-hoc pass: attempt reconstruction of the series' existence evidence from durable channels (session logs, archived plan-review sidecars, git history of the authoring date), then either restore any recoverable record bytes to the primary reviews home or record the loss disposition durably beside the plan's citation; never fabricate record content. If recovery is impossible, the disposition note closes this row as witnessed-and-accepted loss.
