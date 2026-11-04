# Empty-diff route code-review residuals (run 2026-11-04-2041z)

Driving force: correctness (primary), safety (secondary)

Source: the execute-plan code-review r1 panel over the empty-diff-closeout-route landing (staging series .ai-playbook/reviews/2026-11-04-empty-diff-closeout-route-code-review-r1.md). The blocking operand and citation findings were fixed in-commit; the items below are the valid unfixed residuals, captured per the backlog-deferral default.

## Items

1. **Verdict-gate only-clause tension** (quality#verdict-gate-only-vs-retained-removal-tension, Low): the plans Final Step arm's "removal proceeds only on accounted verdicts" clause contradicts its retained-verdict sentence in the clean-retained corner (the gate prints pass with a removal line); soften so worktree removal follows the printed pass while branch deletion stays only on accounted verdicts.
2. **Landing-op uniqueness presentation** (implementation#landing-op-uniqueness-preempts-arm-trigger, Low): in the equal-tip scenario the landing step's lane-level uniqueness refusal fires before the helper, so the arm's trigger never occurs; plan the uniqueness-refusal presentation of the same stranded-closeout defect (the plan's Outcome records it out of scope by decision).
3. **Wiped-delta indistinguishability** (security#wiped-delta-indistinguishable-from-represented, Low): a prior union-intent-violating rebase that dropped branch-unique content is indistinguishable from fully-represented on the exact-tree route; the gate's re-verification duty never re-verifies branch-side additions. Requires the prior violation to be reachable; price a branch-side-additions re-verification arm beside the gate.
4. **Unverifiable trigger conjunct** (simplification#unverifiable-trigger-conjunct, Low): the "already fully represented" conjunct is adjudicated downstream by the gate verdict; recorded so a future editor does not promote it into a self-attested pre-check.

Cluster: none (first witness of the class in this route's own review).
5. **Noclobber corner has no named preservation home** (quality#noclobber-corner-no-named-preservation-home, Low, r2): when the draft's destination home already holds a newer primary-home file, the noclobber clause forbids the preservation write and no alternate home is named; the arm fails closed, but a hurried executor could compose the removal commit and destroy the only draft copy. Name the alternate home (or the explicit fail presentation) beside the clause.
6. **"Covering plan" double referent** (documentation#covering-plan-double-referent, Low, r2): in the arm, the gate-removal operand sentence's "the covering plan" means the closing-out run's own plan while the witness-citation sentence's means the founding plan; a future generic run could resolve the operand to the founding plan's twin (fail-closed: the gate's identity binding refuses). Disambiguate to "the closing-out run's own plan" in the operand sentence.
