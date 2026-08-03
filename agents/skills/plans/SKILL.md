---
name: plans
description: "Full plan lifecycle; create, edit, and complete implementation plans. Use when writing a new plan, updating an existing one, or marking a plan done (archive to project plans_completed_dir). Trigger phrases; \"create a plan\", \"create plan\", \"write a plan\", \"write plan\", \"make a plan\", \"implementation plan\", \"update the plan\", \"update plan\", \"plan for\", \"plan as per\", \"plan based on\", \"plan is done\", \"mark plan complete\", \"plan complete\"."
---

# Plans

**Documentation paths:** Read `{plans_dir}`, `{plans_completed_dir}`, `{reviews_dir}`, `{tmp_dir}`, and `{rfcs_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Do not hardcode `docs/plans/` unless TOML keys are missing and on-disk exploration shows that layout.

**Announce at start (create):** "I'm using the plans skill to create the implementation plan."

**Announce at start (update / complete):** "I'm using the plans skill to update the plan." (or "…mark the plan complete.")

**Create vs update:** Run **Phase 0 (branch setup)** and **Phase 1 (requirements discovery)** only when **creating** a new plan. Skip both phases for plan updates or completion unless the repo is in detached HEAD or the user asks to switch branches.

**Writing:** Follow `agent_workflow_guidelines.md` §45. Use plain English in **Gist & Examples** and **Design Invariants** (e.g. "public API response shape unchanged", not "wire contract stable"). Add `## Terms` after the title when the plan uses 3+ project-specific words. TDD labels (RED/GREEN) stay in task checklists only. Before each plan-file Write, refresh the skill-gate marker per `ai-playbook/agents/hooks/skill-gate/README.md` (the recipe derives `project` and `session` per Terms (Skill-gate marker; Session key), invokes the shared `session_channel.py` subprocess VERBATIM, ensures `~/.ai-playbook/runtime/skill-invoked/` exists, then ATOMICALLY writes the marker, and is FAIL-LOUD). Run this on EVERY plan-file write, including updates and completion, not only at create-only Phase 0. This skill and the gate adapter share the ONE helper subprocess (Family D: single source of truth); do NOT inline the path/body/window constants here, the full `project`/`session` derivation lives only in the plan Terms.

**Exploration discipline:** When creating a plan, use targeted grep/glob to find file paths, class names, and method signatures. Do not read full test files or deeply explore implementation details beyond what is needed to write accurate file paths and test method names in plan tasks. Produce the plan file promptly; do not keep exploring after you have enough to write the tasks. **Before writing any exact file path in a plan task, verify it exists** with glob/bash; an unverified path is a review blocker that only the quality gate catches.

**For detailed plan quality guidance:** Resolve from `{guidelines_path}` or architecture/maintenance docs named in project guidelines (legacy: `docs/domain/plan_quality_guidelines.md`). Otherwise, see Universal Patterns below.

`**When updating or optimizing an existing plan:** compare the plan against the current code shape, git history, task evidence, the RFC/PRD, and any predecessor phase plans before editing. Prefer patching the plan directly when improvements are clear. **Also verify all required sections are present** (`## Gist & Examples`, `## Evaluation Criteria`, `## Review Scope`, `## Validation Commands`); pre-existing plans may be missing them; add any absent sections before making other edits. When Review Scope or Validation Commands exist, check them against the **Scope model (two tiers)** and **Validation Commands (authoring rules)** below. **When the update notes that work is "already done", verify the implementation and commit state from the actual source and git history**; do not rely on session summaries, review labels, or unchecked task text. If implementation has started, preserve completed task history and add or revise only the remaining corrective work instead of relabeling the implemented phase as unstarted or not ready. When an existing on-disk plan differs from the local `docs` shadow branch, treat the on-disk plan as current and the shadow copy as history; never restore stale shadow content over an existing file.

**Save plans to:** `{plans_dir}/<STORY-KEY>-<feature-name>.md` (story key prefix) or `{plans_dir}/YYYY-MM-DD-<feature-name>.md` (date prefix when no story key applies).

**CRITICAL:** Plans go in the resolved `{plans_dir}` in the project repository; never in tool-default locations (`.claude/plans/`, `.opencode/plans/`, `.codex/`, `.cursor/`, etc.). When a tool suggests its own default path, override it with `{plans_dir}`.

