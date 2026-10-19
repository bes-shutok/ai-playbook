# Backlog: done's plain landing commit has no serialization against concurrent squash-landing ref moves

- **Filed:** 2026-10-13, authoring residual of the small-change direct-commit policy plan (r2 review convergence)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low; the window is a pre-existing property of the done commit ladder, plausible-edge to hit, and the review that sized it recorded the analysis so the sizing decision starts from evidence
- **Origin class:** observed workflow friction (review convergence trace, not a witnessed loss)
- **Class:** landing critical section ownership analysis
- **Skill/step:** `scripts/done_run.sh` commit ladder; `agents/skills/done/SKILL.md` Step 3; `scripts/land_squash.sh` (the lock-holding landing class)

- **Cluster:** docs/history/plans/completed/2026-10-16-worktree-done-boundary-gate-roster-split.md, docs/history/backlog/2026-10-16-done-setup-after-task-edits-foreign-staging-trap.md, docs/history/backlog/2026-10-06-done-boundary-review-candidates.md, docs/history/backlog/2026-10-12-done-interrupted-manifest-state-classification-certification-residuals.md
- docs/history/plans/2026-10-19-executor-landing-helper-routing-gap.md (shared surface: the landing critical section; distinct family: done-commit serialization, not executor-side helper routing; origin row deleted on that plan's 2026-10-19 landing)

## Problem

The done commit run's landing commit (fused with the owned-commits ledger append) executes outside every merge-landing-lock span: the only runner-held spans in the ladder belong to the worktree migration and the docs-branch sync, each releasing in its own finally before the landing commit runs. If a peer worktree run's squash landing moves the base branch ref by two-value CAS between a direct session's gate run and its landing commit, the commit takes the new tip as parent with the stale index tree, so its diff silently reverts the peer's landed paths. A second owned shape: the deferred-landing-record interleaving. A recorded pending landing (the scheduler state file's pending_landing field) holds no lock, its branch field carries the landing's source branch, and its destination is contractually the default branch per the record family's landed_path proof surface, so no class-level lock consult can discriminate it; a drain turn's landing can move the default branch between a direct session's consult and its commit with no gate catching the resulting revert. No current gate catches either shape: the reverse-squash check-staged fires only on archive-egress and reviews-home signatures, and the foreign-dirt ladder adjudicates baseline dirt, not mid-run ref movement. The 2026-10-13 direct-commit policy plan recorded this as a residual: its scope freezes script bytes and rejects machinery growth, so it routed the window here instead of widening its own change.

## Expected

A sizing decision, not an automatic mechanism: either the window is accepted as a recorded bound of the done commit ladder (with the consult-and-stand-down discipline the direct-commit class uses, plus the base-freshness gates the squash class already carries, named as the compensating controls), or a merge-lock span around the landing commit is admitted through the machinery-admission protocol with a witnessed incident, because the two implementation shapes considered both carry real costs.

## Evidence

- r2 review trace (2026-10-13, plan-review-small-change-direct-commit-policy-r2.md F1): the interleaving T1-T3 (stage, peer CAS, commit) with the stale-index revert outcome; verified against `scripts/done_run.sh` (landing commit outside lock spans), `scripts/docs_branch_sync.sh` (unconditional merge-lock acquire), and `done-lock.sh` (no reentrance).
- A session-held span across the commit stage self-collides: the docs-branch sync inside the same ladder acquires the same repository-keyed lock unconditionally and the lock has no reentrance, so the naive span wedges every run into blocked.
- The direct-commit policy plan's consult discipline (a read-only merge-status consult immediately before the commit stage, standing down while it reports any holder) narrows both windows but cannot close them; the consult-to-commit remainder is the same pre-existing property.

## Alternatives

- **Session-held merge-lock span around the whole commit stage:** rejected by the r2 reviewers because it self-collides with the sync's own unconditional acquire inside the ladder (no reentrance), and carrying lock exports between the session and the runner contradicts the done skill's lock posture; would also need the sync deferral choreography on every tiny edit.
- **Teaching done_run.sh to hold a span around the landing commit:** rejected for the policy plan's scope (script bytes frozen) and deferred here because the window has no witnessed loss to price the machinery against; this row is the admission path if one is witnessed.
- **Restricting the direct-commit class to quiescent repositories:** rejected as redundant; the class already stands down while the merge-landing lock reports any holder, and stricter idle-time requirements would erase the class's operator-time benefit.

## Dedup probe

Searched open backlog filenames and Problem sections for landing-commit lock spans, stale-index reverts, and merge-lock serialization of the done ladder (2026-10-13). The nearest rows are `2026-10-13-reverse-squash-execute-plan-landing-prefix-gap.md` (a landing-commit prefix defect, not a serialization gap) and the executed machinery-admission registry rows (no done-ladder landing-commit span row exists). No duplicate.
