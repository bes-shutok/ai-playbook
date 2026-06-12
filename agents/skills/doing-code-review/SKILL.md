---
name: doing-code-review
description: >
  Active code review skill. Orchestrates 8 parallel CR sub-agents for thorough review of PRs, diffs, or branches. Language-agnostic core with runtime language overlays (Java/Spring, Kotlin/Spring, Python). Two modes: posts PR review comments by default; fix mode (auto-commit) when explicitly asked. Trigger phrases: "let's review", "review this PR", "review the changes", "review changes in", "review branch", "review against", "code review", "look at this PR", "check this PR", "check this diff", "doing-code-review". Do not use for addressing existing reviewer comments; use receiving-code-review instead.
---

# Active Code Review

**Documentation paths:** Resolve `{reviews_dir}` per `_shared/doc-paths.md` before writing staging docs. Examples below use `{reviews_dir}/`; substitute the resolved path.

## Boundary

Use this skill for **active review**: producing new review findings for a PR, diff, or branch.

Do not use this skill for implementing, triaging, or replying to existing review comments. Use `receiving-code-review` for passive review feedback. For GitHub PR operations (fetching metadata, files, diffs, existing comments, posting reviews), use the shared primitives in `github-pr-workflow`.

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

- Launching fewer sub-agents because the user's request seems narrow or focused. The user asked for a review; launch the full agent set unless an explicit skip rule applies.
- Reporting grep results, manual scans, or inline analysis as the review output. Sub-agents provide coverage a single pass cannot; the staging doc is the deliverable.
- Replacing the sub-agent pipeline with a targeted scan because "the user only asked about X." A focused scan cannot find what it was not asked to look for; the full agent set can.

## Step 1: Gather Context

For a GitHub PR URL, use `github-pr-workflow` to resolve owner, repo, PR number, base branch, head branch, changed files, diff, and existing review comments.

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

## Step 3: Launch Sub-Agents in Parallel

Launch all review worker agents **in parallel** using your agent's sub-agent execution capability (parallel launches when supported). Wait for all to complete before proceeding.

Each agent receives:
1. Its own prompt (from the corresponding `.md` file in `~/.agents/skills/review-agents/`)
2. The language overlay content
3. Instructions to run `git diff <base>...<head>` and read source files for full context
4. The base and head branch names
5. Output format: return a JSON array of `{path, line, side, body, severity}` findings — severity is `Low / Medium / High / Critical`. Sub-agent `body` must already meet §4.12 depth for its severity; do not write one-paragraph stubs expecting the orchestrator to expand them.
6. An explicit constraint: "Do not over-investigate or validate every single line number. Read the diff and key source files, then report findings. Write each `body` to full §4.12 depth: quote contract/doc text, name the code path, describe actual behavior, state why it matters, and suggest fix options. For Medium+, include all four Comment sections inline in `body` using `**Bold headings**`."

**Timeout handling:** If a sub-agent has not completed within 10 minutes, launch a replacement with a more focused prompt (limit to first 1500 lines of diff via `| head -1500`, add "read key source files directly" instead of exhaustive investigation). Do not wait indefinitely for stuck agents.

Sub-agents (all files in `~/.agents/skills/review-agents/`):

| Agent file | Focus |
|---|---|
| `quality.md` | Bugs, logic errors, edge cases, error handling, correctness, type safety |
| `implementation.md` | Requirement coverage, correctness of approach, wiring, completeness |
| `testing.md` | Test coverage, quality, fake tests, independence |
| `simplification.md` | Over-engineering, excessive abstraction, premature generalization |
| `architecture.md` | God classes, SOLID, DDD, CQRS, clean architecture, aggregates, value objects, extraction opportunities |
| `documentation.md` | Missing documentation updates for user-visible changes |
| `security.md` | Injection, secrets, input validation, data leakage, auth |
| `concurrency.md` | Race conditions, transactional scope, isolation, locking gaps |
| `premortem.md` | Design-level failure modes, operational risks, architectural blind spots |

Each agent returns a JSON array. Medium+ `body` values must be self-contained (orchestrator splits into Comment/Analysis and polishes tone; it should not need to re-read sources to fill gaps):
```json
[
  {
    "path": "src/File.java",
    "line": 42,
    "side": "RIGHT",
    "body": "**What the contract says**\nThe OpenAPI `409` response says updates are rejected before any write.\n\n**What the code does**\n`ConsentController` pre-checks status, then the orchestrator re-reads inside `@Transactional` with no row lock. Under READ COMMITTED, a concurrent delete after the re-read can still allow writes.\n\n**Why this matters**\nContract drift: integrators expect strict `409`; the race is documented elsewhere but not in OpenAPI.\n\n**What we could do**\nSoften the OpenAPI description to match runtime behavior, or add `SELECT … FOR UPDATE` before the first mutating statement.",
    "severity": "Medium"
  }
]
```

