---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any grill trigger phrases.
metadata:
  upstream: "https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling"
---

# Grilling

Interview me relentlessly about every aspect of this until we reach a shared understanding. Walk down each branch of the decision tree. For each question, provide your recommended answer.

**Default cadence (unclear-first sequential, clear tail batched):** the interview runs in three phases:

1. **Look up facts.** Resolve anything that is a *fact* (filesystem, git, tooling) by exploring the environment rather than asking. Skip anything already decided or look-uppable.
2. **Ask unclear questions one at a time.** Sort the genuinely **unclear** decision questions most-unclear-first. Ask a single self-contained question and wait for the answer before the next, especially when one question determines how the next is framed (e.g. "targeted edit or rewrite?" cannot be answered until "what is broken?" is settled). Each question must carry: the concrete context (affected table, API, event, or component), why it matters, a **recommended decision**, the **reasoning**, and a **before/after example**.
3. **Clamp the clear tail.** Once only low-ambiguity questions remain, present them as one numbered confirmation block with suggested solutions, and let the user accept-in-batch or override per item.

A question qualifies for the tail block only when **all three** hold: (a) **no upstream dependency** on any still-open one-at-a-time question; (b) a **defensible default** exists with concrete reasoning, not just "it depends"; (c) **low surprise**: flipping the answer is a confirm-or-tweak, not a redesign. If any fails, keep it one-at-a-time. Failure signal: if a tail question's recommendation reads "depending on Q1," it belongs upstream.

This respects the user's time without collapsing dependent decisions: the unclear core is resolved sequentially, and only the genuinely clear remainder is batched.

**Batch-all mode (when the user asks for it):** if they explicitly want every question at once ("show me everything," "batch mode"), present all remaining decision questions in one reply with a single numbered suggested-solutions list, then wait.

When grilling a plan, make each question self-contained. Define any plan term before using it and include the concrete context needed to decide: the affected table, API, event, or component; the reason it matters; and a short example of the before-and-after behavior. Do not ask the user to choose based on an unexplained label such as a "slice" or a summary of a data flow.

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
When the user wants terminology and decisions captured during the interview, use `grill-with-docs` (combines this skill with inline `domain-modeling`). When running the default hybrid cadence, doc capture happens between one-at-a-time questions, not deferred to the end of the batch. After shared understanding without doc capture, offer `domain-modeling` to persist resolved terms and ADRs.
