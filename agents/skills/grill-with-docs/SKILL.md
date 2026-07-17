---
name: grill-with-docs
description: Relentless interview to sharpen a plan or design while updating glossary and architectural decisions inline. Use when the user wants to grill and document terminology or ADRs as you go.
disable-model-invocation: true
metadata:
  upstream: "https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs"
---

# Grill with docs

Run a `grilling` session with `domain-modeling` active throughout the interview.

## Workflow

1. Read `domain-modeling/SKILL.md` Step 0 and resolve glossary and decision paths before the first question.
2. Follow `grilling`: one question at a time, recommended answer per question, facts from the environment not the user, no action until shared understanding is confirmed.
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

### With `rfc-design` / `plans` skills
When the subject is a feature design or implementation plan, reference the RFC or plan path once it exists; write ubiquitous terms to the repo glossary, not duplicated into chat.
