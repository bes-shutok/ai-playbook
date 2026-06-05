---
name: review-agents
description: "Shared sub-agent pattern catalog used by doing-code-review and review-plan. Not meant to be invoked directly. Contains quality, implementation, architecture, testing, simplification, documentation, security, concurrency, and premortem agent files."
---

# Review Agents (Shared Pool)

This skill is a shared library of review sub-agent pattern catalogs.

**Do not invoke this skill directly.** It is loaded by `doing-code-review` and `review-plan`, which provide the execution framing and output format for each context.

## Agents

| File | Focus |
|---|---|
| `quality.md` | Bugs, logic errors, edge cases, error handling, correctness, type safety |
| `implementation.md` | Requirement coverage, wiring, completeness, return value propagation |
| `architecture.md` | God classes, SOLID, DDD, CQRS, clean architecture, aggregates, value objects |
| `testing.md` | Test coverage, quality, fake tests, independence |
| `simplification.md` | Over-engineering, excessive abstraction, premature generalization |
| `documentation.md` | Missing documentation updates for user-visible changes |
| `security.md` | Injection, secrets, input validation, data leakage, auth |
| `concurrency.md` | Race conditions, transactional scope, isolation, locking gaps |
| `premortem.md` | Design-level failure modes, operational risks, prospective hindsight |

## How orchestrating skills use these agents

**Code review context** (`doing-code-review`): agents receive the git diff and key source files, return `{path, line, side, body, severity: Low/Medium/High/Critical}`. The `body` must meet §4.12 depth in `doing-code-review` for its severity (Medium+ requires four titled sections inline). Returns must be self-contained so the orchestrator can dedup, spot-check, and stage without re-reading sources or re-authoring analysis.

**Plan review context** (`review-plan`): agents receive the plan document and referenced source files, return `{location_in_plan, issue, severity: Block/Mitigate/Monitor/Accept, fix}`. Each return must include **evidence** (what was read, what the source shows) and a concrete fix — not issue stubs the orchestrator must research.

The pattern catalogs in each agent file are context-neutral. Execution framing, output depth, and completeness requirements are injected by the orchestrating skill.
