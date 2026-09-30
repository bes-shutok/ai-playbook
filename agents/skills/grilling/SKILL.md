---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any grill trigger phrases.
metadata:
  upstream: "https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling"
  local_fork: "deliberate; see the Local fork notice below and the Vendored Asset Sync Rules in the repository AGENTS.md"
---

# Grilling
> **Local fork notice:** this file carries a deliberate local fork of the upstream `productivity/grilling` skill (`metadata.upstream`). Deliberate divergences: the three-phase default cadence (unclear-first sequential, clear tail batched) replaces the upstream frontier/rounds format; batch-all mode; self-contained question rules; the mandatory ambiguity triggers (cleanup and restoration); the lifecycle-verb clarification trigger; the context-bound generic-acknowledgement rule; the answer-state rule (per-question `open`/`closed`); the opt-in phrase "accept the recommendation for this question"; per-question decision receipts; question economy with the consolidated assumptions list; the Integration Points section and its sync note with the plans skill Step 1.4 meta-rule. A future upstream sync of this directory must re-apply this fork (recovery source: git history of this path) or consciously drop it with the decision recorded; see the Vendored Asset Sync Rules in the repository AGENTS.md.

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

**Mandatory ambiguity triggers (cleanup and restoration):** when a request says simplify, remove, delete, clean up, clean the branch, restore, or make it match the base, or otherwise asks to remove, revert, or reduce files toward an earlier state, or whose natural fulfillment includes deleting, reverting, or reorganizing files (tidy, organize, dedupe), and the working tree or branch (including committed changes relative to the base) contains more than the obvious feature work, or git status shows pre-existing paths you did not create or modify this session, ask one focused scope question before any edit or restore operation. Recommended wording: Should I change only the files, classes, and methods required by this feature, while preserving every other file and all pre-existing uncommitted content? Do not treat cleanup wording as permission to make the branch resemble its base; distinguish the task-owned diff from pre-existing work before touching anything.

**Lifecycle-verb clarification trigger:** when a user says skip, leave, drop, defer, preserve, or otherwise uses a lifecycle verb whose effect on the current tree is unclear, restate the candidate interpretations as concrete tree actions (for example: remove it from the current change now, defer it to a later change, or leave it in place untouched) and ask which applies; record the answer before treating the candidate as settled.

**No generic acknowledgement confirms a material choice:** a reply such as sure, ok, or confirmed confirms only the material decisions explicitly named in the question or confirmation block; a decision about one adjacent concern is never generalized to another unlisted concern.

**Answer state:** every material question has a per-question answer state, `open` or `closed`. A question is `open` from the moment it is asked until the user gives an answer that addresses THAT question or explicitly rejects the recommended option, or accepts via the acknowledgement and opt-in rules below. While any material question is open, the plan or design may be edited only for non-decision facts or question framing.

**Generic acknowledgements are context-bound:** when the immediately preceding question or confirmation block presents exactly one clearly labeled recommended option and asks the user to choose, a bare affirmative acknowledgement ("sure", "yes", "okay") closes that question as acceptance of the named recommendation (record the one-line receipt naming the accepted recommendation); in every other shape - multiple recommendations, bundled decisions, an unclear referent, or an answer about an adjacent concern - the acknowledgement resumes the interview (restate the same question or ask the next one) and closes nothing, and the opt-in phrase below remains the acceptance path. Witnessed 2026-09-29: "sure" answered to a sole-recommendation question forced a repeat of the choice. Examples: (accepts) Q: "Recovery design A (recommended) or design B?" - "sure" closes the question as accepting A; (resumes) two recommendations pending across two open questions - "sure" resumes without closing either; (adjacent) a question about the keymap, answered "sure" - closes nothing about the pending recovery design.

**Opt-in phrase:** when the sole-labeled-recommendation condition (above) does not hold, the way to accept a pending recommendation without answering is the user's exact sentence "accept the recommendation for this question"; it is never inferred from "sure", "okay", "go on", or an adjacent answer.

**Receipts:** when a question closes, record a one-line decision receipt (decision, source, date, affected plan section) before asking the next question.

**Question economy and the consolidated assumptions list:** only genuinely unclear decisions are asked; anything safely inferable or already decided is never asked. Collect every clear or safely inferable assumption during the interview; they are presented as one consolidated list at the end of the interview, before the shared-understanding or readiness confirmation, so wrong assumptions can be vetoed in a single pass.

## Integration Points

### With `premortem` skill
After shared understanding is confirmed, offer `premortem` to stress-test the decision from adversarial personas (failure modes, blast radius). Grilling resolves *what* to build; premortem attacks *how it fails*.

### With `plans` skill
During plan creation, grilling can deepen Phase 1 requirements discovery when scope or trade-offs are ambiguous. Do not replace the plans skill interview structure; use grilling when the user explicitly asks to grill a decision or design.

Sync note: the plans Step 1.4 confirmation meta-rule mirrors this skill's generic-acknowledgement, lifecycle-verb, answer-state, and opt-in-phrase clauses for confirmation-time self-containment, so an edit to either set of clauses must update the peer in the same change.

### With `rfc-design` skill
Use before drafting or after a first RFC draft when design choices need explicit user sign-off. Reference the saved RFC path once it exists; do not duplicate RFC content in chat.

### With `grill-with-docs` / `domain-modeling` skills
When the user wants terminology and decisions captured during the interview, use `grill-with-docs` (combines this skill with inline `domain-modeling`). When running the default hybrid cadence, doc capture happens between one-at-a-time questions, not deferred to the end of the batch. After shared understanding without doc capture, offer `domain-modeling` to persist resolved terms and ADRs.