The premortem agent maps its output: Block → severity High; Mitigate → severity Medium; Monitor/Accept → dropped (not actionable in a code review).

**Skip premortem when** the diff is purely mechanical (renames, formatting, dependency bumps) or total changed lines < 20.

Report problems only. No positive observations.

## Orchestrator Boundary

The orchestrator **coordinates** sub-agents; it does **not** re-do their analysis. Keep orchestrator context lean: collect agent JSON, dedup, spot-check, format the staging doc — do not re-read diffs or source files to author finding detail that belongs in sub-agent `body`.

| Do | Do not |
|----|--------|
| Launch agents, wait, parse JSON returns | Re-analyze the diff inline while agents run |
| Dedup, tone-check, verify line numbers, drop invalid findings | Re-read sources to expand thin `body` text (relaunch the agent instead) |
| Spot-check a claim only when the agent's stated evidence is missing or contradicts a quick grep | Re-derive full contract-vs-code analysis the agent should have returned |
| Write staging doc from agent payloads + §4.12 polish | Copy full agent JSON into orchestrator chat when paths/counts suffice |

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
- Self-documenting code flagged for missing docs
- A cache operation that is a defensive no-op (keys already expired by TTL at call time) flagged as "incomplete" or "broken"

**Verification methodology**: before **keeping** a finding about a potential runtime failure (duplicate keys, null values, missing constraints), confirm the failure is reachable. Prefer evidence the sub-agent already cited; if missing, one targeted read of the enforcement layer (DB schema, framework validation, upstream guards) — not a full re-analysis. If the sub-agent did not cite enforcement-layer evidence and a spot-check is inconclusive, relaunch that agent to verify rather than expanding inline.

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
- Scalability: state a realistic upper bound for the domain
- Suggested fix cost: when proposing "add fallback" or "add guard", state the cost (extra I/O per call, lock contention, memory) and confirm the failure scenario being guarded against is reachable given the lifecycle. A "fix" that adds N DB reads per tick for a scenario that cannot occur is worse than the "problem".

Drop findings where the impact is negligible even if technically correct (e.g. a log line might be off by 1 second, a counter might briefly disagree with another counter). Review comments should surface risks that affect users, correctness, or operability, not theoretical imprecisions with no practical consequence.

### 4.5 Dedup Against Existing Comments and Own Findings
Use `github-pr-workflow` existing-review-comments primitive. Drop findings already raised.

Also dedup within your own findings before posting. If two findings describe the same underlying problem (even from different perspectives, e.g. a concurrency agent and a premortem), keep only the one with the clearest explanation and strongest fix suggestion. Never post two comments that a reader would perceive as "the same point said differently".

**Dependent fixes must be merged into one finding.** When Finding A recommends a structural change that forces a dependent change elsewhere (e.g., removing a default parameter from a constructor requires updating test verify blocks to pass the argument explicitly, otherwise the test fails to compile), the dependent change is not a separate finding — it is part of A's complete fix. Presenting it as a separate Lower-severity finding creates a contradiction: the secondary finding reads as optional/advisory even though A makes it mandatory. Ask: "If the author applies this fix, do any other files break or become incomplete?" If yes, include those changes in the same finding's fix suggestion.

### 4.6 PR Chain Awareness
Check whether missing logic/tests exist in a downstream PR in the chain. If yes, drop.

To check: fetch the list of open PRs targeting the base branch of the PR under review and scan their diffs for the expected code. Do this before flagging any missing test or missing follow-up logic.

### 4.7 Cross-File Findings
When a finding's evidence is in a file that IS in the diff but the recommended fix belongs in a different file that is NOT in the diff (for example: application-layer validation with no DB constraint backup), post the comment on the file where the evidence is visible. Do not drop the finding just because the fix target file is absent from the diff.

