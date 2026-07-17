---
name: rfc-design
description: >
  Create, edit, or structurally review Design RFCs in Markdown. Use for design RFC, feature design,
  technical design doc, architecture RFC, API design, or /rfc-design. Modes: create (full intake),
  edit (existing file), review-local (Step 2 only). Confluence-hosted pages: use review-confluence-doc.
  Creation uses intake gates, then draft plus tiered review-agents pass before final output.
---

# Command: Generate MVP Design RFC (Implementation-ready, succinct)
# Intent: Produce a concise, actionable, implementation-ready RFC suitable for linking into Jira stories.
# Note: Command verbosity is acceptable. Output must be succinct and implementation-oriented.

**Writing:** Follow `agent_workflow_guidelines.md` §45. RFC prose uses plain English; add `## Terms` when using 3+ project-specific words. Transport/code docs may keep "wire format" where the team already uses it.

## Core Concepts
- Hard gate: a mandatory stop point where RFC generation cannot continue without explicit user confirmation.
- Coverage checklist: a pre-generation scope contract that confirms in-scope surfaces and MVP boundaries.
- Canonical ID: the single identifier returned by resolve-style APIs for downstream composition.
- Server-owned field: state/audit field (for example `updated_at`, version) set by the service, not by client input.
- Core vs custom properties split: core cross-tenant dimensions are first-class fields; tenant-defined extensions are a flexible map.

## When to Use

| User intent | Mode | Skill path |
|-------------|------|------------|
| Create or draft a new Design RFC | **Create** | Steps 0 → 0.1 → 1 → 2 → 3 |
| Update an existing Markdown RFC file | **Edit** | **Read this skill + `references/rfc-sections.md` first**; skip Steps 0–0.1 unless scope changed; apply editing checklist; run Step 2 (Light) when edit is substantial **or** after a formatting/readability cleanup pass (formatting alone misses contract gaps). Use targeted edits (`StrReplace`), not full-file overwrite, on large RFCs. |
| Review a local Markdown RFC only | **Review-local** | Step 2 on the provided draft; no regeneration |
| Review an RFC/TDD on Confluence | **Redirect** | `review-confluence-doc` (fetch page, quality feedback) |
| Turn an approved RFC into an implementation plan | **Handoff** | `plans` skill; reference the saved RFC path in the plan header |

**Announce at start:** "I'm using the rfc-design skill in **{mode}** mode."

**Do not use** for implementation plans (`plans`), code review (`doing-code-review`), or Confluence page review (`review-confluence-doc`).

## Workflow Overview

| Phase | Step | Hard gate? | Output |
|-------|------|------------|--------|
| Intake | Step 0 – Input collection | Yes | Input inventory only |
| Intake | Step 0.1 – Assumptions and coverage | Yes | Coverage checklist for user confirm |
| Draft | Step 1 – Generate RFC draft | No (after gates) | Full RFC sections 1–8 per structure below |
| Review | Step 2 – Review pass (sub-agents) | Tiered (light default; full on request) | Staging review file under `{reviews_dir}/`; revised RFC |
| Deliver | Step 3 – Finalize | No | Markdown RFC only (findings folded in; no separate review artifact in chat) |
| Handoff (optional) | After Step 3 | No | Offer `plans` when user wants implementation planning |

**Section template:** Read `references/rfc-sections.md` when drafting §1–8, Technical Decision Notes, or editing an existing RFC. Read `references/contract-blueprint-example.md` before drafting or revising **§5 Contracts**.

## Documentation paths (doc-hierarchy aligned)

Read path keys from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0; `bootstrap-ai-playbook` when triggers fire). Do **not** hardcode `docs/rfcs/`, `docs/plans/`, or module-split trees.

| Key | Role | Post-migration default (Layer 3) |
|-----|------|----------------------------------|
| `{rfcs_dir}` | Canonical **Design RFC** files (history, flat) | `docs/history/feature-notes/` |
| `{proposals_dir}` | Pre-canonical RFC **drafts** only (optional) | `docs/history/feature-notes/proposals/` or legacy `docs/proposals/` |
| `{reviews_dir}` | RFC review staging docs and `.stats.json` sidecars | `docs/reviews/` |
| `{tmp_dir}` | Session scratch (not review staging) | `docs/tmp/` |

