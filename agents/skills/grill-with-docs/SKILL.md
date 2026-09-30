---
name: grill-with-docs
description: Relentless interview to sharpen a plan or design while updating glossary and architectural decisions inline. Use when the user wants to grill and document terminology or ADRs as you go.
metadata:
  upstream: "https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs"
  local_fork: "deliberate; see the Local fork notice below and the Vendored Asset Sync Rules in the repository AGENTS.md"
---

# Grill with docs
> **Local fork notice:** this file carries a deliberate local fork of the upstream `engineering/grill-with-docs` skill (`metadata.upstream`). Deliberate divergences: the expanded Workflow (inline `domain-modeling` application, doc-path resolution before the first question, a doc summary on confirmation); the answer-state restatement in Workflow step 2 (per-question `open`/`closed` state, the opt-in phrase "accept the recommendation for this question", per-question decision receipts, the consolidated assumptions list); the no-batching rule for glossary and ADR updates; the Integration Points section (grilling, premortem, execute-plan, rfc-design/plans); and the deliberate omission of the upstream `disable-model-invocation: true` frontmatter flag, which must NOT be restored by a sync. A future upstream sync of this directory must re-apply this fork (recovery source: git history of this path) or consciously drop it with the decision recorded; see the Vendored Asset Sync Rules in the repository AGENTS.md.

Run a `grilling` session with `domain-modeling` active throughout the interview.

## Workflow

1. Read `domain-modeling/SKILL.md` Step 0 and resolve glossary and decision paths before the first question.
2. Follow `grilling`: one question at a time, recommended answer per question, facts from the environment not the user, no action until shared understanding is confirmed. The interview tracks each material question's answer state per the grilling rules: a question stays open until the user answers that question, says the opt-in phrase "accept the recommendation for this question", or gives a bare affirmative acknowledgement when the question presented exactly one clearly labeled recommended option (which closes it as accepting that recommendation); in every other shape generic acknowledgements resume the interview; a one-line receipt is recorded per closed question during the interview; never present a plan or RFC as ready while any question is open; clear or safely inferable items are never asked and surface in the one consolidated assumptions list at the end of the interview.
3. During the interview (not after), apply `domain-modeling` session rules:
   - Challenge terms against the glossary
   - Sharpen fuzzy language
   - Stress-test with concrete scenarios
   - Update the glossary inline when a term is resolved
   - Offer numbered ADRs when all three ADR criteria are met
4. When shared understanding is confirmed, summarize which doc files were created or updated and their paths.

Do not batch glossary or ADR updates to the end of the session.

## Integration Points

### With `grilling` skill
This skill is a documented combination of `grilling` plus inline `domain-modeling`. Do not replace either skill; invoke both behaviors in one user session.

### With `premortem` skill
After shared understanding and docs are captured, offer `premortem` for failure-mode analysis.

### With `execute-plan` skill
`execute-plan` Step 1.3b (Layer 2 documentation checkpoint) invokes this skill when the correct SOT owner, document role, or placement for documentation touched during execution is genuinely unclear; the checkpoint pauses for the grill instead of duplicating or contradicting existing docs. Same one-question-at-a-time and inline glossary/ADR rules as the `plans` Phase 1 path.

### With `rfc-design` / `plans` skills
`plans` Phase 1 invokes this skill through its confidence gate whenever an unclear requirement point is rated low-confidence; confirmed answers feed the plan's requirements buffer, while high-confidence points skip the grill and are listed in the plan's `## Assumptions` section instead. When the subject is a feature design or implementation plan, reference the RFC or plan path once it exists; write ubiquitous terms to the repo glossary, not duplicated into chat. The plans skill's Phase 1 scope-extension hard gate routes every proposed scope extension through this interview before the plan file admits it; record the in / split / defer decision inline per this skill's glossary and ADR capture. When the interview resolves a plans confidence-gate decision point, record the answer as a one-line receipt (decision, source, date, affected plan section) in the requirements buffer's Decision points requiring a grill subsection during the interview, not after it.
