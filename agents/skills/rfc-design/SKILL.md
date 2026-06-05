---
name: rfc-design
description: >
  Manage the full RFC lifecycle: create, edit, and maintain Design RFCs in Markdown format.
  Use when the user asks to create, write, draft, edit, update, or review an RFC or feature design document.
  Creation follows a two-gate process: (1) input collection and (2) assumptions & coverage confirmation before generating any RFC sections.
  Editing follows the structural conformance rules in the "Editing an Existing RFC" section.
---

# Command: Generate MVP Design RFC (Implementation-ready, succinct)
# Intent: Produce a concise, actionable, implementation-ready RFC suitable for linking into Jira stories.
# Note: Command verbosity is acceptable. Output must be succinct and implementation-oriented.

## Core Concepts
- Hard gate: a mandatory stop point where RFC generation cannot continue without explicit user confirmation.
- Coverage checklist: a pre-generation scope contract that confirms in-scope surfaces and MVP boundaries.
- Canonical ID: the single identifier returned by resolve-style APIs for downstream composition.
- Server-owned field: state/audit field (for example `updated_at`, version) set by the service, not by client input.
- Core vs custom properties split: core cross-tenant dimensions are first-class fields; tenant-defined extensions are a flexible map.

Generate a **Design RFC** in **Markdown format**.

The **output must be Markdown only**.

The RFC must be:
- succinct and skimmable
- actionable for implementation stories (API, DB, logic)
- implementation-ready to the level achievable with the provided inputs

Do NOT include generation-time reasoning, meta commentary, or attribution.

---

## Terminology (Mandatory)

At the very beginning of the document, include a `Terminology` section that defines
the key domain concepts used throughout the RFC, including any **non-trivial or domain-specific abbreviations**.

Rules:
- Explain terms (including abbreviations) that may be ambiguous, security-sensitive, or domain-specific.
- Do NOT explain universally known technical terms.

Must be explained if used:
- RBAC, SSO, IAM, PII
- Company- or product-specific abbreviations
- Cross-domain abbreviations whose meaning is not obvious

Must NOT be explained:
- API
- HTTP / REST
- JSON / XML
- DB / SQL
- UI / UX

Format:
- Bullet list
- One term per bullet
- One-line explanation
- No repetition elsewhere in the document

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
- Every bullet must be either:
  - a requirement
  - a decision
  - a contract
  - a dependency
  - or an implementation task input
- Do NOT list obvious/generic statements unless explicitly required by provided inputs.
- Keep sections short; avoid exhaustive inventories.
- Use stable headings so Jira stories can link to specific sections.

---

## RFC Output Structure (Must Follow Exactly)

Produce the RFC with the following numbered sections, in this order.
Do NOT rename, reorder, merge, omit, or add sections.

If a section is not applicable for MVP, write only:
- `Not applicable for MVP: <one-line reason tied to scope or provided inputs>`

### 1. Header
Must include:
- RFC title (feature name)
- Owning team (if provided; otherwise `(TODO: confirm)`)
- Status: Draft / In Review / Approved (default Draft)
- Created date (infer from current date if not provided; mark `(TODO: confirm)` if inferred)
- Last updated date (same rule as created date)
- Links:
  - PRD link or identifier (or `(TODO: add link)`)
  - Architecture doc link or identifier (or `(TODO: add link)`)

Keep this section compact. The metadata table must be placed **inside** `## 1. Header` — not as a floating table above the Terminology section.

---

### 2. Problem, Goals, Non-goals
Purpose: clarify why we are doing this, what success means, and where the hard boundaries are.

Rules:
- Goals must be specific and testable where possible.
- Non-goals: only include items that are **not obvious from the Goals alone** and could plausibly be pulled into scope during planning or implementation. For each item give a one-line reason why it is excluded. Omit anything that is self-evidently out of scope. Do NOT write placeholder text such as "None" or generic deferrals.
- Non-goals must not use "this RFC scopes to `<service>`" as the reason for exclusion. An RFC is scoped to a **feature**, not a service; cross-service impact is documented in §3 and §5.4. When deferring a cross-service analysis, state the actual dependency that makes it premature (e.g. "rate depends on BO trigger-rule configuration not yet defined") rather than attributing exclusion to service ownership.

