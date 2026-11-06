# Backlog: execute-plan conflates project test policy with plan validation scope

Status: open
Workflow: backlog
Priority: high
Origin class: self-serving
Consumer urgency: Company-scoped projects that consume execute-plan require the complete repository suite before final completion; do not defer this shared-skill correction as skills-repository formal-hardening.
Class: fix-class
Driving force: efficiency + consistency
Cluster: docs/history/backlog/2026-10-24-liveness-pin-plans-archive-twin-span-missing.md (prior full-suite catch that motivated the shared execution policy; retain its focused regression coverage)

## Problem

The execute-plan contract unconditionally runs the complete repository-standard suite for ordinary plans and stack-task runs (`agents/skills/execute-plan/SKILL.md`, Phase 2 and stack-task entry; `agents/skills/execute-plan/runtime-contract.md`, Stack-task entry and ordinary full-plan lifecycle). It has no explicit per-project suite policy. This makes the shared workflow select a full suite even when the target repository's intended policy is narrower.

The 2026-11-02 review-freshness plan listed two focused pytest cases under `Validation Commands` and separately said the full repository-standard suite must pass in `Done when`. These are distinct obligations: the former are plan-specific witnesses, while execute-plan adds the project-level suite. The earlier session report called this wording an ambiguity; that diagnosis conflated the two scopes. The remaining gap is that the skill does not let the target project's policy narrow or require the repository suite explicitly.

Expected behavior: resolve plan-specific validations and target-project test policy as separate inputs. Company-scoped projects run their complete standard suite before final completion. The ai-playbook skills repository never runs its whole test suite during plan execution; it runs the plan's relevant focused tests and required repository gates. Other repositories follow their own explicit test policy. Plan authoring states these categories separately and brings a missing or conflicting project policy to the operator before certification.

## Exact location

- `agents/skills/execute-plan/SKILL.md`, Phase 2 and stack-task entry.
- `agents/skills/execute-plan/runtime-contract.md`, stack-task and ordinary full-plan requirements.
- `agents/skills/plans/validation-authoring-rules.md`, project versus plan validation authoring.
- `projects/.ai-playbook/coding_guidelines.md`, this repository's test guidance.

## Reproduction evidence

- `docs/history/plans/completed/2026-11-02-review-freshness-and-code-coverage-gaps.md`, `Done when`, `Validation Commands`, and `Review Scope > Tests` distinguish the complete suite requirement from two focused pytest cases.
- `docs/history/plans/completed/2026-10-29-stacked-pr-plan-execution.md` introduced the full-suite requirement after a missed liveness suite left the base red. It records unknown expected catch frequency and an initial policy review date of 2026-11-29; the corrective policy must preserve targeted coverage for the witnessed liveness regression.
- Implementation landed as `7d4d3f7a24794b2a60014ff8556345fdb9420179` at 2026-11-04 05:07 UTC; plan archive landed as `0085b695c797c8fef457485fa1e8bd0721beb507` at 10:58 UTC. The elapsed time was mostly worktree recovery, rebases, review refresh, and archive/closeout repair, not test runtime.
- Session records for this plan show the two focused pytest cases passing in 10.48s and 17.66s. A separate machinery-inventory authoring worktree also ran those two cases in about 10.55s. No whole-repository suite invocation or multi-hour test runtime is evidenced for this plan.
- A later execution of `docs/history/plans/completed/2026-11-03-certification-gates-full-violation-reporting.md` provides a separate current witness: on 2026-11-06 its refreshed 84-suite Phase 2 run was stopped by the operator after 23 suites completed and 123 tests passed in `test_done_run_wrapper.py`; 60 suites remained unrun and Phase 2 was recorded incomplete (commit `803cc1584`). This is an interrupted validation, not an assertion failure or a full-suite pass.
- This repository currently has 84 `scripts/test_*` files. That is an inventory count, not a measured full-suite runtime. No profiling evidence supports rewriting the tests in Rust or Go.
- On 2026-11-04 the operator clarified the intended policy: complete-suite validation is required for company-scoped project execution, while the ai-playbook repository must never run its whole suite.

## Suspected root area

The execute-plan skill treats “repository-standard suite” as a universal run requirement instead of resolving an explicit policy from the target repository. Plan authoring does not provide a clear place to state the plan-specific test set separately from project-wide final validation. The prior session diagnosis also failed to read those as two separate requirements. The universal requirement was added to catch a missed liveness regression, but no ai-playbook full-suite catch or multi-hour test cost is evidenced here; preserve that protection through relevant focused suites instead of overriding the user's ai-playbook policy.

## Fix shape

Add a project-policy resolution to execute-plan and an authoring distinction in plans. Represent plan-specific validation commands and target-project final validation as separate requirements. Honor `never run the whole suite` for this skills repository and `full suite before final completion` for company-scoped projects. Define behavior for other or missing policies without silently promoting focused commands to a full suite or skipping an explicit requirement. Plan authoring lists the two scopes separately and brings any apparent conflict between plan text and project policy to the operator before certification. For this repository, never invoke the whole suite under ordinary, stack-task, or recovery execution; select relevant regression tests and run the named repository gates.

Do not rewrite the suite in Rust or Go without a measured profile identifying language-runtime overhead as the dominant cost. First establish a reproducible baseline and identify slow tests or subprocess costs; prefer targeted selection or test-harness improvements when they address the measured bottleneck.

## Severity and source

Severity: Medium; the universal suite mandate can spend substantial time in repositories whose policy does not require it, while the absence of an explicit project-policy resolution can obscure a company project's required final suite.
Source: operator correction and execution records from the 2026-11-04 run; plan and commit references above.

## Why not fixed now

This request authorized incident analysis and durable backlog capture. Changing shared execution and authoring contracts affects every consuming repository and needs a focused, reviewed plan that preserves the company-project full-suite requirement.

## Dedup probe

Searched open backlog filenames and problem bodies for `repository-standard suite`, `full suite`, `complete suite`, `test scope`, and `suite policy`. The nearest item is `docs/history/backlog/2026-11-02-plan-done-when-enumeration-gap.md`, which concerns a plan omitting a deliverable from its Done-when list; it does not address the two-tier test policy or per-project suite resolution. No open item covers this root cause.

Environment: Codex, 2026-11-04; self-serving issue in the shared skills repository runtime.
Capture hygiene: public-hygiene and em-dash scans required before commit.
