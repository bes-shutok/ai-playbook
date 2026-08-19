---
name: review-confluence-doc
description: >
  Review RFC and TDD documents on Confluence for quality, clarity, and actionability.
  Fetches a Confluence page, analyzes its content, and provides structured feedback.
  Console output by default; optionally posts accepted feedback as a Confluence comment.
  Trigger phrases: "review RFC", "review TDD", "review confluence page".
---

# Review Confluence Document

**Writing:** Follow `agent_workflow_guidelines.md` §45 when suggesting rewrites. Feedback should prefer plain English (e.g. "API contract", not "wire contract") and recommend a `## Terms` section when the page uses 3+ project-specific words.

Review an RFC or TDD document hosted on Confluence. Provide quality feedback focused on clarity, actionability, and missing context.

## Documentation paths

Read `{reviews_dir}` and `{tmp_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Primary review staging docs go under `{reviews_dir}` per `review-staging`; do not use `{tmp_dir}` for the main review artifact.

## Configuration (from facts document)

This skill reads environment-specific values from the user's facts/profile document (e.g., `facts.md` or equivalent). Never hardcode personal paths, org names, or domains in the skill itself.

| Key | Purpose | Example |
|-----|---------|---------|
| `atlassian_domain` | Default Atlassian cloud domain | `acme.atlassian.net` |
| `docs_tmp_dir` | Legacy alias; prefer resolved `{reviews_dir}` for staging docs | `docs/reviews/` |
| `reviews_dir` | Primary staging doc directory (see `review-staging`) | `docs/reviews/` |

If a key is missing from `.ai-playbook/facts.md`, follow `using-skills` Step 0 (bootstrap only when Terms triggers fire); ask the user only when resolution is ambiguous.

## Workflow

### Confluence publication and diagram integrity

When the task includes publishing or refreshing a local RFC/TDD copy on Confluence, treat the repository document as the source of truth and the page as a rendered derivative.

1. Publish the complete document body in one intentional update. Do not test connectivity by replacing a live page with a short stub.
2. Preserve Mermaid diagrams as fenced `mermaid` source blocks when the target Confluence space natively renders Mermaid code blocks. Do not add a second Mermaid extension macro or image embed for the same source block: Confluence can render the fenced block and the extension independently, producing duplicate diagrams.
3. If the target page already uses native Mermaid extension blocks, inspect the stored HTML before editing. Reuse that representation only when the source code block and extension are a known single-rendering pair. After publishing, verify the page has exactly one rendering representation per intended diagram: no duplicate extension/image derivative alongside a natively rendered Mermaid block.
4. Verify the published page through HTML, not only the editor preview. Count Mermaid source blocks, Mermaid extension nodes, and image embeds. For a native fenced-block target, expected counts are: one Mermaid source block per diagram, zero Mermaid extension nodes, and zero generated image embeds. Also confirm that the page still contains the full body.
5. Record the resulting Confluence `version.number`, last-modified timestamp, source revision, and sync status in the repository's existing sync manifest or ledger. Set `synced` only after the full-body update and HTML verification succeed.

These checks apply after any full-body replacement because Confluence stores presentation derivatives (for example, Mermaid extension nodes) alongside source content and can retain or duplicate them when the body is reconstructed.

### Step 0 – Pre-requisite: Verify Atlassian integration

1. Verify you can read Confluence pages via your environment's **Atlassian integration** (page fetch capability).
2. If the integration is unavailable:
   ```
   ⚠️  Atlassian integration is not available.

   Install and authenticate Confluence/Atlassian access for your agent environment,
   then retry this workflow. See user AGENTS.md or your agent setup docs if present.
   ```
   STOP and wait for the user.
3. If calls fail with OAuth refresh errors (`invalid_grant`, `Invalid refresh token`, `OAuth token refresh failed`), tell the user to re-authenticate the Atlassian integration, then retry.
4. When the integration is authenticated, proceed to Step 1.

---

### Step 1 – Identify the Document

Accept input in any of these forms:
- A Confluence page URL (e.g., `https://your-org.atlassian.net/wiki/spaces/~SPACE-KEY~/pages/123456/My+RFC`)
- A page title + space key
- A page ID

If none provided, ask: "Please provide the Confluence page URL, or the page title and space key."

Extract:
- `cloudId` / site (from URL domain or user profile/facts)
- `pageId` (from URL path or by searching by title in the given space)

---

### Step 2 – Fetch the Document

1. Fetch the page via your Atlassian integration (HTML or markdown content as supported).
2. If the page has child pages that form part of the document (e.g., appendices, sub-sections), fetch those as well.
3. If the fetch fails, show the error and ask the user to verify the URL/permissions.