**Save location rules:**

1. Resolve `{rfcs_dir}` from facts; use the on-disk path only (bootstrap never invents paths).
2. **Doc-hierarchy migration-complete repos:** save finished RFCs as **flat files** under `{rfcs_dir}` (Layer 3 history). Prefer `{SERVICE}_rfc.md` or `{feature}-rfc.md` per `doc-hierarchy/migration-map.md`. Do **not** create `docs/rfcs/` at `docs/` root; verify script flags that as a migration failure.
3. **Legacy repos (pre-migration):** if `docs/rfcs/` still exists on disk and facts point there, save there until **doc-hierarchy-migrate** runs; do not create new legacy roots on repos already on the three-layer layout.
4. **Work-in-progress drafts** the user has not approved for the history corpus: `{proposals_dir}` when that key exists; otherwise ask before writing under `{rfcs_dir}`.
5. **Placement questions** (RFC vs architecture topic vs investigation note): read `doc-hierarchy` skill; RFCs are Layer 3 feature notes, not Layer 2 architecture topics.

**Review staging** (Step 2) always under `{reviews_dir}/YYYY-MM-DD-rfc-review-<slug>-<mode>.md` per `review-staging`, never under `{rfcs_dir}` or `{tmp_dir}/rfc-review/`.

Generate a **Design RFC** in **Markdown format**.

The **output must be Markdown only**.

The RFC must be:
- succinct and skimmable
- actionable for implementation stories (API, DB, logic)
- implementation-ready to the level achievable with the provided inputs

Do NOT include generation-time reasoning, meta commentary, or attribution.

---

## Terminology (Mandatory)

Place **`# Terminology`** (or `# Dictionary`) at the **very beginning** of the document. It is the **only** block before **`### 1. Header`**. Numbered sections 1–8 and any **Addendum** sections follow Header.

### Reader-facing glossary (not writer instructions)

The Terminology block is for **readers** implementing the RFC. It is **not** a place for authoring policy, eval-ban tables, jargon-usage essays, or "if you meant X use Y" disambiguation matrices. Those belong in project guidelines, agent skills, or feature working notes.

**Allowed in Terminology:**

- One optional intro sentence (e.g. two concepts that must not be confused).
- A **flat, alphabetically sorted** bullet list: one term per bullet, short clear definition.
- Jargon and abbreviations (e.g. tombstone, DLQ, MQ) when defined here before first body use.

**Forbidden in Terminology:**

- Topic subsections (`#### People and audience`, `#### Filters and bitmaps`, etc.).
- Writer meta tables or prose ("Use them when they are unambiguous", "Do not use eval").
- Operator matrices, catalog tables, or long comparative notes (move to **Addendum** at document end).

**Body prose:** Do not use ambiguous catch-alls (e.g. **eval**, **evaluation**) as a stand-in for distinct operations. Name the **one** operation: operator preview, segment membership, rule compilation, snapshot build, bitmap maintenance, list count/page. Agent-centric working notes may keep **eval** for brevity.

### What to define

- Explain terms (including abbreviations) that may be ambiguous, security-sensitive, or domain-specific.
- Do NOT explain universally known technical terms (API, HTTP, JSON, DB, UI).

Must be explained if used: RBAC, SSO, IAM, PII; company/product abbreviations; cross-domain abbreviations whose meaning is not obvious.

### Format

- Bullet list; **bold term** first; one short definition per bullet.
- Sort entries **A–Z** by the bold term (ignore leading "The").
- No repetition of full definitions elsewhere in the document; body may use the term once defined.
- Do not bold cross-references or emphasis inside a definition; use plain words for other glossary terms already defined above.

### Bold and emphasis (§1–8 and Addendum)

- **Terminology only:** bold the term label at the start of each glossary bullet (`- **Term**:`). Nowhere else in the RFC.
- **Body sections:** use `####` / `#####` headings to partition content. Do not bold glossary terms, operation names, or whole sentences for emphasis.
- **Code and literals:** use backticks for field names, operators, table/column names, and wire values.
- If a block needs visual separation, add a heading; do not substitute bold paragraphs.

### Addendum (supplementary material)

After **`### 8. Testing & Rollout`**, optional **`### Addendum A.`**, **`### Addendum B.`**, … for material that supports the RFC but is not a glossary entry:

