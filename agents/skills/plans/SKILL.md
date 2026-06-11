---
name: plans
description: "Full plan lifecycle — create, edit, and complete implementation plans. Use when writing a new plan, updating an existing one, or marking a plan done (moving to docs/plans/completed/). Trigger phrases — \"create a plan\", \"create plan\", \"write a plan\", \"write plan\", \"make a plan\", \"implementation plan\", \"update the plan\", \"update plan\", \"plan for\", \"plan as per\", \"plan based on\", \"plan is done\", \"mark plan complete\", \"plan complete\"."
---

# Plans

**Announce at start (create):** "I'm using the plans skill to create the implementation plan."

**Announce at start (update / complete):** "I'm using the plans skill to update the plan." (or "…mark the plan complete.")

**Create vs update:** Run **Phase 0 (branch setup)** and **Phase 1 (requirements discovery)** only when **creating** a new plan. Skip both phases for plan updates or completion unless the repo is in detached HEAD or the user asks to switch branches.

**Writing:** Follow `agent_workflow_guidelines.md` §45. Use plain English in **Gist & Examples** and **Design Invariants** (e.g. "public API response shape unchanged", not "wire contract stable"). Add `## Terms` after the title when the plan uses 3+ project-specific words. TDD labels (RED/GREEN) stay in task checklists only.

**Exploration discipline:** When creating a plan, use targeted grep/glob to find file paths, class names, and method signatures. Do not read full test files or deeply explore implementation details beyond what is needed to write accurate file paths and test method names in plan tasks. Produce the plan file promptly — do not keep exploring after you have enough to write the tasks. **Before writing any exact file path in a plan task, verify it exists** with glob/bash — an unverified path is a review blocker that only the quality gate catches.

**For detailed plan quality guidance:** If the project has `docs/domain/plan_quality_guidelines.md`, consult it for domain-specific examples and patterns. Otherwise, see Universal Patterns below.

**When updating or optimizing an existing plan:** compare the plan against the current code shape, the RFC/PRD, and any predecessor phase plans before editing. Prefer patching the plan directly when improvements are clear. **Also verify all required sections are present** (`## Gist & Examples`, `## Evaluation Criteria`, `## Review Scope`, `## Validation Commands`) — pre-existing plans may be missing them; add any absent sections before making other edits. **When the update notes that a code change is "already done", read the actual source file to verify the claim** — do not rely on session summaries or memory; an incorrect "already done" note becomes a review blocker.

**Save plans to:** `docs/plans/<STORY-KEY>-<feature-name>.md` (story key prefix) or `docs/plans/YYYY-MM-DD-<feature-name>.md` (date prefix when no story key applies).

**CRITICAL:** Plans go in `docs/plans/` in the project repository — never in tool-default locations (`.claude/plans/`, `.opencode/plans/`, `.codex/`, `.cursor/`, etc.). When a tool suggests its own default path, override it and write to `docs/plans/` instead.

**For company projects:** Design RFCs go in `docs/rfcs/`. When a plan implements an RFC, add a one-line reference to it in the plan header (the optional line below the `# Plan:` title).
When an RFC phase already has its own implementation Jira task, use that phase task key in the plan filename and title instead of the parent RFC/story key; keep the RFC reference line in the header for traceability.

## Phase 0: Branch Setup (Run Once at Plan Creation Start)

Before writing the plan file, set up a dedicated branch when appropriate. Planning often overlaps with early exploration, scaffolding, and the first commits — isolating that work on a feature branch keeps `main`/`develop` clean and aligns the plan with the branch that will carry implementation.

**Announce:** "Before creating the plan, I'll set up a dedicated branch. This keeps planning and implementation isolated from other work."

### Step 0.1 — Propose branch creation

Ask the user for confirmation to create a new branch:

**Branch naming convention:**

1. Extract Jira task ID from user context if present (pattern: `[A-Z]+-\d+`, e.g. `PROJ-1234`)
2. If found: branch name = `<JIRA-TASKID>-<short-description>`
3. If not found: branch name = `YYYY-MM-DD-<short-description>`

