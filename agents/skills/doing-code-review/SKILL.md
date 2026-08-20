---
name: doing-code-review
description: >
  Active code review skill. Orchestrates the recommended five-worker panel from review-panel-selection for thorough review of PRs, diffs, or branches. Language-agnostic core with runtime language overlays (Java/Spring, Kotlin/Spring, Python). Two modes: posts PR review comments by default; fix mode (auto-commit) when explicitly asked. Trigger phrases: "let's review", "review this PR", "review the changes", "review changes in", "review branch", "review against", "code review", "look at this PR", "check this PR", "check this diff", "doing-code-review". Do not use for addressing existing reviewer comments; use receiving-review instead.
---

# Active Code Review

**Documentation paths:** Read `{reviews_dir}` and `{tmp_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0) before writing staging docs or any diff snapshot files. Examples below use `{reviews_dir}/` and `{tmp_dir}/`; substitute the resolved paths.

## Boundary

Use this skill for **active review**: producing new review findings for a PR, diff, or branch.

Do not use this skill for implementing, triaging, or replying to existing review comments. Use `receiving-review` for passive review feedback. For GitHub PR operations (fetching metadata, files, diffs, existing comments, posting reviews), use the shared primitives in `github-pr-workflow`.

**Caller: `execute-plan` Phase 3.** The execute-plan **parent** is this skill's orchestrator by default: it launches lens workers and writes the staging doc. Do not wrap this skill in a nested "Code Review" sub-agent when the parent can fan out (see `execute-plan` Step 3.1). Nested recovery is only for hosts that cannot launch workers.

**Doc/skill-only diffs.** When the review scope is Markdown, skills, or guidelines and the plan's Validation Commands are grep/hygiene (no production mutators), the `testing` worker uses those commands as primary evidence. Do not invent mutation trees, scratch validators, or throwaway harnesses under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` or `{tmp_dir}/code-review/`.

## Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Staged** (default) | "review this PR", "let's review", "review the changes", "review changes in", "review branch", "review against" | Write findings to `{reviews_dir}/` (create dir if missing) |
| **Direct** | "review and post directly", "skip staging" | Post findings immediately to PR (legacy behavior), still write staging doc as record |
| **Fix** | "review and fix", "fix mode" | Fix confirmed issues, commit, signal for re-review |

**Always produce the staging doc**, regardless of mode. For local branch reviews (not GitHub PRs), use branch-based naming. The staging doc serves as both approval artifact (for PRs) and persistent record (for all reviews).

### Hard Gates (apply before and after every step)

1. **Launch all relevant sub-agents before assessing findings.** Do not replace the sub-agent pipeline with manual analysis, grep scans, or inline investigation regardless of how narrow the user's request seems.
2. **Write the staging doc before reporting any findings to the user.** The staging doc is the deliverable. Conversation-only findings do not count.
3. **Do not skip the staging doc because findings seem too few or too simple.** Even zero findings must be recorded in the staging doc.

### Focused Reviews

When the user provides a specific concern in their request (e.g., "check for secrets", "look for performance issues", "make sure there is no personal data"), this does **not** narrow the review scope. The user's concern is a priority lens, not a scope filter. Launch all relevant sub-agents as usual; the user's focus area often surfaces findings that a narrow scan would miss.

If the user explicitly says "only check X" or "skip everything except X", honor that request but still write the staging doc with whatever findings result.

User args (e.g., "check for secrets", "against branch X") provide context for the review, not a mode selection. The review mode (Staged/Direct/Fix) is determined by trigger phrases, not by the content of the args.

### Anti-patterns

- Inventing panel composition inline. Use the full or focused panel rules in `review-panel-selection.md`.
- Reporting grep results, manual scans, or inline analysis as the review output. Sub-agents provide coverage a single pass cannot; the staging doc is the deliverable.
- Replacing the sub-agent pipeline with a targeted scan because "the user only asked about X." A focused scan cannot find what it was not asked to look for; the selected panel can.
- Writing diff/review capture files to the repo root or other tracked paths. Diff artifacts belong under `{tmp_dir}/` only (see **Diff access** below; canonical rule in `agent_workflow_guidelines.md` §50.3.2).
- Silently inferring the diff base for a branch review, or proceeding when the basis is ambiguous: ask the user for the comparison base instead. Leaving `<base>` as a literal placeholder in a branch review is this anti-pattern.

## Step 1: Gather Context

### Resolve the comparison basis

Resolve the `<base>` / `<head>` to diff against before any `git diff` or sub-agent launch. The resolution depends on the review source:

