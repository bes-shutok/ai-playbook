---
name: review-plan
description: >
  Review implementation plans for correctness, completeness, and risks. Orchestrates parallel
  sub-agents that analyze different quality dimensions of a plan document. Use when a plan is
  written or updated and needs validation before execution. Trigger phrases: "review the plan",
  "review plan", "check the plan", "validate the plan", "plan review".
---

# Plan Review

## Boundary

Use this skill for **reviewing implementation plan documents** under resolved `{plans_dir}/` (see `_shared/doc-paths.md`).

Do not use for:
- Reviewing actual code diffs (use `doing-code-review`)
- Creating or editing plans (use `plans`)
- General premortem stress-testing of ideas (use `premortem`)

## When to Run

- After creating or significantly updating a plan
- Before starting execution of a plan
- When asked to "review the plan" or "validate the plan"

## Step 1: Load Plan and Context

1. Read the plan file in full
2. Identify all source files referenced in the plan (from Review Scope, Task file lists)
3. Read key referenced source files to understand current code shape (function signatures,
   data structure definitions, pipeline order, return types)
4. **Existing-method modification audit**: for every existing method the plan modifies, compute
   pre-change line count and the new line count implied by the planned edits. Flag any
   post-modification method that would exceed repo complexity limits (cyclomatic, nesting depth,
   line length — see repo-specific overrides in Step 2 item 5). New methods get audited by the
   relevant agent; modifications to existing methods are easy to miss otherwise.
5. **Replacement / supersession map**: list any new class, enum, method, or table the plan
   introduces that overlaps in purpose with existing code (e.g. a new policy enum that supersedes
   a static-constants class). For each, check whether the plan also deletes the original or
   justifies retention. Unaddressed supersession is a finding for the simplification agent.

## Step 2: Launch Sub-Agents in Parallel

Launch ALL review agents simultaneously using your agent's parallel execution capability
(e.g., background execution mode, parallel sub-agent launch, or equivalent mechanism).
Wait for all agents to complete before proceeding.

Each agent receives:
1. The full plan content
2. Relevant source file excerpts (signatures, data structure definitions, pipeline structure)
3. Its specific review lens from `~/.agents/skills/review-agents/<agent>.md`
4. The project's CLAUDE.md content (for repository conventions)
5. **Repo-specific overrides take precedence**: if `CLAUDE.md`, `{guidelines_path}` (resolved per `_shared/doc-paths.md`; typically `docs/maintenance/project-guidelines.md`), or any loaded company/project guideline defines complexity, naming, comment, or layering rules that conflict with the generic pattern catalog, the agent MUST apply the repo-specific value, not the catalog default. Example: catalog says "functions >50 lines" but `company-guidelines.md #17` says "≤30 lines per method" — apply the 30-line rule.
6. **Execution framing**: "You are reviewing an IMPLEMENTATION PLAN, not a code diff. Read the plan tasks and the referenced source files to understand what is being proposed. Apply your pattern catalog to identify whether the proposed changes would introduce the issues you are responsible for detecting."
7. **Output format**: for each finding provide `{location_in_plan, issue, severity: Blocker/Medium/Low/Monitor, fix, evidence}` — no `path/line/side` fields (those are for code review). **`issue` and `evidence` must be self-contained**: name the plan task, quote or paraphrase the contradicting plan text, cite what the referenced source file shows, and state the concrete fix. Do not return stubs the orchestrator must research.

### Shared agents (from `~/.agents/skills/review-agents/`)

| Agent file | Focus in plan context |
|---|---|
| `quality.md` | Will the proposed algorithm produce correct results? Data type/API assumption errors? |
| `implementation.md` | Missing wiring, return value propagation gaps, backward compatibility holes |
| `architecture.md` | Would the proposed design introduce SOLID violations, layer crossings, god classes? |
| `testing.md` | Are the described tests sufficient? Could a test pass even if the implementation is wrong? |
| `simplification.md` | Is the planned approach over-engineered for the problem? |
| `documentation.md` | Are docs for user-visible behavior changes included in the plan? |
| `security.md` | Would the proposed changes introduce security vulnerabilities? |
| `concurrency.md` | Would the proposed changes introduce race conditions or transactional scope issues? |
| `premortem.md` | Design-level failure modes; "it shipped and failed — why?" |