**RFCs:** When the project uses RFCs, resolve `{rfcs_dir}` and reference the RFC in the plan header when applicable.
When an RFC phase already has its own implementation Jira task, use that phase task key in the plan filename and title instead of the parent RFC/story key; keep the RFC reference line in the header for traceability.

## Phase 0: Branch Setup (Run Once at Plan Creation Start)

Before writing the plan file, set up a dedicated branch when appropriate. Planning often overlaps with early exploration, scaffolding, and the first commits; isolating that work on a feature branch keeps `main`/`develop` clean and aligns the plan with the branch that will carry implementation.

**Announce:** "Before creating the plan, I'll set up a dedicated branch. This keeps planning and implementation isolated from other work."

### Step 0.1; Propose branch creation

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

### Step 0.2; Create and push the branch

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

### Step 0.3; Verify branch state

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

For each confirmed decision, record it to a temporary notes buffer (write to `{tmp_dir}/plan-requirements-<slug>.md`). This becomes input for the `## Gist & Examples` section.

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

Every plan follows this exact structure; no variations:

```markdown
# Plan: <Feature Name>

[Optional: one-line reference to RFC/PRD/ticket]

[Optional: ## Terms; required when 3+ project-specific terms; see agent_workflow_guidelines.md §45]

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

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `path/to/NewFile.ext` *(new)*
- `path/to/ExistingFile.ext`

**Tests:**
- `path/to/NewTest.ext` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `path/to/UnrelatedFile.ext`; reason

## Validation Commands

```bash
<test-command>
```

### Task 1: [Name]

Files:
- `path/to/NewFile.ext` *(new)*
- `path/to/ExistingFile.ext`

- [ ] `SomeClassTest#methodName`; given `<input/scenario>`, expects `<outcome>`
- [ ] `SomeClassTest#methodName_edgeCase`; given `<boundary condition>`, expects `<outcome>`
- [ ] Run → expect RED: `<test-command>`
- [ ] Write minimal implementation
- [ ] Run → expect GREEN
- [ ] Commit: `feat: <short description>`
```

**Test item format; required:**

Every test item must be self-contained so a reader can understand what will be verified without reading the code:

```
- [ ] `ClassName#method_name`; given <scenario/inputs>, expects <outcome>
```

Examples:
```
- [ ] `DividendParserTest#test_usd_dividend_with_wht`; given a USD dividend row paired with a withholding-tax row, expects gross=50 EUR, wht=7.50 EUR, net=42.50 EUR using the configured rate
- [ ] `DividendParserTest#test_missing_isin`; given a dividend row whose symbol has no ISIN in the security map, expects processing continues with `MISSING_ISIN_REQUIRES_ATTENTION` and an ERROR log
- [ ] `CryptoFifoTest#test_partial_sell_placeholder`; given two buy lots of 1 BTC each and a sell of 3 BTC, expects a placeholder-buy entry for the unmatched 1 BTC with a warning log
```

**Never write a bare method name** (`SomeClassTest#method`) without the given/expects description; that tells the reader nothing about what the test covers or why it matters.

**Rules:**
- Title is always `# Plan: <name>`; no other heading format.
- Every item is `- [ ]`; concrete and verifiable, never vague.
- For behavior changes: use the RED → GREEN → commit TDD cycle above.
- For non-behavior changes (config, docs, SQL): use concise `- [ ]` action items with exact file paths.
- Include inline code snippets when the implementation pattern is non-obvious.
- No meta-tasks ("review docs", "confirm scope").
- When the RFC or rollout defines multiple deployable safe-ship phases, create one plan file per phase instead of one monolithic plan. Prefix filenames and titles with the explicit phase order (for example `phase-1`, `Phase 1 - ...`).
- When a plan builds on prior completed phases, include a **Design Invariants (CR Guard)** section after the header listing prior-phase decisions that must not be compromised during code review, with specific rationale for each (e.g. RFC constraint ID, elimination trail reference).
- Before finalizing a CR Guard, cross-check every design decision source (RFC rules, design notes, prior phase decisions, PRD constraints, team agreements) against the guard lines. Guards should protect both prohibitions ("must not do X") and positive design decisions ("must preserve Y", e.g. ungated fallthrough for future extensibility).
- **Do not make bare "inherited/validated/previously-reviewed/tested" claims.** Phrasing like "gate-core inherited," "validated by prior rounds," or "unchanged and already tested" creates a review blind spot: `review-plan` panels treat the assertion as proof and skip re-measuring the mechanism. If a mechanism genuinely carries over, name the specific mechanism AND the input/condition it was validated against (e.g. "the fence-aware parser resets `in_fence` at each heading; tested against the real corpus's odd fence count"), or re-state what the mechanism does and how it is tested in THIS plan. A claim of validity is not a substitute for the test.
- Every plan must include a **Review Scope** section (see below).
- Every plan must include a **Gist & Examples** section (see Universal Patterns).
- Every plan must include an **Evaluation Criteria** section defining quality dimensions and release gates (see Phase 1).
- Before finalizing, verify pre-computation bug pattern checks are addressed (see Universal Patterns).