Must include:
- Problem statement (1–3 bullets)
- Goals (3–7 bullets)
- Non-goals (only when items exist that pass the above gate; omit otherwise)

---

### 3. Scope & Dependencies
Purpose: define what THIS service/team owns vs what is upstream/downstream.

Must include:
- In-scope components (owned by this team/service) with 1-line responsibility each
- Dependencies (external components THIS service requires):
  - Only list if THIS service directly depends on them
  - State what THIS service needs from them (1 line)
  - Omit owner/team unless critical to unblock implementation
- Assumptions that affect behavior (only those relevant to MVP and implementation)

Rules:
- **Do NOT list downstream consumers** - services that call THIS service or consume its events belong in documentation for those services, not here.
- **Do NOT list sibling services** unless THIS service has a direct runtime dependency on them.
- **Do NOT inventory the entire system** - only include what THIS service directly needs to function.
- Only list constraints/rules that are enforced by this service or directly required for this service to function.
- If a rule is enforced elsewhere, do NOT restate it as a requirement; record it as a dependency/assumption only if THIS service relies on it at runtime.
- Do NOT include negative-scope statements such as "X does not apply to this feature" or "X is handled elsewhere". If something is not relevant to this service, omit it — documenting its absence adds noise.

---

### 4. Functional Overview
Purpose: describe runtime behavior precisely.

Must include:
- At least one end-to-end MVP flow (step-by-step, numbered)
- Edge cases (only the important ones) using the format:

**Edge case: <title>**
- Condition:
- Behavior:
- Outcome:
- Notes:

Rules:
- Keep flows readable. No diagrams required.
- No arrows (→). No shorthand.
- Include only edge cases that impact business correctness, money, user experience, or support load.
- **Multi-flow structure**: when multiple flows share most steps, structure as a base flow covering the shared path, plus derived flows that document only their divergences. Each derived flow must open with "Flow X applies with one divergence at step N" (or "Flow X applies in full") and close with "All other steps identical to Flow X."
- **Metrics placement**: metrics that fire on the base/shared path belong in the base flow step where they fire. Do not repeat them in derived flows; derived flows document only metrics specific to their divergence (e.g. a suppression-hit counter that never fires in the base path).
- **Error propagation scope**: error propagation notes must explicitly state the unit of failure — per-message, per-thread, or per-batch — and explain the isolation boundary (e.g. "returns RECONSUME_LATER for that one message only; other consumer threads ACK their own messages independently").

---

### 5. Contracts (API, Events, Data)
Purpose: provide implementation-ready external and persistence contracts.

Include only what is in scope per confirmed coverage:
- APIs (HTTP endpoints)
- Domain events / message queues (if any)
- Database schema changes (if any)

#### 5.1 APIs
For each new or modified endpoint, include:
- Method + path
- Purpose (1 line)
- Authn/authz expectations if non-obvious and explicitly required by inputs
- Required headers ONLY if relevant (e.g. idempotency key, correlation id)
- Request body in a code fence (JSON)
- Response body in a code fence (JSON)
- Status codes (only those actually used)
- Idempotency semantics (if applicable)
- Error contract (brief): error code + when it happens

Rules:
- If an endpoint exists but details are missing, still list it and use `(TODO: define)` in the body fields.
- No generic "standard errors" statements.
- Prefer unambiguous field names (for example `consent_state` instead of ambiguous qualifiers) when terms affect decision interpretation.

#### 5.2 Events / Messaging (if applicable)
For each event/message:
- Name
- Producer
- Consumers (if known)
  - **Always include this field** - it documents the integration contract and what downstream services expect from THIS service
  - List known services that subscribe to or consume this event
  - This is different from Section 3 dependencies (what THIS service requires); this documents what THIS service provides to others