- Operator / filter matrices (e.g. MVP filter operators D24)
- Naming rationale tables (e.g. `HAS_OCCURRED` vs `EXISTS`)
- Accepted risks overflow when §8 is already dense

Addenda use the same heading rules as §1–8 (see `references/rfc-sections.md`).

---

## Document structure and headings (Mandatory)

Read `references/rfc-sections.md` for the full section template. Summary:

| Level | Use for |
|-------|---------|
| `# Terminology` | Glossary only (before §1) |
| `### N. Section title` | Numbered sections 1–8, Addendum |
| `#### Subsection title` | Problem statement, Goals, In-scope, Contract notes, Critical tests, … |
| `#####` | Per-endpoint examples under §5.1, per-event under §5.2 |

**Subsection rule:** Inside `### 2. Problem, Goals, Non-goals` (and §3, §5, §7, §8, etc.), use **`#### Subsection title`** plus a blank line, then bullets or prose. Do **not** use nested list labels (`- Problem statement:`) or bold inline titles (`**Goals:**`) as pseudo-headings; they do not separate visually in Confluence or Markdown previews.

**Edit mode (mandatory):** Before changing an existing RFC, read this skill and `references/rfc-sections.md`, then run the **Editing checklist** in `rfc-sections.md` before presenting the update.

---

## Step 0 – Input Collection Mode (Hard Gate)

Inputs may be provided via:
1) CLI/context arguments supplied to the tool (preferred when present)
2) Repository documents discovered by searching the repo (preferred when available)
3) Inline pasted text in chat (fallback)

Required inputs (as text available in the current context, from any of the above sources):
- PRD (full text or relevant excerpts)
- High-level architecture (full text or relevant excerpts)
- Relevant service documentation (including subfolders) or key excerpts
- Any existing API contracts / schemas / DB schemas that are relevant (if they exist)

Hard gate rules:
- Until the user gives an explicit "go ahead" signal, you MUST NOT generate any part of the RFC (no section drafts, no outlines, no partials).
- In this mode, you may ONLY:
  - list what inputs are missing
  - ask targeted questions to obtain missing details
  - request specific missing excerpts ONLY if they are not present in CLI/context arguments and cannot be found in the repo 
  - restate what was received in a short inventory (no interpretation)

Proceed signal:
- Only start generating the RFC after the user explicitly indicates readiness, e.g. "OK, proceed", "Go ahead", or "Generate the RFC".

**Fast path (skip separate Step 0 inventory):** When the user already attached or pointed to PRD + architecture (+ contracts when APIs/events/DB are in scope) **and** said to proceed, draft, or generate, treat Step 0 as satisfied. Produce Step 0.1 coverage checklist in the same message (do not wait for a second turn unless a blocking gap remains).

---

## Step 0.1 – Assumptions & Coverage Confirmation (Hard Gate)

After all inputs are provided (but before generating the RFC), produce an **Assumptions & Coverage** checklist for user confirmation.

The checklist MUST include:
- In-scope surfaces for THIS RFC:
  - Backend / Frontend / Mobile (iOS) / Mobile (Android) / DevOps-Infrastructure
- MVP scope boundaries:
  - explicitly in MVP
  - explicitly deferred (if stated)
- Which RFC sections will be present with real content vs "Not applicable for MVP"
- Any inferred scope decisions marked `(TODO: confirm)`
- Any missing technical decisions that block implementation-ready details

Hard gate rules:
- Do NOT generate any RFC sections until:
  1) the checklist is produced, AND
  2) the user confirms the checklist AND gives the Proceed signal.

**Fast path:** When the user message includes both complete inputs and an explicit proceed/generate signal, present the checklist and start Step 1 in the same turn after a one-line assumption summary. Do not block on a second confirmation unless the checklist contains `(TODO: confirm)` items that block implementation-ready contracts.

---

## Global Inference Rules (Mandatory)

Inference is allowed, but controlled.

Rules:
- Do NOT infer:
  - ownership, authority, approvals, or named stakeholders
  - compliance regimes (e.g. GDPR) unless explicitly in the inputs