## Documentation Impact Assessment

Before writing any tasks, scan the project's `docs/` directory and identify which existing docs need updating for this feature. Route new content to the right place; never use `README.md` as a catch-all.

**Step: list existing docs**
```bash
ls docs/
```

**Routing rules:**
| What the feature introduces | Where it goes |
|---|---|
| New config properties, defaults, validation | `README.md`; config section only |
| New metrics (counters, latency, reservations) | `docs/metrics.md` (or equivalent metrics reference) |
| New architectural/engineering conventions | `{guidelines_path}` (from `.ai-playbook/facts.md` TOML when present; typically `docs/maintenance/project-guidelines.md`) as a numbered rule |
| New workflow steps or pipeline behavior | The relevant workflow doc |
| New API contracts or BO behavior | The relevant API or workflow doc |
| Time-bounded migration/rollout instructions | PR description only; never a permanent doc |
| Operational runbook content (rollout steps, debugging tips) | Ops wiki or PR description; not `README.md` or `docs/` |

**For each affected existing doc:** add an explicit `- [ ]` task in the plan with the exact file path and what section to update.

**For genuinely new reference material with no existing home:** add a `- [ ]` task to create the appropriate doc under `docs/` with the correct canonical name.

**Do not document in `README.md`:** time-bounded migration notes, out-of-scope changes, operational runbook content, changes from prior phases mislabelled as this one, or unverified runtime/startup behavior claims.

## Review Scope

Every plan must contain a `## Review Scope` section using the **two-tier scope model** below. The explicit list is a floor, not a ceiling; review and address-review may include plan-related findings outside the list when the causal link to this plan is clear.

**When to generate it:**
- At plan creation time: list every file referenced in the plan's Tasks sections under **Explicit must-fix**. Mark new files with *(new)*.
- When updating a plan mid-feature: re-derive the explicit list from `git diff <base-branch>..HEAD --name-only` and classify each file as must-fix or out-of-scope based on whether it was changed to implement this feature's tasks.

**How to derive explicit must-fix files when building on a prior branch:**
```bash
git diff <prior-phase-branch>..HEAD --name-only
```
Classify each file as:
- **Explicit must-fix**; changed to implement a task defined in this plan (feature code, tests, config, docs the plan names).
- **Out of scope**; present in the diff due to incidental cleanup, review-driven fixes of pre-existing issues in unrelated components, or formatter noise. List these explicitly with a one-line reason.

**Format:**
```markdown
## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `path/to/NewFile.ext` *(new)*
- `path/to/ExistingFile.ext`

**Tests:**
- `path/to/NewTest.ext` *(new)*
- `path/to/ExistingTest.ext`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `path/to/UnrelatedFile.ext`; one-line reason
```

**Placement:** immediately after `## Evaluation Criteria` and before `## Design Invariants` (if present) or `## Validation Commands`.

**Scope model (two tiers):**

| Tier | Role | Review / address behavior |
|------|------|---------------------------|
| **Explicit must-fix** | Paths from task `Files:` lists and named plan deliverables | Always review; valid findings must be fixed or explicitly triaged |
| **Plan-related extension** | Unlisted paths touched during execution or full-branch review | In scope only when causally related to plan goals; assess each finding; do not auto-drop because the path was omitted from the plan |

**Plan-related test (use during review triage):** Can you tie the finding to a specific plan task, explicit must-fix change, or contract the plan altered? If yes → in scope. If no → drop. When an explicit must-fix change implies follow-on updates elsewhere (supporting scripts, linked instructions, config the runtime reads), those follow-ons are plan-related even if omitted from the explicit list.