- When emitted
- Delivery semantics: at-least-once / at-most-once / exactly-once (or `(TODO: define)`)
- Ordering guarantee (or state none)
- Payload (code fence, JSON) with PII fields clearly marked

#### 5.3 Database (if applicable)
Provide DDL for new/changed tables and indexes.

Rules:
- Use the best-fit SQL dialect if DB engine is known.
- If DB engine is unknown, use generic SQL and mark engine-specific details `(TODO: confirm)`.
- Include:
  - table definition(s)
  - primary key
  - important indexes
  - key constraints that can be determined
- Keep DDL minimal but sufficient for implementation stories.

**When there are no schema changes, do not limit the section to "no schema changes."** Instead document the hot-path read queries that fire per event:
- Include the full query (SQL or equivalent).
- Name the covering index; note whether its leading column matches the most selective predicate or forces a range scan with trailing filters.
- Document any in-process cache protecting the query: cache key, TTL, invalidation trigger, and worst-case miss rate.
- Explicitly call out non-hot-path queries (CRUD, admin lookups) as off-hot-path so reviewers can distinguish them.

#### 5.4 Downstream Service Impact (if applicable)
When the RFC involves publishing events or messages that a downstream service consumes (e.g. triggering a notification pipeline, a scheduling service, or a downstream processor), include a section documenting:
- Which consumer/handler in the downstream service receives the message and how it routes the payload.
- The immediate-processing path vs any deferred/scheduled path (e.g. `delay = 0` → direct dispatch vs `delay > 0` → scheduled record written to a DB table polled by a cron/scheduler).
- Volume impact on the downstream service relative to today (increased / decreased / unchanged), broken down per message type or activity if they differ.
- **RFC-owned operational deliverables**: if the feature requires a BO operator to create configuration records, templates, or flags in a downstream service before activation (e.g. a `t_notification_setting` row, a template record), treat these as tracked RFC deliverables — not "prerequisites another team owns". Document them here with the full BO → management → service call chain if applicable (never reference internal `/inner/` endpoints for operator-facing steps), state what error occurs if the records are absent (error type, retry behavior), and track them in §8 Rollout phases.
- Clearly distinguish: (a) **source-code changes** in the downstream service (developer work, scoped to this RFC if needed) vs (b) **BO/operator configuration actions** (no code change, but still RFC-scoped deliverables). A statement "no code changes needed in service X" is incomplete when BO setup actions are also required.


Purpose: define implementation behavior and precedence.

Must include:
- Ordered rules (numbered) that define:
  - decision logic
  - precedence (what wins when conflicts happen)
  - idempotency/dedup behavior (if applicable)
- For each rule:
  - trigger/inputs (1 line)
  - behavior (1–3 bullets)
  - output/effect (1 line)

Rules:
- Only include rules that matter for correctness (money, identity, eligibility, state transitions).
- Avoid repeating functional flow steps; focus on rules/decisions.

---

### 7. Operability (Metrics, Logs, Alerts)
Purpose: minimum viable observability for MVP.

Must include:
- 4–5 metrics total (operational + business mixed), each with:
  - name
  - type (counter/gauge/histogram/timer)
  - emitted by (service + operation)
  - labels (max 4)
  - what to do when abnormal (1 line)
- Key logs (only if non-obvious):
  - what is logged
  - what is NEVER logged (PII safety if relevant)
- Alerts (only if clearly justified by MVP risk):
  - condition
  - severity
  - owning/on-call team (or `(TODO: confirm)`)

Rules:
- Do NOT create long SLO/SLA theory. Keep it operational.
- If nothing meaningful is stated in inputs, write:
  - `Not applicable for MVP: observability handled elsewhere` (only if supported by inputs) OR
  - provide minimal metrics anyway (preferred).

---

### 8. Testing & Rollout
Purpose: only the critical tests and rollout steps that prevent expensive failures.

Must include:
- Critical tests (max ~10 bullets unless inputs demand more), focused on:
  - edge/marginal business cases
  - idempotency/dedup (if applicable)
  - failure modes that cause user-visible or financial impact