- If database engine is not specified, use **generic SQL** for DDL where possible and mark engine-specific parts as `(TODO: confirm)`.
- If you include engine-specific SQL examples while the decision is pending, label them as examples and add a one-line portability note.
- When referencing internal repository documents, use document names (in parentheses) and do not use file paths or Markdown links to internal `.md` files.
- Before including an external URL in a canonical document, verify it is accessible; if verification cannot be performed or fails, do not include the URL.
- Do not mix inferred and sourced facts in the same bullet.
- Use `(TODO: confirm)` when a decision must be confirmed.
- Use `(TODO: define)` when a detail is required to implement but not provided.
- For resolve-style endpoints, default to returning only the canonical identifier unless trace details are explicitly required.
- Keep server-owned fields out of client-write request examples unless override semantics are explicitly required by inputs.
- When modeling flexible attributes, separate core cross-tenant dimensions from tenant-defined custom properties.

---

## Global Succinctness & Actionability (Mandatory)

Rules:
- Prefer concrete bullets over narrative.
- **Succinct vs telegraphic:** Bullets must stay skimmable **and** self-contained for readers who land mid-document (§4 edge cases, §6 rules, §7 alerts). Succinct is short with complete meaning; telegraphic drops subjects, uses undefined jargon, or hides thresholds (e.g. "alert if ≥3 in 24h" without saying **what** is counted). When a term is in Terminology, still spell out the behavior once in edge cases and operability rows (table/column names OK).
- **§5 Contracts:** prefer **implementation blueprints** (JSON request/response bodies, event payloads, DDL/SQL) over wordy explanations. If a fact is not in a fenced example, it is not implementation-ready. Minimum bar: `references/contract-blueprint-example.md`.
- Every bullet must be either:
  - a requirement
  - a decision
  - a contract
  - a dependency
  - or an implementation task input
- Do NOT list obvious/generic statements unless explicitly required by provided inputs.
- Keep non-contract sections short; §5 endpoint inventories are expected to be complete, not minimal.
- Use stable headings so Jira stories can link to specific sections.

---

## Step 1 – Generate RFC Draft

After Step 0 and Step 0.1 gates pass, draft all RFC sections in one pass per `references/rfc-sections.md`. Do not run Step 2 until the draft is complete (all sections present or marked "Not applicable for MVP").

## Skill Ownership for RFC Lessons

When a lesson changes RFC authoring workflow, section content requirements, or review-checklist expectations:
- update this `rfc-design` skill or `references/rfc-sections.md` at the relevant section
- add an example/playbook only when needed to illustrate the rule; use project-resolved path from `.ai-playbook/facts.md` TOML (`caller_catalog`, `{tmp_dir}`, or legacy examples dir if the repo still has one)
- do not treat editing an individual module RFC as the primary fix unless the underlying skill rule is already correct

---

## Step 2 – Review Pass (Sub-Agents, Tiered)

After Step 1 draft is complete (or when running **Review-local** mode), read `review-agents/review-panel-selection.md` for RFC Light/Full panels and conditional agents, then launch review sub-agents **in parallel** before presenting the final RFC. Do not replace this pass with inline orchestrator analysis.

### Review depth

| Depth | When | Agents |
|-------|------|--------|
| **Light** (default) | MVP RFC, first draft, user did not ask for full review | `quality`, `implementation`, `security`, `architecture`, `simplification`, `documentation`, `concurrency` (when matched; see Conditional agents), inline consistency |
| **Full** | User says "full review", money/security-critical feature, or RFC touches async/queues/multi-service events | All agents in the table below plus inline consistency |
| **Skip** | Trivial config/doc tweak, or user says "skip review" | None |

User may request **Full** explicitly; do not default to Full without a signal.

### Hard gates

1. **Launch all relevant sub-agents before revising the RFC.** Do not skip the pipeline because the draft "looks fine."
2. **Write the staging review file** under `{reviews_dir}/YYYY-MM-DD-rfc-review-<rfc-slug>-<mode_or_round>.md` and the matching `.stats.json` sidecar before folding findings into the RFC. Include `## Review Statistics` per `review-staging`.
3. **Fold findings into the RFC structure** (Step 3). Do not present a separate premortem or review report in chat; print only a short summary and the staging file path.
4. **Partial review gate:** when more than 2 agents fail (see Budget), write the staging file but do **not** fold findings into the RFC until the user chooses re-review or manual continuation.

