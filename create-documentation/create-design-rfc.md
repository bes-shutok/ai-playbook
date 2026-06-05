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
- Until the user gives an explicit “go ahead” signal, you MUST NOT generate any part of the RFC (no section drafts, no outlines, no partials).
- In this mode, you may ONLY:
  - list what inputs are missing
  - ask targeted questions to obtain missing details
  - request specific missing excerpts ONLY if they are not present in CLI/context arguments and cannot be found in the repo 
  - restate what was received in a short inventory (no interpretation)

Proceed signal:
- Only start generating the RFC after the user explicitly indicates readiness, e.g. “OK, proceed”, “Go ahead”, or “Generate the RFC”.

---

## Step 0.1 – Assumptions & Coverage Confirmation (Hard Gate)

After all inputs are provided (but before generating the RFC), produce an **Assumptions & Coverage** checklist for user confirmation.

The checklist MUST include:
- In-scope surfaces for THIS RFC:
  - Backend / Frontend / Mobile (iOS) / Mobile (Android) / DevOps-Infrastructure
- MVP scope boundaries:
  - explicitly in MVP
  - explicitly deferred (if stated)
- Which RFC sections will be present with real content vs “Not applicable for MVP”
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

Keep this section compact.

---

### 2. Problem, Goals, Non-goals
Purpose: clarify why we are doing this, what success means, and what we are NOT doing.

Rules:
- Goals must be specific and testable where possible.
- Non-goals must reflect explicit MVP deferrals or clear boundaries from inputs.
- Only include non-obvious items. Do NOT restate generic service responsibilities.
- If there are no meaningful non-goals from the inputs, omit the Non-goals sub-section entirely. Do NOT write placeholder text such as "None" or generic deferrals.

Must include:
- Problem statement (1–3 bullets)
- Goals (3–7 bullets)
- Non-goals (only when meaningful deferrals or out-of-scope decisions exist; omit otherwise)

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
- No generic “standard errors” statements.
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

---

### 6. Business Logic Rules
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
- If no rollout info exists in inputs:
  - state `(TODO: define rollout plan)` only if needed for MVP delivery.

---

## Final Output Contract

- Output Markdown only.
- Follow the RFC structure exactly (Sections 1–8).
- Succinct, actionable, implementation-ready to the level achievable from inputs.
- No filler, no generic best practices, no compliance assumptions unless explicitly in inputs.
- Respect the two hard gates:
  - Step 0 (input collection only)
  - Step 0.1 (assumptions & coverage confirmation before generation)
