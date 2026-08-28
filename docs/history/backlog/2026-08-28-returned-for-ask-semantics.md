# Backlog: Returned-for-ask semantics completion (fix-risk deferred)

Status: backlog
Workflow: pre-plan (promote via `plans` skill when scheduled)

## Problem

Three findings from the 2026-08-28 fix-risk-triage-skills review r8 (all workers, zero-blocking clear round) on the returned-for-ask state introduced by the r7 consumer sweep:

1. **Exception scope mismatch across four sites.** `receiving-review/SKILL.md` Backlog capture shields only "a must-stay-blocking finding held for the fix-risk user decision", while the Fix-risk closing paragraph holds any Critical/High/Medium rules-2-3 finding at `pending` until answered, and both execute-plan consumers (Step 3.3 gate #4, subagent-prompts step 7) use the broad scope. For a non-blocking High/Medium finding awaiting the ask, the provider's literal exception does not apply and a literal reader must create the backlog item now — conflicting with the do-not-backlog-until-answered instruction. Candidate fix: align all four sites to one scope ("a finding held `pending` for the fix-risk user decision").
2. **"Returned-for-ask" has no defined record form or location.** Three workers converged: the term is not a staging Status/Triage value (done/drop/pending/deferred), no file says where the record lives (Analysis section? address log?), and review-staging's receiving-review consumer row was extended for Blocking re-evaluation but not for this state. The Step 3.3 gate demands an artifact it cannot describe. Candidate fix: define the marker once (e.g. "returned-for-ask" on the finding's Analysis section, Status/Triage stay `pending`) in review-staging's consumer row or the provider section; call sites point at it.
3. **The interactive fix-risk ask is sanctioned but never mandated before the next fold.** Hard Gate 17 permits the ask and the relay clause says who asks, but nothing obligates the orchestrator to relay the returned question before incrementing `review_round`; an interactive run has a user, so the Step 3.5 stop row (no additive path or user) does not fire and the loop can legally fold on a rule-2-frozen finding until the round cap. Candidate fix: a Step 3.3/3.5 gate row — "a returned-for-ask presentation outstanding → perform the ask before done / before returning to Step 3.1" — mirrored in review-loop orchestration rule 4.

Exact locations: `receiving-review/SKILL.md` Backlog capture exception + Fix-risk closing; `execute-plan/SKILL.md` Step 3.3 gate #4, Step 3.5 table, Hard Gate 17; `execute-plan/subagent-prompts.md` step 7; `review-staging/SKILL.md` receiving-review consumer row; `review-loop/SKILL.md` orchestration rule 4.

## Why not fixed now

The r8 round was blocking-clean (the loop's exit condition). The fix-risk policy and the loop-bound addendum prescribe exiting on zero-blocking with the non-blocking residue tallied and backlogged rather than folding more: rounds r4-r7 of this same loop each generated a new finding from fixes to the fix-risk closing paragraph, and items 1-2 above edit that same paragraph family. Recorded durably for one deliberate pass.

## Source

- Review staging: `docs/reviews/2026-08-28-fix-risk-triage-skills-code-review-r8.md` (r8, staged 5, 0 blocking)
- Severity: Medium x2, Low x1; correctness-completeness lead, contract-docs and design-simplicity echoes