### Budget (default)

- Launch all agents for the selected depth in **one parallel batch**; do not run Step 2 twice in one session unless the user requests re-review.
- **Max 1 relaunch** per agent for insufficient output; record relaunch in the staging file Agent status table.
- If **more than 2 agents** fail (timeout, empty, or unusable return): write the staging file with partial findings, **do not fold** into the RFC, and report partial review status to the user.
- **Light:** up to 8 agents (6 shared + consistency, or 7 shared + consistency when `concurrency` matches).
- **Full:** up to 10 agents (7 shared + conditional concurrency/premortem + consistency); same relaunch and failure rules.

### Orchestrator boundary

| Do | Do not |
|----|--------|
| Launch agents, wait, parse returns, dedup, write staging file with Review Statistics | Re-analyze the RFC inline while agents run |
| Fold accepted findings into RFC sections per severity map | Re-read source inputs to expand thin agent findings (relaunch the agent instead) |
| Spot-check a claim only when evidence is missing or contradicts a quick grep | Author full analysis the agent should have returned |

**Insufficient sub-agent output:** relaunch the responsible agent with a focused prompt ("expand finding N with quoted RFC section and concrete fix").

### Launch sub-agents in parallel

Each agent receives:
1. Full RFC draft from Step 1
2. Original inputs from Step 0 (PRD excerpts, architecture, contracts) when available for evidence checks
3. Its pattern catalog from `review-agents/<agent>.md` (resolve via shared skills registry)
4. **Execution framing:** "You are reviewing a Design RFC draft, not a git diff or implementation plan. Read the RFC sections and referenced input context. Apply your pattern catalog to what the RFC **proposes**. Do not flag correct template placement (Terminology before §1, `###` numbered sections). **Do** flag Terminology writer meta, non-alphabetical or subsectioned glossaries, pseudo-headings (`- Label:` / `**Label:**`), operator matrices in Terminology instead of Addendum, **telegraphic edge cases or operability rows** (undefined jargon, missing Condition/Behavior/Outcome in §4, thresholds without units/subjects), and **body prose that assumes Terminology was read** without restating behavior once. Return `{section_anchor, quoted_excerpt, issue, severity: Block/Mitigate/Monitor/Accept, fix, evidence}`."
5. **Output limit:** 2–3 findings max per agent; report problems only.

#### Shared agents (from `review-agents/`)

Launch only the agents required by the selected **review depth** and `review-panel-selection.md`. Full depth runs shared agents marked yes in Full plus consistency; Light runs agents marked yes in Light plus consistency. **`concurrency.md` and `premortem.md` follow panel-selection heuristics/overrides** (concurrency is always on for Full; premortem is never forced by Full alone). **`concurrency.md` also runs at Light when the Conditional agents rule matches.**

| Agent file | Focus in RFC context | Light | Full |
|---|---|:---:|:---:|
| `quality.md` | Logic gaps in flows and rules; incorrect assumptions; edge cases missing from §4 | yes | yes |
| `implementation.md` | Missing wiring, contract field gaps, backward compatibility holes, `(TODO: define)` that block stories; §5 missing per-endpoint JSON bodies | yes | yes |
| `security.md` | Auth gaps, PII handling, injection surfaces in proposed APIs or events | yes | yes |
| `architecture.md` | Layer violations, god-service patterns, unnecessary complexity in proposed structure | yes | yes |
| `testing.md` | §8 tests insufficient for §4 flows or §6 rules; tests that could pass with a broken design | | yes |
| `simplification.md` | Over-engineered approach for stated MVP scope | yes | yes |
| `documentation.md` | Missing doc surfaces for user-visible changes; redundant or verbose RFC prose; duplicate sources of truth; **telegraphic §4/§6/§7 bullets** that omit subjects or reuse jargon without restating behavior (two-phase agent) | yes | yes |
| `concurrency.md` | Race conditions, transactional scope, ordering gaps in proposed behavior | when matched | yes |
| `premortem.md` | Design-level failure modes; frame: "This RFC was approved, implemented, and failed in production. Why?" (all six personas); opt-in per `review-panel-selection.md` heuristics/overrides | when matched | when matched |

#### RFC consistency agent (inline; no shared file)