**After execution:** if review repeatedly surfaces plan-related findings in the same unlisted area, add that path to **Explicit must-fix** on the next plan update; the explicit list should converge toward what the work actually touched.

**Partially-in-scope files:** when a large existing file is in scope for only specific methods, name those methods explicitly and add a freeze note: "All other methods in this file are frozen; reject any review finding that touches them." A file listed as in scope without a method-level constraint is treated as fully open, which invites out-of-scope fixes during review. See `agent_workflow_guidelines.md §15`.

**Out-of-scope bug findings:** when a reviewer raises a real bug in a method that is frozen or out of scope, document it as a separate ticket with the file, method, and a one-line description. Decline the finding with "out of scope for this PR; tracked as [ticket/note]". Do not fix it in-place. See `agent_workflow_guidelines.md §15`.

**How to revert out-of-scope files to the base branch:**

Before reverting any candidate file, verify that no in-scope file calls any API (function/method signature, parameter type, property name) that was changed in it. If such a dependency exists, the file is in-scope; do not revert it; move it to the in-scope list with a one-line reason instead. See `agent_workflow_guidelines.md §11`.

For modified files:
```bash
git checkout <prior-phase-branch> -- path/to/file.ext
```
For newly added files (not present in the base branch):
```bash
git rm path/to/NewFile.ext
```
Verify the build compiles after reverting. A compile error is hard evidence of a missed API dependency; un-revert the file and reclassify it.

## Validation Commands (authoring rules)

Every plan must include a `## Validation Commands` fenced bash block (see plan template). Authoring rules:

1. **Scope-aligned checks:** When validation uses grep/search for stale strings, paths, or renamed dependencies, cover every **explicit must-fix** path and any surfaces the plan's contract changes reasonably affect; not a single entry point when multiple artifacts carry the same contract. Breadth should match what plan-related review would still need to verify.

2. **Executable vs reference prose:** When a task changes behavior documented as a script, monolithic bash block, or named file to run, validation must exercise the **canonical executable artifact** (the block labeled as the script to run, or the invoked file path); not an illustrative snippet elsewhere in the doc. A green grep over reference-only prose does not prove wiring is correct.

3. **Contract-removal checks:** When removing or renaming a dependency (module, env var, path key, CLI flag, workflow step), include at least one command that searches the explicit must-fix set and other surfaces where stale references would break plan goals.

4. **Validation minimality still applies:** Prefer the narrowest command that proves the task, but never narrower than what the two-tier Review Scope requires; a passing check that ignores plan-implied follow-on surfaces is a plan defect.

5. **Boolean mutator negative paths:** When a task adds or changes a public method that returns `boolean` / `Optional` success from a **multi-row SQL CTE or multi-statement write** (activate + supersede, claim + update, insert + promote, compare-and-set), the plan **must** include at least one RED→GREEN IT in `given/expects` form where the call **returns false / empty** (missing row, wrong status, stale id) and asserts **no destructive side effects** on unrelated rows (for example prior ACTIVE not superseded; other keys untouched). Happy-path and concurrent-success ITs alone are not enough; execute-plan Phase 3 will still require a mutator failure-mode matrix, but the plan must force the negative IT into implementation.

6. **Zero-match assertions must negate the search command:** When a validation command's stated success condition is "no remaining hits" / "returns empty" / a stale-reference sweep with zero matches expected, the command itself must assert that explicitly (`! grep ...`, `grep -L`, or equivalent). A bare `grep`/`rg` search exits non-zero when there are zero matches, which is the **opposite** of what "no remaining hits" means as a pass condition; a plan that pastes the search command without negating it fails its own gate exactly when the underlying work is correct.

