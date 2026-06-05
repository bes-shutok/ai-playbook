---
name: premortem
description: >
  Diverse premortem analysis — stress-test plans, designs, code changes, and test strategies
  by imagining failure from multiple adversarial perspectives. Use before finalizing plans,
  during code review, when designing test strategies, or when the user asks to "premortem",
  "stress-test", "what could go wrong", or "challenge this". Trigger phrases — "premortem",
  "stress-test this", "what could go wrong", "challenge this plan", "devil's advocate",
  "run a premortem", "failure modes".
---

# Diverse Premortem

## Core Concept

A premortem assumes the project/plan/change has already failed and works backwards to identify
*why*. Unlike a post-mortem, it exploits the power of prospective hindsight — people are better
at explaining past events than predicting future ones.

**Diverse** means using multiple distinct adversarial personas, each with different expertise
and blind spots, to maximize failure-mode coverage.

## When to Use

- Before finalizing an implementation plan
- During code review (as an additional analysis lens)
- When designing test strategy (identifying gaps)
- When reviewing an RFC or design document
- Standalone when the user asks to stress-test a decision

## The Iron Law

```
IMAGINE IT HAS ALREADY FAILED. YOUR JOB IS TO EXPLAIN WHY.
```

Do not defend the plan. Do not soften findings. Each persona must genuinely try to break it.

## Personas

Launch each persona as a distinct thinking thread. Each operates independently and must not
see other personas' findings until the synthesis phase.

| Persona | Focus | Asks |
|---------|-------|------|
| **The Pessimist** | Murphy's Law scenarios | "What breaks under realistic bad luck?" |
| **The Newcomer** | Cognitive load, implicit assumptions | "What would confuse someone seeing this for the first time?" |
| **The Operator** | Production runtime, observability, rollback | "How does this fail at 3 AM and how do we recover?" |
| **The Attacker** | Security, abuse, edge-case exploitation | "How would I break this intentionally?" |
| **The Impatient User** | UX, latency, timeouts, partial failures | "What makes users give up or retry dangerously?" |
| **The Future Maintainer** | Technical debt, coupling, extensibility | "What makes this painful to change in 6 months?" |

### Persona Selection

Not every premortem needs all personas. Select based on context:

| Context | Required personas | Optional |
|---------|-------------------|----------|
| Implementation plan | Pessimist, Newcomer, Operator, Future Maintainer | Attacker, Impatient User |
| Code review | Pessimist, Attacker, Operator | Future Maintainer |
| Test strategy | Pessimist, Attacker, Impatient User | Newcomer |
| RFC/Design | All six | — |
| Quick challenge | Pessimist + one most relevant | — |

## Process

### Phase 1: Frame the Subject

State in 1-2 sentences what is being premortemed:
- The plan/design/change under review
- Its stated goals and constraints
- The definition of "failure" in this context

### Phase 2: Independent Persona Analysis

For each selected persona, independently generate:

1. **Failure scenario** — a concrete, specific way this fails (not vague "it might be slow")
2. **Trigger conditions** — what realistic circumstances cause this failure
3. **Blast radius** — who/what is affected and how severely
4. **Detection difficulty** — would we notice before users do? How long until detection?
5. **Existing mitigation** — does the current plan already address this? (If yes, note it and move on)

**Rules:**
- Each finding must be *concrete* — name specific components, data flows, or user actions
- No duplicate findings across personas (deduplicate in synthesis)
- If a persona finds nothing credible, it reports "No findings" — do not invent weak concerns
- Findings already mitigated by the plan are acknowledged and skipped, not re-raised

### Phase 3: Synthesis

After all personas complete:

1. **Deduplicate** — merge findings that describe the same root failure from different angles
2. **Rank by risk** — severity × likelihood matrix:

| | Low likelihood | Medium likelihood | High likelihood |
|---|---|---|---|
| **High severity** | Monitor | Mitigate | Block |
| **Medium severity** | Accept | Mitigate | Mitigate |
| **Low severity** | Accept | Accept | Monitor |

3. **Classify action**:
   - **Block** — must address before proceeding
   - **Mitigate** — add safeguard, test, or monitoring
   - **Monitor** — add observability, accept residual risk
   - **Accept** — documented risk, no action needed

### Phase 4: Output

Format findings as a ranked list:

```markdown
## Premortem: [Subject]

### Blockers
1. [Finding] — Persona: X — Trigger: Y — Mitigation: Z

### Mitigations Needed
1. [Finding] — Persona: X — Trigger: Y — Suggested fix: Z

### Monitor
1. [Finding] — Persona: X — Trigger: Y — Observability: Z

### Accepted Risks
1. [Finding] — Persona: X — Rationale for acceptance: Y
```

## Integration Points

### With `plans` skill
Invoked as part of the Plan Quality Gate, after drafting tasks but before structural checks.
Personas: Pessimist, Operator, Newcomer (always) + Future Maintainer (large plans).
Blockers become additional plan tasks. Mitigations become test cases or validation steps.

### With `doing-code-review` skill
Invoked as one of the shared `review-agents/` sub-agents. The `review-agents/premortem.md` wrapper
reads this skill for persona definitions and process, then applies sub-agent overrides (change-type
persona selection, max 2 findings per persona). Only Block and Mitigate findings surface as review
comments. Skipped for trivial diffs (<20 lines).

### With `tdd-guide` skill
Invoked during the Bug Fix Workflow (step 4) after defining outcomes but before proposing
the test plan. Personas: Pessimist + Attacker. Frame: "Tests passed but the bug reappeared."
Findings become additional test cases or assertions.

### With `rfc-design` skill
Invoked as a gate before final RFC output. All six personas. Blockers revise RFC sections.
Mitigations feed §8 (Testing & Rollout). Monitors feed §7 (Operability).
Accepted risks go in an appendix subsection. Output is folded into the RFC, not shown separately.

### With `review-confluence-doc` skill
Invoked in Step 4.5 after initial quality analysis of a fetched Confluence page.
All six personas for RFC/Design; Pessimist + Attacker + Operator for TDD docs.
Blockers become 🔴 Critical items. Mitigations become 🟡 Suggestions.
Monitor items are shown as ℹ️ Advisory. Output is merged into the review feedback, not shown separately.

## Anti-Patterns

| Anti-pattern | Correction |
|---|---|
| Vague concerns ("might be slow") | Demand specifics: which endpoint, what load, what latency |
| Defending the plan instead of attacking | Re-read the Iron Law. Your job is to break it. |
| All findings are Low severity | Either the plan is excellent or personas are too gentle. Try harder. |
| Persona overlap (same finding 3×) | Deduplicate aggressively in synthesis |
| Premortem longer than the plan itself | Cap at 2-3 findings per persona. Quality over quantity. |
| Raising issues already addressed | Read the plan fully before generating findings |

## Standalone Invocation

When invoked directly (not as part of another skill):

1. Ask the user what to premortem (or infer from context)
2. Select appropriate personas based on context type
3. Run the full Phase 1-4 process
4. Present the output
5. Offer: "Want me to address any blockers or mitigations now?"