`<short-description>` is derived from the feature name or planned plan slug, kebab-case, max ~40 chars.

Ask the user:

```
I'll create a new branch for this plan:
- Base: current branch (<current-branch>)
- New branch name: <computed-branch-name>
- This branch will track origin (push -u on first commit)

Proceed with branch creation? (yes/no)
```

Wait for explicit user confirmation before proceeding.

### Step 0.2 — Create and push the branch

If the user confirms (yes):

```bash
# From user context / ticket / proposed filename
JIRA_ID="<PROJ-1234-or-empty>"
FEATURE_DESC="<short feature description>"

if [ -n "$JIRA_ID" ]; then
    SHORT_DESC="$(echo "$FEATURE_DESC" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g' | sed 's/-$//' | cut -c1-40)"
    BRANCH_NAME="${JIRA_ID}-${SHORT_DESC}"
else
    SHORT_DESC="$(echo "$FEATURE_DESC" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g' | sed 's/-$//' | cut -c1-40)"
    BRANCH_NAME="$(date +%Y-%m-%d)-${SHORT_DESC}"
fi

git checkout -b "$BRANCH_NAME"
git push -u origin "$BRANCH_NAME"
```

If the user declines (no):

```
Understood. I'll proceed on the current branch: <current-branch>
Note: Plan work and any early commits will mix with existing changes on this branch.
```

### Step 0.3 — Verify branch state

Before writing the plan file:

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "No tracking branch yet"
```

If detached HEAD: refuse to proceed and ask the user to create or switch to a branch first.

Report the final branch state to the user before continuing.

**Hard gate:** Do not write the plan file until branch setup is complete or explicitly declined by the user.

## Phase 1: Requirements Discovery & Validation (Run Once at Plan Creation Start)

After branch setup and before writing the plan content, interview the user to validate requirements, scope, and key decisions. This prevents wasted effort on misunderstood goals or over-scoped plans.

**Announce:** "Now I'll validate requirements and key decisions before writing the plan. This ensures we build the right thing with clear boundaries."

### Step 1.1: Discover the real goal

Ask targeted questions to uncover the actual objective, not just the surface request:

1. **What problem does this solve?** Ask for the motivating problem or user pain point
2. **What does success look like?** Ask for concrete examples of the working end state
3. **Who is this for?** Ask which user, component, or system will consume this work
4. **What stays the same?** Ask what must NOT change (invariants, existing behavior, API contracts)

Bias the user toward **small, compartmentalized specs**:
- If the scope covers multiple independent concerns, suggest splitting into separate plans
- If the plan mixes refactoring with new behavior, suggest separating them
- If the plan touches multiple layers (UI, business logic, data), ask which layer is the primary goal

### Step 1.2: Verify key decisions explicitly

Before proceeding, explicitly confirm each critical decision with the user. When the decision involves a trade-off with multiple reasonable paths, present structured options to the user:

**Confirm these elements:**
1. **Scope boundaries:** what is IN vs OUT
2. **Primary success criterion:** the one observable behavior that defines "done"
3. **Key invariants:** what must NOT break or change
4. **External dependencies:** what teams, systems, or migrations this depends on
5. **Rollout strategy:** single deploy vs phased rollout

**Example confirmation questions:**

- "Is this correct? The primary goal is X. Success means Y. We must not break Z."
- "Should this plan handle both A and B, or just A (with B deferred to a separate plan)?"
- "Is the rollout a single deploy or phased across multiple releases?"
- "Does this depend on any external work (other teams, migrations, infra changes)?"

For each confirmed decision, record it to a temporary notes buffer (write to `docs/tmp/plan-requirements-<slug>.md`). This becomes input for the `## Gist & Examples` section.

### Step 1.3: Define evaluation criteria

Before writing tasks, define explicit criteria for evaluating whether the final product is high-quality. Ask the user to refine:

