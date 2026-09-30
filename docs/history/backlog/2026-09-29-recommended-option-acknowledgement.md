# Recommended-option acknowledgements should close the named decision

- **Filed:** 2026-09-29
- **Status: done (2026-10-01; executed+landed docs/history/plans/completed/2026-10-01-context-bound-recommended-option-acknowledgement.md, squash main c4396776, exec review r1 ready=yes zero blocking)(docs/history/plans/2026-10-01-context-bound-recommended-option-acknowledgement.md)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Projects using the shared plans and grilling workflows need natural, context-sensitive confirmation handling; the skills-repo personal priority profile must not park or defer this shared-skill fix as formal-hardening for the skills repo alone.
- **Origin class:** self-serving
- **Driving force:** simplicity
- **Source:** Interactive plan-authoring interview, 2026-09-29. The assistant asked which of two recovery designs to use, explicitly recommended one, and the user replied “sure.” The assistant then treated the answer as non-responsive and asked the user to repeat the choice. Relevant rules: `agents/skills/grilling/SKILL.md` acknowledgement rules and `agents/skills/plans/SKILL.md` Step 1.4. Environment: Codex desktop session using the skills-repository copies, 2026-09-29. Capture hygiene: scan-public-hygiene --files pass.

## Problem

`agents/skills/grilling/SKILL.md` says generic acknowledgements such as “sure” never accept a pending recommendation and requires the exact sentence “accept the recommendation for this question.” `agents/skills/plans/SKILL.md` mirrors the confirmation rule. In a question that presents one clear recommendation and one alternative, a plain “sure” in direct response naturally accepts the recommendation, but the current instructions force another confirmation turn. In this witnessed session, that added friction and the assistant stopped useful work despite the context identifying the recommendation unambiguously.

The opposite failure also matters: a generic acknowledgement must not be stretched across several independent or unnamed decisions. The defect is the absolute magic-phrase rule, not the per-question answer-state or decision-receipt safeguards.

## Expected behavior

- When the immediately preceding question offers one clearly labeled recommendation and asks the user to choose, a direct affirmative acknowledgement such as “sure” or “yes” closes that question as acceptance of the named recommendation.
- When the prompt presents multiple recommendations, bundles decisions, or leaves the referent unclear, the acknowledgement resumes the interview and the assistant asks only about the unresolved decision.
- Keep per-question open/closed state, one-line decision receipts, and the consolidated assumptions list. Update `grilling` and its synchronized `plans` Step 1.4 rule together; update `grill-with-docs` if its answer-state wording otherwise overstates the peer contract.
- Add realistic examples or skill evals for a single recommendation accepted by “sure,” an ambiguous acknowledgement with multiple open decisions, and an acknowledgement referring only to an adjacent concern.

## Dedup probe

Searched open backlog filenames and Problem text for “generic acknowledgement,” “exact phrase,” “sure recommendation,” and “magic phrase.” No open item covers acknowledgement interpretation across `grilling` and `plans`. The nearest filename match is `docs/history/backlog/2026-09-28-execute-plan-resume-reentry-arm.md`, which concerns execute-plan worktree re-entry and is unrelated. No merge recommended.

## Suggested fix

Replace the absolute “generic acknowledgements resume, never accept” rule with a context-bound rule: an affirmative acknowledgement accepts the sole explicit recommendation in the immediately preceding self-contained question or confirmation block; otherwise it resumes the interview without closing any material question. Preserve the opt-in phrase only for contexts where no sole recommendation is available. Synchronize the corresponding plans and grill-with-docs references and add examples that pin both acceptance and ambiguity behavior.

## Why not fixed now

The active request is to author the execute-plan runtime follow-up plan. Editing shared interview skills would expand that plan-authoring scope and introduce a separate behavioral change. The user asked for the witnessed failure to be captured as a durable ai-playbook backlog item.