---

### Step 3 – Determine Document Type

Classify the document as one of:
- **RFC / Design Document**: architecture decisions, API contracts, system design
- **TDD / Test Design Document**: test strategy, test cases, coverage plan
- **Other**: general technical document

Use the page title, labels, and content structure to classify. If ambiguous, ask the user.

---

### Step 4 – Analyze and Generate Feedback

#### Step 4.0 – Select the review panel

Use `review-panel-selection.md`. A normal RFC or TDD review uses the five-worker panel. A prose-only page may use a focused `contract-docs` panel, adding `correctness-completeness` when the prose specifies normative behavior.

Each selected worker receives:
1. Full fetched document content (parent page plus child pages from Step 2)
2. Document type from Step 3 (RFC / TDD / Other)
3. Its assigned lenses, shared severity calibration, and finding budget
4. Execution framing to quote the reviewed prose and return the shared finding fields plus `descendant_launches`

The `contract-docs` worker applies the prose checks below. Document inconsistency remains `Low` unless tangible consequence justifies promotion.

Review the document for the following quality dimensions (orchestrator-owned; supplement with sub-agent output above):

#### 4.1 Clarity
- Are terms defined or unambiguous?
- Is the writing concise and skimmable?
- Are there vague statements that need specifics?

#### 4.2 Actionability
- Can an engineer implement from this document without guessing?
- Are decisions stated explicitly (not implied)?
- Are open questions clearly marked as such?

#### 4.3 Missing Context
- Are there unstated assumptions that should be explicit?
- Are dependencies on other systems/teams identified?
- Are constraints (performance, security, compliance) addressed where relevant?

#### 4.4 Structural Coherence
- Does the document flow logically?
- Are sections at the right level of detail (not too deep, not too shallow)?
- Is there redundancy or contradiction between sections?

#### 4.5 Completeness (light check)
- Are obvious gaps present (e.g., no error handling discussion, no rollback plan, no success criteria)?
- This is NOT a full template conformance check; just flag clearly missing concerns.

---

### Step 4.5 – Risk Worker

The full panel's `risk` worker always loads security. Load premortem for RFC/Design and TDD risk analysis, using personas as internal reasoning sections without child launches.

**Configuration:**
- Context type: **RFC/Design** (use all six personas).
- Frame: "This design was implemented as written. It has failed in production. Why?"
- Input to premortem: the full document content + any constraints/assumptions identified in Step 4.

Calibrate every risk finding with the shared consequence tiers and independent blocking status.

---

### Step 4.6 – Code Review Pass (Conditional)

If the document contains implementation logic (code snippets, pseudocode, algorithm descriptions, SQL migrations, API contract examples, or configuration samples), run a code review pass using the `doing-code-review` analysis approach.

**Trigger criteria (any one is sufficient):**
- Code blocks (fenced or indented) totaling > 10 lines
- SQL DDL/DML statements
- API request/response examples with logic (not just illustrative payloads)
- Pseudocode describing algorithms or state machines
- Configuration that encodes business logic (feature flags, routing rules, validation rules)

**How to apply:** select the workers whose lenses match the implementation logic. Review in document context and anchor every finding to the specific block or section.

Tag implementation findings `[Code]`. If no implementation logic is present, skip this pass.

---

### Step 4.7 – Record Review Statistics (Mandatory)

While merging Step 4, 4.5, and 4.6 returns, populate `## Review Statistics` per `review-staging` before writing the staging file:

1. **Panel:** one row per actual worker launch with loaded lenses, parent worker, Solo/Echo, and descendant declarations. Write the required `.stats.json` sidecar alongside staging.
2. **Raw counts:** count every finding each source returned before dedup (orchestrator dimensions count as one combined Raw total).
3. **Deduplication groups:** list all contributing workers and the staged finding kept.
4. **Discarded findings:** record worker, lens pattern, severity, reason, and lead ownership.
5. **Severity calibration** and **Triage outcomes** placeholder per `review-staging`.

Do not report results to the user until statistics are complete (including explicit `None` rows when a table is empty).

---

### Step 5 – Present Feedback

Output the feedback to a staging Markdown file per `review-staging`, and print a summary to the console.

**File output:**
1. Write the full review to `{reviews_dir}/YYYY-MM-DD-confluence-review-<page-title-kebab>.md`
   - Read `{reviews_dir}` from `.ai-playbook/facts.md` TOML at skill start.