### Plan-specific agent (inline — no shared file)

#### Consistency Agent

```
Review this implementation plan for internal contradictions and alignment issues.

Check:
1. Design invariants vs task descriptions: Does any task step violate a stated
   design invariant? Are invariants complete (missing guards)?
2. Test expectations vs implementation: Do tests expect behavior X while the
   implementation description says Y?
3. Cross-task coherence: Does Task N produce output that Task M expects in the
   right format? Are intermediate states valid?
4. Naming consistency: Are the same concepts named identically across tasks?
   (e.g., function names, field names, parameter names)
5. Commit boundaries: Can each commit compile independently? Does splitting
   across commits create broken intermediate states?
6. Stale references after restructuring: After any renumber, file-move, package-change,
   or path change in the plan, scan ALL file paths AND all task cross-references
   (e.g. "Tasks 1–N", "see Task M") for staleness. A path that still says `domain/`
   after the file moved to `application/`, or a "Tasks 1–7" reference after the plan
   grew to 10 tasks, must be flagged.
7. Evaluation Criteria substance: Does the plan's Evaluation Criteria section contain
   specific, verifiable criteria (e.g. "API returns 404 for unknown IDs", "batch completes
   within 5s at 10k records")? Vague criteria like "it should work" or "tests pass" must
   be flagged as a Medium finding.

For each finding, provide:
- The two contradicting statements (with task numbers)
- Which one is correct (based on source code and domain rules)
- Severity: Blocker / Medium / Low
- Evidence: what was read in source files or plan text that supports the finding
- Suggested resolution
```

## Step 3: Synthesize Findings

After all sub-agents complete, **synthesize from agent returns only** — do not re-read source files or re-analyze the plan in the orchestrator context. The orchestrator dedups, ranks, and formats; sub-agents already did the reading and reasoning.

1. **Deduplicate**: Merge findings that describe the same root issue from different angles
2. **Rank by severity**:
   - **Blocker** — must address before execution
   - **Medium** — should add safeguard, test, or step to plan
   - **Low** — minor improvement, optional in plan revision
   - **Monitor** — note as risk, add observability
3. **Cross-reference with plan**: For each finding, note whether the plan already
   addresses it (and mark as "Already mitigated" if so)
4. **Incomplete agent output**: if a finding lacks `evidence` or a concrete `fix`, relaunch that agent focused on the gap — do not fill it inline

## Step 4: Output

Write the review to `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md` (resolve `{reviews_dir}` per `_shared/doc-paths.md`; use `-r1`, `-r2`, … per loop iteration):

```markdown
# Plan Review: <Plan Title>

**Date:** YYYY-MM-DD
**Plan:** `{plans_dir}/<filename>.md`
**Prior:** `{reviews_dir}/<prior-rN>.md` *(omit on r1)*
**Agents:** quality, implementation, architecture, testing, simplification, documentation, security, concurrency, premortem, consistency

## Summary

<1-2 sentence overall assessment>
**Counts:** Blockers: N | Medium: N | Low: N | Monitor: N
**Ready for execution:** Yes/No (Yes only when Blocker=0 AND Medium=0)

## Blockers

### 1. <Title>
- **Agent:** quality | implementation | architecture | testing | simplification | documentation | security | concurrency | premortem | consistency
- **Location:** Task N, bullet M
- **Issue:** <concrete description>
- **Evidence:** <what the source code shows>
- **Fix:** <specific change to the plan>

## Medium

### 1. <Title>
- **Agents:** ...
- **Location:** ...
- **Issue:** ...
- **Suggested addition:** <new step, invariant, test, or scope entry required before execution>

## Low

### 1. <Title>
- **Agents:** ...
- **Location:** ...
- **Issue:** ...
- **Fix:** <optional one-line plan clarification>

## Monitor

### 1. <Title>
- **Agent:** Risks
- **Scenario:** ...
- **Observability:** <what logging/metrics to add>

## Accepted Risks

### 1. <Title>
- **Rationale:** ... (Low findings the plan author chooses not to address)

## Amendments

| # | Finding | Affects | Action |
|---|---------|---------|--------|
| 1 | ... | Task N | Add step / revise step / new invariant |
```