**Ask:**
1. **What quality dimensions matter most for this change?** (examples: correctness, performance, maintainability, security, test coverage, observability)
2. **What metrics or checks will verify success?** (examples: specific test commands, load test targets, latency SLO checks, security scan results)
3. **What are the release gates?** (examples: code review approval, CI passing, performance regression tests, security sign-off)

Write these to the requirements buffer as `## Evaluation Criteria`. This becomes a required section in the final plan.

### Step 1.4: Confirm and proceed

Present the validated requirements and evaluation criteria back to the user in summary form:

```
## Validated Requirements

**Goal:** <one-sentence objective>

**Scope boundaries:**
- IN: <what this plan delivers>
- OUT: <what is explicitly deferred>

**Success criterion:** <primary observable behavior that defines done>

**Key invariants:** <what must not break>

**Evaluation criteria:**
- <quality dimension>: <specific check or metric>
- <quality dimension>: <specific check or metric>

**Release gates:** <what must pass before this can ship>

Proceed with writing the plan? (yes/no; if no, tell me what to adjust)
```

Wait for explicit confirmation before proceeding to write the plan file. If the user asks to adjust, update the requirements buffer and reconfirm.

**Hard gate:** Do not write the plan file until requirements are validated and confirmed.

## Plan Format

Every plan follows this exact structure — no variations:

```markdown
# Plan: <Feature Name>

[Optional: one-line reference to RFC/PRD/ticket]

[Optional: ## Terms — required when 3+ project-specific terms; see agent_workflow_guidelines.md §45]

## Gist & Examples

[Human-readable explanation of what changes and why, with concrete examples]

## Evaluation Criteria

[Specific criteria for evaluating whether the final product is high-quality]

**Quality dimensions:**
- <dimension> (e.g., correctness, performance, maintainability): <specific check or metric>
- <dimension>: <specific check or metric>

**Release gates:**
- <what must pass before this can ship>

## Review Scope

Files directly changed as part of this plan. Review feedback is accepted **only** for the files listed here.
Any finding about a file not in this list must be rejected as out of scope.

**Production code — in scope:**
- `path/to/NewFile.ext` *(new)*
- `path/to/ExistingFile.ext`

**Tests — in scope:**
- `path/to/NewTest.ext` *(new)*

**Out of scope — reject all review feedback:**
- `path/to/UnrelatedFile.ext` — reason

## Validation Commands

```bash
<test-command>
```

### Task 1: [Name]

Files:
- `path/to/NewFile.ext` *(new)*
- `path/to/ExistingFile.ext`

- [ ] `SomeClassTest#methodName` — given `<input/scenario>`, expects `<outcome>`
- [ ] `SomeClassTest#methodName_edgeCase` — given `<boundary condition>`, expects `<outcome>`
- [ ] Run → expect RED: `<test-command>`
- [ ] Write minimal implementation
- [ ] Run → expect GREEN
- [ ] Commit: `feat: <short description>`
```

**Test item format — required:**

Every test item must be self-contained so a reader can understand what will be verified without reading the code:

```
- [ ] `ClassName#method_name` — given <scenario/inputs>, expects <outcome>
```

Examples:
```
- [ ] `DividendParserTest#test_usd_dividend_with_wht` — given a USD dividend row paired with a withholding-tax row, expects gross=50 EUR, wht=7.50 EUR, net=42.50 EUR using the configured rate
- [ ] `DividendParserTest#test_missing_isin` — given a dividend row whose symbol has no ISIN in the security map, expects processing continues with `MISSING_ISIN_REQUIRES_ATTENTION` and an ERROR log
- [ ] `CryptoFifoTest#test_partial_sell_placeholder` — given two buy lots of 1 BTC each and a sell of 3 BTC, expects a placeholder-buy entry for the unmatched 1 BTC with a warning log
```

**Never write a bare method name** (`SomeClassTest#method`) without the given/expects description — that tells the reader nothing about what the test covers or why it matters.