### 4.8 Tone Check
- Always use suggestion tone, never directive/ordering tone. This applies to all comments regardless of severity, including comment **titles and headings** (bold text at the start of a comment). Severity controls whether the review requests changes or approves with comments, not the tone of individual comments. Use phrases like "we could", "we should", "one option might be", "what about", or a direct question ("could you add X?") instead of direct orders. Avoid "Consider doing X" as well: although it sounds soft, it still reads as an instruction that the reader is expected to comply with. Bad title: "Dead branch: both paths are identical". Good title: "This conditional could probably be simplified". Bad body: "Wrap the post-send steps in try/finally", "Consider wrapping the post-send steps in try/finally". Good body: "We should probably wrap the post-send steps in try/finally here", "One option: wrapping post-send in try/finally. What do you think?"
- No em dashes (the "—" character) anywhere in comment text. Use commas, semicolons, colons, or parentheses instead. Scan every comment body for "—" before posting and replace any occurrence.
- Use globish: plain, short words a non-native speaker can follow.
- When a fix changes one token, say so explicitly.
- Spell out abbreviations; do not use jargon shortcuts (write "IllegalStateException", not "ISE").

### 4.9 Verify Line Numbers
Before posting, confirm two things for each comment's `line` value:

1. The line matches the actual line in the HEAD commit (use `grep -n` or `view` on the target file).
2. The line falls within one of the diff hunks for that file. GitHub's `POST /pulls/{n}/reviews` endpoint rejects comments on lines outside the diff with `"Line could not be resolved"`. Reviewable lines are the added or context lines shown in the unified diff hunks — anything else cannot be commented on inline.

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

### 4.9.0 Severity Defaults
Severity reflects user impact and operability risk, not how thorough the comment is. Common defaults:

- **High**: data loss, security exposure, or wrong-result bug reachable in normal traffic.
- **Medium**: behavior regression in normal traffic, correctness gap in a documented edge case, missing test for a code path that itself has a real failure mode.
- **Low**: style/readability, naming, log-level mismatch, dead code, comment-only fix, observability gap where the underlying behavior is correct.

**Metrics / observability asks are Low by default.** A missing counter for a drop path is an observability gap, not a defect: the drop itself is correct behavior, dashboards just can't see it. Promote to Medium only when the missing telemetry would mask an active production problem (e.g. the drop path is on a hot user-visible flow, or it competes with an alert that already exists at a different level). Promote to High essentially never.

**Test asks are Low by default**, with one exception: Medium if the untested code path itself contains a real failure mode the team relies on (e.g. a per-step catch that bounds failure blast radius). "There's no test for X" alone is Low; "there's no test for X, and X is the only thing preventing Y" is Medium.

**Documentation/inline-comment asks are Low**, regardless of doc length or topic.

**Feature-flag gating does not reduce severity.** A bug that causes silent data loss or complete feature outage is High regardless of whether it is guarded by a feature flag. The flag only controls when the bug is reachable; once enabled, the full impact applies. Do not list "gated by a flag" as a mitigating factor when calibrating severity.

**Pre-existing pattern does not reduce severity of newly introduced issues.** If a PR introduces code that follows the same broken pattern as pre-existing code elsewhere, the new instance is a NEW issue at full severity. The pre-existing instance is EXISTING debt (note briefly at Low or omit). Do not conflate "consistent with existing behavior" with "acceptable new behavior".

**Non-trivial fix suggestions must include a code snippet.** When the recommended fix involves a structural change (parsing to an enum, adding a validation guard, restructuring a method), include a concrete before/after or "could look like" code snippet in the comment body. Single-token fixes ("rename to X") do not need a snippet.

### 4.9.1 No References To Gitignored Local Docs In Posted Comments
Posted PR comments are public and must not cite documents that do not exist on the PR's base branch. The author and external reviewers cannot read them, and citing them either looks like a broken reference or projects private rules onto someone else's code.

Before posting each comment, scan the body for references to any of the following and rewrite or drop:
- Project-local instruction files that are gitignored in this repo: `CLAUDE.md`, `AGENTS.md`, `docs/project-guidelines.md`, `docs/company-guidelines.md`, `docs/glossary.md`, `docs/facts.md`, and post-migration equivalents under `docs/maintenance/` (`project-guidelines.md`, `company-guidelines.md`, `glossary.md`, `facts.md`)
- User-level instruction files: anything under `~/.claude/`, `~/.codex/`, `~/.agents/`
- Cross-project shared docs that are gitignored on the target repo: files under `shared_docs_dir` in `~/.ai-playbook/facts.md` (e.g. `coding_guidelines.md`, `jvm_guidelines.md`, `kotlin_guidelines.md`, `python_guidelines.md`, `agent_workflow_guidelines.md`), company ownership docs under `company_projects_root/.ai-playbook/` (see `~/.ai-playbook/facts.md`; `facts.md`, `dictionary.md`, `company-guidelines.md`)

