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
- **Separate protection domains:** when a design applies similar security mechanisms at different trust boundaries, give each domain its own contract subsection with key ownership, format, lifecycle, and failure policy. Describe cross-domain interaction in a separate end-to-end flow so shared vocabulary does not imply shared keys or rotation semantics.
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

After Step 1, read `review-panel-selection.md` and launch the selected workers in parallel.

### Review depth

| Depth | When | Workers |
|-------|------|---------|
| **Light** (default) | MVP RFC, first draft | Focused panel with explicit selection reason |
| **Full** | User says full review, or high-impact cross-domain design | All five recommended workers |
| **Skip** | Trivial config/doc tweak, or user says "skip review" | None |

User may request **Full** explicitly; do not default to Full without a signal.

### Hard gates

1. **Launch the selected workers before revising the RFC.** Do not skip the pipeline because the draft "looks fine."
2. **Write the staging review file** under `{reviews_dir}/YYYY-MM-DD-rfc-review-<rfc-slug>-<mode_or_round>.md` and the matching `.stats.json` sidecar before folding findings into the RFC. Include `## Review Statistics` per `review-staging`.
3. **Mechanical gate (before folding findings into the RFC):** run the review-staging validator on the staging path; do not proceed to folding until the staging doc and its `.stats.json` sidecar both pass:
   ```bash
   VALIDATOR="${REVIEW_STAGING_VALIDATOR:-$HOME/.ai-playbook/scripts/validate_review_staging.py}"
   python3 "$VALIDATOR" --hard "$STAGING_PATH"
   ```
4. **Fold findings into the RFC structure** (Step 3). Do not present a separate premortem or review report in chat; print only a short summary and the staging file path.
5. **Partial review gate:** when any required worker fails after one relaunch, write staging but do not claim a full review.

### Budget (default)

- Full depth launches the recommended five-worker panel once.
- Light depth may use a focused panel with a recorded selection reason.
- Allow one relaunch per failed worker; keep the failed and replacement launches visible in statistics.
- The hard ceiling is six actual launches, including descendants and escalation.
- Apply the shared finding budget after deduplication.

### Orchestrator boundary

| Do | Do not |
|----|--------|
| Launch agents, wait, parse returns, dedup, write staging file with Review Statistics | Re-analyze the RFC inline while agents run |
| Fold accepted findings into RFC sections per severity map | Re-read source inputs to expand thin agent findings (relaunch the agent instead) |
| Spot-check a claim only when evidence is missing or contradicts a quick grep | Author full analysis the agent should have returned |

**Insufficient sub-agent output:** relaunch the responsible agent with a focused prompt ("expand finding N with quoted RFC section and concrete fix").

### Launch workers in parallel

Each agent receives:
1. Full RFC draft from Step 1
2. Original inputs from Step 0 (PRD excerpts, architecture, contracts) when available for evidence checks
3. Its assigned lens catalogs from `review-agents/`
4. The shared severity and finding-budget policy
5. **Execution framing:** review what the RFC proposes, quote evidence, report problems only, and return the shared finding fields plus `descendant_launches`.

#### Worker bundles

Use `review-panel-selection.md`:

| Worker | RFC focus |
|--------|-----------|
| `correctness-completeness` | Logic, flows, requirements, contracts, compatibility |
| `testing` | §8 coverage of §4 flows and §6 rules |
| `design-simplicity` | Architecture boundaries and avoidable complexity |
| `contract-docs` | Documentation plus RFC consistency checks below |
| `risk` | Security baseline plus signaled concurrency and premortem reasoning |

#### RFC consistency lens inside `contract-docs`

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

Return the shared finding fields with the two contradicting statements quoted.

### Conditional lenses

See `review-agents/review-panel-selection.md` for canonical rules. Summary:

| Condition | Action |
|-----------|--------|
| RFC describes async, queues, `@Transactional`, or multi-threaded flows | Load `concurrency.md` in `risk` |
| Premortem signals match or user says `include premortem` | Load `premortem.md` in `risk`; personas remain reasoning sections |
| RFC is trivial config or documentation-only (see skip rules) | Skip entire Step 2 |
| User says "skip review" | Skip Step 2 |
| User says "full review" | Use **Full** depth |

### Staging review file format

Write under `{reviews_dir}/` using the universal `review-staging` hierarchy and shared severities.

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
| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| correctness-completeness | quality, implementation | none | complete | 2 | 1 | 1 | no |

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
- **Pattern**: quality#logic-error
- **Workers**: correctness-completeness
- **Triage**: pending
- **Anchor**: §N <RFC section>
- **Source**: [Prose] | [Premortem] | [Code]

#### Comment (posted as-is when approved)
<Self-contained, suggestion-tone explanation.>

#### Analysis (not posted)
<Verification trail, fold target (§N / appendix), severity rationale.>

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

Dedup before folding: when two agents describe the same root issue, keep the clearest fix, record the merge in **Deduplication groups**, and discard extras with reason `duplicate` or `severity-merged`. Drop findings already addressed in the draft (`already-mitigated`).

### Fold into RFC

| Finding | RFC action |
|----------------|------------|
| `blocking: true` | Revise the cited RFC section before final output |
| Non-blocking behavioral risk | Add the concrete safeguard to §8 Testing and Rollout |
| Operability risk | Add the concrete metric, log, or alert to §7 |
| Accepted residual risk | Add a brief Accepted Risks item |

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
5. Print to console: staging review path, counts by shared severity, partial-review flag if applicable, and one-line readiness note.

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
Step 2 launches the five worker bundles from `review-panel-selection.md`; `contract-docs` includes the RFC consistency lens.

### With `review-staging` skill
Consumes `review-staging` for path pattern `{reviews_dir}/YYYY-MM-DD-rfc-review-<slug>-<mode>.md`, required `## Review Statistics`, and matching `.stats.json` sidecar. Write staging before folding findings into the RFC; do not use `{tmp_dir}/rfc-review/`. A `--hard` validator gate runs over the staging path before findings are folded into the RFC.

### With `premortem` skill
The `risk` worker reads the premortem catalog when signals match and applies personas as internal reasoning sections without child launches.

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