Review the RFC draft for internal contradictions:

1. §2 goals vs §3 scope vs §4 flows
2. §4 flows vs §5 contracts vs §6 rules
3. §5.2 event consumers vs §5.4 downstream impact
4. §8 tests vs §4 edge cases
5. Terminology vs body usage (undefined terms, conflicting names; glossary must be flat A–Z with no writer meta; supplementary tables in Addendum not Terminology)
6. Subsection headings (`####` / `#####`) vs pseudo-headings (nested `- Label:` bullets, bold paragraphs, or `Edge case:` plain lines without `#####`)
7. Bold usage (glossary term labels only in Terminology; body must not re-bold defined terms)
8. Technical Decision Notes vs chosen approach elsewhere
9. **§4 edge cases** use **Edge case: \<title\>** plus Condition / Behavior / Outcome (and Notes when needed); not one-line telegraphic bullets
10. **§4 edge cases, §6 rules, §7 metrics/alerts** restate behavior in plain language (table/column names OK); thresholds name **what** is counted and the **time window** (e.g. "3+ PARTIAL runs in rolling 24h", not "≥3 in 24h" alone)

Return `{section_anchor, issue, severity: Block/Mitigate/Monitor/Accept, fix, evidence}` with the two contradicting statements quoted.

### Conditional agents

See `review-agents/review-panel-selection.md` for canonical rules. Summary:

| Condition | Action |
|-----------|--------|
| RFC describes async, queues, `@Transactional`, or multi-threaded flows | Include `concurrency.md` at **any depth** (Light or Full; required, not optional) |
| Premortem domain signals match (`cross-service`, `auth`, `infra-config`, `rollout`, `concurrency`, `new-public-api`) or user says `include premortem` | Include `premortem.md` at **any depth** (Full does not force it) |
| RFC is trivial config or documentation-only (see skip rules) | Skip entire Step 2 |
| User says "skip review" | Skip Step 2 |
| User says "full review" | Use **Full** depth |

### Staging review file format

Write under `{reviews_dir}/` using naming rules from `review-staging`. The staging doc uses the universal hierarchy (`## Metadata`, `## Review Statistics`, `## Findings`) plus RFC-specific finding severities (`Block` / `Mitigate` / `Monitor` / `Accept`) in **Severity** until folded into the RFC.

Minimum `## Review Statistics` content per `review-staging`: Panel (Solo/Echo columns), Counts, Deduplication groups, Discarded findings (with Pattern), Severity calibration, Triage placeholder. Each staged finding lists **Agents**, **Pattern**, and **Source** `[Prose]` / `[Premortem]` / `[Code]` when applicable.

```markdown
# RFC Review: <title>

## Metadata
- Type: RFC Review
- Date: YYYY-MM-DD
- URL or Artifact: <path or "inline draft">
- Depth: light | full
- Domains: concurrency, auth
- Findings: <staged count>
- Status: STAGED

## Review Statistics

### Panel
| Agent | Status | Raw | Solo | Echo | Relaunch |
|-------|--------|-----|------|------|----------|
| quality | complete | 2 | 1 | 1 | no |

### Counts
- Agents launched: <N>
- Agents skipped: <N>
- Raw findings (all agents): <N>
- Staged findings: <N>
- Discarded during synthesis: <N>
- Solo staged (unique agent origin): <N>
- Echo staged (multi-agent dedup): <N>

### Deduplication groups
| Staged # | Agents | Theme |
|----------|--------|-------|

### Discarded findings
| Agent | Agent severity | Pattern | Theme | Reason | Notes |
|-------|----------------|---------|-------|--------|-------|

### Severity calibration
| Staged # | Agent | Agent severity | Staged severity | Delta |
|----------|-------|----------------|-----------------|-------|

### Triage outcomes
Pending triage.

## Findings

### 1. <short title>
- **Severity**: Block | Mitigate | Monitor | Accept
- **Agent severity**: Mitigate *(omit when equal)*
- **Pattern**: quality#logic-error
- **Agents**: quality
- **Triage**: pending
- **Anchor**: §N <RFC section>
- **Source**: [Prose] | [Premortem] | [Code]

#### Comment (posted as-is when approved)
<Self-contained, suggestion-tone explanation.>

#### Analysis (not posted)
<Verification trail, fold target (§N / appendix), severity rationale.>
---
```

