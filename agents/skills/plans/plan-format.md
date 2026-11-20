## Plan Format

Every plan follows this exact structure; no variations:

The template block below carries the author-facing source of truth for trailer acceptance mechanics (the bracketed Assumptions line inside it); the readiness validator (scripts/plan_readiness.py, decision_marker_problem) owns enforcement and points here, and sibling skill documents must link to one of these two surfaces instead of restating the mechanics.

A plan may also be stored as a directory under the plans root (the directory shape): the charter file `PLAN.md` carries the shared sections (the template below, minus the task sections), and the `tasks/` subdirectory carries exactly one Markdown file per task, each holding that task's `### Task N:` section, `Files:` list, Evidence bullets, and acceptance checkboxes; the directory name is the plan slug (`YYYY-MM-DD-<slug>/`). Under the directory shape a worker reads the charter plus exactly that worker's one task file, whole (the worker read contract), so no worker context is span-extracted. A plan adopts the directory shape when a substantial edit reopens it (migrate on touch); existing plans keep their single-file bytes, and there is no bulk migration. The plan-shape resolver (scripts/plan_shape.py) is the single grammar both shapes resolve through, and directory-plan digests are manifest hashes over the charter plus every task file (rule 9 carries the verification wording).

```markdown
# Plan: <Feature Name>

[Optional: one-line reference to RFC/PRD/ticket]

[Required metadata block; plans declare one block, not separately-owned lines. It sits in the header region between the title line and the first `## ` heading (the region the maintenance park-guard classification scans), and the `External gate:` line, when a plan carries one, is a member of the same block. The block's fixed lines:]
Backlog origin: <path> [when the plan promotes a `{backlog_dir}` item; otherwise the line reads `Backlog origin: none`]
Driving force: <tag>
Plan review record: the staging series {reviews_dir}/YYYY-MM-DD-plan-review-<artifact-slug>[-p<identity-token>]-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically; `<artifact-slug>` is the canonical artifact slug, the plan's feature slug lowercased). The optional `-p<identity-token>` infix is the canonical identity token derived from this source-plan path (`p` plus the first eight hex of its SHA-256); a tokenless citation still recognizes tokened records at closeout, and a read-only identity diagnostic reports records whose sidecar `extensions.plan_identity` or Metadata `URL or Artifact` does not resolve to this plan - the diagnostic warns only and never filters members, changes selection, or affects exit status.
[The worktree-removal gate normalizes both the literal `YYYY-MM-DD` placeholder and wildcard date prefixes in plan-review series citations, so either form verifies when the records are present, while concrete dates stay exact; the concrete-date prefix is the preferred authoring form.]
Execution budget: <total>h total, largest task <max>h [optional member of the block; size it from the task-shape weight table below before writing tasks]
Executed: no [member of the block; `no` at authoring; after the execution landing the execution closeout flips it to `yes (<recorded tip>)`, the recorded tip being the executed branch's pre-squash tip sha named explicitly, never the landing commit digest (which does not exist at rider time); the metadata-retrofit rule: existing plans gain the field at their next natural edit or revival, never swept]
[The execution budget numbers are the author's non-negative decimal-hour estimates with an optional single fractional part (integers valid; `3h` and `3.0h` are the same value; a missing number, a negative, or a non-numeric value is a malformed line). Estimate execution hours from the task-shape weight table below; preserve tracker points or days in their native units and never convert them to hours without an explicit agreed conversion. If execution hours are not credibly estimated, omit this optional line and report the tracker estimate separately. The task-shape weight table: prose-only 0.25-0.5h; new module with selftest ~1h; large existing-file refactor 1-1.5h; any task estimated above 1.5h splits into its own plan. The weights are calibration defaults updated as landed runs provide data, not a gate. The readiness pre-round gate reads the declared numbers and never estimates cost from plan content: a declared total over 3.0h, a largest task over 1.5h, or more than four `### Task N:` headings each emit one non-blocking `readiness PRE-ROUND WARNING:` line on stderr (see `scripts/plan_readiness.py --pre-round`); plans without the line stay silent.]
[The force tag uses the closed taxonomy `efficiency` | `token-usage` | `simplicity` | `code-quality` | `automation` | `new-capability` | `external`, where `external` must cite its source; compound forces are ranked primary + secondary; the `simplicity` force is active elimination, never status-quo keeping: a simplicity plan deletes machinery (gates, protocol depth, fencing, automation lanes, scheduler state fields) whose continued existence no witnessed failure justifies, where a witness is a recorded incident, a red test, or an explicit user decision; the burden of proof sits on the complexity to cite its witness, not on the deletion to justify itself, so keeping unproven complexity is a simplicity violation just as adding it is; the `automation` force covers work that removes recurring manual direction: the plan's result is machinery that runs a routine loop (survey, author, execute, land, report) itself, and a pipeline step that still needs a human to trigger it is automation debt; a plan whose force is not one of the five driving principles (`efficiency`, `token-usage`, `simplicity`, `code-quality`, `automation`) carries a one-line justification naming why it is implemented anyway and why park-triage would or would not take it. Plan bytes carry no self-referential review-state prose: no latest-round pointers, no verdict citations, no round-attributed residual narratives except the `## Residual findings (cap closure)` section required by the cap-closure terminal shape, which is the sanctioned in-plan home for cap-round residual dispositions; deferred residuals live in the staging record, which remains authoritative after certification.]

## Terms

<The plan dictionary: one bullet per plan- or project-specific term with a one-line definition; render even when empty, as: none.>

## Why

<The reason for this change in one to three plain sentences.>

## Gist & Examples

[Required first line, rendered exactly as shown; one or two phrases; everything already in the section stays below it]
TLDR: <what changes>, <why, naming the driving force>.

[Human-readable explanation of what changes and why, with concrete examples]

## Outcome

<One plain sentence: the aim of this plan.>

- <Positive result of executing it: what works after that breaks or is missing today.>
- <Positive result.>
- <Optional positive result.>

[Required: Gate delta: one line declares net machinery across refusal classes, hard gates, fences, protocol layers, schema fields, and any task condition that pauses dispatch or later work, including prose-only requirements and external surveys; price additions (including refusal-surface or checked-set growth) with a paying sibling or a completed-integrity-failure witness; a fix-class refusal-path addition may instead use Rule 42's origin-cited no-exit justification when its origin records the alternatives and why each is impossible (if it records none, only a paying sibling or completed-failure witness can price it); for the five runtime classes, require the completed-integrity-failure bar unless that Rule 42 exception applies, and require it for deletable machinery kept; name every removed refusal, check, or field; declare blocking review-layer duties separately with a witness; use explicit none when unchanged]

[Required: ## Terms; always renders even when empty; the FIRST section immediately after the header metadata block; the plan dictionary]
[Required: ## Why; the second section; the reason for the change in one to three plain sentences, per the plain-globish bar]
[Required: ## Gist & Examples; the third section; directly after Why and before Outcome; the required opening TLDR line plus the before/after examples per Universal Patterns]
[Required: ## Outcome; after Terms, Why, and Gist & Examples; see the required-elements prose for the plain-globish bar]

[Required: ## Assumptions; always renders even when empty; one bullet per high-confidence assumption with its basis, then the trailer line "Decision points requiring a grill: none remain." or the same single trailer line carrying all per-point receipts carried from the Step 1.4 confirmation, semicolon-separated (never comma-separated; the readiness gate splits receipt segments on semicolons only); never one trailer line per point; the readiness gate accepts the literal none-remain line case-insensitively with an optional trailing period, and treats a trailer value as an unresolved placeholder when the start of the value or of any semicolon-separated receipt segment is pending, tbd, todo, or open (case-insensitive) followed by end-of-value, whitespace, or more word characters, unless it is followed immediately by a hyphen (a hyphen reads as a resolved receipt: `todo-list`, `tbd-for-now`, and `open-question` pass; `todos`, `pending2`, and `TBD for now` fail), or when a segment starts with the character `<`. In the plan file the trailer drops the bold markers and any list prefix and sits as a plain unindented line starting exactly `Decision points requiring a grill:`. Fenced code blocks (terminated or not, backtick or tilde) are invisible to the trailer check; the trailer must sit as a plain unfenced line inside ## Assumptions]

## Standing constraints

[Optional, declared when needed: render the section only when the plan carries repo-wide rules, conventions, or invariants every task must respect; one bullet per constraint, stated once here and referenced by every task's context surface, never restated]

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

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `path/to/NewFile.ext` (Task 1) *(new)*
- `path/to/ExistingFile.ext` (Task 1)

**Tests:**
- `path/to/NewTest.ext` (Task 1) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `path/to/UnrelatedFile.ext`; reason

## Validation Commands

```bash
<test-command>
```

### Task 1: [Name]

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `path/to/NewFile.ext` *(new)*
- `path/to/RemovedFile.ext` *(deleted)*
- `path/to/ExistingFile.ext`

Primary class anchors:
- `OwningClass` in `path/to/ExistingFile.ext`

- [ ] `OwningClass` delivers `<behavior name>`: given `<observable scenario>`, expects `<observable outcome>`
- [ ] Safety witness (when the task owns a safety decision): given `<unsafe input or failure>`, expects `<contained outcome>`
- [ ] Run → expect RED: the behavior's failing check (tests, fixtures, and commands are selected at execution from repository evidence)
- [ ] Write minimal implementation
- [ ] Run → expect GREEN
- [ ] Commit: `feat: <why-first short description>`
```

**Plan-owned behavior and safety decisions; required:** Every plan states, and every task carries, the decisions that stay plan-owned: public behavior, invariants, ownership, state transitions, observable acceptance, and external release conditions. The task checklist states these as observable witnesses: a witness names a concrete scenario and the observable outcome that demonstrates required behavior or safety, in the given/expects form (given `<scenario/inputs>`, expects `<observable outcome>`); a task owning a safety decision states its safety witness the same way. A behavior or safety claim with no observable witness is a review-blocking defect; review-plan's readiness boundary examples own the paired ready and blocked judgments.

**Primary class anchors; required:** Every plan task that owns production behavior declares a `Primary class anchors:` block immediately after its `Files:` list naming the production class or classes that own the task's behavior, each with its source path (one bullet per anchor, the runtime-owned entry shape - `ClassName` in `path/to/file.ext`, both tokens backticked, optionally followed by a comma and prose - the form's single owner is the `PRIMARY_CLASS_ANCHOR_ENTRY` grammar in `scripts/plan_shape.py`, which the readiness pre-round gate and execution seeding both enforce; an anchor name is a repository-verifiable identifier, never a descriptive phrase). The anchor identifies the behavior owner review and execution start from; it is an implementation anchor, not an exhaustive permission list, and execution records the expanded task scope before worker launch.

**No guessed implementation inventory:** The plan does not name supporting production or test paths, test identities, fixture wiring, schema resources, or exact task commands; execution discovers and validates that scope from repository evidence before manifest creation and records it in the manifest task record. Reintroducing a guessed inventory item as a plan-authoring or review-readiness requirement is a defect; the structural readiness validator stays path-structural and never requires them.

**Rules:**
- Title is always `# Plan: <name>`; no other heading format.
- Every plan must include an **Outcome section** (`## Outcome`) after the always-rendered `## Terms` dictionary, the `## Why` reason-for-change section, and the `## Gist & Examples` section that directly follows Why: one plain-globish aim sentence plus two to four result bullets stating what works after execution; the summary is self-contained (understandable without Terms or Tasks), uses no internal codenames or task jargon, and is specific enough to classify the plan (what breaks today, what works after); the plans review flags its absence like any other required element. The Outcome region also carries the required `Gate delta:` line per the template spec.
- **Follow-up disposition declaration:** a plan whose Done-when criteria allow an evidence-backed stopping point, whose tasks name candidate rejection, or whose outcome is a user-requested follow-up states its plan-specific follow-up disposition rule in the Outcome region before review: the anticipated candidate leads it may leave behind and the route each takes — promoted to a durable backlog origin with a ready-to-dispatch prompt, or recorded as a rejected disposition with its ruling evidence — so closure never orphans still-viable follow-up work named by the run's own outputs.
- Every plan carries the readability contract over the section range from `## Why` through `## Evaluation Criteria` inclusive: plain human-readable prose, only required jargon, and every plan- or project-specific term used in that range defined in the `## Terms` dictionary; the plans review and the documentation lens flag violations like any other required element.
- **Standing constraints read surface:** the template's `## Standing constraints` section is optional-declared and ungated: a plan declares it when it carries repo-wide rules, conventions, or invariants every task must respect, stated once in the section and referenced by every task's context-surface line, never restated per task; an existing plan without the section stays valid and no readiness check requires it. Curation stays an optimization never a restriction: a worker that finds its declared slice (Terms plus the task plus Standing constraints) insufficient reads the whole plan and reports it; the done and review gates keep reading everything; quoted landing text is never deduplicated.
- The Gist section opens with a required one-line summary: the first line of `## Gist & Examples` says what changes and why in one or two phrases, naming the plan's declared force; everything already in the section stays below that opening line (the placeholder form lives only in the Plan Format template block above).
- **Metadata retrofit rule:** existing certified plans (the latest review sidecar digest matches the plan's current bytes) are never rewritten solely to add the header metadata fields or the Gist opening summary; they gain them at the next natural edit or at deferred/ revival.
- Every included task item is `- [ ]`; concrete and verifiable, never vague.
- **Checklist inclusion gate:** first classify every proposed candidate as **repository implementation**, **external prerequisite**, or **release condition**.
- In this classification, a release condition means release gate.
- **Fail closed on ambiguity:** if ownership, target, or evidence source is unclear, do not label the candidate as repository implementation, and do not open a release-gate exception. Put it under **Ship when** as an external prerequisite or release gate until ownership is affirmative.
- Only repository implementation becomes an **executable plan task** and uses `- [ ]` by default. Put external prerequisites and release conditions under **Ship when** as prose.
- **Classification tag rule:** every task checklist item carries a classification tag at the end of the item line: `[class: IMPLEMENTATION_REQUIRED]` for implementation work, `[class: REPOSITORY_TEST]` for in-repo verification work. The tag sits on the item's FIRST (checkbox-marker) line; a multi-line (wrapped) item never carries the tag on a continuation line, where the readiness parser cannot see it, and `scope_classification_problem` reports the placement instead of classifying the item untagged. External-gate and operations requirements are never task items; they are written in **Ship when** prose with their class (`[class: EXTERNAL_RELEASE_GATE]` or `[class: OPERATIONS_FOLLOW_UP]`), their evidence owner, and their closure condition named in the prose. `plan_readiness.py` enforces the tag rule under the sidecar-date rule (see `scope_classification_problem` in scripts/plan_readiness.py for the vocabulary, the Ship-when exemption, and the exact date).
- **Gate delta ledger citation:** when a plan's `Gate delta` line declares an addition of a gate or fence (two of the five counted classes), the line also cites the guard liveness ledger's current catch-to-incident ratio (run `python3 scripts/gate_liveness_ledger.py show` at authoring time), so the section 64 fewer-moving-artifacts rule reads a measured catch-to-incident ratio instead of a per-mechanism judgment alone; a plan adding no gate or fence cites nothing.
- **Review tier hint (optional):** a task line may carry `Review tier: <L|M|H>`; the author sets it when they know the expected review weight, and omitting it lets the executor derive the tier from the task's files and changed-content signals. The tier is a starting point only: post-implement risk signals may raise the tier and never lower it. Treat the `### Per-task intermediate review selection` subsection of `agents/skills/review-agents/review-panel-selection.md` as the sizing authority; reference its tier table, do not duplicate it.
- **Intermediate reviews opt-out (optional):** a plan header line `Intermediate reviews: off` skips the per-task Step 1.2b intermediate review for that run; absence of the line or any other value keeps it on (default on). See `agents/skills/execute-plan/SKILL.md` Step 1.2b.
- The taxonomy mapping and conflict rule: the four classification tags refine the inclusion gate's classes. `IMPLEMENTATION_REQUIRED` and `REPOSITORY_TEST` refine the repository-implementation class; `EXTERNAL_RELEASE_GATE` refines the release-condition class and `OPERATIONS_FOLLOW_UP` refines the external-prerequisite class. On conflict the stricter inclusion-gate classification wins: an item carrying a gate or operations obligation is classified by the stricter class and moves under **Ship when**.
- **Scope ledger (prevention):** classification is recorded at plan creation and re-checked at the first readiness review, so misclassification surfaces at the readiness boundary, not mid-execution.
- **Ownership ledger (prevention):** the ownership ledger of files, witnesses, and their owning tasks is written before prose expansion, so method-level ownership ordering is settled at authoring time rather than rediscovered mid-execution.
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
- **Files:-coverage (required):** every path a task's acceptance items require is in that task's `Files:` list, and every `Explicit must-fix` path carries `(Task N)` matching that task's `Files:` list or `(review-only)`; the readiness validator's warning-only Files:-coverage arm reports both.
- **Planned-deletion marker:** a task `Files:` item carrying *(deleted)* declares that the task deletes that path at execution; it is not a creation record (it never claims the path the way *(new)* does), and the readiness Files-existence check exempts it whether or not the path exists today. An unannotated later listing of a path an earlier task already marks *(new)* is accepted as-is; no author action or grammar token is needed for it.
- Include inline code snippets when the implementation pattern is non-obvious.
- No meta-tasks ("review docs", "confirm scope").
- When the RFC or rollout defines multiple deployable safe-ship phases, create one plan file per phase instead of one monolithic plan. Prefix filenames and titles with the explicit phase order (for example `phase-1`, `Phase 1 - ...`).
- **Two-round alarm:** when a second review round ends without certification, the mechanism is too novel: split the mechanism, not the tasks (a novel mechanism reviewed inside a larger plan drags every round over its whole surface; a split isolates the novelty so certified parts land while the novel part iterates).
- **Seam rule:** a split boundary never cuts a shared-file set (tasks editing the same production or test file stay in one plan); when a split is still needed, the resulting strictly sequenced plans declare a header execution dependency under the existing parked-dependency machinery (the execute-plan queue-drain contract's live `parked_dependencies` entries and dependency-blocked marks), so the successor waits on the predecessor's landed branch instead of manufacturing rebase churn.
- When a plan builds on prior completed phases, include a **Design Invariants (CR Guard)** section after the header listing prior-phase decisions that must not be compromised during code review, with specific rationale for each (e.g. RFC constraint ID, elimination trail reference).
- Before finalizing a CR Guard, cross-check every design decision source (RFC rules, design notes, prior phase decisions, PRD constraints, team agreements) against the guard lines. Guards should protect both prohibitions ("must not do X") and positive design decisions ("must preserve Y", e.g. ungated fallthrough for future extensibility).
- **Do not make bare "inherited/validated/previously-reviewed/tested" claims.** Phrasing like "gate-core inherited," "validated by prior rounds," or "unchanged and already tested" creates a review blind spot: `review-plan` panels treat the assertion as proof and skip re-measuring the mechanism. If a mechanism genuinely carries over, name the specific mechanism AND the input/condition it was validated against (e.g. "the fence-aware parser resets `in_fence` at each heading; tested against the real corpus's odd fence count"), or re-state what the mechanism does and how it is tested in THIS plan. A claim of validity is not a substitute for the test.
- Every plan must include a **Review Scope** section (see below).
- Every plan must include a **Gist & Examples** section (see Universal Patterns).
- Every plan must include an **Evaluation Criteria** section defining quality dimensions, **Done when**, and **Ship when** (see Phase 1).
- When Phase 1 recorded high-confidence assumptions (confidence gate), the plan must include an `## Assumptions` section listing each assumption with its basis; a plan that silently builds on an unlisted assumption is a defect; the section always renders and closes with the decision-points trailer carried from the Step 1.4 confirmation, and plan_readiness.py enforces the trailer under the sidecar-date rule (see the DECISION_MARKER_MIN_DATE constant in scripts/plan_readiness.py for the exact date and exemption semantics). A tracker-linked plan also carries the confirmation block's Sources inspected record as its own Assumptions bullet, so the reconciliation survives into the reviewed plan bytes.
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
- At plan creation: list every file the Tasks sections reference under **Explicit must-fix**, each annotated `(Task N)` or `(review-only)`; mark new files with *(new)*.
- When updating a plan mid-feature: re-derive the explicit list from `git diff <base-branch>..HEAD --name-only` and classify each file as must-fix or out-of-scope based on whether it was changed to implement this feature's tasks.

**How to derive explicit must-fix files when building on a prior branch:**
```bash
git diff <prior-phase-branch>..HEAD --name-only
```
Classify each file as:
- **Explicit must-fix:** changed to implement a task defined in this plan (feature code, tests, config, docs the plan names).
- **Out of scope**; present in the diff due to incidental cleanup, review-driven fixes of pre-existing issues in unrelated components, or formatter noise. List these explicitly with a one-line reason.

**Format:**
```markdown
## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `path/to/NewFile.ext` (Task 1) *(new)*
- `path/to/ExistingFile.ext` (Task 1)

**Tests:**
- `path/to/NewTest.ext` (Task 1) *(new)*
- `path/to/ExistingTest.ext` (review-only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `path/to/UnrelatedFile.ext`; one-line reason
```

**Placement:** immediately after `## Evaluation Criteria` and before `## Design Invariants` (if present) or `## Validation Commands`.

**Scope model (two tiers):**

| Tier | Role | Review / address behavior |
|------|------|---------------------------|
| **Explicit must-fix** | Task `Files:` paths and named deliverables | Always review; valid findings must be fixed or explicitly triaged |
| **Plan-related extension** | Unlisted paths touched during execution or full-branch review | In scope only when causally related to plan goals; assess each finding; do not auto-drop because the path was omitted from the plan |

**Plan-related test (use during review triage):** Can you tie the finding to a specific plan task, explicit must-fix change, or contract the plan altered? If yes → in scope. If no → drop. When an explicit must-fix change implies follow-on updates elsewhere (supporting scripts, linked instructions, config the runtime reads), those follow-ons are plan-related even if omitted from the explicit list.

**After execution:** if review repeatedly surfaces plan-related findings in the same unlisted area, add that path to **Explicit must-fix** on the next plan update.

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

Load on demand: read agents/skills/plans/validation-authoring-rules.md when a plan's Validation Commands section is authored or reviewed; the module owns the authoring rules for plan-specific validation commands and their separation from project-wide final validation (the target project's suite-policy obligation at its own final boundary), including routing a plan instruction that conflicts with the target suite policy to the operator before certification.