Quick scan command before posting (resolve `REVIEWS_DIR` per `_shared/doc-paths.md` first; use the exact staging path from the review session when known, otherwise resolve exactly one `${REVIEWS_DIR}/*-PR-<N>-*.md`):
```bash
STAGING="${STAGING:-$(ls -1 "${REVIEWS_DIR}"/*-PR-<N>-*.md 2>/dev/null | head -1)}"
awk '/^#### Comment/{p=1;next} /^#### Analysis/{p=0} p' "$STAGING" | \
  grep -nE "project-guidelines|company-guidelines|docs/maintenance/|docs/glossary|docs/facts|coding_guidelines|jvm_guidelines|kotlin_guidelines|python_guidelines|CLAUDE\.md|AGENTS\.md|agent_workflow_guidelines|shared_docs_dir|~/\.claude|~/\.codex|~/\.agents"
```

Rewrite rules:
- If the citation is the source of an objective rule the PR author would also recognize (project method-length limit, metrics convention, naming convention), restate the principle inline without citing the file. Example: `"see company-guidelines.md #17 (≤30 lines)"` → `"this is hard to scan and exceeds typical method-length limits"`.
- If the citation is the only justification for the finding (i.e. the rule lives only in your private docs), drop the finding entirely. Personal style preferences from user-level instructions are not project conventions the PR author has agreed to follow. Em-dash bans, no-also-chain rules, specific log-format preferences, and similar are common examples. The right place for these is the gitignored doc itself, not a public PR comment.

If a rule should be enforced project-wide, propose it first as a PR to the shared project doc (where the author can agree or push back), then cite it in future reviews. Do not retroactively flag PRs against rules that exist only in your private instructions.

Analysis sections of the staging doc may reference any local doc freely — they are internal scratch and never posted.

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

### 4.10 Empirical Verification of Test/Compile Claims
Before posting a finding that claims tests will fail, code will not compile, or runtime errors will occur, attempt to verify by actually running the build or tests locally. If the local environment cannot run the build (missing dependencies, VPN, etc.), state explicitly in the comment that the claim is based on static analysis and has not been empirically verified. Never present an unverified inference as a confirmed fact.

### 4.11 NEW vs EXISTING Debt (All Findings)

When reporting issues that involve file/module size or structural concerns (god classes, large functions, layer violations), distinguish between:

- **NEW issues**: Introduced by this PR (new files, new functions, significant structural changes) — report at full severity
- **EXISTING debt**: Pre-existing problems this PR only contributed to (adding lines to already-large files) — downgrade to Low or omit

**Rationale:** A PR should not be punished for technical debt that existed before it started. Only report EXISTING debt when the PR significantly compounds the problem.

**How to detect:**
- Use `git diff <base>...<head> --name-status` to identify new (A) vs modified (M) files
- Use `git show <base>:<file>` to check if a function/structure existed before
- If adding lines to an already-large function: EXISTING debt contribution
- If creating a new large function: NEW issue

This applies to all sub-agents, but is most relevant for architectural findings (god classes, layer violations) and simplification findings (over-engineering).

### 4.12 Finding Explanation Depth (Comment and Analysis)

The staging doc has two audiences:
- **Comment** — read by the PR/branch author (and posted to GitHub when approved). It must stand alone: the author should understand the issue, why it matters, and what to do **without** asking for a follow-up explanation.
- **Analysis** — internal scratch for the reviewer; never posted. Holds verification steps, severity rationale, alternatives, and dropped counterarguments.

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
1. **What was checked** — files read, grep/schema queries, tests run or not run
2. **Why this severity** — tie to §4.9.0 defaults; say if downgraded from an agent's initial severity and why
3. **Alternatives considered** — other fix options, or why "document as accepted MVP race" vs "add row lock"
4. **Why not higher/lower** — one line on what would change the severity
5. **Related findings** — dedup notes, prior review IDs, intentional decisions (for example r1 fix that explains `now()` vs `RETURNING`)

#### Sub-agent `body` depth (required at collection time)

Sub-agents must return `body` text that already satisfies the Comment depth table above. The orchestrator should not be the primary author of finding detail.

