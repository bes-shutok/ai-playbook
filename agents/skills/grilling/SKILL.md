---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any grill trigger phrases.
metadata:
  upstream: "https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling"
---

# Grilling

Interview me relentlessly about every aspect of this until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing. Asking multiple questions at once is bewildering.

If a *fact* can be found by exploring the environment (filesystem, tools, etc.), look it up rather than asking me. The *decisions*, though, are mine; put each one to me and wait for my answer.

Do not act on it until I confirm we have reached a shared understanding.

## Integration Points

### With `premortem` skill
After shared understanding is confirmed, offer `premortem` to stress-test the decision from adversarial personas (failure modes, blast radius). Grilling resolves *what* to build; premortem attacks *how it fails*.

### With `plans` skill
During plan creation, grilling can deepen Phase 1 requirements discovery when scope or trade-offs are ambiguous. Do not replace the plans skill interview structure; use grilling when the user explicitly asks to grill a decision or design.

### With `rfc-design` skill
Use before drafting or after a first RFC draft when design choices need explicit user sign-off. Reference the saved RFC path once it exists; do not duplicate RFC content in chat.

### With `grill-with-docs` / `domain-modeling` skills
When the user wants terminology and decisions captured during the interview, use `grill-with-docs` (combines this skill with inline `domain-modeling`). After shared understanding without doc capture, offer `domain-modeling` to persist resolved terms and ADRs.