7. **Dedicated greps per structural obligation (no context spillover):** When Validation Commands assert that several structural obligations exist (Hard Gates, anti-pattern rows, Recovery order, named Step subsections), give each obligation its own dedicated search that fails when THAT obligation is absent. Do not rely on a wide `-A`/`-B` context window around a different anchor to "also cover" siblings. Context spillover is not a gate (see `development_lessons.md` #186).

8. **Full chain for ordered sequences:** When Validation Commands assert an N-step order (for example marker → mark → Launch done), require the full chain (`a < b < c`), not only each step before the last (`a < c` and `b < c`). Pairwise-before-last checks still green on a middle swap. After writing the check, simulate the swapped adjacent pair and confirm it fails (see `development_lessons.md` #187).

9. **Character order when phrases can share a line:** When Validation Commands assert that phrase A must precede phrase B inside one step, do not rely on presence-only greps or `a_ln <= b_ln` (same-line inversion stays green). Assert character order inside the matched window (for example a `case` pattern `*A*B*`). Simulate same-line reverse order and two-sentence reverse order; both must fail (see `development_lessons.md` #189).

10. **Explicit abort on every required check (fail-closed block):** Multi-check Validation Commands must abort on miss or forbidden match. Wrap positive greps with `|| { echo …; exit 1; }` (or `if ! { … }; then exit 1; fi`). For forbidden matches use `if grep …; then echo …; exit 1; fi`. Do not rely on bare grep exit status, `test A && test B` alone, `! grep`, or `set -e` (bash exempts `!` and non-final `&&` failures). After writing, strip one required obligation or add a bypass phrase and confirm the block exits non-zero before hygiene (see `development_lessons.md` #190).

11. **Polarity-aware policy greps:** When asserting FAIL-LOUD stop, marker refresh, or similar policy, grep for the positive obligation verbs inside a tight window, and abort on inverted phrases (`continue editing`, `without refreshing`, `skip.*marker`). Presence of leftover tokens (`unwritable`, `WRITE RECIPE`) is not polarity. Simulate inverted wording and confirm failure (see `development_lessons.md` #190).

## Plan Quality Gate

Before finalizing a new or updated plan, run the `review-plan` skill as a sub-agent:

**Execution:** Launch a sub-agent with the `review-plan` instructions. It must run the recommended five-worker panel from `review-panel-selection.md`: correctness-completeness, testing, design-simplicity, contract-docs, and risk. Workers load multiple lenses but must not launch nested review agents. Focused panels are valid only under the shared selection rules.

**Sub-agent prompt template:**
```
You are running the review-plan skill. Review the following implementation plan with the recommended
five-worker panel from review-panel-selection.md. Apply severity-calibration.md, record each worker's
loaded lenses, and do not launch nested review agents.

Read the actual source files referenced in the plan to verify assumptions about data types,
function signatures, pipeline ordering, and return contracts.

Classify every finding as Critical, High, Medium, or Low, with independent blocking status.

Write the review output to: `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md`
(use `-r1`, `-r2`, … for each loop iteration)

Return in the review Summary:
- counts: Critical | High | Medium | Low
- ready=yes only when no unresolved finding has blocking=true

<plan content here>
```

**Review severity:** use `review-agents/severity-calibration.md`. Document inconsistency alone is Low. Blocking is independent from severity.

**If the sub-agent has not completed within 15 minutes**, proceed with an inline spot-check using the same shared severity and blocking contract. Incorporate the delegated result when it completes.

**After the sub-agent completes**, incorporate findings into the plan from the review artifact; do not re-run plan analysis inline. (These rules govern **plan** reviews only, `source_kind: "plan"`. Code/branch reviews follow `doing-code-review` and `review-loop`, whose post-fix worker selection, every owning or affected worker, is unaffected by the Medium+ narrowing in rule 4.)
1. Fold every accepted finding with `blocking: true`; fold other material findings by consequence.
2. **A fold is a digest change, regardless of severity.** After ANY fold (blocking or non-blocking) that edits the plan artifact, the source digest has changed: recompute it and launch a fresh round before exit is allowed. A non-blocking fold is not exempt: a fold that looks mechanical (test rewrite, grep broadening, scoping tweak, preserve-note) can still break a path, a test, or a validation command. Re-probe because the digest moved, not because the finding was severe.
3. **Re-probe set after a fold:** launch blind `correctness-completeness` plus every distinct owning or affected worker whose domain the folds touched. The blind `correctness-completeness` probe is mandatory on every post-fold round; it is the regression catcher for folds and must not be dropped.
4. **Final-round worker selection (when the prior round found zero blocking):** the final round is the blind `correctness-completeness` probe plus only the workers that produced a **Medium or higher** finding in the prior round. Low-only and finding-free workers are not re-launched. If no worker produced Medium+, the final round is the blind `correctness-completeness` probe alone. This is the only round where the Medium+ rule narrows the panel; rounds that follow a fold of a blocking finding still launch every affected worker per rule 3.
5. If the re-probe set is all five workers, count it as a full-panel round.
6. Exit only when one fresh review on the **post-fold** digest reports zero unresolved blocking findings. "Same digest" in rule 7 means the exact post-fold digest; an exit on a pre-fold digest is never valid.
7. Do not run a second clean full panel on the same digest.
8. Reconcile after three non-monotonic rounds. Before a sixth full-panel round, stop for user direction.

**Ready for execution** means the latest review artifact explicitly states `ready=yes` with zero unresolved blocking findings. Open the artifact and verify its verdict rather than relying on chat summary. The post-fold-digest requirement (rule 6) is enforced by the `--source-plan` mechanical gate in `review-plan` Step 4; a `ready=yes` recorded before a fold fails that gate and does not count.

Then verify these structural failure modes and fix them in the plan:

- **Current ownership:** if a prior phase extracted or renamed the owner of behavior, put new work in the final owner, not the old location. Avoid "implement in A, then move to B" churn unless the refactor itself is the goal.
- **Coherent commits:** each task ending in a commit must leave the code compiling. Do not split one required model/signature propagation across multiple commits when the intermediate state cannot compile.
- **Constructor-signature-change audit:** when a task adds, removes, or reorders a constructor parameter on an existing class, grep the whole repo for `new ClassName(` before finalizing the task and list every direct construction site explicitly (production and test). A compatibility method overload preserves *behavior* for existing callers but does not preserve *construction* call sites, which still need the new argument to compile. For each listed site, state whether it exercises the changed method (needs a configured stub proving the new behavior) or not (an unconfigured mock is enough); do not describe a test as "unaffected" without checking whether it stubs/verifies the method the constructor change feeds into.
- **Right-layer tests:** place failing tests at the layer that can observe the behavior. A mocked downstream collaborator cannot verify logic owned by that collaborator.
- **Side-effect safety:** when adding a guard around an irreversible side effect, specify failure semantics explicitly (claim/confirm/release, fail-open/fail-closed, TTL) so retries do not skip work that never succeeded.
- **Existing constants and config:** verify whether metrics, properties, flags, or key prefixes already exist before planning new ones. Reuse existing names unless the RFC requires a new external contract.
- **Validation minimality:** avoid redundant validation commands. Prefer the narrowest command that proves the task, and a final scoped `verify` when it subsumes compile/test; but never narrower than the two-tier Review Scope (see **Validation Commands (authoring rules)**).
- **Review scope completeness:** explicit must-fix covers all task `Files:`; plan-related extension policy is stated; validation breadth matches contract changes the plan introduces.
- **Language-specific testing traps:** before finalizing test tasks, link to the language guidelines for this project (e.g. `kotlin_guidelines.md`, `python_guidelines.md`) in the plan header so the implementer has the relevant silent-failure patterns at hand. For metrics coverage, also link to the applicable company or project guidelines.
- **Branch count verification:** when specifying helper extraction from a branching function, count all conditional branches in the function body before writing the task. An incomplete branch list silently omits emission paths.

## Investigation Quality Requirements

When a plan investigates "is X handled correctly?" or "does the system correctly handle Y?", code inspection alone is INSUFFICIENT. The investigation tasks must include ACTUAL data trace verification:

1. **Trace the user's specific case:** For the exact reported scenario, verify data flows from source CSV/database through to final output. Do not rely on code inspection alone.
2. **Verify output matches source classification:** If the source report shows "Loss" and the output shows "Gain", the investigation is incomplete regardless of whether code CAN handle negatives.
3. **Use grep/compare commands:** Include tasks like `grep "specific_value" source.csv` and comparison with actual output file content
4. **Cross-report validation for multi-source systems:** When systems process data from multiple source reports, verify classifications match across ALL reports before concluding correctness. Document which report is authoritative when sources disagree.
5. **Failure consequence:** An investigation that concludes "no code changes needed" without performing data trace verification is INCOMPLETE and must be redone.

**Task ordering:** Use verification-first task ordering for investigation plans: code inspection, test execution, documentation review, and data trace verification BEFORE any implementation tasks. Skip implementation only after verification confirms correctness.

**Example:** A plan investigating whether the system correctly handles negative values must trace actual data: find a specific entry in Source Report A (shows classification "Type X"), compare it with the actual output cell value (shows conflicting classification "Type Y"), and identify why the discrepancy exists (e.g., system processes only Source Report B, ignoring Report A). Code inspection alone cannot detect this mismatch.

## TDD Task Ordering

Plan tasks MUST be ordered so that failing tests come before implementation:
1. **RED tasks first**; write failing tests for the new behavior
2. **GREEN tasks after**; implement the minimal code to pass
3. **Refactor tasks last**; DDD extraction, naming, cleanup

Never place implementation tasks before their corresponding test tasks. Group related RED/GREEN pairs when tests and implementation are tightly coupled.
When a phase plan contains multiple code changes, order tasks so earlier tasks establish prerequisites for later ones within that same phase (for example retry semantics before activating new traffic paths).

**Pure-refactoring tasks (no new behavior):** use concise `- [ ]` action items instead of RED→GREEN cycles. However, when the refactor risks breaking unstated invariants (ordering, error attribution, mutable side effects, pre-condition checks), add characterization test items in `given/expects` format. These run GREEN before the refactor and must remain GREEN after. Write them as `- [ ] Run → expect GREEN (characterization: captures existing behaviour before refactor)`, not RED→GREEN. Reference existing tests by class and method name where they cover the invariant; add a new test only for invariants with no existing coverage.

## DDD Extraction

When a plan modifies domain types (value objects, entities, enums) that live in a large file (>1k lines), include a task for evaluating extraction to a dedicated domain module. Specifically:
- If the affected types form a cohesive aggregate (e.g., related domain types that work together), propose extracting them to a new module under `domain/` or `application/`.
- Place the extraction task AFTER the GREEN tasks (implementation works) but BEFORE the final validation task.
- The extraction task must verify no circular imports and update all import paths in tests and production code.

## Plan Lifecycle

- When all items are `[x]`, move the file to `{plans_completed_dir}/`.
- When superseded, delete rather than leaving stale `[ ]` items.

## Universal Patterns

Core plan quality principles applicable across all projects and languages:

- **Gist & Examples section**: Every plan must include a human-readable "Gist & Examples" section after the header that explains: what changes (plain language), why the change is needed (problem statement or context), concrete input/output examples showing before/after behavior, and edge cases that motivated design decisions. This serves as the on-ramp for both implementers and reviewers who need context before diving into tasks.

- **Evaluation Criteria section**: Every plan must include an "Evaluation Criteria" section that defines how quality will be assessed for the final product. This includes quality dimensions (correctness, performance, maintainability, security, test coverage, observability) with specific checks or metrics for each, and release gates (what must pass before the change can ship). Criteria must be precise and verifiable; not vague statements like "it should work" but concrete tests, commands, or metrics.

- **Core concepts**: Edge cases (boundary conditions requiring explicit handling), negative requirements (what must NOT be done), acceptance criteria (definition of done), validation sequence (ordered steps in which processing must occur).

- **Pattern-specific specifications**: Use exact pattern matching with start/end anchors (not `startswith()` or broad regex), include examples of what NOT to match, explicitly state what is out of scope.

- **Data classification specifications**: Define the source of truth, list explicit exclusions with reasons, handle edge cases (collisions, ambiguous values), specify fallback behavior.

- **Error handling specifications**: State what exception type to raise, what cleanup must occur before re-raising, what must NOT happen (silent continuation, partial output).

- **Pre-computation bug pattern checks**: Before finalizing tasks involving data processing, verify: unit verification (correct units), temporal gating (earlier events cannot consume later state), empty string handling (aggregation min/max filters), boundary values (tests at exact threshold), zero-cost propagation (flagged with review reason), fee/completeness (all components included), error scope (row-level parse errors caught per-row).

- **Stateful helper contracts:** when specifying a helper function that mutates shared state (dict, set, deque passed by reference), list ALL mutated parameters in the function signature spec; including those mutated as side effects that do not appear in the return type. A helper signature that omits a mutated parameter is an incomplete contract and will produce incorrect extraction.

- **Test specification format**: Every test item must use the `given/expects` format: `` `ClassName#method`; given <scenario>, expects <outcome> ``. Include positive tests (happy path), negative tests (what must NOT happen), edge case tests (boundary conditions), and error path tests (exception handling and cleanup). A bare method name without a scenario description is not acceptable; the plan must be readable without opening the test file.

- **Boolean / Optional multi-row mutators:** When specifying a port or adapter method that returns success/failure from a CTE or multi-statement write, always add a negative `given/expects` IT: call fails (wrong id, wrong status, stale token) **and** persisted state for other rows is unchanged. See **Validation Commands (authoring rules)** item 5. Incident reference: `promoteToActive` superseded ACTIVE while returning `false` on a missing BUILDING target.

- **Integration testing requirements**: For multi-step pipelines, include integration tests that exercise the full flow, not just unit tests for individual components.

- **Boundary test checklist**: When implementing threshold-based logic (>=, <=, >, <), always include tests at the exact boundary value. Off-by-one errors at boundaries are common sources of incorrect behavior.

Projects with detailed plan quality guidelines should document them in `{guidelines_path}` or a named architecture/maintenance doc; not `docs/domain/` or `docs/<module>/` on migration-complete company services. The generic skill provides only the universal patterns above.

## Execution Handoff

After saving, offer:

> "Plan saved to `{plans_dir}/<filename>.md`. Ready to execute with `execute-plan`, in this session manually, or hand off to a new session?"

**Plan path without invocation:** If the user references an existing plan file under `{plans_dir}` (`@` mention or filename only) without invoking execute-plan (no `execute plan`, no shorthand `execute`/`implement`/`run` + plan path, no `/execute-plan`, skill not attached), **do not** assume implementation. Run the three-way gate from the `execute-plan` skill (execute-plan / manual / read-only) before any production code edits.

**Automated execution:** Use the `execute-plan` skill (reads same paths from `.ai-playbook/facts.md`). Archive to `{plans_completed_dir}/`; session logs under `{tmp_dir}/execute-plan/<slug>/` on success only.

**Manual execution in this session:** Use `tdd-guide` and `unit-test-runner` per task (fresh output before marking the task complete). One task per commit. Use `done` only when the user ends the session (learn + commit across repos). Do not use this path when the user asked for `execute-plan` / `/execute-plan`.

## Final Step: Run `done`

After the plan file is saved, the review gate reports `ready=yes`, and the execution-handoff choice has been offered, invoke the `done` skill as the last step of the plans workflow. This finalizes the plan-creation session: `learn` captures any cross-repo lessons, `docs-branch` syncs any shadow review files under `{reviews_dir}`, and the plan file (plus the review artifact) is committed across all repositories.

**Scope:** the `done` run covers only this plan-creation session's changes (plan file, review artifact, docs-branch shadows). It does **not** start implementation or mark plan tasks complete.

**Skip only when:**
- The user explicitly says "not yet" / "wait" / "I'll commit myself"; honor that and stop.
- The execution-handoff gate selected `execute-plan` and the user wants the plan commit folded into the first task's `done`; in that case, say so and let `execute-plan` own the first commit.

**Do not skip** just because the plan file looks small or the session feels incomplete. The plan file and its review artifact are deliverables; `done` is the canonical commit path for them.

Announce: "Running `done` to finalize the plan-creation session (learn + docs-branch + commit across repos)."

## Integration Points

### With `bootstrap-ai-playbook` skill
Writes and refreshes `.ai-playbook/facts.md` when Terms triggers fire (`using-skills` Step 0). This skill reads `{plans_dir}`, `{plans_completed_dir}`, `{reviews_dir}`, `{tmp_dir}`, and `{rfcs_dir}` from that file.

### With `execute-plan` skill
Consumer of plan format, task order, `## Validation Commands`, `## Review Scope`, per-task commit lines, and completed-plan archival. Shares Phase 0 branch-setup semantics: `plans` runs it at plan creation; `execute-plan` runs it at implementation start and reuses an existing feature branch when appropriate. Both skills refresh the plans-class skill-gate marker per `ai-playbook/agents/hooks/skill-gate/README.md` Marker WRITE RECIPE before plan-file edits. After plan creation or update, hand off to `execute-plan` when the user wants automated iterative implementation with per-task commits and post-implementation review loops.

### With `grilling` skill
When Phase 1 requirements discovery hits ambiguous scope or trade-offs, and the user asks to grill a decision, invoke `grilling` for one-question-at-a-time resolution. Do not replace the plans interview structure; grilling deepens specific decisions.