| Severity | Sub-agent `body` minimum |
|----------|--------------------------|
| **Critical / High** | All Medium sections below, plus user/runtime impact and urgency |
| **Medium** | Four sections with `**Bold headings**`: What the contract/docs say; What the code does; Why this matters; What we could do |
| **Low** | Claim, one sentence of evidence, fix or optional-cleanup suggestion |

Include verification notes (files read, schema checks, severity rationale, alternatives) in the same `body` under an `**Analysis**` heading when useful — the orchestrator moves that block to the staging doc's Analysis section.

#### Orchestrator polish pass (mandatory before staging doc is final)

After dedup in §4.5, for every **Medium+** finding:
1. Confirm the sub-agent `body` satisfies §4.12 Comment depth. If thin, **relaunch the responsible sub-agent** to expand — do not re-read sources in the orchestrator to fill gaps (recovery path only when relaunch is impractical).
2. Apply tone check (§4.8), assumption verification (§4.2–4.4) using cited evidence, and line-number verification (§4.9).
3. Split `body` into staging **Comment** and **Analysis** sections; refine wording but preserve substance — do not shorten a detailed agent `body` for brevity.

**Self-check before marking staging doc complete:** For each Medium+ finding, ask: "Could the author act on this Comment alone without a chat follow-up?" If no, sub-agent output was insufficient — relaunch or expand in staging from the agent payload, not from orchestrator re-analysis.

#### Comment example (Medium, contract drift)

```markdown
**What the contract says**
The `409` response for `PATCH /v1/consent-updates` says consent updates are "rejected before any write". That reads as a hard guarantee: `DELETED` profile, no consent or suppression rows persisted.

**What the code does**
`ConsentController` pre-checks `DELETED`, then `ExternalConsentUpdateOrchestrator` re-reads profile status inside `@Transactional` via plain `findProfile` (no row lock). Under READ COMMITTED, a concurrent soft-delete after that re-read can still allow batch writes while the usual path returns `409` / `PROFILE_DELETED`.

**Why this matters**
This is contract drift, not a typical happy-path logic bug. OpenAPI readers expect strict `409`; api-reference §8b documents the race as an accepted MVP limitation. Integrators or codegen clients may assume behavior the runtime does not fully guarantee.

**What we could do**
One option: soften the OpenAPI `409` description to match api-reference (document the READ COMMITTED race). Another: tighten with `SELECT … FOR UPDATE` on the profile row and re-check immediately before the first mutating statement, if we want the strict contract.
```

#### Analysis example (same finding)

```markdown
Read `openapi.yaml` line 261, `ExternalConsentUpdateOrchestrator.java`, api-reference §8b edge-case table. Verified no `FOR UPDATE` in profile module. Severity Medium per §4.9.0: documented edge-case correctness gap between normative OpenAPI and implemented/documented behavior; not data loss in normal sequential traffic. Downgraded from agent High: narrow window, FK still valid on DELETED row. Intentional r2 doc fix already softened Javadoc; OpenAPI not updated yet. Alternatives: nullable/error-code change not needed; this is wording vs locking choice.
```

## Step 5: Output

**ALWAYS write the staging document**, regardless of mode. The staging doc is the primary deliverable and serves as both approval artifact (for PRs) and persistent record (for all reviews).

### Step 5.1: High-level tasks follow-up (module-split repos)

After the staging doc is written, scan **Medium+** findings (and any accepted Low that describes implementation vs doc/contract drift) for gaps between **current code** and what module docs imply.

When a finding fits, update the module high-level tasks doc in the review session (or tell the user which task block to extend if the review is read-only). Resolve paths from `{guidelines_path}` / project guidelines — do not assume legacy `docs/<module>/` layout on migration-complete repos.

| Module (example) | Legacy path | Post-migration |
|------------------|-------------|----------------|
| Module A | `docs/<module>/<service>-high-level-tasks.md` | path named in project guidelines |
| Module B | `docs/<module>/<service>-high-level-tasks.md` | path named in project guidelines |

Record **tech debt** (document limitation, MVP doc fix, defer code) or **implementation fix** (named target task, tests expected). Do not rely on gitignored `{reviews_dir}/` as the only backlog.

Cross-repo: same pattern when a repo maintains module high-level tasks docs (path from project guidelines).

