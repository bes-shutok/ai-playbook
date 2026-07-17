---
name: review-agents
description: "Shared sub-agent pattern catalog used by doing-code-review, review-plan, review-confluence-doc, and rfc-design. Not meant to be invoked directly. Contains quality, implementation, architecture, testing, simplification, documentation (missing docs + prose), security, concurrency, premortem, and review-panel-selection."
---

# Review Agents (Shared Pool)

This skill is a shared library of review sub-agent pattern catalogs.

**Do not invoke this skill directly.** It is loaded by `doing-code-review`, `review-plan`, `review-confluence-doc`, and `rfc-design`, which provide the execution framing and output format for each context.

**Panel selection:** orchestrators read `review-panel-selection.md` for default panels, conditional launch (`premortem`, `concurrency`), and tiered ownership before launching sub-agents.

**Code review severity:** orchestrators prepend `severity-calibration.md` to every sub-agent prompt alongside the specialist file. RFC/plan reviews use caller-specific severity labels but should apply the same impact-first reasoning where applicable.

## Agents

| File | Focus |
|---|---|
| `severity-calibration.md` | **Prepend for code review.** Tier definitions, decision procedure, category defaults |
| `quality.md` | Bugs, logic errors, edge cases, error handling, correctness, type safety |
| `implementation.md` | Requirement coverage, wiring, completeness, return value propagation |
| `architecture.md` | God classes, SOLID, DDD, CQRS, clean architecture, aggregates, value objects |
| `testing.md` | Test coverage, quality, fake tests, independence |
| `simplification.md` | Over-engineering, excessive abstraction, premature generalization; tagged output (`delete:`, `stdlib:`, `native:`, `yagni:`, `shrink:`) |
| `documentation.md` | Missing docs for user-visible changes; prose clarity (merged from legacy `prose-clarity.md`) |
| `review-panel-selection.md` | Default panels, conditional launch rules, tiered ownership (orchestrator reference; not a sub-agent) |
| `security.md` | Injection, secrets, input validation, data leakage, auth |
| `concurrency.md` | Race conditions, transactional scope, isolation, locking gaps |
| `premortem.md` | Design-level failure modes, operational risks, prospective hindsight |

## How orchestrating skills use these agents

**Code review context** (`doing-code-review`): prepend `severity-calibration.md`, then the specialist agent file. Agents receive the git diff and key source files (run `git diff <base>...<head>` directly, or read `{tmp_dir}/.../diff-r<R>.patch` / `src-diff-r<R>.patch` when the orchestrator materialized snapshots under `{tmp_dir}/` per **Diff access** in `doing-code-review`). Return `{path, line, side, body, severity: Low/Medium/High/Critical, pattern: <agent>#<kebab-slug>}` per `severity-calibration.md`. The `body` must meet §4.12 depth in `doing-code-review` for its severity (Medium+ requires four titled sections inline). Actionable code/test/config fixes at any severity must include a §4.9.0 snippet in `body`; test snippets should assert via fixture getters, not duplicated literals. Returns must be self-contained so the orchestrator can dedup, spot-check, and stage without re-reading sources or re-authoring analysis.

**Plan review context** (`review-plan`): agents receive the plan document and referenced source files, return `{location_in_plan, issue, severity: Critical/Suggestion/Advisory, fix, evidence, pattern: <agent>#<kebab-slug>}`. Each return must include **evidence** (what was read, what the source shows) and a concrete fix; not issue stubs the orchestrator must research.

**Confluence doc context** (`review-confluence-doc`): agents receive the full fetched page content (and child pages when applicable). Return `{section_anchor, issue, severity: Critical/Suggestion/Advisory, fix, pattern: <agent>#<kebab-slug>}` with a quoted excerpt of the prose under review. `documentation.md` (phase 2 prose) is mandatory for document prose; other agents run only when implementation logic is present (see `review-confluence-doc` Step 4.6).

**RFC design context** (`rfc-design`): agents receive the Step 1 RFC draft plus original inputs when available. Return `{section_anchor, quoted_excerpt, issue, severity: Block/Mitigate/Monitor/Accept, fix, evidence, pattern: <agent>#<kebab-slug>}`. **Light** depth runs quality, implementation, security, architecture, simplification, documentation, and inline consistency; **Full** depth runs all agents (see `rfc-design` Step 2). Findings fold into RFC sections per severity map; staging file lives under `{reviews_dir}/`.

The pattern catalogs in each agent file are context-neutral. Execution framing, output depth, and completeness requirements are injected by the orchestrating skill.

**Pattern tag deprecation:** orchestrators accept legacy `prose-clarity#<slug>` in historical reviews; new findings use `documentation#prose-<slug>` or `documentation#missing-<slug>`. Do not emit new `prose-clarity#` tags.

**Review Statistics:** orchestrators must record per-agent raw finding counts, Solo/Echo staged counts, Pattern tags, Severity calibration, and discarded returns in the staging doc `## Review Statistics` section (see `review-staging`). Each staged finding lists originating agent id(s) in **Agents** and the closest **Pattern** id.