**Rules:**
- Title is always `# Plan: <name>` — no other heading format.
- Every item is `- [ ]` — concrete and verifiable, never vague.
- For behavior changes: use the RED → GREEN → commit TDD cycle above.
- For non-behavior changes (config, docs, SQL): use concise `- [ ]` action items with exact file paths.
- Include inline code snippets when the implementation pattern is non-obvious.
- No meta-tasks ("review docs", "confirm scope").
- When the RFC or rollout defines multiple deployable safe-ship phases, create one plan file per phase instead of one monolithic plan. Prefix filenames and titles with the explicit phase order (for example `phase-1`, `Phase 1 - ...`).
- When a plan builds on prior completed phases, include a **Design Invariants (CR Guard)** section after the header listing prior-phase decisions that must not be compromised during code review, with specific rationale for each (e.g. RFC constraint ID, elimination trail reference).
- Before finalizing a CR Guard, cross-check every design decision source (RFC rules, design notes, prior phase decisions, PRD constraints, team agreements) against the guard lines. Guards should protect both prohibitions ("must not do X") and positive design decisions ("must preserve Y", e.g. ungated fallthrough for future extensibility).
- Every plan must include a **Review Scope** section (see below).
- Every plan must include a **Gist & Examples** section (see Universal Patterns).
- Every plan must include an **Evaluation Criteria** section defining quality dimensions and release gates (see Phase 1).
- Before finalizing, verify pre-computation bug pattern checks are addressed (see Universal Patterns).

## Documentation Impact Assessment

Before writing any tasks, scan the project's `docs/` directory and identify which existing docs need updating for this feature. Route new content to the right place — never use `README.md` as a catch-all.

**Step: list existing docs**
```bash
ls docs/
```

**Routing rules:**
| What the feature introduces | Where it goes |
|---|---|
| New config properties, defaults, validation | `README.md` — config section only |
| New metrics (counters, latency, reservations) | `docs/metrics.md` (or equivalent metrics reference) |
| New architectural/engineering conventions | `docs/project-guidelines.md` as a numbered rule |
| New workflow steps or pipeline behavior | The relevant workflow doc |
| New API contracts or BO behavior | The relevant API or workflow doc |
| Time-bounded migration/rollout instructions | PR description only — never a permanent doc |
| Operational runbook content (rollout steps, debugging tips) | Ops wiki or PR description — not `README.md` or `docs/` |

**For each affected existing doc:** add an explicit `- [ ]` task in the plan with the exact file path and what section to update.

**For genuinely new reference material with no existing home:** add a `- [ ]` task to create the appropriate doc under `docs/` with the correct canonical name.

**Do not document in `README.md`:** time-bounded migration notes, out-of-scope changes, operational runbook content, changes from prior phases mislabelled as this one, or unverified runtime/startup behavior claims.

## Review Scope

Every plan must contain a `## Review Scope` section that explicitly lists which files are in scope for code review. Review agents must reject all findings about files not in this list.

**When to generate it:**
- At plan creation time: list every file referenced in the plan's Tasks sections. Mark new files with *(new)*.
- When updating a plan mid-feature: re-derive from `git diff <base-branch>..HEAD --name-only` and classify each file as in-scope or out-of-scope based on whether it was changed to implement this feature's tasks.

**How to derive in-scope files when building on a prior branch:**
```bash
git diff <prior-phase-branch>..HEAD --name-only
```
Classify each file as:
- **In scope** — changed to implement a task defined in this plan (new feature code, tests for it, config, docs).
- **Out of scope** — present in the diff due to incidental cleanup, review-driven fixes of pre-existing issues in unrelated components, or formatter noise. List these explicitly with a one-line reason.

