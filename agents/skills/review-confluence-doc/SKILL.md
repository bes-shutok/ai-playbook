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

Resolve `{tmp_dir}` per [`_shared/doc-paths.md`](../_shared/doc-paths.md) before writing review output files. Do not hardcode `./docs/tmp/` when project guidelines document a resolved path.

## Configuration (from facts document)

This skill reads environment-specific values from the user's facts/profile document (e.g., `facts.md` or equivalent). Never hardcode personal paths, org names, or domains in the skill itself.

| Key | Purpose | Example |
|-----|---------|---------|
| `atlassian_domain` | Default Atlassian cloud domain | `acme.atlassian.net` |
| `docs_tmp_dir` | Directory for review output files (prefer resolved `{tmp_dir}`) | `docs/tmp/` |

If a key is missing from facts, resolve `{tmp_dir}` per `_shared/doc-paths.md`; ask the user only when resolution is ambiguous.

## Workflow

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
- A Confluence page URL (e.g., `https://your-org.atlassian.net/wiki/spaces/TEAM/pages/123456/My+RFC`)
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

Review the document for the following quality dimensions:

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

### Step 4.5 – Premortem Analysis (Mandatory)

After the quality analysis in Step 4, invoke the `premortem` skill against the design/plan described in the document.

**Configuration:**
- Context type: **RFC/Design** (use all six personas).
- Frame: "This design was implemented as written. It has failed in production. Why?"
- Input to premortem: the full document content + any constraints/assumptions identified in Step 4.

**Output handling:**
- **Blockers** from premortem become 🔴 Critical items in the final feedback.
- **Mitigations Needed** become 🟡 Suggestions.
- **Monitor** items are mentioned as advisory notes (not elevated to suggestions unless severe).
- **Accepted Risks** are omitted from feedback unless they reflect genuinely unacknowledged risks in the document.

Do NOT skip premortem even if the document appears solid; the point is adversarial stress-testing.

---

### Step 4.6 – Code Review Pass (Conditional)

If the document contains implementation logic (code snippets, pseudocode, algorithm descriptions, SQL migrations, API contract examples, or configuration samples), run a code review pass using the `doing-code-review` analysis approach.

**Trigger criteria (any one is sufficient):**
- Code blocks (fenced or indented) totaling > 10 lines
- SQL DDL/DML statements
- API request/response examples with logic (not just illustrative payloads)
- Pseudocode describing algorithms or state machines
- Configuration that encodes business logic (feature flags, routing rules, validation rules)

**How to apply:**
- Do NOT use the full PR-oriented `doing-code-review` workflow (no GitHub PR, no sub-agents, no line comments).
- Instead, apply the *review lens* from relevant sub-agent focus areas:
  - `quality`: bugs, logic errors, edge cases, error handling
  - `security`: injection, secrets, input validation, auth gaps
  - `concurrency`: race conditions, isolation issues (if concurrent logic is present)
  - `simplification`: over-engineering in the proposed implementation
- Review the code in context of the document's stated goals and constraints.
- Each finding must reference the specific code block/section.

**Output handling:**
- Findings become additional items in the 🔴 Critical or 🟡 Suggestions sections, tagged with `[Code]` prefix.
- If no implementation logic is present, skip this step silently.

---

### Step 5 – Present Feedback

Output the feedback to a temporary Markdown file for easy reading, and print a summary to the console.

**File output:**
1. Write the full review to `<project_docs_tmp>/review-<page-title-kebab>-<YYYY-MM-DD>.md`
   - Resolve `<project_docs_tmp>` from the user's facts document (key: `docs_tmp_dir`), or fall back to `./docs/tmp/` relative to the current project root.
2. Create the directory if it does not exist.
3. The file contains the full structured feedback (all sections below) with proper Markdown formatting (headings, bullet lists, code blocks, and tables render correctly in any editor/previewer).

**Console output:**
- Print the file path.
- Print a condensed summary: count of critical/suggestion/advisory items and the top 3 critical findings.
- Do NOT dump the full review to console; the file is the primary artifact.

**File format:**

```
📝 Review: <Page Title>
   Type: <RFC | TDD | Other>
   URL:  <page URL>

─────────────────────────────────────

🔴 Critical (blocks implementation)
   • <issue>
   • [Premortem] <issue> (Persona: <X>)
   • [Code] <issue>

🟡 Suggestions (improves quality)
   • <issue>
   • [Premortem] <issue> (Persona: <X>)
   • [Code] <issue>

🟢 Strengths
   • <positive observation>

ℹ️  Advisory (premortem, monitor-level)
   • <observation> (Persona: <X>)

─────────────────────────────────────
```

