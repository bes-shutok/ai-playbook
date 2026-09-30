# Plan: Context-bound recommended-option acknowledgements across grilling, plans, and grill-with-docs

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-09-29-recommended-option-acknowledgement.md`
Driving force: simplicity

## Gist TLDR

TLDR: replace the absolute "generic acknowledgements resume, never accept" rule with a context-bound rule across `grilling`, the `plans` Step 1.4 meta-rule, and `grill-with-docs`: an affirmative acknowledgement ("sure", "yes", "okay") accepts the named recommendation when the immediately preceding question offers exactly one clearly labeled recommendation and asks the user to choose; in every other shape (multiple recommendations, bundled decisions, unclear referent, adjacent concern) the acknowledgement resumes the interview exactly as today - so the witnessed friction ("sure" answered to a sole-recommendation question forced a repeat) disappears without weakening the per-question safeguards.

## Outcome + Gate delta

The interview's confirmation machinery becomes context-sensitive at one boundary: the sole-labeled-recommendation question. The per-question answer states, one-line decision receipts, the consolidated assumptions list, the opt-in phrase for every non-sole shape, and the adjacency guard all stay byte-untouched. `grill-with-docs`'s answer-state restatement is updated to mirror the context-bound rule so its wording no longer overstates the peer contract.

Gate delta: rewords one grilling rule paragraph (Generic acknowledgements resume, never accept) into the context-bound form and amends its adjacent Opt-in phrase paragraph's "only way" claim; amends the plans Step 1.4 meta-rule's mirror sentence the same way; amends grill-with-docs's Workflow answer-state restatement sentence; adds three worked examples to the grilling rule (sole-recommendation acceptance by "sure", ambiguity across multiple open decisions resuming, an adjacent-concern acknowledgement not closing anything); no script, hook, gate, schema, or protocol layer is added; the recipes' behavioral surface is the interview, exercised by the rules' own examples.

## Terms

- **Sole-labeled-recommendation question**: the immediately preceding question or confirmation block presents exactly one clearly labeled recommended option (explicitly marked as the recommendation) alongside its alternative(s), and asks the user to choose.
- **Affirmative acknowledgement**: a bare affirmative reply ("sure", "yes", "okay") with no additional content.
- **Resuming acknowledgement**: an affirmative or continue-style reply in any shape that does not meet the sole-labeled-recommendation condition; it resumes the interview per today's rule, closing nothing.

## Assumptions

- The rule is context-bound, not abolished: the opt-in phrase "accept the recommendation for this question" remains the acceptance path whenever the sole-recommendation condition does not hold, and the adjacency guard (no generalization across concerns) stays byte-untouched. Basis: the origin's Expected behavior and Suggested fix.
- The Answer-state paragraph's closing clause is amended in the same edit (acceptance via the acknowledgement/opt-in rules joins "answers that address the question" and "explicit rejection" as the third closing path), so the file's two rules cannot be read as contradicting each other; the opt-in-phrase acceptance already lived with this wording gap before this plan, and the amendment closes it for both paths.
- grilling is the rule's home (its Local fork notice already lists the no-generic-acknowledgement rule and the opt-in phrase as deliberate divergences); plans Step 1.4 and grill-with-docs carry mirror sentences that must be synchronized, per the origin's update instruction.
- The three examples pin both polarities (acceptance and resumption) so a future editor cannot silently re-absolute the rule; examples live inside the rule paragraph as the skill's other rules do.
- The witnessed session's added friction is the priced defect; the ambiguity-resumption behavior is unchanged, so no review-panel or eval machinery rides this plan (the examples are the eval surface).

Decision points requiring a grill: none remain - the origin's Suggested fix prescribes the context-bound shape and the synchronization set verbatim.

### Task 1 - Grilling: the context-bound rule and its examples

- [x] In `agents/skills/grilling/SKILL.md` (also amending the Answer-state paragraph's closing clause "...or explicitly rejects the recommended option" to read "...or explicitly rejects the recommended option, or accepts via the acknowledgement and opt-in rules below" so the acceptance path this rule adds does not contradict the Answer-state wording), replace the paragraph `**Generic acknowledgements resume, never accept:** ...` (re-derive exact bytes from the worktree before the edit) with the context-bound rule: `**Generic acknowledgements are context-bound:** when the immediately preceding question or confirmation block presents exactly one clearly labeled recommended option and asks the user to choose, a bare affirmative acknowledgement ("sure", "yes", "okay") closes that question as acceptance of the named recommendation (record the one-line receipt naming the accepted recommendation); in every other shape - multiple recommendations, bundled decisions, an unclear referent, or an answer about an adjacent concern - the acknowledgement resumes the interview (restate the same question or ask the next one) and closes nothing, and the opt-in phrase below remains the acceptance path. Witnessed 2026-09-29: "sure" answered to a sole-recommendation question forced a repeat of the choice. Examples: (accepts) Q: "Recovery design A (recommended) or design B?" - "sure" closes the question as accepting A; (resumes) two recommendations pending across two open questions - "sure" resumes without closing either; (adjacent) a question about the keymap, answered "sure" - closes nothing about the pending recovery design.` [class: IMPLEMENTATION_REQUIRED]
- [x] In the same file, amend the `**Opt-in phrase:**` paragraph's opening claim: replace "the only way to accept a pending recommendation without answering is" with "when the sole-labeled-recommendation condition (above) does not hold, the way to accept a pending recommendation without answering is", keeping the rest of the paragraph byte-untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the file's Local fork notice list entry "the no-generic-acknowledgement rule" to read "the context-bound generic-acknowledgement rule" so the fork inventory names the current rule. [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Plans Step 1.4 meta-rule mirror

- [x] In `agents/skills/plans/SKILL.md`, the Step 1.4 meta-rule comment (the sentence `A generic acknowledgement or continue request ("go on", "sure", "okay") restates the same question or resumes the interview instead of accepting the pending recommendation; the only acceptance without answering is the explicit opt-in phrase "accept the recommendation for this question".`): reword to the context-bound mirror - `A generic acknowledgement or continue request ("go on", "sure", "okay") accepts the pending recommendation only when the immediately preceding question presented exactly one clearly labeled recommended option and asked the user to choose (record the receipt naming it); in every other shape it restates the same question or resumes the interview instead of accepting, and the acceptance without answering is the explicit opt-in phrase "accept the recommendation for this question".` [class: IMPLEMENTATION_REQUIRED]

### Task 3 - grill-with-docs answer-state mirror

- [x] In `agents/skills/grill-with-docs/SKILL.md`, the Workflow step 2 sentence (the answer-state restatement containing `a question stays open until the user answers that question or says the opt-in phrase "accept the recommendation for this question"; generic acknowledgements resume the interview`): reword to `a question stays open until the user answers that question, says the opt-in phrase "accept the recommendation for this question", or gives a bare affirmative acknowledgement when the question presented exactly one clearly labeled recommended option (which closes it as accepting that recommendation); in every other shape generic acknowledgements resume the interview.` [class: IMPLEMENTATION_REQUIRED]

### Task 4 - Validation

- [x] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]

## Evaluation Criteria

- The grilling rule is context-bound with the three examples pinning acceptance, resumption, and adjacency; the opt-in phrase survives for every non-sole shape; the fork notice names the current rule.
- The plans Step 1.4 meta-rule and the grill-with-docs restatement mirror the context-bound rule.
- The per-question answer states, receipts, consolidated assumptions list, adjacency guard, and the opt-in phrase's text are byte-untouched.

## Review Scope

Editable regions: `agents/skills/grilling/SKILL.md` (the Generic-acknowledgements paragraph, the Opt-in phrase paragraph's opening claim, the Local fork notice's rule-list entry only), `agents/skills/plans/SKILL.md` (the Step 1.4 meta-rule's acknowledgement sentence only), `agents/skills/grill-with-docs/SKILL.md` (the Workflow step 2 answer-state sentence only). Read-only: the origin backlog item; `agents/skills/receiving-review/SKILL.md`; every other file.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero).

1. `grep -q "Generic acknowledgements are context-bound" agents/skills/grilling/SKILL.md || { echo FAIL: context-bound rule missing; exit 1; }` - the new rule is present (absent on main).
2. `test "$(grep -cF 'Generic acknowledgements resume, never accept' agents/skills/grilling/SKILL.md)" -eq 0 || { echo FAIL: old absolute rule survived; exit 1; }` - the absolute rule paragraph is gone (its header text absent).
3. `grep -q "closes that question as acceptance of the named recommendation" agents/skills/grilling/SKILL.md || { echo FAIL: acceptance arm missing; exit 1; }` and `grep -q "resumes the interview (restate the same question or ask the next one) and closes nothing" agents/skills/grilling/SKILL.md || { echo FAIL: resumption arm missing; exit 1; }` - both arms pinned.
4. `test "$(grep -c 'accept the recommendation for this question' agents/skills/grilling/SKILL.md)" -ge 1 && test "$(grep -c 'when the sole-labeled-recommendation condition (above) does not hold' agents/skills/grilling/SKILL.md)" -eq 1 || { echo FAIL: opt-in phrase mis-amended; exit 1; }` - the opt-in phrase survives and the "only way" claim is amended.
5. `grep -q "(accepts)" agents/skills/grilling/SKILL.md && grep -q "(resumes)" agents/skills/grilling/SKILL.md && grep -q "(adjacent)" agents/skills/grilling/SKILL.md || { echo FAIL: examples missing; exit 1; }` - the three polarity examples are pinned.
6. `grep -q "accepts the pending recommendation only when the immediately preceding question presented exactly one clearly labeled recommended option" agents/skills/plans/SKILL.md || { echo FAIL: plans mirror missing; exit 1; }` - the plans meta-rule mirrors the context-bound rule.
7. `grep -q "or gives a bare affirmative acknowledgement when the question presented exactly one clearly labeled recommended option" agents/skills/grill-with-docs/SKILL.md || { echo FAIL: gwd mirror missing; exit 1; }` - the grill-with-docs restatement mirrors the rule.
8. `grep -qF "context-bound generic-acknowledgement rule" agents/skills/grilling/SKILL.md || { echo FAIL: fork notice stale; exit 1; }` - the fork notice names the current rule.
9. `diff_out=$(git diff "$(git merge-base main HEAD)" -- agents/skills/grilling/SKILL.md) || { echo FAIL: diff error; exit 1; }; test "$(printf '%s\n' "$diff_out" | grep -cE '^-.*No generic acknowledgement confirms a material choice')" -eq 0 || { echo FAIL: adjacency guard touched; exit 1; }` - fail-closed: a diff or merge-base error aborts; zero matching removed lines means the adjacency guard is byte-untouched.
10. `bash scripts/check-no-em-dash.sh added-lines --base main agents/skills/grilling/SKILL.md && bash scripts/check-no-em-dash.sh added-lines --base main agents/skills/plans/SKILL.md && bash scripts/check-no-em-dash.sh added-lines --base main agents/skills/grill-with-docs/SKILL.md || { echo FAIL: em dash; exit 1; }` - the added-lines gate passes over all three files.
11. Run the public-hygiene scan from the user facts document's `public_hygiene_scan_script` key over the repository; exit 0 required.