**File location** (create `{reviews_dir}/` if it doesn't exist):
- For GitHub PR reviews: `{reviews_dir}/YYYY-MM-DD-PR-<number>-<title>.md`
- For local branch reviews: `{reviews_dir}/YYYY-MM-DD-branch-review-<branch_name>.md`
- For plan-based reviews: `{reviews_dir}/YYYY-MM-DD-plan-review-<plan_name>.md`

Branch names are sanitized: slashes replaced with dashes, max 30 chars. No prefix (REVIEW/PR) needed since the directory already indicates these are reviews.

### Staged Mode (default)

Write all findings to the staging document instead of posting directly. This allows the reviewer to inspect, edit, or drop findings before they reach the PR author.

**Document format**:

```markdown
# Code Review: <PR #<number> — <title> OR Branch <head> → <base>>

## Metadata
- Type: PR Review / Branch Review
- Date: YYYY-MM-DD
- PR: <url> (if PR review)
- Branch: <head> → <base> (if branch review, include plan reference if applicable)
- Findings: <count>
- Status: STAGED (not yet posted)

## Findings

### 1. <short title>
- **Status**: `pending`
- **Severity**: High | Medium | Low
- **File**: path/to/File.kt
- **Line**: 115

#### Comment (posted as-is when approved)

<self-contained explanation per §4.12. Medium+: What contract/docs say → What code does → Why this matters → What we could do. Low: claim + evidence + suggestion.>

#### Analysis (not posted — reviewer context only)

<per §4.12 Analysis depth: what was checked, severity rationale, alternatives, dedup/prior-review notes>

---
```

Do not include `Side` in staging documents; it is always `RIGHT` for GitHub inline comments and adds noise for branch-only reviews. When posting approved findings to a PR, set `side: RIGHT` in the API payload only (not in the markdown staging file).

**Status values** (user edits these before giving "post comments" command):
- `pending` — not yet reviewed by user
- `post` — approved, will be posted to PR
- `drop` — rejected, will not be posted
- `edit` — user modified the Comment section, post the updated text

**After writing the staging doc**, inform the user:

For PR reviews:
> "Staged N findings in {reviews_dir}/YYYY-MM-DD-PR-<number>-<title>.md. Review and mark each status as post/drop/edit, then say 'post comments' when ready."

For branch reviews:
> "Review complete. Findings written to {reviews_dir}/YYYY-MM-DD-branch-review-<branch_name>.md with N findings (H: X, M: Y, L: Z)."

### Posting Staged Findings

When the user says "post comments", "post the review", or "post approved":
1. Read the staging doc from the review session path, or resolve exactly one `{reviews_dir}/*-PR-<number>-*.md`
2. Collect all findings with `status: post` or `status: edit`
3. Post them via `github-pr-workflow` as inline comments
4. Update the staging doc: change Status header to `POSTED`, mark posted findings as `posted`, keep dropped findings as `drop`
5. Report which findings were posted and which were dropped

### Direct Mode (skip staging)

When the user explicitly says "post directly", "skip staging", or "review and post":
- Post findings immediately to GitHub (legacy behavior)
- Still write the staging doc as a record with all findings marked as `posted`

**For branch reviews (not GitHub PRs)**: Direct mode is the default behavior since there is no PR to post to. The staging doc is the complete deliverable — always write it with findings marked as `posted`.

For PR reviews, post via `github-pr-workflow`:
```json
{
  "event": "COMMENT",
  "body": "",
  "comments": [...]
}
```

For branch reviews, skip the posting step — the staging doc is the complete deliverable. Inform the user where the doc was written.

Each finding must be posted as an **inline comment** at its specific file and line (for PR reviews). Never consolidate multiple findings into a single top-level review body comment (that makes findings hard to locate and resolve).

**Exception — multi-key deploy checklists:** when several Low findings describe ordered BO/ops steps across different config keys (for example credentials key + routing key), we may post one PR thread comment with the full ordered checklist and delete the superseded inline comments. Keep code-specific inline comments (naming, missing beans) separate.

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

### With `execute-plan` skill
Invoked as a sub-agent in **branch review** mode after all plan tasks are implemented. Review scope comes from the plan's `## Review Scope` section. Output staging doc path: `{reviews_dir}/YYYY-MM-DD-plan-review-<plan-slug>-r<N>.md`. The orchestrator loops review → `receiving-code-review` until two consecutive clear review rounds (zero **remaining** Medium+ after triage — not raw review output).

## Limitations

- In comment mode: read-only. Do not modify any repository file.
- The review deliverable is the staged review document (or posted comments). Do not fix findings, commit changes, or start implementing suggestions after the review is complete — those are separate tasks that require explicit user request.
- Before starting, identify PR author. If PR was not created by current user, enforce read-only with no exceptions.
- Respond in English.