Rules:
- Be specific: reference the section or paragraph where the issue appears.
- Be constructive: suggest what to add/change, not just what's wrong.
- Limit to the most impactful items (max ~5 critical, ~7 suggestions). Do not produce exhaustive nitpick lists.
- If the document is well-written, say so. Do not invent issues.
- Tag premortem findings with `[Premortem]` and the originating persona.
- Tag code review findings with `[Code]`.
- **Never cite local or internal files** (e.g. `jvm_guidelines.md`, `CLAUDE.md`, internal playbooks) anywhere in the review output: not in the file, not on console, not in Confluence comments. The document author has no access to these files. State the principle and the reason it matters inline instead.
- **Write the review doc in comment-ready tone.** The review file is the source the comments are posted from; use the same wording (suggestion tone: "we could", "one option might be") in the file so no rephrasing is needed at posting time.
- **No em dashes** ("—") anywhere in the review output: not in the file, not on console, not in Confluence comments. Use commas, semicolons, colons, parentheses, or split into separate sentences.
- **Spell out jargon and acronyms on first use.** Engineering shorthand (e.g. "p99 latency", "OCP", "JWKS", "CSRF") is opaque to readers from adjacent disciplines or non-native speakers. Where a term is used, briefly expand it the first time (e.g. "p99 latency under 200ms, meaning 99% of requests complete in under 200ms").
- **Verify acronym meaning from the document, not from industry default.** Acronyms in document titles or section headers may have project-specific meanings (e.g. "TDD" can mean "Technical Design Document" rather than "Test-Driven Development"). Do not raise findings that depend on a particular expansion of an acronym without confirming the author's intent from the document content. If unclear, ask before posting.

**Console summary example:**
```
📝 Review written to: ./docs/tmp/review-my-rfc-title-2026-05-19.md
   🔴 3 critical · 🟡 5 suggestions · ℹ️ 2 advisory

   Top critical:
   1. [Premortem] No rollback strategy for migration (Persona: Operator)
   2. [Code] SQL migration missing index on high-cardinality column
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

- **Suggestion tone, never directive.** Use "we could", "one option might be", "what about", "we should probably". Never issue orders ("Add X", "Remove Y", "Change Z"). Severity (Critical/Suggestion/Question) controls whether action is required, not the tone.
- **No em dashes** ("—") anywhere in comment text. Use commas, semicolons, colons, or parentheses instead. (See also the global rule in Step 5.)
- **Plain language (globish).** Short words, short sentences. Avoid jargon a non-native speaker would not know.
- **Never reference internal machine-specific docs** (e.g. JVM guidelines, CLAUDE.md rules, internal playbooks) in Confluence comments. Explain the principle and its benefits directly instead.
- **Status lozenges for severity**: use `Critical` (red), `Suggestion` (yellow), `Question` (blue), `Advisory` (yellow) at the start of each comment so the reader can scan severity at a glance.

#### 6.3 Comment lifecycle rules

- **Never add a self-correction reply** ("Correction to the above:"). If a posted comment needs correction, tell the user and ask them to delete the original. Then repost the clean version.
- **Never add unsolicited notes or replies** to existing comment threads unless the user specifically asks.
- The Atlassian integration may not expose comment edit or delete. Acknowledge this limitation to the user when a correction is needed.
- Confirm each successful post: `✅ Comment posted on <anchor text>.`

---

## Integration Points

### With `premortem` skill (mandatory)
Invoked in Step 4.5 after initial quality analysis. All six personas for RFC/Design documents;
Pessimist + Attacker + Operator for TDD documents. Blockers become Critical feedback items.
Mitigations become Suggestions. The premortem is run against the document content, not against code.

### With `doing-code-review` skill (conditional)
Applied in Step 4.6 only when implementation logic is present in the document (code blocks > 10 lines,
SQL, pseudocode, config-as-logic). Uses the review lens (quality, security, concurrency, simplification)
but NOT the full PR workflow. Findings are tagged `[Code]` in the output.

---

## Guidelines

- Do NOT modify the Confluence page content. This skill is read + comment only.
- Do NOT apply the full `rfc-design` template as a conformance checklist. The review is about quality, not format compliance.
- Keep feedback proportional to document length: a 1-page doc gets a few bullets, not a page of feedback.
- If the document references external resources (Jira tickets, other Confluence pages, diagrams), note when those references are broken or unclear, but do not fetch and review them recursively.
- Premortem is NOT optional; even well-written documents benefit from adversarial stress-testing.
- Code review pass IS optional; only triggered when implementation logic is detected.
