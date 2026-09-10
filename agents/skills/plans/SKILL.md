---
name: plans
description: "Full plan lifecycle; create, edit, and complete implementation plans. Use when writing a new plan, updating an existing one, or marking a plan done (archive to project plans_completed_dir). Trigger phrases; \"create a plan\", \"create plan\", \"write a plan\", \"write plan\", \"make a plan\", \"implementation plan\", \"update the plan\", \"update plan\", \"plan for\", \"plan as per\", \"plan based on\", \"plan is done\", \"mark plan complete\", \"plan complete\"."
---

# Plans

**Documentation paths:** Read `{plans_dir}`, `{plans_completed_dir}`, `{backlog_dir}`, `{backlog_completed_dir}`, `{reviews_dir}`, `{tmp_dir}`, and `{rfcs_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Do not hardcode `docs/plans/` unless TOML keys are missing and on-disk exploration shows that layout.

**Announce at start (create):** "I'm using the plans skill to create the implementation plan."

**Announce at start (update / complete):** "I'm using the plans skill to update the plan." (or "…mark the plan complete.")

**Create vs update:** Run **Phase 0 (branch setup)** and **Phase 1 (requirements discovery)** only when **creating** a new plan. Skip both phases for plan updates or completion unless the repo is in detached HEAD or the user asks to switch branches.

**Writing:** Follow `agent_workflow_guidelines.md` §45. Use plain English in **Gist & Examples** and **Design Invariants** (e.g. "public API response shape unchanged", not "wire contract stable"). Add `## Terms` after the title when the plan uses 3+ project-specific words. TDD labels (RED/GREEN) stay in task checklists only. When a plan embeds an exact-content artifact that itself contains fenced code blocks (a canary fixture, a file template), wrap the outer fence in four backticks; a three-backtick outer fence closes at the artifact's first inner fence and makes the content boundary ambiguous. Before each plan-file Write, refresh the skill-gate marker per `ai-playbook/agents/hooks/skill-gate/README.md` (the recipe derives `project` and `session` per Terms (Skill-gate marker; Session key), invokes the shared `session_channel.py` subprocess VERBATIM, ensures `~/.ai-playbook/runtime/skill-invoked/` exists, then ATOMICALLY writes the marker, and is FAIL-LOUD). Run this on EVERY plan-file write, including updates and completion, not only at create-only Phase 0. This skill and the gate adapter share the ONE helper subprocess (Family D: single source of truth); do NOT inline the path/body/window constants here, the full `project`/`session` derivation lives only in the plan Terms. **After each successful plan-file mutation under `{plans_dir}` (Write, Edit, or StrReplace; excluding `{plans_completed_dir}`), append the repo-relative plan path to `{tmp_dir}/done-session/plan-deliverables.txt`** (create the directory/file if missing; one path per line; skip duplicates). That file is the producer `done` Step 1.5 reads when porcelain is clean after a mid-session commit.

