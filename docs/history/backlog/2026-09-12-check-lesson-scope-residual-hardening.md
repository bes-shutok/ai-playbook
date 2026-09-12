# check_lesson_scope: residual hardening from the r5 exit round

Status: open
Workflow: backlog
Source: execute-plan Phase 3 round 5 review of the learn-company-scope-placement plan (8 valid non-blocking findings deferred at the max-round cap per the backlog-deferral default)
Severity: Medium (family; per-finding severity below)
Class: validator robustness and test discrimination

Residuals from the fresh blocking-clean exit round, all on
`scripts/check_lesson_scope.py` / `scripts/test_check_lesson_scope.py` /
`agents/skills/done/SKILL.md` / `README.md`. None blocks the plan's
completion criteria; each carries its pattern id from the r5 staging doc
(docs/reviews/2026-09-12-2026-09-09-learn-company-scope-placement-code-review-r5.md).

## Medium

1. `quality#whitespace-only-no-zero-block-warning` (H1): a whitespace-only
   corpus parses to one empty block, so the documented zero-block WARNING
   never fires and done treats it as clean. Fix: treat an all-blank
   headingless file as zero blocks in `parse_blocks` plus a regression test
   writing `"\\n   \\n"` asserting WARNING with exit 0.
2. `security#fragment-split-duplicate-evasion` (H2): internal `#{1,3}`
   subheadings split a duplicated rule into fragments that individually miss
   the ratio gate (reproduced: exit 0 on a real duplicate whose internal
   heading structure differs across files). Fix options: `#{1,2}` boundaries
   as a documented amendment (supersedes the h3-split pin) or merged-text
   comparison of consecutive blocks; add the discriminating test.

## Low

3. `testing#fence-close-same-char-unpinned`: add
   `test_tilde_line_does_not_close_backtick_fence` (mixed-fence body still
   matches, exit 1); the same-char closer conjunct is mutation-removable today.
4. `testing#fence-closer-info-string-unpinned`: add
   `test_fence_line_with_trailing_text_does_not_close`; the no-trailing-content
   conjunct is mutation-removable today.
5. `testing#zero-block-master-warning-unpinned`: add `test_zero_block_master_warns`
   mirroring the corpus-side zero-block WARNING test.
6. `architecture#unbounded-runtime-obligation`: the done 4a.1 runtime-expectation
   sentence has no mechanism; wrap the invocation in `timeout 120` (exit 124 =
   tool failure) or delete the sentence.
7. `architecture#stderr-prose-contract`: the gate contract scans free-text
   stderr; either dedicate an exit code for cold start/zero-block or pin with a
   test that WARNING lines are emitted in exactly the documented conditions.
8. `documentation#prose-readme-exit2-contract-incomplete`: extend the README
   Scripts-row parenthetical to "2 usage/IO error or unclosed code fence".

## Suggested fix

Take 1, 2, and 8 together in one pass (behavior + doc); 3-5 are three small
tests; 6-7 are one-point changes to the done invocation and the consumer
contract. Re-run the plan's Validation Commands block plus the validator suite
after any of them.