**Format:**
```markdown
## Review Scope

Files directly changed as part of this plan. Review feedback is accepted **only** for the files listed here.
Any finding about a file not in this list must be rejected as out of scope.

**Production code — in scope:**
- `path/to/NewFile.ext` *(new)*
- `path/to/ExistingFile.ext`

**Tests — in scope:**
- `path/to/NewTest.ext` *(new)*
- `path/to/ExistingTest.ext`

**Documentation — scope-linked (not a closed file list):**

List production code and tests explicitly (review is file-scoped). For documentation, use a **scope-linked** policy instead of enumerating every doc path:

- Any file under `docs/` (and `README.md` only when it catalogs endpoints or auth touched by the feature) may be edited when the change is **substantively required** to keep docs aligned with the feature (same change set as OpenAPI/transport; project-guidelines.md #70).
- Task 6 (or equivalent doc-closure task) must include grep/search over `docs/` for stale references, not only pre-listed files.
- Review accepts doc feedback that meets the scope bar; reject unrelated doc refactors.
- Give **likely touch points** as examples, not an exhaustive allow-list — omitting paths (e.g. BFF contract docs) must not block required sync.

**Out of scope — reject all review feedback:**
- `path/to/UnrelatedFile.ext` — one-line reason
```

**Placement:** immediately after `## Evaluation Criteria` and before `## Design Invariants` (if present) or `## Validation Commands`.

**Partially-in-scope files:** when a large existing file is in scope for only specific methods, name those methods explicitly and add a freeze note: "All other methods in this file are frozen — reject any review finding that touches them." A file listed as in scope without a method-level constraint is treated as fully open, which invites out-of-scope fixes during review. See `agent_workflow_guidelines.md §15`.

**Out-of-scope bug findings:** when a reviewer raises a real bug in a method that is frozen or out of scope, document it as a separate ticket with the file, method, and a one-line description. Decline the finding with "out of scope for this PR — tracked as [ticket/note]". Do not fix it in-place. See `agent_workflow_guidelines.md §15`.

**How to revert out-of-scope files to the base branch:**

Before reverting any candidate file, verify that no in-scope file calls any API (function/method signature, parameter type, property name) that was changed in it. If such a dependency exists, the file is in-scope — do not revert it; move it to the in-scope list with a one-line reason instead. See `agent_workflow_guidelines.md §11`.

For modified files:
```bash
git checkout <prior-phase-branch> -- path/to/file.ext
```
For newly added files (not present in the base branch):
```bash
git rm path/to/NewFile.ext
```
Verify the build compiles after reverting. A compile error is hard evidence of a missed API dependency — un-revert the file and reclassify it.

## Plan Quality Gate

Before finalizing a new or updated plan, run the `review-plan` skill as a sub-agent:

**Execution:** Launch a sub-agent with the full plan content and `review-plan` skill instructions. The agent performs the review independently using 9 parallel sub-agents from the shared review-agents catalog (quality, implementation, architecture, testing, simplification, documentation, security, concurrency, premortem) plus an inline consistency agent, and returns structured findings. Do NOT run the review inline — always delegate to a sub-agent so the main context stays clean.

**Sub-agent prompt template:**
```
You are running the review-plan skill. Review the following implementation plan by launching
9 parallel sub-agents from the shared review-agents catalog (quality, implementation, architecture,
testing, simplification, documentation, security, concurrency, premortem) plus an inline consistency
agent, as described in the skill instructions.

Read the actual source files referenced in the plan to verify assumptions about data types,
function signatures, pipeline ordering, and return contracts.

Classify every finding as Blocker, Medium, Low, or Monitor (see severity rules below).

Write the review output to: docs/reviews/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md
(use `-r1`, `-r2`, … for each loop iteration)

Return in the review Summary:
- counts: Blockers | Medium | Low | Monitor
- ready=yes only when Blocker=0 AND Medium=0

<plan content here>
```

**Review severity (plan gate):**

| Severity | Meaning | Plan action before next round |
|----------|---------|-------------------------------|
| **Blocker** | Plan is wrong or unimplementable as written; execution would fail or violate invariants | Revise tasks, invariants, or scope — mandatory |
| **Medium** | Plan is implementable but missing wiring, tests, concurrency guards, or has internal contradictions that will cause rework | Revise tasks or add explicit steps/tests — mandatory |
| **Low** | Doc nits, redundant bullets, minor test gaps with safe fallbacks elsewhere | Fold into plan when trivial; optional same round |
| **Monitor** | Accepted deferred risk with named owner | Add/update `## Monitor` with owner cross-reference |

