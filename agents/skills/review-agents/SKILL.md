---
name: review-agents
description: "Shared sub-agent pattern catalog used by doing-code-review, review-plan, review-confluence-doc, and rfc-design. Not meant to be invoked directly. Contains quality, implementation, architecture, testing, simplification, documentation (missing docs + prose), security, concurrency, premortem, and review-panel-selection."
---

# Review Agents (Shared Pool)

This skill is a shared library of review sub-agent pattern catalogs.

**Do not invoke this skill directly.** It is loaded by `doing-code-review`, `review-plan`, `review-confluence-doc`, and `rfc-design`, which provide the execution framing and output format for each context.

**Panel selection:** orchestrators read `review-panel-selection.md` for the recommended five-worker panel, focused panels, conditional lenses, escalation, launch accounting, and tiered ownership.

**Severity:** orchestrators prepend `severity-calibration.md` to every worker prompt. Code, plan, RFC, and document reviews all use `Critical`, `High`, `Medium`, and `Low`, with independent blocking status.

## Agnostic catalogs vs loadable conventions

| Layer | Where | Contains |
|-------|-------|----------|
| Pattern catalogs | `review-agents/*.md` (this skill) | Language- and project-agnostic defect shapes and `pattern` IDs |
| Language / stack overlays | `doing-code-review/<overlay>.md` | Stack triggers that map abstract patterns to framework APIs |
| Guideline Pack | Built by `doing-code-review` Step 2.5 from facts | Shared language guidelines (`shared_docs_dir`); when company-scoped, **company guidelines** (`company_guidelines_master` under `company_ownership_docs_dir`) **together with** project guidelines (`project_guidelines_rel`) |

**Do not** put a single project's test-class suffixes, runner names, or module paths into these catalogs as universal requirements. Express the abstract rule here; let overlays name framework types; let the Guideline Pack (company + project when company-scoped) and in-repo sibling tests name local conventions.

## Agents

| File | Focus |
|---|---|
| `severity-calibration.md` | **Prepend for code review.** Tier definitions, decision procedure, category defaults |
| `quality.md` | Bugs, logic errors, edge cases, error handling, correctness, type safety |
| `implementation.md` | Requirement coverage, wiring, completeness, return value propagation |
| `architecture.md` | God classes, SOLID, DDD, CQRS, clean architecture, aggregates, value objects |
| `testing.md` | Test coverage, quality, fake tests, independence, hermeticity (ambient inputs) |
| `simplification.md` | Over-engineering, excessive abstraction, premature generalization; tagged output (`delete:`, `stdlib:`, `native:`, `yagni:`, `shrink:`) |
| `documentation.md` | Missing docs for user-visible changes; prose clarity (merged from legacy `prose-clarity.md`) |
| `review-panel-selection.md` | Default panels, conditional launch rules, tiered ownership (orchestrator reference; not a sub-agent) |
| `security.md` | Injection, secrets, input validation, data leakage, auth |
| `concurrency.md` | Race conditions, transactional scope, isolation, locking gaps |
| `premortem.md` | Design-level failure modes, operational risks, prospective hindsight |

## How orchestrating skills use these agents

**Code review context** (`doing-code-review`): prepend `severity-calibration.md`, then the specialist agent file, then the language overlay, then the **Guideline Pack** index (paths + section hints; workers open sections on demand). Agents receive the git diff and key source files (run `git diff <base>...<head>` directly, or read `{tmp_dir}/.../diff-r<R>.patch` / `src-diff-r<R>.patch` when the orchestrator materialized snapshots under `{tmp_dir}/` per **Diff access** in `doing-code-review`). Never write review/diff captures to the repo root; on stdout truncation prefer the runtime's saved capture or `{tmp_dir}/code-review/<slug>/` (canonical rule in `agent_workflow_guidelines.md` §50.3.2). Return `{path, line, side, body, severity: Low/Medium/High/Critical, pattern: <agent>#<kebab-slug>}` per `severity-calibration.md`. The `body` must meet §4.12 depth in `doing-code-review` for its severity (Medium+ requires four titled sections inline). Actionable code/test/config fixes at any severity must include a §4.9.0 snippet in `body`; test snippets should assert via fixture getters, not duplicated literals. Returns must be self-contained so the orchestrator can dedup, spot-check, and stage without re-reading sources or re-authoring analysis.

**Plan review context** (`review-plan`): workers receive the plan and referenced source files, load their assigned lenses, and return `{location_in_plan, issue, severity, blocking, consequence, reachability, blast_radius, confidence, fix, evidence, pattern, descendant_launches}`.

**Confluence doc context** (`review-confluence-doc`): workers receive the full fetched page content and return the shared finding fields plus a quoted excerpt. `contract-docs` is mandatory for document prose; focused panels add other workers only when their domains are present.

**RFC design context** (`rfc-design`): workers receive the draft and original inputs, use the shared severity fields, and preserve the originating lens pattern. Light depth may use a focused panel; Full depth uses the five-worker panel.

The pattern catalogs in each agent file are context-neutral. Execution framing, output depth, and completeness requirements are injected by the orchestrating skill.

**Pattern tag deprecation:** orchestrators accept legacy `prose-clarity#<slug>` in historical reviews; new findings use `documentation#prose-<slug>` or `documentation#missing-<slug>`. Do not emit new `prose-clarity#` tags.

**Review Statistics:** orchestrators record actual worker launches, loaded lenses, parent worker, raw and Solo/Echo counts, pattern tags, calibration, discarded returns, and overflow per `review-staging`.