2. Create the directory if it does not exist.
3. The file uses the universal staging hierarchy: `## Metadata`, `## Review Statistics`, `## Findings` (each finding with **Agents**, **Anchor**, **Source**, `#### Comment`, `#### Analysis`).
4. **Mechanical gate (before reporting the review):** write the matching `.stats.json` sidecar (required artifact per `review-staging`) and run the validator on the staging path; do not report the review complete until both pass:
   ```bash
   VALIDATOR="${REVIEW_STAGING_VALIDATOR:-$HOME/.ai-playbook/scripts/validate_review_staging.py}"
   python3 "$VALIDATOR" --hard "$STAGING_PATH"
   ```

**Console output:**
- Print the file path.
- Print a condensed summary by `Critical`, `High`, `Medium`, and `Low`, plus discarded count and top blocking themes.
- Do NOT dump the full review to console; the file is the primary artifact.

**File format** (see `review-staging` for full template):

```markdown
# Confluence Review: <Page Title>

## Metadata
- Type: Confluence Review (<RFC | TDD | Other>)
- Date: YYYY-MM-DD
- URL or Artifact: <page URL>
- Findings: <staged count>
- Status: STAGED

## Review Statistics

### Panel
| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| contract-docs | documentation, consistency | none | complete | 2 | 2 | 0 | no |
| risk | security, premortem | none | complete | 4 | 2 | 2 | no |

### Counts
- Workers launched: <N>
- Workers skipped: <N>
- Raw findings (all workers): <N>
- Staged findings: <N>
- Discarded during synthesis: <N>
- Solo staged (unique agent origin): <N>
- Echo staged (multi-agent dedup): <N>

### Deduplication groups
| Staged # | Workers | Lenses | Theme |
|----------|---------|--------|-------|

### Discarded findings
| Worker | Worker severity | Pattern | Theme | Reason | Notes |
|--------|-----------------|---------|-------|--------|-------|

### Severity calibration
| Staged # | Worker | Lens | Worker severity | Staged severity | Delta |
|----------|--------|------|-----------------|-----------------|-------|

### Triage outcomes
Pending triage.

## Findings

### Critical

#### F1. <short title>
- **Severity**: Critical | High | Medium | Low
- **Blocking**: true | false
- **Consequence**: <tangible outcome>
- **Reachability**: expected | common | plausible-edge | theoretical
- **Blast radius**: global | multi-service | single-service | local
- **Confidence**: verified | strong-evidence | hypothesis
- **Worker severity**: Medium *(omit when equal to Severity)*
- **Pattern**: premortem#rollback-gap
- **Workers**: risk
- **Triage**: pending
- **Anchor**: §3.2 Upstream timeout handling
- **Source**: [Premortem]

#### Comment (posted as-is when approved)
<Comment-ready wording for Confluence.>

#### Analysis (not posted)
<Persona, verification trail, severity rationale.>

---

### High

None.

### Medium

None.

### Low

None.

### Overflow manifest
| Worker | Pattern | Anchor | Severity | Confidence | Consequence |
|--------|---------|--------|----------|------------|-------------|
```

Optional `## Strengths` section (after Findings) when the document is well-written; list up to 3 bullets. Do not invent issues to fill quotas.

Rules:
- Be specific: reference the section or paragraph where the issue appears.
- Be constructive: suggest what to add/change, not just what's wrong.
- Apply the shared finding budget. Do not produce exhaustive nitpick lists.
- If the document is well-written, say so. Do not invent issues.
- Tag premortem findings with `[Premortem]` and the originating persona.
- Tag code review findings with `[Code]`.
- Tag documentation prose findings with `[Prose]`.
- **Never cite local or internal files** (e.g. `jvm_guidelines.md`, `CLAUDE.md`, internal playbooks) anywhere in the review output: not in the file, not on console, not in Confluence comments. The document author has no access to these files. State the principle and the reason it matters inline instead.
- **Write the review doc in comment-ready tone.** The review file is the source the comments are posted from; use the same wording (suggestion tone: "we could", "one option might be") in the file so no rephrasing is needed at posting time.
- **No em dashes** ("; ") anywhere in the review output: not in the file, not on console, not in Confluence comments. Use commas, semicolons, colons, parentheses, or split into separate sentences.
- **Spell out jargon and acronyms on first use.** Engineering shorthand (e.g. "p99 latency", "OCP", "JWKS", "CSRF") is opaque to readers from adjacent disciplines or non-native speakers. Where a term is used, briefly expand it the first time (e.g. "p99 latency under 200ms, meaning 99% of requests complete in under 200ms").
- **Verify acronym meaning from the document, not from industry default.** Acronyms in document titles or section headers may have project-specific meanings (e.g. "TDD" can mean "Technical Design Document" rather than "Test-Driven Development"). Do not raise findings that depend on a particular expansion of an acronym without confirming the author's intent from the document content. If unclear, ask before posting.

