# Backlog: drift-witness corpus-commit fallback for gitignored-corpus sessions

- Date: 2026-09-14
- Status: done (closed stale 2026-09-15: the company-master-scoping-loop-residuals execution landed the corpus-commit-body witness without claiming this item - done SKILL items 4a/6 now carry the lesson-scope-audit body line on the drift path; verified on main dded309c)
- Origin: plan review r5 (Low, non-blocking, `quality#witness-presupposes-corpus-commit`) on `docs/plans/2026-09-14-company-master-scoping-loop-residuals.md`; staged in `docs/reviews/2026-09-14-plan-review-company-master-scoping-loop-residuals-r5.md`
- Disposition: authoring review loop at its certification cap (round 5, ready=yes, zero blocking); the Low was left unfixed per the phase-3 churn-control bound and captured here per the backlog capture rule

## Item 1: drift-witness fallback when the corpus change rides the docs branch

- Lens/Pattern: quality#witness-presupposes-corpus-commit
- Anchor: `agents/skills/done/SKILL.md` Step 3 item 4a drift branch (the sentence prescribed by plan Task 2: "the commit message body of the Step 3 commit that stages this corpus change carries the drift witness ...")
- Observation: the prescribed drift-path witness presupposes a Step 3 commit staging the corpus change on the working branch. Under done 4b's supported gitignored-corpus configuration (corpus rides the orphan docs branch only), no such working-branch commit exists, so the drift witness stays transcript-only there, while the plan's Gist implies only the out-of-scope and cold-start witness paths stay transcript-only.
- Candidate direction: add one fallback clause to the done 4a drift branch: when the session's corpus change rides the docs branch (gitignored corpus per item 4b), carry the same `lesson-scope-audit:` body line in the docs-branch sync commit message body instead.
- Why deferred: folding would have invalidated the certified digest at the loop cap for a Low-severity wording fallback; the primary drift-path witness (working-branch corpus commits) is unaffected.