Dedup before folding: when two agents describe the same root issue, keep the clearest fix, record the merge in **Deduplication groups**, and discard extras with reason `duplicate` or `severity-merged`. Drop findings already addressed in the draft (`already-mitigated`).

### Severity map (fold into RFC)

| Agent severity | RFC action |
|----------------|------------|
| **Block** | Revise the cited RFC section before final output (constraints, approach, contracts) |
| **Mitigate** | Add to §8 Testing and Rollout as critical test or rollout gate |
| **Monitor** | Add to §7 Operability as metric, log note, or alert |
| **Accept** | Brief "Accepted Risks" appendix subsection (max 3 bullets) |

**Skip Step 2 when:**
- The RFC is a trivial configuration change or documentation-only tweak
- User explicitly requests skipping review

**Harness regression:** Read `references/eval-cases.md` when auditing this skill or after a Step 2 gate failure.

---

## Step 3 – Finalize

1. Apply severity map revisions to the RFC draft.
2. Re-scan Terminology for terms introduced during revisions.
3. Run the editing checklist in `references/rfc-sections.md` when modifying an existing file.
4. Present **Markdown RFC only** to the user (no generation-time reasoning, no meta commentary).
5. Print to console: staging review path, counts folded (Block/Mitigate/Monitor/Accept), partial-review flag if applicable, and one-line readiness note.

---

## Final Output Contract

- Output Markdown only.
- Follow the RFC structure exactly (Sections 1–8).
- Succinct, actionable, implementation-ready to the level achievable from inputs.
- No filler, no generic best practices, no compliance assumptions unless explicitly in inputs.
- Respect the hard gates:
  - Step 0 (input collection only)
  - Step 0.1 (assumptions and coverage confirmation before generation)
  - Step 2 (review pass before final RFC unless skip rule applies)

## Integration Points

### With `review-agents` skill (review pass)
Step 2 launches shared pattern catalogs from `review-agents/` plus the inline consistency agent. Execution framing, tiered depth, and severity mapping live in this skill.

### With `review-staging` skill
Consumes `review-staging` for path pattern `{reviews_dir}/YYYY-MM-DD-rfc-review-<slug>-<mode>.md`, required `## Review Statistics`, and matching `.stats.json` sidecar. Write staging before folding findings into the RFC; do not use `{tmp_dir}/rfc-review/`.

### With `premortem` skill
`premortem.md` sub-agent reads the standalone `premortem` skill for personas and process. Do not invoke the standalone premortem skill directly in the orchestrator; launch the sub-agent in the Step 2 parallel panel only when `review-panel-selection.md` heuristics or user overrides say launch (Full depth does not force premortem).

### With `review-confluence-doc` skill (redirect)
Confluence-hosted RFCs/TDDs: use `review-confluence-doc` for published-page review. This skill owns **local Markdown** authoring; it does not fetch Confluence.

### With `review-plan` skill
Implementation plans derived from an RFC use `review-plan` at execution time. This skill's Step 2 reviews the RFC design artifact, not the downstream plan.

### With `plans` skill (handoff)
After Step 3, when the user wants implementation work, offer the `plans` skill. Reference the saved RFC file path (under resolved `{rfcs_dir}`) in the plan header.

### With `grilling` skill
Use before drafting or after a first RFC draft when design choices need explicit user sign-off. Grilling resolves decisions one at a time; do not duplicate RFC body content in chat. Reference the saved RFC path once it exists.

### With `doc-hierarchy` skill (placement)
RFCs are **Layer 3** history (`{rfcs_dir}`, typically `docs/history/feature-notes/` flat). Do not file them under Layer 2 `docs/architecture/` or legacy `docs/rfcs/`. Read `doc-hierarchy` for layout rules; run **doc-hierarchy-upkeep** when the RFC changes user-visible behavior documented in Layer 1/2.

### With `agents-best-practices` skill (reference)
For harness-level questions (approval gates, tool permissions, eval strategy for RFC quality), read `agents-best-practices/references/evals.md` and `security-observability.md`. Regression cases for this harness live in `references/eval-cases.md`. This skill owns the RFC document contract; that skill owns general agent harness design.