Map review-plan agent output when synthesizing: **Block** → Blocker; **Mitigate** that would cause implementation rework or silent failure → Medium; remaining **Mitigate** → Low or Monitor depending on whether a plan step is required.

**If the sub-agent has not completed within 15 minutes**, proceed with an inline spot-check: read the files referenced in the plan, verify branch counts (count all conditional branches in branching constructs), verify helper signatures against actual function definitions, and verify all mutated parameters are listed. Classify inline findings with the same Blocker/Medium/Low/Monitor taxonomy. Continue working; incorporate the agent's findings when it eventually completes. Do not wait idle.

**After the sub-agent completes**, incorporate findings into the plan from the review artifact — do not re-run plan analysis inline:
1. **Blocker** findings → add or revise plan tasks to address them (mandatory)
2. **Medium** findings → add or revise plan tasks, tests, invariants, or Review Scope entries (mandatory — same bar as Blockers for loop exit)
3. **Low** findings → fold into plan when the fix is a one-line clarification; otherwise leave noted in the review artifact
4. **Monitor** findings → note in the plan's `## Monitor` section; **always resolve ownership**: if an existing plan task or high-level task doc covers the area, assign the item there and cross-reference both ways; if no relevant task exists, suggest creating a new story/task. Never leave a Monitor item as "tracked for a follow-up" without naming its owner task or proposing a new one.
5. Review output is saved to `docs/reviews/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md`
6. Add a reference line in the plan header: `Plan review: docs/reviews/<latest-rN>.md (latest, ready) · …`
7. Re-check the plan after incorporating findings
8. **Repeat until zero Blockers AND zero Medium (minimum 2 rounds):** after incorporating all Blocker and Medium findings, re-run the review sub-agent with the next numbered review file (`…-r2.md`, `…-r3.md`, …). Continue the loop until the latest review reports **Blocker=0 AND Medium=0**. One review round is not sufficient when the plan has multiple new or substantially rewritten tasks, or when the prior round had any Medium+ finding.
9. **Minimum two reviews:** run at least two complete review rounds (r1, r2) even if the first review returns zero Blockers and zero Medium. This catches issues that emerge only after applying fixes from the first review (new Blockers, incomplete Medium fixes, or cascading changes). Only stop when both: (a) the latest review round has **Blocker=0 AND Medium=0**, AND (b) at least two review rounds have completed.

**Ready for execution** means the latest review artifact explicitly states `ready=yes` (or equivalent verdict) with Blocker=0 and Medium=0. Low and Monitor counts do not block handoff to `execute-plan`.

Then verify these structural failure modes and fix them in the plan:

- **Current ownership:** if a prior phase extracted or renamed the owner of behavior, put new work in the final owner, not the old location. Avoid "implement in A, then move to B" churn unless the refactor itself is the goal.
- **Coherent commits:** each task ending in a commit must leave the code compiling. Do not split one required model/signature propagation across multiple commits when the intermediate state cannot compile.
- **Right-layer tests:** place failing tests at the layer that can observe the behavior. A mocked downstream collaborator cannot verify logic owned by that collaborator.
- **Side-effect safety:** when adding a guard around an irreversible side effect, specify failure semantics explicitly (claim/confirm/release, fail-open/fail-closed, TTL) so retries do not skip work that never succeeded.
- **Existing constants and config:** verify whether metrics, properties, flags, or key prefixes already exist before planning new ones. Reuse existing names unless the RFC requires a new external contract.
- **Validation minimality:** avoid redundant validation commands. Prefer the narrowest command that proves the task, and a final scoped `verify` when it subsumes compile/test.
- **Language-specific testing traps:** before finalizing test tasks, link to the language guidelines for this project (e.g. `kotlin_guidelines.md`, `python_guidelines.md`) in the plan header so the implementer has the relevant silent-failure patterns at hand. For metrics coverage, also link to the applicable company or project guidelines.
- **Branch count verification:** when specifying helper extraction from a branching function, count all conditional branches in the function body before writing the task. An incomplete branch list silently omits emission paths.

