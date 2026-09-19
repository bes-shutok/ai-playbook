# Backlog: pin plan-authoring asks to the plans skill

Captured: 2026-09-19 (source: cross-session friction audit - user-correction mining over 1,776 typed prompts, 2026-07-17 → 09-19)
Status: open
Priority: low

Workflow: backlog

## What was witnessed

~24 corrections across all repos (Jul 25 → Sep 14) where the user had to ask whether a skill was used at all: "you should have used plans skill instead"; "did you use plans skill? Why didn't you switch the branch?"; "I asked you to create plan using plans skill. What did you actually do?"; "Didn't you run the done skill afterwards?"; "Some facts are already in the project. Why didn't you find these? facts.md". The using-skills SessionStart principles pin execute-plan invocation detection (principle 6), review-loop, rfc-design, and harness-design skills - but plan-AUTHORING has no counterpart: an authoring-shaped ask ("author a plan for X", "turn this backlog item into a plan") that lacks the literal word "plan" in an expected position is not bound to the plans skill, and env-specific answers still sometimes skip the facts.md lookup.

## Suggested fix

Extend the SessionStart principles with an authoring twin of principle 6: any plan-shaped deliverable (backlog item → plan, feature → plan, "how should we do X" asking for a plan) invokes the plans skill regardless of phrasing; and reinforce that environment-specific answers resolve from facts.md (Step 0) before answering from memory.

## Acceptance

- The principles text carries the authoring pin.
- No new "you should have used plans skill" corrections in the next corrections-mining pass.
