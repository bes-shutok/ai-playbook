# Landing diagnostic selects a foreign plan and a foreign source worktree

- **Filed:** 2026-10-21, execute-plan closeout of plan-validation-command-undefined-repo (landed 28127e322)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (warning-only diagnostic; no block, but most receipts diagnose an unrelated plan)
- **Cluster:** docs/history/backlog/2026-10-21-seal-landing-survival-review-residuals.md (same surface: the post-squash certification diagnostic and its receipt ledger)
- **Origin class:** self-serving
- **Class:** fix-class (the receipt's plan selection resolves a corpus-wide highest-ready record instead of the landing's own archived plan, so the receipt certifies nothing about the landing it rode; default shape remove the false target)
- **Driving force:** reliability (primary), correctness (secondary)
- **Skill/step:** the post-squash warning-only certification diagnostic wired into `land_squash.sh land-worktree` (receipt kind `certification-seal-landing-diagnostic`, ledger `docs/history/certification-seal-landing-diagnostics.md`); receipt contract in Task 2 of `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md`
- **Source reference:** the receipt row appended at landing 28127e322 (committed by the peer as 1846d9e6b): `plan_path` resolves to a peer's open plan (`update-stacked-branch-promoted-commit-exclusion`), `source_worktree_head` resolves to a foreign worktree (7f7c18d6), and both validator commands record `state: not run, reason: landing-context proof failed or was inconclusive`; capture hygiene: `scan-public-hygiene.sh --files` pass
- **Why not fixed now:** the diagnostic is warning-only and the row is honest about not observing anything; narrowing the selection touches the just-landed receipt contract (Task 2's outcome matrix is the declared single source for receipt branch behavior), so it needs a planned change, not an ad-hoc edit
- **Dedup probe:** searched open backlog filenames and Problem text for `diagnostic`, `landing receipt`, `readiness-not-pass`; nearest: `docs/history/backlog/2026-10-21-seal-landing-survival-review-residuals.md` (same diagnostic surface, carries the readiness-not-pass residual over an archived identity, not the selection rule) and `ada922c7e` (the first receipt row); no open row owns the selection rule; no merge

## Problem

Corrected archaeology (2026-10-21): the procedure text (`agents/skills/plans/SKILL.md`, the landing-closeout bullet's Post-squash certification diagnostic arm) already scopes the target ("the highest ready review record **for this plan**"), and the receipt contract names the plan path plus that record path. The witnessed failure is a resolution drift, not the selection design: at landing 28127e322 the receipt's `plan_path` resolved to a peer's unrelated open plan, the `source_worktree_head` to a third session's worktree, and the proof went inconclusive (every validator command `not run`, warning `not_observed`), so the receipt documents nothing about the landing that produced it. The producer is a manual procedure with no mechanical tie to the landing's own archived identity and no post-append check that the receipt's plan path equals the landed plan, so any acting session can resolve "this plan" wrong and land a foreign-target row on the tracked ledger.

## Suggested fix

Smallest arm first: add one contract sentence beside the receipt content contract (the ledger header or the procedure arm): the receipt's `plan_path` must equal the landing's own archived-plan identity and `source_worktree_head` the landing's own source worktree; a mismatch is recorded through the existing `docs/history/certification-seal-landing-diagnostic-write-failures.md` fallback instead of the main ledger. Reconcile the wording with Task 2's receipt outcome matrix (the declared single source for receipt branch behavior). A mechanical producer script keyed on the landing commit is the priced-larger alternative (see the investigate entry's rejected dispositions).