## Investigation Quality Requirements

When a plan investigates "is X handled correctly?" or "does the system correctly handle Y?", code inspection alone is INSUFFICIENT. The investigation tasks must include ACTUAL data trace verification:

1. **Trace the user's specific case:** For the exact reported scenario, verify data flows from source CSV/database through to final output. Do not rely on code inspection alone.
2. **Verify output matches source classification:** If the source report shows "Loss" and the output shows "Gain", the investigation is incomplete regardless of whether code CAN handle negatives.
3. **Use grep/compare commands:** Include tasks like `grep "specific_value" source.csv` and comparison with actual output file content
4. **Cross-report validation for multi-source systems:** When systems process data from multiple source reports, verify classifications match across ALL reports before concluding correctness. Document which report is authoritative when sources disagree.
5. **Failure consequence:** An investigation that concludes "no code changes needed" without performing data trace verification is INCOMPLETE and must be redone.

**Task ordering:** Use verification-first task ordering for investigation plans: code inspection, test execution, documentation review, and data trace verification BEFORE any implementation tasks. Skip implementation only after verification confirms correctness. See `development_lessons.md` #71.

**Example:** A plan investigating whether the system correctly handles negative values must trace actual data: find a specific entry in Source Report A (shows classification "Type X"), compare it with the actual output cell value (shows conflicting classification "Type Y"), and identify why the discrepancy exists (e.g., system processes only Source Report B, ignoring Report A). Code inspection alone cannot detect this mismatch.

## TDD Task Ordering

Plan tasks MUST be ordered so that failing tests come before implementation:
1. **RED tasks first** — write failing tests for the new behavior
2. **GREEN tasks after** — implement the minimal code to pass
3. **Refactor tasks last** — DDD extraction, naming, cleanup

Never place implementation tasks before their corresponding test tasks. Group related RED/GREEN pairs when tests and implementation are tightly coupled.
When a phase plan contains multiple code changes, order tasks so earlier tasks establish prerequisites for later ones within that same phase (for example retry semantics before activating new traffic paths).

**Pure-refactoring tasks (no new behavior):** use concise `- [ ]` action items instead of RED→GREEN cycles. However, when the refactor risks breaking unstated invariants (ordering, error attribution, mutable side effects, pre-condition checks), add characterization test items in `given/expects` format. These run GREEN before the refactor and must remain GREEN after. Write them as `- [ ] Run → expect GREEN (characterization: captures existing behaviour before refactor)`, not RED→GREEN. Reference existing tests by class and method name where they cover the invariant; add a new test only for invariants with no existing coverage.

## DDD Extraction

When a plan modifies domain types (value objects, entities, enums) that live in a large file (>1k lines), include a task for evaluating extraction to a dedicated domain module. Specifically:
- If the affected types form a cohesive aggregate (e.g., related domain types that work together), propose extracting them to a new module under `domain/` or `application/`.
- Place the extraction task AFTER the GREEN tasks (implementation works) but BEFORE the final validation task.
- The extraction task must verify no circular imports and update all import paths in tests and production code.

## Plan Lifecycle

- When all items are `[x]`, move the file to `docs/plans/completed/`.
- When superseded, delete rather than leaving stale `[ ]` items.

## Universal Patterns

Core plan quality principles applicable across all projects and languages:

- **Gist & Examples section**: Every plan must include a human-readable "Gist & Examples" section after the header that explains: what changes (plain language), why the change is needed (problem statement or context), concrete input/output examples showing before/after behavior, and edge cases that motivated design decisions. This serves as the on-ramp for both implementers and reviewers who need context before diving into tasks.

- **Evaluation Criteria section**: Every plan must include an "Evaluation Criteria" section that defines how quality will be assessed for the final product. This includes quality dimensions (correctness, performance, maintainability, security, test coverage, observability) with specific checks or metrics for each, and release gates (what must pass before the change can ship). Criteria must be precise and verifiable — not vague statements like "it should work" but concrete tests, commands, or metrics.