**Exploration discipline:** When creating a plan, use targeted grep/glob to find file paths, class names, and method signatures. Do not read full test files or deeply explore implementation details beyond what is needed to write accurate file paths and test method names in plan tasks. Produce the plan file promptly; do not keep exploring after you have enough to write the tasks. **Before writing any exact file path in a plan task, verify it exists** with glob/bash; an unverified path is a review blocker that only the quality gate catches. **Verify batch semantics against the local source and migration documents before choosing a generic partitioning or classification design:** distinguish the documented payload shape, per-item outcome contract, and adjacent event flows from the rollout scope actually requested. **Behavioral claims need a probe, not an absence-grep:** verify what passes/fails and the exact error text by exercising the real function or validator once; absence of a gate's error string in the source, or a claim inherited from a backlog item or review finding, is not verification (user-level lessons #56, #246). Superlative or comparative prose claims inherited from the origin prompt or backlog text ("the oldest X", "the only Y") are measured against the actual corpus before entering plan prose; the origin text asserting them is not evidence (a review caught "oldest unclaimed backlog item" as false: an older open item existed). A behavior-change fixture's expected post-state is such a claim: produce it by running today's code on the fixture input and then the prescribed rule (a simulation suffices), never by hand-editing today's transcript, and execute every defang or parity assert against the real fixture build (user-level lesson #253).

**For detailed plan quality guidance:** Resolve from `{guidelines_path}` or architecture/maintenance docs named in project guidelines (legacy: `docs/domain/plan_quality_guidelines.md`). Otherwise, see Universal Patterns below.

`**When updating or optimizing an existing plan:** compare the plan against the current code shape, git history, task evidence, the RFC/PRD, and any predecessor phase plans before editing. Prefer patching the plan directly when improvements are clear. **Also verify all required sections are present** (`## Gist & Examples`, `## Evaluation Criteria`, `## Review Scope`, `## Validation Commands`); pre-existing plans may be missing them; add any absent sections before making other edits. When Review Scope or Validation Commands exist, check them against the **Scope model (two tiers)** and **Validation Commands (authoring rules)** below. **When the update notes that work is "already done", verify the implementation and commit state from the actual source and git history**; do not rely on session summaries, review labels, or unchecked task text. If implementation has started, preserve completed task history and add or revise only the remaining corrective work instead of relabeling the implemented phase as unstarted or not ready. When an existing on-disk plan differs from the local `docs` shadow branch, treat the on-disk plan as current and the shadow copy as history; never restore stale shadow content over an existing file.

**Save plans to:** `{plans_dir}/<STORY-KEY>-<feature-name>.md` (story key prefix) or `{plans_dir}/YYYY-MM-DD-<feature-name>.md` (date prefix when no story key applies).

**CRITICAL:** Plans go in the resolved `{plans_dir}` in the project repository; never in tool-managed default locations outside the repository. When a tool suggests its own default path, override it with `{plans_dir}`.

**RFCs:** When the project uses RFCs, resolve `{rfcs_dir}` and reference the RFC in the plan header when applicable.
When an RFC phase already has its own implementation Jira task, use that phase task key in the plan filename and title instead of the parent RFC/story key; keep the RFC reference line in the header for traceability.

**Backlog origin:** When a plan promotes a `{backlog_dir}` item (captured per `receiving-review` **Backlog capture**), reference the backlog file path in the plan header next to any RFC/ticket reference. Keep the backlog item in place under `{backlog_dir}` while the plan is open; the completion step in **Plan Lifecycle** moves it to `{backlog_completed_dir}`.

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

**Automatic path from clean trunk (fail-closed):** before asking, check the auto-branch conditions. When all of the following hold:

- the current branch is exactly `master` or `main` (not detached HEAD, not any other branch),
- both `git status --porcelain` and `git status --porcelain --ignored` are empty (non-empty ignored content keeps the confirmation; it may be user content that must not be buried by a branch switch),
- the proposed branch name is derived from the requested task or plan slug via the naming convention above, and
- the destination branch does not already exist (`git rev-parse --verify` fails for it, local or remote),

then create and verify the local feature branch via Step 0.2 without asking for branch confirmation, and report what was created. Every other case keeps the explicit confirmation ask below: detached HEAD, dirty tracked content, untracked content, non-empty ignored content, a non-trunk base, an ambiguous target, an existing destination branch, or any history-rewriting operation. The automatic path does not skip or satisfy the requirements confirmation (Phase 1 still runs in full).

Truth table (A = auto-branch without ask, C = explicit confirmation):

```
- clean `master`, computed name, no destination: A
- clean `main`, computed name, no destination: A
- dirty tracked content on trunk: C
- untracked content on trunk: C
- non-empty ignored content on trunk: C
- non-trunk base (e.g. `develop` or a feature branch): C
- detached HEAD: C
- existing destination branch: C
- ambiguous target or any history-rewriting operation: C
```

Ask the user:

```
I'll create a new local branch for this plan:
- Base: current branch (<current-branch>)
- New branch name: <computed-branch-name>
- Push stays off until you explicitly ask to push

Proceed with branch creation? (yes/no)
```

Wait for explicit user confirmation before proceeding.

### Step 0.2; Create the branch

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
```

Do **not** run `git push` here. Branch-create confirmation is not push authorization. Push only after an explicit user request in the current message (user `AGENTS.md` Git Push Policy).

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

**Unclear points, confidence gate (grill or record assumptions):** Throughout Phase 1, whenever a requirement point stays unclear after checking the repo first (code, docs, git history, prior plans, `.ai-playbook/facts.md`), rate confidence in the interpretation the plan is about to build on. SOT ownership is a first-class unclear point: when the plan cannot tell which document owns a rule (wire contract versus Layer 2 topic versus glossary versus ADR versus history) or where new content belongs, treat the point as low confidence unless repo evidence (doc-hierarchy roles, the existing SOT) settles it. Rate each point against the two tiers below:

- **Low confidence:** multiple reasonable interpretations exist, the answer materially changes scope, tasks, invariants, or Validation Commands, or repo evidence is missing or contradictory. Do not guess and do not silently pick one. Invoke the `grill-with-docs` skill to resolve the point with the user (one question at a time, inline glossary and ADR capture per that skill) and fold each confirmed answer into the requirements buffer before continuing. Borderline cases count as low confidence (fail closed, same stance as the Checklist inclusion gate).
- **High confidence:** exactly one reasonable interpretation exists, choosing any other would be unreasonable or is cheap to correct, and that interpretation is supported by repo evidence, established convention, or an already-confirmed user decision. Do not interrogate the user; record the assumption in the requirements buffer as `- assume <assumption>; basis: <evidence, convention, or confirmed decision>`.

**Facts versus decisions (gate dividing line):** source verification resolves facts (what exists, what the sources already decide), not unselected design trade-offs. A material decision point is any choice between two or more plausible plan shapes that differ in scope, source-of-truth ownership, module boundary, compatibility mode, error policy, rollout shape, history strategy, preservation rules, deletion permissions, or validation evidence. Source detail never converts a decision point into a fact: authoritative sources that describe multiple alternatives leave the point low-confidence. Test every proposed task: if another reasonable design would remove, add, move, or materially change that task, the underlying choice is a low-confidence decision point regardless of source authority or detail. Do not grill factual lookups whose result is directly observable and involves no choice, and do not grill a design the user has already explicitly selected when no separate material ambiguity remains; the scope-extension hard gate below stays independent and is cross-referenced, not duplicated.

**Confidence-gate regression cases (fail-closed routing):** (1) a single-boundary feature whose single implementation is clearly required stays eligible for a high-confidence assumption; (2) a feature with an adjacent boundary, compatibility path, or ownership choice routes to `grill-with-docs`; (3) authoritative sources describing multiple alternatives still route to the grill; (4) a cleanup request with one apparently unrelated commit beside feature work still asks the grilling scope question; (5) a cleanup request with dirty, untracked, or ignored files records preservation before any restore; (6) a source-owned prerequisite is placed under `Ship when`, not converted into an assumption or executable task; (7) an explicit user decision suppresses only the already-resolved question, never unrelated ambiguity.

**Scope-extension hard gate (independent of the confidence tiers):** any proposed plan work that is not required to deliver the stated primary goal (the goal as given in the ticket or user request, not as restated or broadened by the agent) is a scope extension. Scope extensions include, without limiting: a second auth or identity mechanism, a cross-cutting header or principal model, a sibling-service contract the ticket does not own, a multi-tenant or multi-market product shape, and any concern the plan already labels as owned by another ticket or feature. Supporting work for the stated primary goal as given in the ticket or user request (its tests, docs, and validation) is not a scope extension. A scope extension must not enter Terms, Assumptions, Tasks, Files, or Review Scope as a high-confidence assumption; before writing or expanding the plan file to include it, invoke grill-with-docs and get an explicit user decision: keep in this plan, split to a separate plan, or defer. When the user does not explicitly accept the extension into the current plan, its disposition is a backlog item (per receiving-review Backlog capture); a scope extension is never silently absorbed into the current scope. Necessity tie-breaker: if the ticket or user-request text does not name the concern, treat it as a scope extension regardless of claimed necessity. Contradiction check: if OUT-of-scope or owned-elsewhere prose coexists with Tasks or Files that implement that concern, treat the extension as unresolved; grill it or remove the implementing tasks before the plan file is written.

**Cleanup scope ledger:** for multi-file cleanup, simplification, or restoration work, the plan records a scope ledger: the exact base ref, task-owned files, classes, methods, and hunks, frozen areas, pre-existing dirty paths, untracked paths, explicit deletion permissions, and a keep/remove/defer disposition for every non-obvious branch-only change and affected cross-cutting surface (files, interfaces, headers, configuration, documentation), each backed by direct source evidence or an explicit user decision; a broad statement such as "preserve adjacent behavior" is not a substitute for classifying each candidate surface. The mechanical check is the cleanup baseline checker from the skills repo checkout (scripts/check_cleanup_scope_baseline.py; resolve the skills repo checkout from the skills-repo path key in the user facts document; pass the consumer repo via --repo-root); the ledger is its allow-list. Checker limitations at the use site: the checker cannot see gitignored files (capture the ignored set with `git status --porcelain --ignored`, or `git ls-files --others --ignored --exclude-standard`, and record those paths in session notes explicitly) and matches allow-list paths byte-exact relative to the repo root (no `./` prefix).

**Decision-ambiguity scan (mandatory before Step 1.4):** after source discovery, separate discovered facts from decisions still requiring a choice, and record every material decision point in the requirements buffer under a `Decision points requiring a grill` heading. Each entry resolves in exactly one way: grilled via `grill-with-docs` with the user's answer recorded as a one-line receipt (decision, source, date, affected plan section); resolved by an already-confirmed user decision (cite its source); or the scan found no material ambiguity, which renders the literal line `Decision points requiring a grill: none remain.` in the Step 1.4 confirmation block. The subsection always renders; silently omitting it is a detectable violation of this gate.

Keep every high-confidence assumption in one running list in the requirements buffer and present that list in the Step 1.4 confirmation block; the user's yes confirms the listed assumptions as a batch. A rejected assumption is either adjusted and reconfirmed, or downgraded to a low-confidence point and resolved via `grill-with-docs` before the plan is written. Carry the final list into the plan's `## Assumptions` section. Never build a plan on silent assumptions.

**Authoring-session constraints are not plan constraints:** constraints in the authoring task prompt that scope the authoring session's own git behavior (branching, pushing, commit placement, staying on the current branch) are session-scoped; do not write them into the plan document as assumptions (not even with `basis: task constraint`), Gist lines, or acceptance criteria, and keep plans branch-agnostic and push-agnostic so Phase 0 branch setup and the executor's normal git workflow stay intact. Before finishing authoring, sweep the plan's Assumptions, Gist & Examples, Evaluation Criteria, and Validation Commands sections for "current branch", "no new branch", hardcoded branch names, and "never push"; delete any hit (user-level lesson #296).

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

**Third-party AI-conversation sources:** when the requirement comes from a pasted AI chat or share link, treat its concrete architecture (pipelines, model choices, code) as one candidate design, not as the requirement. Restate the goal in the user's own words and confirm scope boundaries (Step 1.2) before adopting anything the conversation demonstrates; the transcript's final example is often an exploration artifact, not the user's intent. (Witness: a plan created from a shared AI conversation adopted its demo local-model pipeline wholesale; the user's actual goal was only a quota-window restart manager, and the plan had to be reshaped after Phase 1 answers were already collected.)

