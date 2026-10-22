# Backlog: dangling Cluster pointers at the retired authoring-certification-staging-series-gate slug

- **Filed:** 2026-10-09, ad-hoc code review final pass (off-plan finding, pre-existing at the merge base)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** formal
- **Skill/step:** docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md (Cluster line)
- **Driving force:** simplicity
Cluster: docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md (one of the two rows citing the retired slug this row repoints)
Cluster: docs/history/backlog/2026-10-19-machinery-registry-witness-ref-rot.md (same defect class: a living record citing a backlog path that moved)
Cluster: docs/history/backlog/completed/ (removed 2026-10-22, covered by the dedupe landing) (same defect class: a living pointer whose referent's canonical home moved to completed/)
Cluster: EXEC-PROMPTS.md entry prompt-log-payload-targets-and-verdict-test-statement (covered 2026-10-22; the payload-target duty sentence landed, the origin row deleted per the covered-row rule)

## Problem

Two living backlog rows cite `docs/history/backlog/2026-10-05-authoring-certification-staging-series-gate.md` in their `Cluster:` lines, but no file of that basename exists anywhere in the tree (`git cat-file -e` fails at HEAD and at recent ancestors; `git ls-tree -r` finds no copy). The row was landed as `docs/history/plans/completed/2026-10-06-authoring-staging-preflight-gates.md`, which itself cites the slug, so the pointer's referent became a completed plan rather than a row.

## Expected

The two living rows' `Cluster:` pointers retarget to the covering completed plan path (or drop the entry), so every Cluster reference in a living row resolves. The slug's citations inside archived completed-plan snapshots are historical records and stand as written.

## Evidence

- `git grep -n "2026-10-05-authoring-certification-staging-series-gate"` at HEAD: exactly the two living rows plus two archived plan files under `docs/history/plans/completed/`.
- Witnessed by the final-focused re-review worker of the driver-create-invocation-fence ad-hoc panel: docs/history/reviews/2026-10-09-adhoc-driver-create-invocation-fence-code-review-r1.md finding F6.

## Why not fixed now

Off-plan finding at the ad-hoc run's final review: the defect pre-exists the change at the merge base, and the ad-hoc arm's containment check bounds the landing bytes to the entry's named surfaces.

## Source

docs/history/reviews/2026-10-09-adhoc-driver-create-invocation-fence-code-review-r1.md (F6)