- **Core concepts**: Edge cases (boundary conditions requiring explicit handling), negative requirements (what must NOT be done), acceptance criteria (definition of done), validation sequence (ordered steps in which processing must occur).

- **Pattern-specific specifications**: Use exact pattern matching with start/end anchors (not `startswith()` or broad regex), include examples of what NOT to match, explicitly state what is out of scope.

- **Data classification specifications**: Define the source of truth, list explicit exclusions with reasons, handle edge cases (collisions, ambiguous values), specify fallback behavior.

- **Error handling specifications**: State what exception type to raise, what cleanup must occur before re-raising, what must NOT happen (silent continuation, partial output).

- **Pre-computation bug pattern checks**: Before finalizing tasks involving data processing, verify: unit verification (correct units), temporal gating (earlier events cannot consume later state), empty string handling (aggregation min/max filters), boundary values (tests at exact threshold), zero-cost propagation (flagged with review reason), fee/completeness (all components included), error scope (row-level parse errors caught per-row).

- **Stateful helper contracts:** when specifying a helper function that mutates shared state (dict, set, deque passed by reference), list ALL mutated parameters in the function signature spec — including those mutated as side effects that do not appear in the return type. A helper signature that omits a mutated parameter is an incomplete contract and will produce incorrect extraction.

- **Test specification format**: Every test item must use the `given/expects` format: `` `ClassName#method` — given <scenario>, expects <outcome> ``. Include positive tests (happy path), negative tests (what must NOT happen), edge case tests (boundary conditions), and error path tests (exception handling and cleanup). A bare method name without a scenario description is not acceptable — the plan must be readable without opening the test file.

- **Integration testing requirements**: For multi-step pipelines, include integration tests that exercise the full flow, not just unit tests for individual components.

- **Boundary test checklist**: When implementing threshold-based logic (>=, <=, >, <), always include tests at the exact boundary value. Off-by-one errors at boundaries are common sources of incorrect behavior.

Projects with detailed plan quality guidelines should document them in a `docs/domain/` or equivalent location; the generic skill provides only the universal patterns above.

## Execution Handoff

After saving, offer:

> "Plan saved to `docs/plans/<filename>.md`. Ready to execute with `execute-plan`, in this session manually, or hand off to a new session?"

**Plan path without trigger phrase:** If the user references an existing plan file (`docs/plans/…`, `@` mention, or filename only) without saying execute-plan / implement plan / run plan, **do not** assume implementation. Run the three-way gate from the `execute-plan` skill (execute-plan / manual / read-only) before any production code edits.

**Automated execution:** Use the `execute-plan` skill. If Phase 0 already created a feature branch, `execute-plan` Phase 0 verifies that branch and offers to continue on it instead of creating another. It orchestrates sub-agents to implement one task at a time (tests must pass), mark checkboxes, run `done` after each task, then run review/fix loops (with `done` after each review iteration) until **two consecutive** clear review rounds (zero remaining Medium+ after `receiving-code-review` triage), **minimum two** and **maximum ten** review rounds, archive the plan to `docs/plans/completed/`, and remove `docs/tmp/execute-plan/<slug>/` on success only. The parent agent must not implement tasks inline or batch commits — see `execute-plan` anti-patterns. Selecting execute-plan authorizes per-task `done` commits without a separate commit prompt for that run (push still requires explicit user instruction).

**Manual execution in this session:** Use `tdd-guide` and `unit-test-runner` per task (fresh output before marking the task complete). One task per commit. Use `done` only when the user ends the session (learn + commit across repos). Do not use this path when the user asked for `execute-plan` / `/execute-plan`.

## Integration Points

### With `execute-plan` skill
Consumer of plan format, task order, `## Validation Commands`, `## Review Scope`, per-task commit lines, and completed-plan archival. Shares Phase 0 branch-setup semantics: `plans` runs it at plan creation; `execute-plan` runs it at implementation start and reuses an existing feature branch when appropriate. After plan creation or update, hand off to `execute-plan` when the user wants automated iterative implementation with per-task commits and post-implementation review loops.