### Step 1.2: Verify key decisions explicitly

Before proceeding, explicitly confirm each critical decision with the user. When the decision involves a trade-off with multiple reasonable paths, present structured options to the user:

**Confirm these elements:**
1. **Scope boundaries:** what is IN vs OUT
2. **Primary success criterion:** the one observable behavior that defines "done"
3. **Key invariants:** what must NOT break or change
4. **External dependencies:** what teams, systems, or migrations this depends on
5. **Rollout strategy:** single deploy vs phased rollout
6. **Scope extensions:** every proposed scope extension, each with its grill outcome (in / split / defer); extensions are listed separately from ordinary assumptions and are never batch-confirmed; the outcome is a backlog item unless the user explicitly accepts the extension into this plan. The Scope extensions block always renders in the Step 1.4 confirmation; when no extensions were proposed it renders the literal line `Scope extensions (grilled): none proposed.`; an absent Scope extensions block is itself a detectable violation of this gate.

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
3. **What proves repository implementation is done?** Separate local, repo-verifiable **Done when** checks from deployed, cross-team, or human-owned **Ship when** conditions.

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

**Assumptions (high-confidence, not grilled):**
- assume <assumption>; basis: <repo evidence, convention, or confirmed decision>

**Decision points requiring a grill:** <point>: <one-line receipt: user decision, source, date, affected plan section>, or the literal line `Decision points requiring a grill: none remain.` when the ambiguity scan found no material decision point; when several points remain, their per-point receipts are carried into the plan's single Assumptions trailer line semicolon-separated (never comma-separated; the readiness gate splits receipt segments on semicolons only), never one trailer line per point.

**Scope extensions (grilled):** <extension>: <grill outcome: in / split / defer>, or the literal line `Scope extensions (grilled): none proposed.` when no extensions were proposed.

<!-- Meta-rule for the authoring agent, not plan content to render: this block always renders, so an absent Scope extensions block is itself a detectable violation of this gate; a bare yes on assumptions does not admit an extension that was never grilled, and an extension without an explicit keep-in-this-plan decision is recorded as a backlog item. An absent Decision points block is a detectable violation of the decision-ambiguity gate; a broad acknowledgement (sure, ok, confirmed) confirms only the material decisions explicitly named in this block, a decision about one adjacent concern is never generalized to another unlisted concern, and an ambiguous lifecycle verb (skip, leave, drop, defer, preserve) must already have been restated as a concrete tree action and answered before its candidate appears here as settled. Any open material grill question or unresolved scope-extension decision is not ready: while one stands the plan may be edited only for non-decision facts or question framing, and the confirmation cannot proceed to readiness; the Assumptions trailer carries it as `open: <question>` so the mechanical readiness gate fails. A generic acknowledgement or continue request ("go on", "sure", "okay") restates the same question or resumes the interview instead of accepting the pending recommendation; the only acceptance without answering is the explicit opt-in phrase "accept the recommendation for this question". Each closed question leaves a one-line receipt (decision, source, date, affected plan section) in the Decision points requiring a grill subsection before the next question. Clear or safely inferable items are never asked and surface only in this block's single consolidated assumptions list. -->

**Evaluation criteria:**
- <quality dimension>: <specific check or metric>
- <quality dimension>: <specific check or metric>

**Done when:** <local and repository-verifiable implementation checks>

**Ship when:** <deployed, cross-team, or human-owned conditions; prose only>

Proceed with writing the plan? (yes/no; if no, tell me what to adjust)
```

Wait for explicit confirmation before proceeding to write the plan file. If the user asks to adjust, update the requirements buffer and reconfirm. A yes confirms the listed assumptions as-is; for any rejected assumption, adjust and reconfirm it or downgrade it to a low-confidence point and resolve it via `grill-with-docs` (see the Phase 1 confidence gate).

**Hard gate:** Do not write the plan file until requirements are validated and confirmed, every low-confidence point is resolved, and every high-confidence assumption is listed in the confirmation block.

## Plan Format

Every plan follows this exact structure; no variations:

The template block below carries the author-facing source of truth for trailer acceptance mechanics (the bracketed Assumptions line inside it); the readiness validator (scripts/plan_readiness.py, decision_marker_problem) owns enforcement and points here, and sibling skill documents must link to one of these two surfaces instead of restating the mechanics.

```markdown
# Plan: <Feature Name>

[Optional: one-line reference to RFC/PRD/ticket]