**Console summary example:**
```
Review written to: {reviews_dir}/2026-05-19-confluence-review-my-rfc-title.md
   Critical: 1 · High: 2 · Medium: 3 · Low: 2 · Discarded: 4

   Top critical:
   1. No rollback strategy for migration ([Premortem])
   2. SQL migration missing index on high-cardinality column ([Code])
   3. Missing error handling for upstream timeout in §3
```

---

### Step 6 – Offer to Post as Confluence Comment

After presenting feedback on console:

1. Ask: "Would you like me to post this review as a comment on the Confluence page?"
2. If user declines → done.
3. If user accepts, post findings one at a time, discussing each with the user before posting.

#### 6.1 Inline vs footer comments

**Prefer inline comments** anchored to specific page text when your integration supports them. Some environments expose footer comments separately from inline comments; confirm you are using the inline capability before posting, not footer-only by accident. Posted comments may not be editable through the integration; wrong-format posts may require manual cleanup in Confluence UI.

- **Default: inline comment** anchored to specific text in the page. This gives the reader immediate context; the comment appears right next to the relevant section.
- **Footer comment**: only when a finding spans many unrelated sections and has no single natural anchor point.
- When a finding touches two locations, post the main comment at the primary location and a short one-liner cross-reference at the secondary location pointing to the main comment (e.g. "See inline comment on §5.2 for the full analysis."). Do not duplicate the full comment.
- Code block text cannot be used as an anchor (Confluence does not allow inline comments on code blocks). Find the nearest prose sentence instead.

#### 6.2 Comment wording rules

Apply these to every comment regardless of severity:

- **Constructive tone, never hostile.** Use direct, actionable wording while keeping blocking status explicit.
- **No em dashes** ("; ") anywhere in comment text. Use commas, semicolons, colons, or parentheses instead. (See also the global rule in Step 5.)
- **Plain language (globish).** Short words, short sentences. Avoid jargon a non-native speaker would not know.
- **Never reference internal machine-specific docs** (e.g. JVM guidelines, CLAUDE.md rules, internal playbooks) in Confluence comments. Explain the principle and its benefits directly instead.
- **Status lozenges for severity**: use `Critical`, `High`, `Medium`, or `Low` at the start of each comment.

#### 6.3 Comment lifecycle rules

- **Never add a self-correction reply** ("Correction to the above:"). If a posted comment needs correction, tell the user and ask them to delete the original. Then repost the clean version.
- **Never add unsolicited notes or replies** to existing comment threads unless the user specifically asks.
- The Atlassian integration may not expose comment edit or delete. Acknowledge this limitation to the user when a correction is needed.
- Confirm each successful post: `✅ Comment posted on <anchor text>.`

---

## Integration Points

### With `review-agents` skill (mandatory prose pass)
`contract-docs` loads `documentation.md` for all document types. Findings use shared severities and `[Prose]`.

### With `premortem` skill (mandatory)
Loaded inside `risk` in Step 4.5. Personas are reasoning sections, not child launches. Findings use shared severity calibration.

### With `doing-code-review` skill (conditional)
Applied in Step 4.6 only when implementation logic is present in the document (code blocks > 10 lines,
SQL, pseudocode, config-as-logic). Selects matching workers without using the PR workflow. Findings are tagged `[Code]`.

### With `review-staging` skill (mandatory)
All reviews write to `{reviews_dir}/` with full `## Review Statistics` per `review-staging` (Solo/Echo, Pattern, Severity calibration, Triage outcomes). Step 5 ends with a `--hard` validator gate over the staging path and its `.stats.json` sidecar before the review is reported. Step 6 Confluence comments post from each finding's `#### Comment` block.

---

## Guidelines

- Do NOT modify the Confluence page content. This skill is read + comment only.
- Do NOT apply the full `rfc-design` template as a conformance checklist. The review is about quality, not format compliance.
- Keep feedback proportional to document length: a 1-page doc gets a few bullets, not a page of feedback.
- If the document references external resources (Jira tickets, other Confluence pages, diagrams), note when those references are broken or unclear, but do not fetch and review them recursively.
- Premortem is NOT optional; even well-written documents benefit from adversarial stress-testing.
- Code review pass IS optional; only triggered when implementation logic is detected.