- **PR URL:** base and head resolve unambiguously via `github-pr-workflow`. This is the "obvious" case; no prompt is needed.
- **Branch review, base not obvious:** do **not** leave `<base>` as a placeholder. If the base cannot be resolved with confidence (no `against X` arg, no single open PR, ambiguous integration branch), resolve it via the tier fallback (the repo's default integration branch per `AGENTS.md`). Then branch on the execution context:
  - **Interactive top-level session:** ask the user explicitly, "What branch/commit should I diff against?" (or confirm the resolved default) before any `git diff` or sub-agent launch.
  - **Non-interactive / execute-plan or review-loop context (risk-F1):** when the execute-plan parent is orchestrating Phase 3, when invoked via the recovery Code Review template, when under `review-loop`, or in a session with no user at the console (CI/scheduled), do **not** prompt. Accepting the resolved default is required to honour `execute-plan`'s "no asking between steps" contract (`execute-plan/SKILL.md` Continuous execution). Record the resolution + reason in the staging-doc Metadata (for example `Base resolved non-interactively: main (repo default; no PR/arg, execute-plan Phase 3)`) so it is auditable rather than silent. The prompt fires only in an interactive top-level session.
- **Magnitude check (all modes):** after resolving the base, run `git diff <base>...<head> | wc -c`. If the byte count exceeds `review_large_diff_bytes` (default `10240`), the change is unexpectedly large. Read `review_large_diff_bytes` from the opening TOML block in `.ai-playbook/facts.md` (same source as the **Documentation paths:** preamble above; absent key ⇒ default `10240`); this read is pinned to Step 1 because the magnitude check runs here, before the later `### Resolve paths from facts` subsection. On a large diff:
  - **GitHub PR URL (base already unambiguous):** do **not** prompt to confirm the basis. Proceed with the PR's base/head and record the byte count plus resolved base in staging Metadata. Asking "confirm this PR base?" when the user already supplied the PR URL wastes a turn; the magnitude gate still records size for audit.
  - **Interactive top-level session (branch review / ambiguous base only):** confirm the basis with the user before launching sub-agents (state the size and proposed base; proceed only once the user confirms). **Decline path:** if the user does not confirm (declines, names a different base, or aborts), re-resolve to the corrected base and re-run the magnitude check, or stop; do not launch against an unconfirmed base.
  - **Non-interactive context:** skip the confirmation prompt (the orchestrator's autonomy contract takes precedence) but still record the diff size and the resolved base in the staging Metadata.

For a GitHub PR URL, use `github-pr-workflow` to resolve owner, repo, PR number, base branch, head branch, changed files, diff, and existing review comments.

Before assessment, scan existing PR review comments for author-documented scope decisions (intentional MVP limits, deferred routes, "for now" behavior). Use them in Step 4.2 assumption checks and dedup; do not treat seed-data or domain-model roles as in-scope requirements when the PR description, tests, and author threads say otherwise.

Pull latest commits:
```bash
git checkout <base-branch> && git pull origin <base-branch>
git checkout <pr-branch>   && git pull origin <pr-branch>
```

Read all changed files to understand the scope:
```bash
git diff --name-only <base>...<head>
git diff --stat <base>...<head>
```

## Step 2: Detect Project Language

Determine the primary language/framework from the changed files and project structure:

| Signal | Language overlay |
|--------|----------------|
| `pom.xml`, `build.gradle`, `.java` files | `java-spring` |
| `build.gradle.kts`, `.kt` files | `kotlin-spring` |
| `requirements.txt`, `pyproject.toml`, `.py` files | `python` |
| Other / mixed | `general` |

Load the matching overlay file from this skill's directory (e.g. `java-spring.md`). The overlay content is appended to each sub-agent prompt as additional language-specific review context.

**Layering rule:** `review-agents/*.md` catalogs stay **language- and project-agnostic** (abstract patterns and pattern IDs only). Stack-specific triggers live in these overlays. Project-specific naming, runner splits, and local harness conventions live in company/project guidelines and are discovered in Step 2.5. Never hardcode a single project's test-class suffix or runner name into an agent catalog or overlay as a universal requirement.

## Step 2.5: Discover related guidelines (Guideline Pack)

After choosing the language overlay, build a **Guideline Pack** so workers can apply local conventions without baking them into shared agent files.

### Resolve paths from facts

Read `user_facts_path` (`~/.ai-playbook/facts.md`), then when under `company_projects_root` also `company_ownership_facts`, then the repo's `repo_facts_rel` (`.ai-playbook/facts.md`). Resolve:

| Key / source | Use |
|--------------|-----|
| `shared_docs_dir` | Shared **language** guidelines (`java_guidelines.md`, `jvm_guidelines.md`, `kotlin_guidelines.md`, `python_guidelines.md`, `coding_guidelines.md`, …) |
| `company_guidelines_master` | Canonical **company** engineering guidelines (under `company_ownership_docs_dir`, for example `…/<company-root>/.ai-playbook/company-guidelines.md`). Prefer this master over any repo `company_guidelines_repo_mirror_rel` copy. |
| `project_guidelines_rel` | **Project** guidelines in the current repo (often `docs/maintenance/project-guidelines.md`) |

### Company + project together

When the workspace is under `company_projects_root` (company-scoped):

1. Attach **both** `company_guidelines_master` and `project_guidelines_rel` to the Guideline Pack whenever each file exists. Do not treat company guidelines as optional once a project file is present, and do not skip the project file when only company rules seem relevant.
2. Use them **together**: company rules own cross-repo conventions (for example test-class naming scope); project rules own repo deltas and indexes (for example which Failsafe patterns or MockMvc rules apply here). When both speak to the same topic, apply company baseline then project deltas; do not invent a third convention.
3. Personal / non-company repos: omit `company_guidelines_master`; use `shared_docs_dir` + `project_guidelines_rel` (and any personal ownership guidelines facts name).

### Overlay → shared language guideline map

| Overlay | Primary shared files under `shared_docs_dir` |
|---------|-----------------------------------------------|
| `java-spring` | `java_guidelines.md`, `jvm_guidelines.md`, `coding_guidelines.md` |
| `kotlin-spring` | `kotlin_guidelines.md`, `jvm_guidelines.md`, `coding_guidelines.md` |
| `python` | `python_guidelines.md`, `coding_guidelines.md` |
| `general` | `coding_guidelines.md` |

### What to pass (progressive disclosure)

Do **not** bulk-paste entire guideline files into every worker prompt.

1. List absolute paths for the language overlay (already loaded) plus the shared language files, and when company-scoped the **pair** `company_guidelines_master` + `project_guidelines_rel` (each if present on disk).
2. Add **section / rule hints** by worker lens and Domains. Prefer each file's own index when present (company numbered rules; project "Testing patterns" / rule-number tables). Examples for the testing worker: company test naming; project MockMvc / integration-runner / harness rules.
3. Instruct workers: open only the hinted sections on demand; apply abstract patterns from the lens catalog; for concrete harness names, class suffixes, and runner commands, read **company and project guidelines together** plus sibling tests in this repo. Do not invent a convention that contradicts either file.

Record in staging Metadata under the `Guideline pack:` field (the field name `review-staging` requires; do not use a snake_case key) with overlay id and the guideline paths actually attached (not the full file bodies), including whether company and project were both present.

## Diff access (orchestrator and sub-agents)

**Preferred:** Each review sub-agent runs `git diff <base>...<head>` and reads changed source files directly. No patch files are required.

**Re-review after local fixes:** `git diff <base>...HEAD` only includes committed `HEAD` changes. Before launching a new review round after applying fixes, either commit/amend the fixes first or explicitly include the working-tree diff (`git diff`) in the sub-agent prompt/materialized snapshot. Do not ask sub-agents to verify uncommitted fixes using only `<base>...HEAD`; they will re-report stale findings from the old commit.

**Optional materialization:** If the orchestrator writes diff snapshot files (for example to share one diff across parallel sub-agents), they **must** live under `{tmp_dir}/`:

| Context | Directory |
|---------|-----------|
| Standalone review (not `execute-plan`) | `{tmp_dir}/code-review/<session-slug>/` |
| `execute-plan` Phase 3 | `{tmp_dir}/execute-plan/<PLAN_SLUG>/` (same session dir as review logs) |

**Naming (when materialized):**

- `diff-r<R>.patch`: full branch diff (all changed files)
- `src-diff-r<R>.patch`: source and config only (for example `*.py`, `*.java`, `*.kt`, `*.ts`, `*.tsx`, `*.js`, `*.go`, `*.rs`, `*.yaml`, `*.yml`, `*.toml`, `*.xml`, `*.gradle*`, `*.properties`, `pom.xml`, `build.gradle*`, `*.sql`)

`<R>` is the review round number when known (execute-plan); omit or use `1` for standalone reviews.

**Hard rules:**

- Do **not** write diff/review artifacts to the repo root, tracked paths, or `{reviews_dir}/`: no patch, diff, or capture file of any name (canonical rule + filename examples in `agent_workflow_guidelines.md` §50.3.2).
- Prefer no on-disk capture. If a tool truncates large `git diff` stdout: (1) read the runtime's saved capture for that command when one exists; (2) otherwise materialize under `{tmp_dir}/code-review/<session-slug>/diff-r1.patch` (create the directory first). Never invent a repo-root scratch file to work around truncation.
- At the start of a review round, remove orphan `diff_r*.patch` / `src_diff_r*.patch` / `*diff-capture*` files from the repo root if a prior run left them behind.

**Cleanup:**

- `execute-plan`: Phase 5 removes `{tmp_dir}/execute-plan/<PLAN_SLUG>/` (logs and diff snapshots together).
- Standalone review: remove `{tmp_dir}/code-review/<session-slug>/` when the staging doc is final.

## Step 3: Launch Sub-Agents in Parallel

Read `review-agents/review-panel-selection.md` to determine the recommended five-worker or focused panel and which conditional lenses `risk` loads. Record selection rationale and Domains in staging metadata.

**Soften watchlist (multi-round / review-loop):** Before launching workers, read `### Soften watchlist` from the previous staging doc for this branch (and git log subjects matching `Soften r` when the section is missing). Pass every `open` row into each relevant worker prompt. Workers must either restage the issue or return an explicit reaffirmation; the orchestrator records the outcome in the new staging doc. Do not discard with `prior-review` alone when the prior outcome was a soften/revert.

Launch all selected review worker agents **in parallel** using your agent's sub-agent execution capability (parallel launches when supported). Wait for all to complete before proceeding.

Each worker receives:
1. **`severity-calibration.md`** (always; tier definitions and decision procedure)
2. Its assigned lens catalogs from `review-panel-selection.md`
3. The language overlay content
4. The **Guideline Pack** index from Step 2.5 (paths + section/rule hints for this worker). Instruction: "Lens catalogs are language/project-agnostic. Use the overlay for stack triggers. For naming, runners, and harness conventions, read Guideline Pack sections on demand: when company-scoped, use **company guidelines and project guidelines together** (company baseline, project deltas); mirror sibling tests in this repo. Do not require a project-specific test-class suffix unless those guidelines or siblings establish it. Prefer `company_guidelines_master` over a repo company-guidelines mirror."
5. Instructions to run `git diff <base>...<head>` (or read `{tmp_dir}/.../diff-r<R>.patch` / `src-diff-r<R>.patch` when the orchestrator materialized snapshots under `{tmp_dir}/`) and read source files for full context
6. The base and head branch names
7. Open soften-watchlist items that match this worker's lenses (pattern prefix / ownership), when any
8. Output format: return the shared finding fields plus `path`, `line`, `side`, `body`, `pattern`, and `descendant_launches`.
9. An explicit constraint: "Do not over-investigate or validate every single line number. Read the diff and key source files, then report findings. Write each `body` to full §4.12 depth: quote contract/doc text, name the code path, describe actual behavior, state why it matters, and suggest fix options. For Medium+, include all four Comment sections inline in `body` using `**Bold headings**`. For any actionable code/test/config fix at any severity, include a concrete before/after or 'could look like' code snippet per §4.9.0 in `body`, preferring inline backtick spans for short snippets and keeping any fenced snippet free of heading-like lines (lines starting with `#`). Include one sentence why the chosen severity applies (`severity-calibration.md`)."
10. **Scratch / truncation (mandatory on every worker and on any sub-agent whose job is to return full `git diff` output):** "Never write `git diff` or review captures to the repo root (see **Diff access** / `agent_workflow_guidelines.md` §50.3.2). If a tool truncates stdout, read the runtime's saved capture for the command or write only under `{tmp_dir}/code-review/<slug>/`. Prefer re-running `git diff` and reading sources over inventing a root scratch file."
11. **Coverage-claim audit (when the worker builds or updates a mutator/failure-mode matrix):** a cell that cites an out-of-container constructor test for a request-boundary component cannot mark production wiring as `checked: yes`. Leave unchecked or stage `testing#coverage-claim-unchecked` / `testing#harness-fidelity-gap` until a Guideline Pack–conformant full-context harness proof exists.

When launching a sub-agent whose job is "return full `git diff` output", include item 10 verbatim and resolve `{tmp_dir}` from the target repo's `.ai-playbook/facts.md` into an absolute path in the prompt (do not leave the placeholder unresolved for that helper).

**Timeout handling:** If a sub-agent has not completed within 10 minutes, launch a replacement with a more focused prompt (limit to first 1500 lines of diff via `| head -1500`, add "read key source files directly" instead of exhaustive investigation). Do not wait indefinitely for stuck agents.

Workers:

| Worker | Lenses |
|--------|--------|
| `correctness-completeness` | `quality`, `implementation` |
| `testing` | `testing` |
| `design-simplicity` | `architecture`, `simplification` |
| `contract-docs` | `documentation` |
| `risk` | `security`, plus signaled `concurrency` and `premortem` |

Each worker returns a JSON array plus `descendant_launches`. Fully expanded findings are self-contained:
```json
[
  {
    "path": "src/File.java",
    "line": 42,
    "side": "RIGHT",
    "body": "**What the contract says**\nThe OpenAPI `409` response says updates are rejected before any write.\n\n**What the code does**\n`ConsentController` pre-checks status, then the orchestrator re-reads inside `@Transactional` with no row lock. Under READ COMMITTED, a concurrent delete after the re-read can still allow writes.\n\n**Why this matters**\nContract drift: integrators expect strict `409`; the race is documented elsewhere but not in OpenAPI.\n\n**What we could do**\nSoften the OpenAPI description to match runtime behavior, or add `SELECT … FOR UPDATE` before the first mutating statement.",
    "severity": "Medium",
    "blocking": false,
    "consequence": "Integrators may implement a retry contract the service does not provide",
    "reachability": "common",
    "blast_radius": "multi-service",
    "confidence": "verified",
    "pattern": "quality#contract-drift"
  }
]
```

**Stats sidecar:** write `{reviews_dir}/<same-basename>.stats.json` per `review-staging` in the same pass as the staging doc.

**Conditional lenses:** load premortem and concurrency inside `risk` per `review-panel-selection.md`.

**Skip `documentation` entirely** only when internal refactor with no user-visible change **and** no added/modified prose in the diff.

Report problems only. No positive observations.

## Orchestrator Boundary

The orchestrator **coordinates** sub-agents; it does **not** re-do their analysis. Keep orchestrator context lean: collect agent JSON, dedup, spot-check, format the staging doc; do not re-read diffs or source files to author finding detail that belongs in sub-agent `body`.

| Do | Do not |
|----|--------|
| Launch agents, wait, parse JSON returns | Re-analyze the diff inline while agents run |
| Dedup, tone-check, verify line numbers, drop invalid findings | Re-read sources to expand thin `body` text (relaunch the agent instead) |
| Record Review Statistics per `review-staging` while deduping (Panel with Solo/Echo, Deduplication groups, Discarded with Pattern, Severity calibration, Triage placeholder) | Re-derive full contract-vs-code analysis the agent should have returned |
| Spot-check a claim only when the agent's stated evidence is missing or contradicts a quick grep | Copy full agent JSON into orchestrator chat when paths/counts suffice |
| Write staging doc from agent payloads + §4.12 polish | |

**Insufficient sub-agent output:** relaunch the responsible agent with a focused prompt ("expand finding N to §4.12 depth with quoted contract and code behavior"). Treat orchestrator expansion as recovery only, not the normal path.

## Step 4: Assessment Pass

After collecting all agent results and premortem findings, run these verification checks **using evidence already in sub-agent `body`**. Re-read source only for a targeted spot-check when a claim lacks cited evidence or a quick check contradicts the agent. Do not re-run full sub-agent analysis in the orchestrator context.

### 4.1 Verify Root Cause Location
Is the comment pointing at the actual source of the issue or at a downstream artifact? Move upstream if needed.

### 4.2 Check Assumptions
Drop or reword findings that assume something not true in context:
- A concern already handled at another layer, DB constraint, or framework feature
- Placeholder/stub code treated as production code
- Project uses an architecture it has not adopted
- Ops/infra dependencies not provisioned yet (Kafka topics, DLT, ingress, secrets managers): reframe as a go-live checklist and doc-now action, not "provision in IaC immediately"; downgrade to Low unless the gap also breaks dev/test or local runs
- Self-documenting code flagged for missing docs (defer to `documentation.md` phase 1); defer redundant or verbose existing prose to `documentation.md` phase 2
- A cache operation that is a defensive no-op (keys already expired by TTL at call time) flagged as "incomplete" or "broken"
- Editing an existing migration in a pre-deploy greenfield service flagged as a Flyway immutability break. First verify whether any shared, CI, staging, or production environment has applied it. If not deployed anywhere and local databases are easy to reset or repair, drop the finding or reframe it as a Low release-readiness note.
- **Author-documented intentional scope in existing PR threads or in-diff docs:** before keeping a Medium+ finding about authorization, RBAC, or feature completeness, read existing PR review comments (including author replies) **and** in-diff TODO/Javadoc/Layer 2 notes that mark a later-story deferral. If the author states an MVP decision ("for now", "no endpoints yet", "configure per route when added", "TODO: wire client in later story", "returns null until that client is implemented"), drop or downgrade unless head code contradicts that stated intent. Fail-closed stubs with an explicit follow-up story are intentional scope, not High merge blockers. After dropping one such finding, scan remaining staged findings for the same intentional-deferral pattern.
- **Story scope vs domain seed data:** roles, enums, or fixtures in seed SQL or domain docs do not by themselves prove the current PR must support that behavior. Verify PR description, changed routes, integration tests, and author threads before staging a High finding that a role or caller type is "blocked incorrectly".

**Verification methodology**: before **keeping** a finding about a potential runtime failure (duplicate keys, null values, missing constraints), confirm the failure is reachable. Prefer evidence the sub-agent already cited; if missing, one targeted read of the enforcement layer (DB schema, framework validation, upstream guards); not a full re-analysis. If the sub-agent did not cite enforcement-layer evidence and a spot-check is inconclusive, relaunch that agent to verify rather than expanding inline.

**Cache lifecycle verification**: before flagging any cache eviction, fallback, or invalidation as incomplete or missing:
1. Find the TTL calculation for the cache keys in question
2. Identify when the method under review is called (pre-TTL or post-TTL?)
3. If post-TTL: the eviction targets already-expired keys; it is a defensive no-op, not a bug
4. Do not suggest "add DB fallback" for a no-op path without calculating the cost (e.g. N extra DB reads per tick) and confirming the scenario where the fallback would be needed is actually reachable given the lifecycle timing

Before criticizing error-handling strategy (throw vs return-default, fail-open vs fail-closed), trace what the caller does with each outcome. Returning a "safe" default (e.g. `false`) can mask infrastructure failures as normal business conditions; throwing may be intentional to let failures propagate to a handler that can log/alert/retry appropriately.

Before claiming a timing or performance issue (lock TTL too short, timeout too tight, queue overflow), verify what the actual I/O operation does. Read the implementation of the slow-path method rather than assuming its transport (e.g. synchronous HTTP vs MQ enqueue vs in-memory call). Overstated severity based on wrong I/O assumptions undermines review credibility.

If the assumption is structurally impossible, drop the finding.

### 4.3 Confirm Fix Scope
Would the suggested fix require duplicating code? If yes, rewrite as rename or config change.

### 4.4 Evidence-Gated Findings
Performance, scale, and race findings require concrete evidence:
- TOCTOU/race: verify the race window is achievable given actual TTL and operation time. For batch loops under a lock lease, compute: (item count × per-item I/O cost) vs lease duration. If the estimate is well under the lease, downgrade severity and suggest a monitoring metric rather than a code fix.
- Latency/timeout: require measured latency or known gateway limits
- Scalability: state a realistic upper bound for the domain. **Exception:** do not drop a finding solely because current N is small when a loop issues per-item repository/persistence reads over a config, catalog, allowlist, or similar bounded list and a bulk/batch read already exists on the same port or mapper. Flag as missing batch use (`quality#catalog-loop-n-plus-one`); severity may stay Low when N is small today.
- Suggested fix cost: when proposing "add fallback" or "add guard", state the cost (extra I/O per call, lock contention, memory) and confirm the failure scenario being guarded against is reachable given the lifecycle. A "fix" that adds N DB reads per tick for a scenario that cannot occur is worse than the "problem".

Drop findings where the impact is negligible even if technically correct (e.g. a log line might be off by 1 second, a counter might briefly disagree with another counter). Review comments should surface risks that affect users, correctness, or operability, not theoretical imprecisions with no practical consequence.

### 4.5 Dedup Against Existing Comments and Own Findings
Use `github-pr-workflow` existing-review-comments primitive. Drop findings already raised.

Also dedup within your own findings before posting. If two findings describe the same underlying problem (even from different perspectives, e.g. a concurrency agent and a premortem), keep only the one with the clearest explanation and strongest fix suggestion. Never post two comments that a reader would perceive as "the same point said differently".

**Tiered ownership:** when deduping, apply lead-agent rules from `review-panel-selection.md`. Ownership affects which agent leads a merge, not silent discard of a different fix at the same site.

**Dependent fixes must be merged into one finding.** When Finding A recommends a structural change that forces a dependent change elsewhere (e.g., removing a default parameter from a constructor requires updating test verify blocks to pass the argument explicitly, otherwise the test fails to compile), the dependent change is not a separate finding; it is part of A's complete fix. Presenting it as a separate Lower-severity finding creates a contradiction: the secondary finding reads as optional/advisory even though A makes it mandatory. Ask: "If the author applies this fix, do any other files break or become incomplete?" If yes, include those changes in the same finding's fix suggestion.

### 4.6 PR Chain Awareness
Check whether missing logic/tests exist in a downstream PR in the chain. If yes, drop.

To check: fetch the list of open PRs targeting the base branch of the PR under review and scan their diffs for the expected code. Do this before flagging any missing test or missing follow-up logic.

### 4.7 Cross-File Findings
When a finding's evidence is in a file that IS in the diff but the recommended fix belongs in a different file that is NOT in the diff (for example: application-layer validation with no DB constraint backup), post the comment on the file where the evidence is visible. Do not drop the finding just because the fix target file is absent from the diff.

### 4.8 Tone Check
- Always use suggestion tone, never directive/ordering tone. This applies to all comments regardless of severity, including comment **titles and headings** (bold text at the start of a comment). Severity controls whether the review requests changes or approves with comments, not the tone of individual comments. Use phrases like "Please consider ...", "we could", "we should", "one option might be", "what about", or a direct question ("could you add X?") instead of direct orders ("Drop line 68", "Remove X", "Add Y"). Avoid bare imperatives even in chat summaries to the reviewer when describing staged findings; the staging **Comment** text and any paraphrase shown in conversation should use the same mild suggestion tone. Avoid "Consider doing X" as well: although it sounds soft, it still reads as an instruction that the reader is expected to comply with. Bad title: "Dead branch: both paths are identical". Good title: "This conditional could probably be simplified". Bad body: "Wrap the post-send steps in try/finally", "Drop line 68 from the README". Good body: "We should probably wrap the post-send steps in try/finally here", "Please consider dropping line 68 from the README. What do you think?"
- No em dashes (the U+2014 character) anywhere in comment text. Use commas, semicolons, colons, or parentheses instead. Scan every comment body for U+2014 before posting and replace any occurrence.
- Use globish: plain, short words a non-native speaker can follow.
- When suggesting integration-test changes, say what happens in plain steps, not Maven jargon alone. Bad: "gate ITs off the default test run". Good: "do not run these tests in normal `mvn test`; run them only when someone starts RocketMQ first" or "start RocketMQ automatically in the test (Testcontainers)".
- When a fix changes one token, say so explicitly.
- Spell out abbreviations; do not use jargon shortcuts (write "IllegalStateException", not "ISE").
- When the staged review uses three or more non-trivial abbreviations or domain terms (for example RBAC, JWT, DLT, TOCTOU, API key, operator, tenant), add a short `## Terms` section before `## Findings`. Define each term in plain language so the staging document and any posted comment can stand alone for a reviewer who is not deep in the local vocabulary.

### 4.9 Verify Line Numbers
Before posting, confirm two things for each comment's `line` value:

1. The line matches the actual line in the HEAD commit (use `grep -n` or `view` on the target file).
2. The line falls within one of the diff hunks for that file. GitHub's `POST /pulls/{n}/reviews` endpoint rejects comments on lines outside the diff with `"Line could not be resolved"`. Reviewable lines are the added or context lines shown in the unified diff hunks; anything else cannot be commented on inline.

To extract the reviewable line range per file:
```bash
gh pr diff <PR> --repo <owner/repo> | awk '
/^diff --git/{file=$0; sub(/.*b\//,"",file)}
/^@@/{
  match($0, /\+[0-9]+,[0-9]+/);
  hunk=substr($0, RSTART+1, RLENGTH-1);
  split(hunk, parts, ",");
  start=parts[1]; len=parts[2];
  printf "%s\t%d-%d\n", file, start, start+len-1
}'
```

If the line you want is outside every hunk, either retarget to the closest hunk-internal line that still anchors the finding, or drop the inline comment in favor of posting on a different file/line that IS in the diff. A whole batch of comments fails atomically if any one line is unresolvable, so verify all of them before posting.

### 4.9.0 Severity defaults

**Canonical rules:** `review-agents/severity-calibration.md` (tier definitions, decision procedure, category defaults, cc-thingz mapping). Sub-agents must set explicit severity on every finding; orchestrator treats missing severity as **Low** until verified.

Orchestrator-specific additions (not duplicated in severity-calibration):

- **Metrics / observability asks are Low by default.** Promote per severity-calibration table; promote to High essentially never.

**Metrics findings: inline placement.** When recommending new counters or Grafana alert wiring on a PR:
- Post **new counter** proposals inline at the code path where the counter would be incremented (emit site), not only in the PR review summary.
- Post **Grafana alert / panel** recommendations inline at the **existing** metric increment call site (for example `incrementDuplicateBlocked`), so the author can wire the alert to the metric already emitted there.
- Findings about telemetry in code **outside the PR diff** (for example an error counter in a class the PR does not touch): post **once in the PR review body**, not as inline comments that fail line resolution.

**Test asks are Low by default** (see severity-calibration); Medium only when the untested path prevents a real failure mode the team relies on.

**Documentation/inline-comment asks are Low**, regardless of doc length or topic.

**Feature-flag gating does not reduce severity** (severity-calibration).

**Pre-existing pattern does not reduce severity of newly introduced issues** (severity-calibration; §4.11 NEW vs EXISTING).

**Actionable fix comments should include a code snippet.** When a finding proposes something the author can apply in code immediately (not an open question, scope-confirmation ask, or optional doc-only note), include a concrete before/after or "could look like" snippet in the Comment body so the author can act without a follow-up chat. In finding bodies, prefer inline backtick spans for short snippets and keep any fenced snippet free of heading-like lines (lines starting with `#`); `review-staging` is the format gold source. Single-token fixes ("rename to X") and prose-only doc edits are exempt. Staging doc Comment sections follow the same rule. Applies at **all severities**, including Low test-gap and config findings.

When a finding presents multiple actionable fix options, include a concrete example for each option, such as one implementation snippet per alternative and a separate regression-test snippet when a test is part of the recommendation. Keep the surrounding explanation concise so the examples carry the detail.

**Test and review-comment snippets:** In suggested test bodies, assert against values already held in a fixture or builder variable (for example `outbox.getCampaignId()`), not a second copy of the same literal. Duplicated literals in setup and asserts can both pass when the mapping is wrong.

### 4.9.1 No References To Gitignored Local Docs In Posted Comments
Posted PR comments are public and must not cite documents that do not exist on the PR's base branch. The author and external reviewers cannot read them, and citing them either looks like a broken reference or projects private rules onto someone else's code.

Before posting each comment, scan the body for references to any of the following and rewrite or drop:
- Project-local instruction files that are gitignored in this repo: `CLAUDE.md`, `AGENTS.md`, `.ai-playbook/facts.md`, `docs/project-guidelines.md`, `docs/company-guidelines.md`, `docs/glossary.md`, and post-migration equivalents under `docs/maintenance/` (`project-guidelines.md`, `company-guidelines.md`, `glossary.md`)
- User-level instruction files: anything under `~/.claude/`, `~/.codex/`, `~/.agents/`
- Cross-project shared docs that are gitignored on the target repo: files under `shared_docs_dir` in `~/.ai-playbook/facts.md` (e.g. `coding_guidelines.md`, `jvm_guidelines.md`, `kotlin_guidelines.md`, `python_guidelines.md`, `agent_workflow_guidelines.md`), company ownership docs under `company_projects_root/.ai-playbook/` (see `~/.ai-playbook/facts.md`; `facts.md`, `dictionary.md`, `company-guidelines.md`)

Quick scan command before posting (read `REVIEWS_DIR` from `.ai-playbook/facts.md` TOML per `using-skills` Step 0 first; use the exact staging path from the review session when known, otherwise resolve exactly one `${REVIEWS_DIR}/*-PR-<N>-*.md`):
```bash
STAGING="${STAGING:-$(ls -1 "${REVIEWS_DIR}"/*-PR-<N>-*.md 2>/dev/null | head -1)}"
awk '/^#### Comment/{p=1;next} /^#### Analysis/{p=0} p' "$STAGING" | \
  grep -nE "project-guidelines|company-guidelines|docs/maintenance/|docs/glossary|\.ai-playbook/facts|coding_guidelines|jvm_guidelines|kotlin_guidelines|python_guidelines|CLAUDE\.md|AGENTS\.md|agent_workflow_guidelines|shared_docs_dir|~/\.claude|~/\.codex|~/\.agents"
```

Rewrite rules:
- If the citation is the source of an objective rule the PR author would also recognize (project method-length limit, metrics convention, naming convention), restate the principle inline without citing the file. Example: `"see company-guidelines.md #17 (≤30 lines)"` → `"this is hard to scan and exceeds typical method-length limits"`.
- **Company engineering rules (public cite):** When a finding rests on employer/company guidelines that are not OpenAPI, README, or other PR-visible docs, do not use the **What the contract or docs say** heading; company guidelines are not API contracts. Use **As per company guidelines** and link the public guidelines URL resolved from facts (`company_guidelines_public_url` or equivalent), with the rule number (for example `https://github.com/example-org/example-guidelines-repo/blob/main/company-guidelines.md` #13 for no PII in logs). **Before posting, verify the cited rule exists** at that URL (fetch or read the linked file; confirm the numbered rule or quoted text is present). Do not cite local `company_guidelines_master` paths, gitignored repo mirrors, or org-specific internal path segments. If the rule is not publicly available or cannot be verified, do not present it as a guideline mandate: rephrase as a suggestion in mild tone and ground it in common engineering practice or widely accepted best practices (for example "we could avoid logging operator-entered field values in validation failures").
- If the citation is the only justification for the finding (i.e. the rule lives only in your private docs), drop the finding entirely. Personal style preferences from user-level instructions are not project conventions the PR author has agreed to follow. Em-dash bans, no-also-chain rules, specific log-format preferences, and similar are common examples. The right place for these is the gitignored doc itself, not a public PR comment.

If a rule should be enforced project-wide, propose it first as a PR to the shared project doc (where the author can agree or push back), then cite it in future reviews. Do not retroactively flag PRs against rules that exist only in your private instructions.

Analysis sections of the staging doc may reference any local doc freely; they are internal scratch and never posted.

### 4.9.2 Doc Findings: Scope By Whether The Doc Is In The Diff
A doc file's status governs whether to comment on it in the PR.

**Doc is in the PR's changed files (tracked, modified by the PR):**
Treat it like any other reviewable artifact. Wording accuracy, doc/code consistency, missing provenance on claims that drive downstream work (migrations, capacity decisions), and structural issues are all fair PR comments. The author opened the doc for review by including it in the diff.

**Doc is NOT in the PR's changed files:**
Do not comment on it in the PR, even if you noticed an issue while reviewing. The author has not opened that doc for review.
- If the doc is tracked and lives elsewhere in the repo, fix it in a separate PR or hand off to the doc owner; do not raise it on this PR.
- If the doc is gitignored (a local instruction file, a personal review/scratch doc, a shadow-branch doc), fix it in place and commit to the orphan docs branch (or your local docs preservation workflow). Never reference gitignored docs in posted PR comments (see § 4.9.1).

**Personal style preferences are never a PR comment, regardless of doc status.**
Rules that exist only in your private instructions (em-dash bans, no-also-chain preferences, specific log-format styles) are not project conventions the PR author has agreed to. Drop those findings even when the doc is in the diff. If the rule should be enforced project-wide, propose it as a PR to the shared style doc first, then cite it in future reviews.

**Quick gate**: before posting any doc finding, run:
```bash
gh pr diff <PR> --name-only | grep -Fx "<doc-path>"
```
If the doc is in the output, the finding is in scope. If not, drop or move to a separate PR.

**Local fixes for dropped doc issues**: when you drop a doc finding because the doc is not in the diff but it lives in a local/gitignored location you maintain, fix it in place and commit to your local docs branch in the same session. Do not leave the issue noted only in the staging doc's "Reason for drop" line; the staging doc is ephemeral.

**PR template placeholder text is not a defect.** PR templates have two kinds of fields:
- **Machine-readable** (checkboxes like `[N]`/`[Y]`, structured metadata like `isRestartRequired: true`). These ARE legitimate findings when missing or wrong, because CI gates on them.
- **Human-prose placeholders** (text like `[Provide a brief summary...]`, `[Add any additional notes...]`). These have default placeholder values; the author is not required to replace them. CI does not gate on prose presence. Do not flag unfilled prose placeholders. The Jira ticket carries the context, and the diff itself is the canonical record of what changed.

Only flag PR-body issues when a CI-gated machine-readable field is missing or wrong (see `agent_workflow_guidelines.md #33` for examples like the `isRestartRequired` metadata in the config repo).

**Stale PR summary prose is not a formal finding by default.** When the PR description disagrees with head code because the author intentionally changed scope (evident from fix commits and updated branch docs) and a human reviewer already approved, do not raise a Medium/Low review comment asking to update the PR body. Drop it or note it in staging Analysis only. Raise it only if the mismatch could mislead merge without approval or runtime behavior is still wrong.

### 4.9.3 Staging doc anchor edits

When correcting `- **File**:` or `- **Line**:` in the staging doc during polish, follow `review-staging` field shape (separate list items for File and Line) and verify values against PR head per §4.9.

### 4.10 Empirical Verification of Test/Compile Claims
Before posting a finding that claims tests will fail, code will not compile, or runtime errors will occur, attempt to verify by actually running the build or tests locally. If the local environment cannot run the build (missing dependencies, VPN, etc.), state explicitly in the comment that the claim is based on static analysis and has not been empirically verified. Never present an unverified inference as a confirmed fact.

### 4.11 NEW vs EXISTING Debt (All Findings)

When reporting issues that involve file/module size or structural concerns (god classes, large functions, layer violations), distinguish between:

- **NEW issues**: Introduced by this PR (new files, new functions, significant structural changes); report at full severity
- **EXISTING debt**: Pre-existing problems this PR only contributed to (adding lines to already-large files); downgrade to Low or omit

**Rationale:** A PR should not be punished for technical debt that existed before it started. Only report EXISTING debt when the PR significantly compounds the problem.

**How to detect:**
- Use `git diff <base>...<head> --name-status` to identify new (A) vs modified (M) files
- Use `git show <base>:<file>` to check if a function/structure existed before
- If adding lines to an already-large function: EXISTING debt contribution
- If creating a new large function: NEW issue

This applies to all sub-agents, but is most relevant for architectural findings (god classes, layer violations) and simplification findings (over-engineering).

### 4.12 Finding Explanation Depth (Comment and Analysis)

The staging doc has two audiences:
- **Comment**: read by the PR/branch author (and posted to GitHub when approved). It must stand alone: the author should understand the issue, why it matters, and what to do **without** asking for a follow-up explanation.
- **Analysis**: internal scratch for the reviewer; never posted. Holds verification steps, severity rationale, alternatives, and dropped counterarguments.

**Posted Comment surface (no process metacomments):** Keep `#### Comment` about the code, contract, or behavior under review. Do **not** put reviewer-process chatter in Comment text that will post to the PR: follow-up ticket IDs created outside this PR, cross-references to other finding IDs (`F4`, `F5`), "when ticket X lands", joint ownership/config asides, or "see F4 for userId". Those belong in `#### Analysis` or Metadata only.

**Narrow triage edits:** When the user asks to change a staged finding in a specific way (for example "only ask for a PII comment"), apply that scope only. Do not expand the Comment into adjacent asks (Javadoc on unrelated fields, bundled naming rationale, extra soft asks) unless the user also requested those.

**Do not trade clarity for brevity on Medium+ findings.** A one-sentence Comment that only names the mismatch (for example "OpenAPI overstates the guarantee") is insufficient.

#### Comment depth by severity

| Severity | Comment minimum |
|----------|-----------------|
| **Critical / High** | All Medium sections below, plus **user/runtime impact** (who is affected, worst case in normal or enabled traffic) and **urgency** (why this should block merge) |
| **Medium** | Four sections (use `**Bold headings**` or short titled paragraphs): **What the contract or docs say** (quote or paraphrase the normative text); **What the code does** (actual behavior, guards, transaction/isolation notes); **Why this matters** (severity rationale: not a happy-path bug vs contract drift vs missing test for a real failure mode); **What we could do** (one or two fix options in suggestion tone, with tradeoffs when non-obvious) |
| **Low** | At least: the claim, one sentence of evidence (file/method/behavior), and a fix or "optional cleanup" suggestion. No four-section template required. |

**Contract-vs-implementation findings** (OpenAPI, README, ADR, api-reference mismatches): the Comment must show **both sides** explicitly. Quote or restate the contract line, then describe implementation behavior and the gap. Do not assume the author remembers an earlier review thread.

**Concurrency / race findings**: the Comment must state isolation level (for example READ COMMITTED), the race window (what can happen between read A and write B), and usual vs edge outcome (for example "usually 409, rare 200 with persisted rows").

**Test-gap findings**: state what the test currently proves, what it does **not** prove, and why that gap matters (only promote to Medium when the untested path has a real failure mode).

#### Analysis depth (all severities; richer for Medium+)

Analysis should answer:
1. **What was checked**: files read, grep/schema queries, tests run or not run
2. **Why this severity**: tie to §4.9.0 defaults; say if downgraded from an agent's initial severity and why
3. **Alternatives considered**: other fix options, or why "document as accepted MVP race" vs "add row lock"
4. **Why not higher/lower**: one line on what would change the severity
5. **Related findings**: dedup notes, prior review IDs, intentional decisions (for example r1 fix that explains `now()` vs `RETURNING`)

#### Sub-agent `body` depth (required at collection time)

Sub-agents must return `body` text that already satisfies the Comment depth table above. The orchestrator should not be the primary author of finding detail.

| Severity | Sub-agent `body` minimum |
|----------|--------------------------|
| **Critical / High** | All Medium sections below, plus user/runtime impact and urgency |
| **Medium** | Four sections with `**Bold headings**`: What the contract/docs say; What the code does; Why this matters; What we could do |
| **Low** | Claim, one sentence of evidence, fix or optional-cleanup suggestion |

Include verification notes (files read, schema checks, severity rationale, alternatives) in the same `body` under an `**Analysis**` heading when useful; the orchestrator moves that block to the staging doc's Analysis section.

#### Orchestrator polish pass (mandatory before staging doc is final)

After dedup in §4.5, for every finding (all severities):
1. Confirm the sub-agent `body` satisfies §4.12 Comment depth for its severity. If thin, **relaunch the responsible sub-agent** to expand; do not re-read sources in the orchestrator to fill gaps (recovery path only when relaunch is impractical).
2. If the finding proposes an actionable code/test/config fix, confirm the Comment includes a concrete snippet per §4.9.0. If missing, relaunch the responsible sub-agent with "expand finding N with §4.9.0 snippet" or add the snippet during staging polish (recovery only when relaunch is impractical).
3. Apply tone check (§4.8), assumption verification (§4.2–4.4) using cited evidence, and line-number verification (§4.9), including staging `- **Line**:` / `- **File**:` per §4.9.3 when needed.
4. Split `body` into staging **Comment** and **Analysis** sections; refine wording but preserve substance; do not shorten a detailed agent `body` for brevity.

**Self-check before marking staging doc complete:** For each finding with an actionable fix, ask: "Could the author apply this without a follow-up chat?" If no, the Comment is missing a §4.9.0 snippet or sufficient detail; relaunch or expand. For Medium+ findings, also confirm §4.12 section depth.

**Mechanical gate:** run `python3 "${REVIEW_STAGING_VALIDATOR:-$HOME/.ai-playbook/scripts/validate_review_staging.py}" --hard "<staging-path>"` before reporting findings to the user. Fix validation errors before the round is complete.

**Contract section gate:** Before using **What the contract says**, name the normative source and confirm it is in the PR diff (for example `app/api/openapi.yaml` response text, a README section the PR edits, a schema or test the PR adds). If the normative source is company engineering guidelines, use **As per company guidelines** with a verified public company-playbook URL and rule number (see §4.9.1), not **What the contract or docs say**. If the rule cannot be verified at a public URL, use suggestion tone and common best practices instead of a guideline citation. If the only source is a gitignored instruction file or private guideline without a public mirror, drop the finding or reframe the opening section as **What this PR establishes** (in-PR design, tests, or persistence the change itself introduces). Do not suggest relaxing or rewriting that source as the fix when the cited "contract" was never PR-visible.

#### Comment example (Medium, contract drift)

```markdown
**What the contract says**
The `409` response for `PATCH /v1/consent-updates` says consent updates are "rejected before any write". That reads as a hard guarantee: `DELETED` profile, no consent or suppression rows persisted.

**What the code does**
`ConsentController` pre-checks `DELETED`, then `ExternalConsentUpdateOrchestrator` re-reads profile status inside `@Transactional` via plain `findProfile` (no row lock). Under READ COMMITTED, a concurrent soft-delete after that re-read can still allow batch writes while the usual path returns `409` / `PROFILE_DELETED`.

**Why this matters**
This is contract drift, not a typical happy-path logic bug. OpenAPI readers expect strict `409`; api-reference §8b documents the race as an accepted MVP limitation. Integrators or codegen clients may assume behavior the runtime does not fully guarantee.

**What we could do**
One option: soften the OpenAPI `409` description to match api-reference (document the READ COMMITTED race). Another: tighten with row lock before the first mutating statement, for example `ProfileRow profile = profileRepository.findByIdForUpdate(profileId);` then `if (profile.getStatus() == ProfileStatus.DELETED) { throw new ProfileDeletedException(profileId); }`.
```

#### Comment example (Low, test gap with snippet)

```markdown
`shouldPublish` only asserts no-throw. We could pull the published message and assert fields from the fixture, for example `MessageExt received = pullMessageByKey(outbox.getDedupeKey());` then `JsonNode json = objectMapper.readTree(received.getBody());` and `assertThat(json.get("campaignId").asText()).isEqualTo(outbox.getCampaignId());`. Use getters from `outbox`, not duplicated literals in asserts.
```

#### Analysis example (same finding)

```markdown
Read `openapi.yaml` line 261, `ExternalConsentUpdateOrchestrator.java`, api-reference §8b edge-case table. Verified no `FOR UPDATE` in profile module. Severity Medium per §4.9.0: documented edge-case correctness gap between normative OpenAPI and implemented/documented behavior; not data loss in normal sequential traffic. Downgraded from agent High: narrow window, FK still valid on DELETED row. Intentional r2 doc fix already softened Javadoc; OpenAPI not updated yet. Alternatives: nullable/error-code change not needed; this is wording vs locking choice.
```

## Step 5: Output

**ALWAYS write the staging document**, regardless of mode. The staging doc is the primary deliverable and serves as both approval artifact (for PRs) and persistent record (for all reviews). Include `## Review Statistics` on every review (including zero-finding rounds) per `review-staging`.

### Step 5.1: High-level tasks follow-up (module-split repos)

After the staging doc is written, scan **Medium+** findings (and any accepted Low that describes implementation vs doc/contract drift) for gaps between **current code** and what module docs imply.

When a finding fits, update the module high-level tasks doc in the review session (or tell the user which task block to extend if the review is read-only). Resolve paths from `{guidelines_path}` / project guidelines; do not assume legacy `docs/<module>/` layout on migration-complete repos.

| Module (example) | Legacy path | Post-migration |
|------------------|-------------|----------------|
| Module A | `docs/<module>/<service>-high-level-tasks.md` | path named in project guidelines |
| Module B | `docs/<module>/<service>-high-level-tasks.md` | path named in project guidelines |

Record **tech debt** (document limitation, MVP doc fix, defer code) or **implementation fix** (named target task, tests expected). Do not rely on gitignored `{reviews_dir}/` as the only backlog.

Cross-repo: same pattern when a repo maintains module high-level tasks docs (path from project guidelines).

**File location** (create `{reviews_dir}/` if it doesn't exist):
- For GitHub PR reviews: `{reviews_dir}/YYYY-MM-DD-PR-<number>-<title>.md`
- For local branch reviews: `{reviews_dir}/YYYY-MM-DD-branch-review-<branch_name>.md` (add `-r<N>` when part of a review-loop)
- For pre-implementation plan reviews (`review-plan`): `{reviews_dir}/YYYY-MM-DD-plan-review-<plan_name>-r<N>.md`
- For execute-plan Phase 3 post-implementation code reviews: `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` (not `-plan-review-r`)

Branch names are sanitized: slashes replaced with dashes, max 30 chars. No prefix (REVIEW/PR) needed since the directory already indicates these are reviews.

### Staged Mode (default)

Write all findings to the staging document instead of posting directly. This allows the reviewer to inspect, edit, or drop findings before they reach the PR author.

**Document format** (hierarchy and `## Review Statistics` per `review-staging`; code-review severities and optional `Status` below):

```markdown
# Code Review: <PR #<number>; <title> OR Branch <head> → <base>>

## Metadata
- Type: PR Review / Branch Review
- Date: YYYY-MM-DD
- PR: <url> (if PR review)
- Branch: <head> → <base> (if branch review, include plan reference if applicable)
- Findings: <staged count>
- Status: STAGED (not yet posted)

## Review Statistics

### Panel
| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| correctness-completeness | quality, implementation | none | complete | 2 | 1 | 1 | no |
| risk | security | none | complete | 0 | 0 | 0 | no |

### Counts
- Workers launched: 5
- Workers skipped: 0
- Raw findings (all workers): 5
- Staged findings: 3
- Discarded during synthesis: 2
- Solo staged (unique agent origin): 1
- Echo staged (multi-agent dedup): 2

### Deduplication groups
| Staged # | Workers | Lenses | Theme |
|----------|---------|--------|-------|
| 1 | correctness-completeness | quality, implementation | Null guard missing on batch path |

When none: `None (each staged finding had a single agent origin).`

### Discarded findings
| Worker | Worker severity | Pattern | Theme | Reason | Notes |
|--------|-----------------|---------|-------|--------|-------|
| documentation | Low | documentation#prose-verbose-comment | Rename variable | noise | Optional cleanup only |

When none: `None.`

### Severity calibration
| Staged # | Worker | Lens | Worker severity | Staged severity | Delta |
|----------|--------|------|-----------------|-----------------|-------|
| 2 | correctness-completeness | quality | Low | Medium | upgraded |

When none: `None (agent severities matched staged severities).`

### Triage outcomes
| Worker | Staged | Fixed | Dropped | Deferred | Pending |
|--------|--------|-------|---------|----------|---------|
| correctness-completeness | 2 | 0 | 0 | 0 | 2 |

Before triage: Pending = Staged for each agent; Fixed/Dropped/Deferred = 0. After `receiving-review`: recompute from finding **Triage** fields.

## Findings

### Critical

None.

### High

#### F1. <short title>
- **Severity**: High | Medium | Low
- **Blocking**: true | false
- **Consequence**: <tangible outcome>
- **Reachability**: expected | common | plausible-edge | theoretical
- **Blast radius**: global | multi-service | single-service | local
- **Confidence**: verified | strong-evidence | hypothesis
- **Worker severity**: Low *(omit when equal to Severity)*
- **Pattern**: quality#null-handling
- **Workers**: correctness-completeness, risk
- **Status**: `pending`
- **Triage**: pending
- **File**: path/to/File.kt
- **Line**: 115

#### Comment (posted as-is when approved)

<self-contained explanation per §4.12. Medium+: What contract/docs say → What code does → Why this matters → What we could do. Low: claim + evidence + suggestion.>

#### Analysis (not posted; reviewer context only)

<per §4.12 Analysis depth: what was checked, severity rationale, alternatives, dedup/prior-review notes>

---

### Medium

None.

### Low

None.

### Overflow manifest
| Worker | Pattern | Anchor | Severity | Confidence | Consequence |
|--------|---------|--------|----------|------------|-------------|
```

Do not include `Side` in staging documents; it is always `RIGHT` for GitHub inline comments and adds noise for branch-only reviews. When posting approved findings to a PR, set `side: RIGHT` in the API payload only (not in the markdown staging file).

**Status values** (user or triage skill edits these):
- `pending`: not yet triaged or still open after triage
- `done`: fixed in code; maps to **Triage** `fixed`
- `drop`: rejected; maps to **Triage** `dropped`
- `deferred`: valid but intentionally deferred; maps to **Triage** `deferred`
- `post`: approved for PR comment (PR staged mode)
- `edit`: user modified Comment before post (PR staged mode)

After triage, update `## Review Statistics` → **Triage outcomes** and each finding's **Triage** per `review-staging`. Update the required `.stats.json` sidecar alongside the staging doc.

**Triage presentation freeze** (see `review-agents/severity-calibration.md` § Ordering): do not reshuffle Findings by blocking, blast radius, reachability, or confidence during triage. Keep ascending finding-ID order within each severity section. When a finding's severity changes, move only that block into the matching `###` section.

**After writing the staging doc**, inform the user:

For PR reviews:
> "Staged N findings in {reviews_dir}/YYYY-MM-DD-PR-<number>-<title>.md. Review and mark each status as post/drop/edit, then say 'post comments' when ready."

For branch reviews:
> "Review complete. Findings written to {reviews_dir}/YYYY-MM-DD-branch-review-<branch_name>.md with N findings (H: X, M: Y, L: Z)."

### Posting Staged Findings

When the user says "post comments", "post the review", or "post approved":
1. Read the staging doc from the review session path, or resolve exactly one `{reviews_dir}/*-PR-<number>-*.md`
2. Collect all findings with `status: post` or `status: edit` (or `pending` when the user explicitly approves posting all pending)
3. For each finding, read the `#### Comment` block verbatim; verify `File`/`Line` are in diff hunks (§4.9); post via `github-pr-workflow` as inline comments
4. Update the staging doc: change Status header to `POSTED`, mark posted findings as `posted`, keep dropped findings as `drop`
5. Report which findings were posted and which were dropped

### Direct Mode (skip staging)

When the user explicitly says "post directly", "skip staging", or "review and post":
- Post findings immediately to GitHub (legacy behavior)
- Still write the staging doc as a record with all findings marked as `posted`

**For branch reviews (not GitHub PRs)**: Direct mode is the default behavior since there is no PR to post to. The staging doc is the complete deliverable; always write it with findings marked as `posted`.

For PR reviews, post via `github-pr-workflow`:
```json
{
  "event": "COMMENT",
  "body": "",
  "comments": []
}
```
Populate `comments` with assessed inline finding objects from the staging doc.

For branch reviews, skip the posting step; the staging doc is the complete deliverable. Inform the user where the doc was written.

Each finding must be posted as an **inline comment** at its specific file and line (for PR reviews). Never consolidate multiple findings into a single top-level review body comment (that makes findings hard to locate and resolve).

**Exception; out-of-diff telemetry:** one PR review body comment for findings about code or metrics outside the diff (see §4.9.0 metrics inline placement). Keep all in-diff metrics recommendations inline.

**Exception; multi-key deploy checklists:** when several Low findings describe ordered BO/ops steps across different config keys (for example credentials key + routing key), we may post one PR thread comment with the full ordered checklist and delete the superseded inline comments. Keep code-specific inline comments (naming, missing beans) separate.

If a posted comment is later found to be incorrect, delete it entirely via the GitHub API. Do not update it with a strikethrough retraction; retracted comments add noise to the PR thread.

Post with `event: "COMMENT"` (non-blocking) unless a finding is Critical or High severity with clear production risk.

### Fix Mode

For each confirmed finding:
1. Fix the issue in the source code
2. Run tests and linter to verify
3. Commit: `git commit -m "fix: address code review findings"`
4. Do NOT output a completion signal; another review iteration must verify the fixes

If no issues found in fix mode, signal completion.

## Response Format (per finding)

Staging doc fields (author-facing quality is in **Comment**, not a terse summary):

- Severity: Low / Medium / High / Critical
- File + line (verified per §4.9)
- **Comment**: per §4.12 depth table (Medium+ must include contract/docs, code behavior, why it matters, fix options)
- **Analysis**: verification trail, severity calibration, alternatives (not posted to GitHub)

## Integration Points

### With `review-staging` skill
Staging doc hierarchy and `## Review Statistics` are defined in `review-staging` (Panel with Solo/Echo, Pattern tags, Severity calibration, Triage outcomes). Populate synthesis stats during orchestrator dedup; update Triage outcomes after triage without rewriting synthesis tables.

### With `bootstrap-ai-playbook` skill
Writes and refreshes `.ai-playbook/facts.md` when Terms triggers fire (`using-skills` Step 0). This skill reads `{reviews_dir}` and other doc paths from that file before writing staging docs under `{reviews_dir}/`.

### With `execute-plan` skill
Phase 3: the execute-plan **parent** runs this skill as the review orchestrator and launches lens workers (default). Nested "Code Review" sub-agent only when the parent cannot fan out. Exits after one fresh review of the current digest has zero unresolved blocking findings. Post-fix reviews use blind correctness plus every distinct owning or affected worker.

## Limitations

- In comment mode: read-only for **source code** under review. Staging doc polish is allowed when the user requests it or during orchestrator polish before the doc is final.
- The review deliverable is the staged review document (or posted comments). Do not fix product code, commit changes, or start implementing suggestions after the review is complete unless the user explicitly requests fix mode or a separate fix workflow.
- Before starting, identify PR author. If PR was not created by current user, enforce read-only with no exceptions.
- Respond in English.