[Optional: ## Terms; required when 3+ project-specific terms; see agent_workflow_guidelines.md §45]

[Required: ## Assumptions; always renders even when empty; one bullet per high-confidence assumption with its basis, then the trailer line "Decision points requiring a grill: none remain." or the same single trailer line carrying all per-point receipts carried from the Step 1.4 confirmation, semicolon-separated (never comma-separated; the readiness gate splits receipt segments on semicolons only); never one trailer line per point; the readiness gate accepts the literal none-remain line case-insensitively with an optional trailing period, and treats a trailer value as an unresolved placeholder when the start of the value or of any semicolon-separated receipt segment is pending, tbd, todo, or open (case-insensitive) followed by end-of-value, whitespace, or more word characters, unless it is followed immediately by a hyphen (a hyphen reads as a resolved receipt: `todo-list`, `tbd-for-now`, and `open-question` pass; `todos`, `pending2`, and `TBD for now` fail), or when a segment starts with the character `<`. In the plan file the trailer drops the bold markers and any list prefix and sits as a plain unindented line starting exactly `Decision points requiring a grill:`. Fenced code blocks (terminated or not, backtick or tilde) are invisible to the trailer check; the trailer must sit as a plain unfenced line inside ## Assumptions]

## Gist & Examples

[Human-readable explanation of what changes and why, with concrete examples]

## Evaluation Criteria

[Specific criteria for evaluating whether the final product is high-quality]

**Quality dimensions:**
- <dimension> (e.g., correctness, performance, maintainability): <specific check or metric>
- <dimension>: <specific check or metric>

**Done when:**
- <local and repository-verifiable implementation check>

**Ship when:**
- <deployed, cross-team, or human-owned condition; no checklist item>

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
- Every included task item is `- [ ]`; concrete and verifiable, never vague.
- **Checklist inclusion gate:** first classify every proposed candidate as **repository implementation**, **external prerequisite**, or **release condition**.
- In this classification, a release condition means release gate.
- **Fail closed on ambiguity:** if ownership, target, or evidence source is unclear, do not label the candidate as repository implementation, and do not open a release-gate exception. Put it under **Ship when** as an external prerequisite or release gate until ownership is affirmative.
- Only repository implementation becomes an **executable plan task** and uses `- [ ]` by default. Put external prerequisites and release conditions under **Ship when** as prose.
- A release condition may become an executable plan task only as an exception. External prerequisites are never exception-admissible. Ask the user, receive an explicit confirmation, and record `exception confirmed by user: <exact confirmation text or stable message reference>; item: <specific checklist action>; target/environment: <specific target or environment>; confirmation time/session: <time and session>`, `why executable now: <reason>`, and `completion evidence: <observable evidence>` beside the task in the plan file. Chat-only confirmation is insufficient. Consumers must verify that the receipt is current and binds the confirmation to that item, target or environment, and time or session, then still follow higher-level authorization rules for external writes.
- Acceptable exception: `- [ ] Run the repository-owned release validation script against <ENVIRONMENT>; exception confirmed by user: <stable message reference>; item: run the repository-owned release validation script; target/environment: <ENVIRONMENT>; confirmation time/session: <YYYY-MM-DD HH:MM, current session>; why executable now: the script and required credentials are available in this repo and session; completion evidence: successful command output recorded in the task log.`
- Reject: `why executable now: user said yes`. Confirmation permits the exception but does not explain why the executor can complete it now.
- Use this short **allow/deny** guide:

  | Candidate | Classification | Checklist |
  |---|---|---|
  | Update a local script, docs, or tests | Repository implementation | Allow |
  | Deploy to `<STAGING_ENVIRONMENT>` | Release gate | Deny by default; exception-only with confirmation receipt, `why executable now`, and observable completion evidence (this-service / repository-owned deploy only; never other-team deploy) |
  | Probe work owned by `<OTHER_TICKET>` | External prerequisite | Deny; put under Ship when |
  | Human merges the pull request | Release gate | Deny by default; exception-only with confirmation receipt, `why executable now`, and observable completion evidence |

- Optional Jira or equivalent tracking for **Ship when** items is allowed only after the user confirms ticket creation. Never auto-create tracking tickets.
- **Anti-pattern:** do not copy rollout checklist shapes from completed plans. Completed history is immutable context, not a template for Ship-when work.
- For behavior changes: use the RED → GREEN → commit TDD cycle above.
- For non-behavior changes (config, docs, SQL): use concise `- [ ]` action items with exact file paths.
- **Cross-cutting/contract tasks:** in `Files:`, prefer the wire contract (OpenAPI) plus the one prose SOT home; do not list every caller catalog as a full-text edit target; peers point at the SOT.
- Include inline code snippets when the implementation pattern is non-obvious.
- No meta-tasks ("review docs", "confirm scope").
- When the RFC or rollout defines multiple deployable safe-ship phases, create one plan file per phase instead of one monolithic plan. Prefix filenames and titles with the explicit phase order (for example `phase-1`, `Phase 1 - ...`).
- When a plan builds on prior completed phases, include a **Design Invariants (CR Guard)** section after the header listing prior-phase decisions that must not be compromised during code review, with specific rationale for each (e.g. RFC constraint ID, elimination trail reference).
- Before finalizing a CR Guard, cross-check every design decision source (RFC rules, design notes, prior phase decisions, PRD constraints, team agreements) against the guard lines. Guards should protect both prohibitions ("must not do X") and positive design decisions ("must preserve Y", e.g. ungated fallthrough for future extensibility).
- **Do not make bare "inherited/validated/previously-reviewed/tested" claims.** Phrasing like "gate-core inherited," "validated by prior rounds," or "unchanged and already tested" creates a review blind spot: `review-plan` panels treat the assertion as proof and skip re-measuring the mechanism. If a mechanism genuinely carries over, name the specific mechanism AND the input/condition it was validated against (e.g. "the fence-aware parser resets `in_fence` at each heading; tested against the real corpus's odd fence count"), or re-state what the mechanism does and how it is tested in THIS plan. A claim of validity is not a substitute for the test.
- Every plan must include a **Review Scope** section (see below).
- Every plan must include a **Gist & Examples** section (see Universal Patterns).
- Every plan must include an **Evaluation Criteria** section defining quality dimensions, **Done when**, and **Ship when** (see Phase 1).
- When Phase 1 recorded high-confidence assumptions (confidence gate), the plan must include an `## Assumptions` section listing each assumption with its basis; a plan that silently builds on an unlisted assumption is a defect; the section always renders and closes with the decision-points trailer carried from the Step 1.4 confirmation, and plan_readiness.py enforces the trailer for plans whose latest review round's sidecar date field is dated on or after 2026-09-08.
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

**Path-category gate (mechanical):** the readiness validator is the single source of truth for Review Scope path-category enforcement (scripts/plan_readiness.py, review_scope_problem); any problem it reports fails the plan's readiness gate (date-gated like the trailer gate). Do not restate its checks here; run the validator.

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

7. **Dedicated greps per structural obligation (no context spillover):** When Validation Commands assert that several structural obligations exist (Hard Gates, anti-pattern rows, Recovery order, named Step subsections), give each obligation its own dedicated search that fails when THAT obligation is absent. Do not rely on a wide `-A`/`-B` context window around a different anchor to "also cover" siblings. Context spillover is not a gate (see `development_lessons.md` #187). A multi-path invocation (one grep over several files) asserts the union, not each file: any single matching file satisfies it while an unwired sibling stays ungated; gate per-file obligations with per-file invocations or loops with `test -f` pre-checks.

8. **Full chain for ordered sequences:** When Validation Commands assert an N-step order (for example marker → mark → Launch done), require the full chain (`a < b < c`), not only each step before the last (`a < c` and `b < c`). Pairwise-before-last checks still green on a middle swap. After writing the check, simulate the swapped adjacent pair and confirm it fails (see `development_lessons.md` #188).

9. **Character order when phrases can share a line:** When Validation Commands assert that phrase A must precede phrase B inside one step, do not rely on presence-only greps or `a_ln <= b_ln` (same-line inversion stays green). Assert character order inside the matched window (for example a `case` pattern `*A*B*`). Simulate same-line reverse order and two-sentence reverse order; both must fail (see `development_lessons.md` #190).

10. **Explicit abort on every required check (fail-closed block):** Multi-check Validation Commands must abort on miss or forbidden match. Wrap positive greps with `|| { echo …; exit 1; }` (or `if ! { … }; then exit 1; fi`). For forbidden matches use `if grep …; then echo …; exit 1; fi`. Do not rely on bare grep exit status, `test A && test B` alone, `! grep`, or `set -e` (bash exempts `!` and non-final `&&` failures). A subprocess fatal error (e.g. `git diff` against a missing ref) emits empty output that a no-match check reads as a pass; capture the subprocess exit status separately and abort non-zero. The hole inverts for forbidden-match sweeps: a `if grep ...; then fail` recipe treats every non-zero exit as clean, so a pre-check `test -f` on every swept path is not enough; the recipe must capture the grep exit status and fail on rc >= 2 as a tool error (unreadable file, ELOOP, missing binary), so only rc 1 passes and rc 0 fails as a forbidden match; this is the same three-way split the `expect_rg_no_match` helper implements for rg. The same hole swallows a missing or erroring tool: rg defines rc 0 = match, rc 1 = clean no-match, rc >= 2 = error (a missing tool is shell rc 127), so under if-then-fail polarity every non-zero rc except a true match silently passes; split the exit codes via a helper (for example `expect_rg_no_match <pattern> <paths>...`: rc 0 fails with the matches, rc 1 passes, rc >= 2 aborts), which subsumes the `test -f` pre-check (see `development_lessons.md` #208). After writing, strip one required obligation or add a bypass phrase and confirm the block exits non-zero before hygiene (see `development_lessons.md` #191).

11. **Polarity-aware policy greps:** When asserting FAIL-LOUD stop, marker refresh, or similar policy, grep for the positive obligation verbs inside a tight window, and abort on inverted phrases (`continue editing`, `without refreshing`, `skip.*marker`). Presence of leftover tokens (`unwritable`, `WRITE RECIPE`) is not polarity. Simulate inverted wording and confirm failure (see `development_lessons.md` #191).
12. **Evidence line for multi-field artifact obligations:** When a Validation Command must verify a conjunction of fields (for example severity AND blocking AND a named input) over a generated artifact whose fields live on separate lines (review staging docs), do not parse the document's section structure: heading granularity varies by artifact and block-scoped conjunctions false-pass (a non-blocking finding can ride a blocking sibling inside one section). Make the task record one dedicated ordered single-line marker instead (for example `CANARY-EVIDENCE: input=... severity=... blocking=true finding=F<N>`) and grep that exact ordered line. Resolve WHICH artifact by identity suffix (`-r<N>`), not mtime; a post-hoc edit to an older round makes newest-mtime stale.
13. **Anchor cwd-dependent scripts:** A validation command that invokes a script resolving its scan root from the invocation cwd (hygiene scanners, repo-root greppers) must anchor it: `( cd "$REPO" && ... )`. Unanchored, such a script can exit 0 while scanning nothing from a foreign cwd; that is the same environment-dependent silent-pass class that hermeticity checks exist to catch.
14. **Import-ban gate completeness:** When a validation command bans ALL references to a module (import ban, not just a patch idiom ban) across a set of files, first inventory tests in that set that legitimately need the reference (for example a retained entry-point/e2e test that drives the banned module). Relocate those tests outside the gated file set in the plan itself; do not weaken the gate to an exclusion list, and do not let the plan contradict its own gate.
15. **Self-match immunity for embedded gates:** When a Validation Command embeds a forbidden-pattern grep inside an artifact that will itself be committed (the plan file is the canonical case), the document's own command text satisfies the pattern once tracked, and the gate fails forever. Bracket-escape one literal character in the pattern (for example `artifact[.]yaml`, not `artifact.yaml`) so the document's own escaped text cannot match while genuine stale references still do; state beside the command that the escape is intentional so a later editor does not "normalize" it, and exclude the embedding document from any sweep instructions (its mentions are the checker literal, not stale references). Verify the gate against the TRACKED state (intent-to-add the document, then run it), not the working tree alone.

16. **Stage-scoped interim validation:** When a plan task runs a subset of the final Validation Commands block at an interim point (for example a mid-plan commit gate before later tasks create their artifacts), scope every path-dependent check to paths that exist at that stage. A search tool's error exit on a missing operand (rg exit 2) makes an `if <tool> …; then fail; fi` branch unreachable, silently disabling the check for the paths that DO exist in the same invocation; either `test -f` pre-check each path or leave the multi-path form to the final task (see `development_lessons.md` #206).
17. **Fold/migration probe inventory:** When a task deletes an artifact (file, command spec, section) and folds its content into surviving artifacts, derive the probe set from the deleted source, not the destination's new prose: inventory every enforceable obligation in the source before deletion (for example `git show <rev>^:<path>`), give each a dedicated probe that fails when absent (rule 7), and make prose remnant sweeps case-insensitive (`grep -niE` with lowercased alternatives). An obligation named only in plan prose is unpinned (see `development_lessons.md` #207).
18. **Probe pattern distinctiveness and scope congruence:** A dedicated grep is dedicated only if deleting the guarded sentence breaks it. Quote a distinctive multi-word span verbatim from the normative rule line and verify the span is unique in the file; a single common token that also appears in unrelated prose of the same file aliases to that other text and stays green when the obligation is deleted. Match the probe's region to the obligation's region: when an obligation is scoped to a sub-region (frontmatter, one section), sweep exactly that region rather than the whole file (the term may legitimately appear elsewhere), extract the region with a fail-closed assertion on an anchor line (for example `^name:`) so a broken extractor cannot pass vacuously, and make forbidden-term sweeps of the region case-insensitive (see `development_lessons.md` #187).
19. **Wrap-tolerant forbidden-phrase sweeps, proven RED today:** a multi-word prose phrase can be line-wrapped in the target document, so a line-based grep can NEVER match it and a "no remaining hits" sweep false-passes forever. Flatten before matching (`tr '\n' ' ' < file | tr -s ' ' | grep -q "<phrase>"`) or sweep a single-line fragment; the `tr -s ' '` squeeze is load-bearing when continuation lines carry leading indentation (wrapped docstrings/comments), which leaves multi-space runs in the flattened text that a single-space fixed-string cannot match; and at authoring time EXECUTE the sweep against the CURRENT content and record that it fires (the gate must be RED-today, flipping GREEN exactly when the rewrite task lands). A reviewer's "verified empirically" claim is not proof; the next round re-executes it (see user-level lessons #220: a vacuous sweep survived three review rounds plus a false empirical-verification claim; project witness: homelab-llm lesson 36, where newline-only flattening still missed indented docstring wraps).
20. **Literal-pinning greps must tolerate the prescribed declaration form:** when a Validation Command asserts an exact assignment literal (constant name plus value) and a task prescribes the declaration WITH a type annotation (`NAME: tuple[float, ...] = (...)`), a grep pinning `NAME = value` cannot match the prescribed line and the final validation task fails against a correctly implemented plan. Pin the name loosely and the value exactly (`grep -q "NAME.*= (…)"`), or simulate the grep against the task's own prescribed snippet before finalizing; the positive-presence mirror of rule 19's RED-today proof (a reviewer caught this as a blocking defect only at round 12, after the annotation form had been introduced by an earlier fold).

21. **Interim task gates state their own tree state:** in multi-task RED-to-GREEN plans, every task's Run-expect line must describe the whole-suite outcome AT THAT TASK POINT (which checks fail, which pass, what the exit code is), not inherit the previous task's expectation; a gate that says "expect GREEN" while a later task's fix is still pending is unsatisfiable and invites pulling the later fix forward. When any sequencing defect surfaces in review, sweep every gate line and acceptance criterion in one pass instead of patching them one round at a time.
22. **Mechanically re-verify exact-text contracts after every fold:** when a plan pins literal validation spans against prescribed task text (the pin/text contract of rules 18-20), every fold that edits either side can silently break the other; after EVERY fold, run a mechanical audit that extracts every pinned span and verifies it occurs exactly once in the plan's prescribed snippets, plus a shell syntax check (`bash -n`) over the Validation Commands block; fix both sides of any mismatch in the same edit, and strip possessive apostrophes from pinned phrases (a literal apostrophe inside a single-quoted pattern is a shell syntax error). Rereading the plan is not verification (see user-level lesson #264).

23. **Witnesses for bounded tolerances overstep the bound dimension alone:** when a task bounds a previously unbounded tolerance (whitespace runs, retry counts, caps, timeouts), the negative witness is the canonical matching form overstepping ONLY that dimension (e.g. a blank line inside an otherwise canonical sentence, for a one-newline whitespace bound); a witness differing in other dimensions too (unrelated text in the gap) passes under both the bound and the unbounded regression and discriminates nothing. Verify the bound numeric itself against its rationale (a bound like `\s{1,3}` still matches two newlines), and simulate the witness under the unbounded form once at authoring time, recording that it flips (see user-level lesson #263).

24. **Generate exact-string expectations by running the prescribed transform:** when a task embeds an exact expected literal (command line, rendered string, serialized form) for code whose inputs pass through a quoting, escaping, encoding, or formatting layer, NEVER hand-write the expectation: execute the prescribed transformation on the sample input first (a one-line REPL/shell run), paste its output, and note beside it which transform produced it. Hand-simulated literals encode a wrong mental model of the transform (`shlex.quote` leaves safe tokens bare) and make the RED test permanently unpassable against a faithful implementation, pressuring the implementer to corrupt the transform instead (a reviewer caught exactly this as a blocking plan defect; see project lesson: generated literal vs prescribed transform).

25. **Task-coupling sweep at authoring and after every fold:** a task's checklist may only call helpers, signatures, and flags that EARLIER tasks created; a call needing a signature born in a later task belongs in that later task, or its own GREEN gate is unsatisfiable as written. Any fold that renumbers or moves tasks must update every textual step-number cross-reference (Review Scope, Gist, other tasks) in the SAME edit. Sweep the whole plan for both coupling defects whenever a fold touches task boundaries, not just the edited task (see project lesson: a task's GREEN gate must pass against the tree that task creates).
26. **Positive-control forbidden-match and count greps in the execution shell:** a forbidden-match or line-count validation grep whose regex carries anchors or embedded variables can match NOTHING under a different grep implementation while still reporting success, and its "guard fires today" zero is indistinguishable from a true no-match. Execute every such grep in the shell and grep implementation that runs it at gate time, positive-control the pattern once against a known-present sibling of the target shape before trusting a zero, and prefer fixed-string matching (`grep -F`) for literal pin lines (see user-level lessons #287).

27. **Build prescribed fixtures literally before certifying (path arithmetic is a behavioral claim):** when a task prescribes test fixtures with literal paths, symlink targets, or relative references, construct the fixture EXACTLY as written and run the prescribed assertions against that construction before certifying the plan. A symlink target resolves relative to the LINK's own directory, not the repo root, and `../` segments stack from the link's parent; path arithmetic written in prose is as mistake-prone as code. Validating the BEHAVIOR with an ad-hoc, differently-built fixture proves the mechanism but not the prescribed recipe; a wrong path string makes the GREEN gate unsatisfiable and the implementer can only improvise (witness: symlink fixtures certified on behavior probes built with different targets, then a reviewer rebuilt them verbatim and every target path was wrong).

28. **Scope never-allowed hygiene sweeps to authored content:** a Validation Command that forbids a pattern (em-dash, stale phrase, legacy token) across files whose existing content legitimately carries it (frozen regions, historical prose) is unsatisfiable on arrival and forces the executor to either violate the Review Scope freeze or fail the gate. Sweep whole only files this plan creates; for edited files, scope to the prescribed insertions, or drop the sweep when the introduced content is already fenced verbatim in the plan. Execute every forbidden-pattern command against today's tree at authoring to prove the scope: a gate that fires on content no task touches is mis-scoped, not effective (witness: an em-dash sweep over two validators carrying 15 and 23 legacy hits in frozen regions blocked an otherwise clean plan as a blocking r1 finding).

29. **Run the repo's cheap mechanical format gates over the plan bytes before the first review round:** the no-em-dash scan and the public-hygiene scan cost seconds and any post-certification byte change forces a fresh certification round, because the digest binding makes no distinction between a formatting fix and a semantic fold. A formatting defect discovered at commit time converts a finished review loop into a full extra round; both witnessed occurrences (2026-09-04 and 2026-09-05 em-dash recerts) were avoidable by running the scan at authoring time.

30. **Derive mutation-probe failing sets empirically, not by prediction:** when a task prescribes a temporary mutation probe with an expected failing-test set, sweep the whole selector for every assertion that observes the mutated call, including PRE-EXISTING witnesses in sibling tests, or execute the probe once at authoring time and paste the observed set. A prediction scoped to the asserts the new test adds misses siblings the selector already runs, and the probe's RED expectation is wrong on arrival (witness: a guard plan's probe predicted two failing tests while an unconditional probe call also tripped the policy-only sibling's pre-existing transport witness; the r1 reviewer found it by execution).

31. **Never pin volatile working-tree state in task gates:** an invariant that asserts another session's mutable tree state (specific files still dirty or uncommitted, a peer's in-flight doc) is stale on arrival when parallel sessions share the branch; peers legitimately commit and rework their own files mid-execution and mid-review. Anchor scope-integrity checks to a base sha recorded before the first task commit and verify `git log --name-only <base>..HEAD` against this plan's own declared file lists instead (see user-level lesson #305).

32. **List-set diffs must match namespace and collation on BOTH sides, proven by execution:** when a Validation Command compares a generated name set (grep over runner output) against an expected literal list, each side must carry the same naming form (strip the family prefix with `sed` or include it in the literals; a `grep -oE 'family/...'` capture keeps the prefix) and the same collation (a `sort -u`-built file emits lexical order, so pipe the literal side through `sort` too). Pin-vs-prescription audits alone do not catch this: EXECUTE the diff once at authoring time against a simulated post-change set (today's real output plus the declared additions) and record that it passes and that stripping one declared addition flips it (witnesses, one session: a preservation diff failed on ordering alone, then on full-prefixed-vs-bare names after the ordering fix).

## Plan Quality Gate

Before finalizing a new or updated plan, run the `review-plan` skill as a sub-agent:

**Execution:** Launch a sub-agent with the `review-plan` instructions. It must run the recommended five-worker panel from `review-panel-selection.md`: correctness-completeness, testing, design-simplicity, contract-docs, and risk. Workers load multiple lenses but must not launch nested review agents. Focused panels are valid only under the shared selection rules.

**Sub-agent prompt template:**
```
You are running the review-plan skill. Review the following implementation plan with the recommended
five-worker panel from review-panel-selection.md. Apply severity-calibration.md, record each worker's
loaded lenses, and do not launch nested review agents.

Read the actual source files referenced in the plan to verify assumptions about data types,
function signatures, pipeline ordering, and return contracts. The plan file itself is
READ-ONLY for you: record findings only in the review artifact (never edit the plan).

Classify every finding as Critical, High, Medium, or Low, with independent blocking status.

Write the review output to: `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md`
(use `-r1`, `-r2`, … for each loop iteration)
AND its `.stats.json` sidecar (`{reviews_dir}/<same-basename>.stats.json`), produced/validated in the same round: the mechanical readiness gate requires the sidecar of the LATEST round to exist with a `source_digest` matching the final plan bytes (a round that writes only the Markdown review fails `plan_readiness.py` with "missing stats sidecar"), and the sidecar MUST satisfy the CURRENT version-1 contract from `review-staging` - a versionless or minimal private shape classifies as legacy and fails the gate with "sidecar schema is legacy/versionless". At minimum declare `"schema_version": 1`, `review_type`, `date`, `artifact_slug`, `round`, `panel_mode` (plus `selection_reason` when focused), `source_kind`, `source_digest`, `escalation_reason`, the four freshness fields (`review_mode`, `risk_signals`, `prior_findings_filter`, `last_fix_commit`), required on records dated on or after `EXTENDED_SIDECAR_MIN_DATE`; values and enum live in `review-staging`, `verdict`, and the `counts`/`panel`/`deduplication_groups`/`discarded`/`severity_calibration`/`triage_outcomes`/`findings`/`overflow`/`soften_watchlist` arrays; every `findings` row uses the gate's enum values (`reachability`: common/expected/plausible-edge/theoretical; `blast_radius`: global/multi-service/single-service/local; `confidence`: verified/strong-evidence/hypothesis), a canonical `pattern` ID, and integer ids matching the `#### F<N>.` headers in the Markdown, with at most 2 non-blocking Low findings per worker (extras go to `overflow`). When `last_fix_commit` is non-null, the staging Markdown Metadata carries the `Witness ledger: N/A (no public mutators)` line (plan reviews have no public mutators; the populated-or-N/A witness shape per `review-staging` is required on any code-review round with a non-null `last_fix_commit`). For records dated on or after `EXTENDED_SIDECAR_MIN_DATE`, the staged Markdown Metadata must also carry the four freshness lines (`Review mode`, `Changed-risk signals`, `Prior findings supplied as filter`, `Last fix commit`) per `review-staging`. The staging Markdown follows the required hierarchy (Metadata, Review Statistics, `### Critical|High|Medium|Low` groups in order, `#### F<N>.` finding blocks with field bullets) so finding conservation passes.

The review artifact itself MUST contain a `## Summary` section recording the counts
(Critical | High | Medium | Low), every blocking finding by id, and the explicit
`ready=yes`/`ready=no` verdict (the exit gate verifies the artifact, not the chat reply;
witness: a round returned ready=yes in chat while the artifact ended at the overflow
manifest, and the orchestrator had to send it back).

<plan content here>
```

**Review severity:** use `review-agents/severity-calibration.md`. Document inconsistency alone is Low. Blocking is independent from severity.

**If the sub-agent has not completed within 15 minutes**, proceed with an inline spot-check using the same shared severity and blocking contract. Incorporate the delegated result when it completes.

**After the sub-agent completes**, incorporate findings into the plan from the review artifact; do not re-run plan analysis inline. (These rules govern **plan** reviews only, `source_kind: "plan"`. Code/branch reviews follow `doing-code-review` and `review-loop`, whose post-fix worker selection, every owning or affected worker, is unaffected by the Medium+ narrowing in rule 4.)
1. Fold every accepted finding with `blocking: true`; fold other material findings by consequence. A fold that changes a contract term must grep the whole plan for the superseded term and re-derive every matching bullet before the next round; sibling bullets written from the old contract are the classic residue (UL #215).
2. **A fold is a digest change, regardless of severity.** After ANY fold (blocking or non-blocking) that edits the plan artifact, the source digest has changed: recompute it and launch a fresh round before exit is allowed. A non-blocking fold is not exempt: a fold that looks mechanical (test rewrite, grep broadening, scoping tweak, preserve-note) can still break a path, a test, or a validation command. Re-probe because the digest moved, not because the finding was severe.
3. **Re-probe set after a fold:** launch blind `correctness-completeness` plus every distinct owning or affected worker whose domain the folds touched. The blind `correctness-completeness` probe is mandatory on every post-fold round; it is the regression catcher for folds and must not be dropped.
4. **Final-round worker selection (when the prior round found zero blocking):** the final round is the blind `correctness-completeness` probe plus only the workers that produced a **Medium or higher** finding in the prior round. Low-only and finding-free workers are not re-launched. If no worker produced Medium+, the final round is the blind `correctness-completeness` probe alone. This is the only round where the Medium+ rule narrows the panel; rounds that follow a fold of a blocking finding still launch every affected worker per rule 3.
5. If the re-probe set is all five workers, count it as a full-panel round.
6. Exit only when one fresh review on the **post-fold** digest reports zero unresolved blocking findings. "Same digest" in rule 7 means the exact post-fold digest; an exit on a pre-fold digest is never valid.
7. Do not run a second clean full panel on the same digest.
8. Reconcile after three non-monotonic rounds. ALWAYS reconcile when a round reports `ready=yes` and any later round reports `ready=no`: stop launching probe rounds, self-audit the fold-induced dependency graph (every moved symbol, fixture capability, or state field: created-in, removed-at, required-by task), fix all violations in ONE comprehensive fold, then run at most one fresh certification round on that digest. Before a sixth full-panel round, stop for user direction (see user-level lesson UL#254).
9. **Post-round digest integrity:** after EVERY review round returns, verify the plan artifact was not edited out-of-process: `shasum -a 256 <plan-file>` must equal the round sidecar's recorded `source_digest`. A reviewer editing the plan AFTER its validator ran (e.g. "helpfully" refreshing a header reference line) silently breaks the exit binding; revert to the exact reviewed bytes and re-verify the hash. Sub-agent review prompts must state the plan file is READ-ONLY for the reviewer.
10. **Review-reference fixed point:** plan headers reference review artifacts by filename PREFIX or glob (e.g. `...-r1.md` …), never an enumerated final round count. The round that reviews the header cannot be counted inside it: an enumerated "through rN" line has no stable fixed point and goes stale every round (witness: a reviewer's post-review header edit had to be reverted under rule 9).

**Ready for execution** means the latest review artifact explicitly states `ready=yes` with zero unresolved blocking findings; any open material grill question or unresolved scope-extension decision is not ready, whatever the review verdict says. Open the artifact and verify its verdict rather than relying on chat summary. The post-fold-digest requirement (rule 6) is enforced by the `--source-plan` mechanical gate in `review-plan` Step 4; a `ready=yes` recorded before a fold fails that gate and does not count.

**Drafting mode:** Conversational Plan Mode is a DRAFTING mode, not a completed plan lifecycle. When the conversation cannot save, review, and finalize the plan artifact, say that review and artifact finalization are pending.

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
- **Symbol-move patch audit:** when a task moves symbols between modules, grep the whole test tree for EVERY patch idiom on the moved names: `monkeypatch.setattr(<module>, "<name>", ...)` AND string-form `unittest.mock.patch("<module>.<name>")`. List each site in the task and require same-commit retargeting to the new owning module; un-retargeted string-form patches fail loudly at import, while un-retargeted `setattr` patches fail SILENTLY (the attribute still exists as a leftover or the patch simply stops intercepting), letting real loaders run inside a characterization net.
- **Recovery-claim feasibility:** when a task specifies a fallback, partial re-scan, or partial-recovery mechanism, trace the new fixture's given/expects through the SPECIFIED mechanism against the real code before finalizing; a fixture expectation the mechanism cannot deliver (for example recovery of content lying inside the malformed region a reset re-scan provably skips) is a spec defect the implementer can only satisfy by improvising a different mechanism. State what the mechanism does NOT recover when today's behavior already loses it, and place a straddling item's load-bearing state before the fallback boundary. (Witness: a plan review caught a seeding contract promising recovery of post-boundary bullets the heading-reset re-scan skips; only reviewer simulation of the real parser state machine exposed it.)

**Pre-finalization self-check (companion to the readiness definition above):** before describing any plan as ready for execution, answer these six questions:

1. Was `review-plan` invoked for this plan?
2. Does the latest Markdown review and `.stats.json` sidecar exist?
3. Does the sidecar digest match the final plan bytes?
4. Does the latest review report `ready=yes`?
5. Are there zero unresolved blocking findings?
6. Does any material grill question or scope-extension decision remain open (any `open:` receipt in the decision-points trailer)?

The agent must not describe the plan as ready for execution when any answer is negative. `scripts/plan_readiness.py` is the mechanical counterpart of this self-check: it is the fail-closed validator that the execution (`execute-plan`) and finalization (`done`) boundaries call on the saved plan artifact; when the plan exists only in conversation, the self-check answers are negative by construction.

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

**RED fixture validity:** every RED fixture must be constructible against the real base shape (build rows through the family's payload helpers, never index into a possibly-empty list), exception-contained when the probe is expected to crash today (wrap it so the harness records a FAIL instead of aborting the run), and pinned to a gate-unique assertion phrase so a pre-existing error cannot satisfy it (see user-level lessons #235). When the fixture injects a mutation or observation through a patched function, place the hook between the initial state read and the first verification on BOTH the pre-fix and post-fix trees: trace where the patched call runs after the planned fix, not only today, or the fixture can never turn GREEN (user-level lesson #258).

## DDD Extraction

When a plan modifies domain types (value objects, entities, enums) that live in a large file (>1k lines), include a task for evaluating extraction to a dedicated domain module. Specifically:
- If the affected types form a cohesive aggregate (e.g., related domain types that work together), propose extracting them to a new module under `domain/` or `application/`.
- Place the extraction task AFTER the GREEN tasks (implementation works) but BEFORE the final validation task.
- The extraction task must verify no circular imports and update all import paths in tests and production code.

## Plan Lifecycle

- When all items are `[x]`, move the file to `{plans_completed_dir}/`.
- When the plan promoted a `{backlog_dir}` item, move that item to `{backlog_completed_dir}/` in the same completion pass, marking it `Status: done` in the same edit (same lifecycle as the plan archive per `doc-hierarchy`).
- When superseded, delete rather than leaving stale `[ ]` items.
- **docs/tmp cleanup (same completion pass, after the archive):** delete the finished plan's `{tmp_dir}` scratch so it cannot accumulate: `{tmp_dir}/plan-requirements-<slug>.md` and `{tmp_dir}/execute-plan/<plan-slug>/` (session logs of a successfully completed plan), plus `{tmp_dir}/review-loop*` / `{tmp_dir}/code-review/` staging that this plan's own review rounds created, but only when that loop's staging is final (the loop reported a clean round); an ACTIVE loop's unsynced staging is never deleted here (same liveness caveat as `done` Step 2.62). When ownership is unclear, leave it in place. Archive first, then clean. Propagation is the `docs-branch` sync's job: `{tmp_dir}` is its one sweep-eligible root, so the branch copies drop in the next sync (usually the same session's `done`).

## Universal Patterns

Core plan quality principles applicable across all projects and languages:

- **Gist & Examples section**: Every plan must include a human-readable "Gist & Examples" section after the header that explains: what changes (plain language), why the change is needed (problem statement or context), concrete input/output examples showing before/after behavior, and edge cases that motivated design decisions. This serves as the on-ramp for both implementers and reviewers who need context before diving into tasks. The Gist is the main user-readable part of the plan: walk at least the happy path as a concrete scenario with clearly separated **Before (today)** and **After (this plan)** paragraphs that name the same trigger and show the different outcome; a terse one-sentence before/after pair is not enough (user correction 2026-09-05).

- **Evaluation Criteria section**: Every plan must include an "Evaluation Criteria" section that defines how quality will be assessed for the final product. This includes quality dimensions (correctness, performance, maintainability, security, test coverage, observability) with specific checks or metrics for each, **Done when** criteria for repository implementation, and **Ship when** conditions for deployed, cross-team, or human-owned evidence. Criteria must be precise and verifiable; not vague statements like "it should work" but concrete tests, commands, metrics, or named release conditions.

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

### Runtime-neutral handoff contract

The normative runtime contract, result schema, policy boundary, manifest
ownership, and continuation transitions live in
`agents/skills/execute-plan/runtime-contract.md`. This skill adds only the
plan-authoring obligation to state required evidence and validation commands;
the continuation driver performs the runtime transitions.

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
Consumer of plan format, task order, `## Validation Commands`, `## Review Scope`, per-task commit lines, and completed-plan archival. It executes only tasks admitted by the Checklist inclusion gate: repository implementation, or a release gate with a current bound exception receipt plus `why executable now` and observable `completion evidence`. External prerequisites are never exception-admissible. Shares Phase 0 branch-setup semantics: `plans` runs it at plan creation; `execute-plan` runs it at implementation start and reuses an existing feature branch when appropriate. Both skills refresh the plans-class skill-gate marker per `ai-playbook/agents/hooks/skill-gate/README.md` Marker WRITE RECIPE before plan-file edits. After plan creation or update, hand off to `execute-plan` when the user wants automated iterative implementation with per-task commits and post-implementation review loops. Scope control happens at plan authoring: execute-plan stays faithful to the plan and never re-grills or re-opens scope mid-implementation; overscope discovered during execution is reported, not silently implemented beyond the plan, and not silently dropped.

### With `review-plan` skill
The `plans` skill provides the Checklist inclusion gate to its consumer, `review-plan`. Plan review verifies that checklist items are repository implementation, and that every release-gate exception has a current bound receipt plus a meaningful `why executable now` and observable `completion evidence`. External prerequisites remain blocking and are never exception-admissible.

### With `grill-with-docs` skill
The Phase 1 confidence gate invokes `grill-with-docs` for every unclear point rated low-confidence. That skill runs a `grilling` interview with `domain-modeling` active throughout, capturing glossary terms and ADRs inline while each point is resolved; confirmed answers feed the requirements buffer, and the plan references the updated glossary/decision docs instead of duplicating terms. High-confidence points skip the grill and land in the plan's `## Assumptions` section instead. The Phase 1 scope-extension hard gate routes every proposed scope extension through this skill before the plan file admits it; the confirmed outcome (in / split / defer) lands in the Step 1.4 confirmation block as a grilled scope extension.

### With `grilling` skill
When the user (not the confidence gate) asks to grill a decision during Phase 1, invoke `grilling` for one-question-at-a-time resolution without doc capture. Do not replace the plans interview structure; grilling deepens specific decisions. Agent-detected low-confidence unclear points route to `grill-with-docs` (see above).

Sync note: the Step 1.4 confirmation meta-rule in this skill restates grilling's generic-acknowledgement, lifecycle-verb, answer-state, and opt-in-phrase rules for confirmation-time self-containment, so an edit to either set of clauses must update the peer in the same change.

### With `done` and `docs-branch` skills (docs/tmp cleanup)
Plan completion deletes the plan's `{tmp_dir}` scratch (Plan Lifecycle bullet). `done` Step 2.62 sweeps ownerless `{tmp_dir}` entries before sync, and the `docs-branch` sync drops branch-tracked `{tmp_dir}` paths absent on disk (its one sweep-eligible root), so branch copies propagate without hand-editing the docs branch.

### With `receiving-review` skill
Provider of the backlog lifecycle that **Backlog capture** points at: captured items live under `{backlog_dir}` with `Status` / `Workflow: backlog` header lines. This skill promotes an item by referencing it from a plan header (**Backlog origin**) and archives it to `{backlog_completed_dir}` when the implementing plan completes (**Plan Lifecycle**).
