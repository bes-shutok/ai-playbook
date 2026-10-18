# exec-review Low residuals: plan-review-story-key-slug-case-mismatch

- Cluster: plan-review identity
- Urgency: low
- Origin: exec review r1 (2026-10-07, ready=yes zero blocking) of docs/history/plans/completed/2026-10-06-plan-review-story-key-slug-case-mismatch.md, landed 80ad2666

## Rows

1. plans/SKILL.md's discoverability warning still quotes `no review artifact for feature slug` as what a case-adjusted round slug surfaces; post-landing that path surfaces the case-variant rename-direction or collision refusal instead, so the quoted literal is exact only for all-lowercase plans. Optional wording follow-up; the plan pinned only that the warning keeps its meaning, which holds.
2. The plan's Task 3 non-edit note about doing-code-review/SKILL.md line 591 was ambiguous between a plan-text annotation and a review-plan SKILL.md sentence; the compliant reading was implemented (doing-code-review byte-unchanged). Optional: a one-sentence inherited-rule note in review-plan Step 4.
3. The glob_metachar_slug selftest arm was retargeted without a plan fixture-list entry (forced: post-change the metachar slug refuses at derivation before discovery); the escaped-glob property survives via two new direct helper pins. Accepted; documented here as the record.