- For each test bullet:
  - scenario/trigger
  - expected behavior
  - assertion (what is checked)

Rollout:
- If there are migrations, flags, or backfills, list:
  - steps (numbered)
  - rollback plan (1–3 bullets)
- When the implementation is intentionally split into deployable phases, add a short phase-separation subsection in §8 before the rollout steps. For each phase include: scope, dependency on earlier phases, and whether it is a safe ship boundary on its own.
- When a feature adds **net-new volume** to a downstream service (previously 0 or near-0, now potentially high), add an explicit capacity review gate in the rollout plan before the trigger goes live. A feature that *reduces* volume (e.g. via suppression) does not need this gate. State which service, what the volume change is, and why it is new.
- If no rollout info exists in inputs:
  - state `(TODO: define rollout plan)` only if needed for MVP delivery.

---

## Technical Decision Notes (Non-obvious Choices)

When the RFC makes a non-obvious implementation choice where multiple approaches exist and constraints drive the selection, document it as a named subsection within the relevant RFC section (e.g., "Concurrency Design Note", "Cache Strategy Note"). Structure it as:

1. **Constraints** (non-negotiable inputs that bound the option space — label C1, C2, …)
2. **Options considered** — comparison table with each constraint as a column; mark ✅ / ❌ per cell
3. **Elimination trail** — one sentence per eliminated option explaining which constraint it violates
4. **Recommendation** — state the chosen option and the decision trail: a numbered sequence that maps each constraint to the option's property that satisfies it
5. **Reversibility note** — one sentence per constraint: which input would need to change to make a previously eliminated option viable again

Rules:
- The decision trail must be written so a reader who did not attend the discussion can independently verify or challenge the choice using only the RFC.
- Keep constraints concrete and verifiable (e.g., "`handleMessage()` throws → retry; any early return = silent ack" not "correctness concerns").
- Do NOT list options that were never seriously considered. Only include options that would be valid if one or more constraints were relaxed.
- Place the note in the section closest to the implementation detail it justifies — typically Section 3 (Core Concepts/Assumptions) for cross-cutting decisions, or Section 4 (Functional Overview) for flow-specific ones.
- **Subsection-local terms**: when a Technical Decision Note (or similar analytical subsection) introduces local variables (e.g. N), notation shorthands (e.g. ~10 ms), or abbreviated concepts not defined in the global Terminology, add a "Terms used in this section" table immediately after the subsection heading, before the Constraints block. One row per term; columns: Term | Meaning.
- **Dimension-specific variable naming**: when an analytical subsection discusses more than one related boundary or cardinality (for example activity-level fan-out vs per-user + task concurrency), do not use a bare single-letter variable like `N` as the primary term. Name the variable after the counted dimension (`fanOut`, `matchedRules`, `distinctTasks`) and state the other boundaries explicitly so the formula cannot be misread as applying to the wrong scope.
- **Formula clarity**: mathematical formulas with ambiguous operator precedence must use explicit parentheses (e.g. `1 000 ms / (N × 10 ms)`, not `1 000 ms / N × 10 ms`).
- **PROD verification query for unbounded/configurable variables**: when a constraint documents a variable that is BO-configurable or unbounded at runtime (e.g. "N rules per activity, no code gate"), include a PROD-runnable SQL query immediately below the constraint so engineers can verify the real current value without digging through the codebase. The query must mirror the exact WHERE clause the application uses (same predicates, evaluated at `NOW()`), group by the dimension being counted, and order by count descending so the maximum is the first row. Always qualify table names with the database name (e.g. `afbet_crm.t_crm_user_activity_trigger`).
- **Zero-row observations**: if the verification query returns zero rows or the inspected table is empty, record that as a point-in-time environment observation only. Do not present it as proof of an upper bound, intended limit, or enforced invariant; pair it with product/source clarification if the design still needs a target boundary.

---

## Editing an Existing RFC