## Step 5: Amend Plan

After writing the review document:

1. For each **Blocker**: update the affected plan task directly (mandatory before next review round)
2. For each **Medium**: update tasks, invariants, tests, or Review Scope (mandatory before next review round)
3. For each **Low**: fold trivial fixes into the plan; otherwise leave in the review artifact
4. For each **Monitor**: add/update the plan's `## Monitor` section with named owner
5. Add a reference line to the plan header: `Plan review: {reviews_dir}/<latest-rN>.md (latest, ready) · …`
6. If the plan has a final validation task, add verification commands for each Blocker/Medium finding

Report to user:
> "Plan review r<N> complete: B blockers, M medium (fixed in plan), L low, Mon monitor.
> Review saved to `{reviews_dir}/<filename>-r<N>.md`.
> Ready for execution: Yes/No (requires Blocker=0 and Medium=0)."

## Iteration Discipline (plans skill gate)

When the user asks to run reviews until clean (e.g. "no medium problems", "until ready"):

1. **Exit condition and minimum rounds:** see `plans` skill Plan Quality Gate (Blocker=0 AND Medium=0, minimum two rounds).
2. **Severity alignment:** agents emit Blocker/Medium/Low/Monitor directly; no mapping step needed.
3. **Treat a clean review as data, not as a terminal verdict.** A 0 Blocker / 0 Medium outcome can mean either (a) the plan is correct, or (b) the agent catalog lacks patterns to detect defects. Run the self-audit below before stopping after only one round.
4. **Run a brief self-audit alongside the agent review.** Before declaring iteration complete, scan the change types introduced by the latest plan revision (new domain types, decomposed methods, replaced classes, modified existing methods, restructured tasks) and verify the catalog has an active pattern for each. If a change type has no corresponding pattern in `~/.agents/skills/review-agents/*.md`, the agents cannot detect defects of that class.
5. **Catalog gap discovered → update the skill before re-iterating.** If the self-audit identifies a missing pattern (e.g. "no agent owns 'type-boundary discipline'", "no agent enumerates switches", "no agent checks for superseded code"), add the pattern to the relevant agent file FIRST, then re-run the review. Patching the plan around a catalog gap leaves the gap for future plans.
6. **Stop when both conditions hold**: the latest review reports Blocker=0 AND Medium=0 (minimum two rounds completed) AND a self-audit against the change types in the plan finds no additional concerns the catalog would have missed.
7. **Record self-audit gaps as catalog improvements**, not as one-off plan patches. When the self-audit found something the catalog missed, the fix is two-part: patch the plan AND update the agent file or `SKILL.md`. The catalog improvement is the persistent gain; the plan patch is local.

## Signal-to-Noise Rules

Adapted from `doing-code-review`:

- **Report problems only.** No positive observations or praise.
- **No vague concerns.** Every finding must name specific components, data flows, or functions.
- **Skip findings the plan already addresses.** Read the full plan (including Design Invariants)
  before generating findings.
- **No style/formatting findings** on the plan document itself.
- **Evidence-gated findings:** correctness claims must be backed by reading the actual source
  file. Do not assume — verify.
- **2-3 findings max per agent.** Quality over quantity. If an agent finds nothing credible,
  it reports "No findings."