When modifying an existing RFC document (adding sections, updating decisions, restructuring content), apply the same structural contract as creation. Do **not** skip this because the skill was not explicitly invoked for the edit.

### Checklist before committing any RFC change

1. **Section order** — Sections must remain Terminology → 1 Header → 2 Problem/Goals → 3 Scope & Dependencies → 4 Functional Overview → 5 Contracts → 6 Business Logic Rules → 7 Operability → 8 Testing & Rollout → Appendix(es). Do not add, rename, reorder, merge, or omit numbered sections.

2. **Placement of new content** — Place new content in the section closest to the detail it justifies:
   - Cross-cutting decisions → Section 3 (Scope & Dependencies)
   - Flow-specific decisions → Section 4 (Functional Overview)
   - Closed decisions (no open alternatives) → inline rationale in the relevant section or a named appendix subsection; do NOT present them as open option comparisons.

3. **Technical Decision Notes** — Any non-obvious technical choice added or substantially revised must follow the full structure defined in §Technical Decision Notes: Constraints → Options table (constraints as columns) → Elimination trail (one sentence per eliminated option) → Recommendation with decision trail → Reversibility note (one sentence per constraint). Partial structures (e.g. recommendation without elimination trail, or options table without reversibility note) are not compliant.

4. **Closed decisions** — When a decision has been made, collapse any options-comparison content to a single named subsection containing: the decision, who made it, when, and the rationale. Remove pros/cons tables for eliminated options; they add noise to a reader trying to understand what will be built.

5. **Terminology** — Any new term introduced in the edit must be defined in the `## Terminology` section. Do not define terms inline in the body for the first time. Exception: subsection-local variables and shorthands used only within a single analytical subsection (e.g. a Technical Decision Note) may be defined in a "Terms used in this section" table at the top of that subsection instead.

6. **Process-tense labels** — Do not use labels that were only meaningful during the review/drafting stage. Replace "(current)" with "(existing)" or "(pre-RFC)", remove "(new)" from stable flow/section headings, and avoid "Refactored" in stable section titles. Use stable descriptive names that remain accurate after the RFC is implemented.

7. **Open question resolution propagation** — When resolving an RFC open question (changing status from "defer" or "open" to decided), grep the entire document for all references to the old state — assumptions, edge cases, flow descriptions, rules, and inline mentions. Update every reference in the same changeset. A resolved question with stale references elsewhere in the RFC is worse than an open question because it creates contradictions.

## Skill Ownership for RFC Lessons

When a lesson changes RFC authoring workflow, section content requirements, or review-checklist expectations:
- update this `rfc-design` skill at the relevant section
- update `docs/examples/` only when an example/playbook is needed to illustrate the rule
- do not treat editing an individual module RFC as the primary fix unless the underlying skill rule is already correct

---

## Premortem Gate (Before Final Output)

After drafting all RFC sections but before presenting the final document, run a premortem
using the `premortem` skill with all six personas:

1. Frame: "This RFC was approved, implemented, and the feature failed in production. Why?"
2. Run full persona analysis (cap at 2-3 findings per persona)
3. Incorporate results:
   - **Block** findings → revise the relevant RFC section (add constraints, change approach, add rollback steps)
   - **Mitigate** findings → add to §8 Testing & Rollout as critical test cases or rollout gates
   - **Monitor** findings → add to §7 Operability as metrics or alerts
   - **Accept** findings → document in a brief "Accepted Risks" appendix subsection (max 3 bullets)
4. Do not present the premortem output separately — fold it into the RFC structure

**Skip premortem when:**
- The RFC is a trivial configuration change or documentation-only
- User explicitly requests skipping it

---

## Final Output Contract

- Output Markdown only.
- Follow the RFC structure exactly (Sections 1–8).
- Succinct, actionable, implementation-ready to the level achievable from inputs.
- No filler, no generic best practices, no compliance assumptions unless explicitly in inputs.
- Respect the two hard gates:
  - Step 0 (input collection only)
  - Step 0.1 (assumptions & coverage confirmation before generation)
