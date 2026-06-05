# Command: Generate Technical Design Document (TDD)
# Intent: Enforce exhaustive, explicit, implementation-grade TDD output
# Note: This command is intentionally verbose to force correctness.
#       Verbosity of the command is NOT a problem. Verbosity of the OUTPUT is.

Generate a **Technical Design Document (TDD)** in **Markdown format**.

The **output must be Markdown only**.

You must strictly follow the **original TDD Template structure and section numbering (1–11)**.
You must NOT rename, reorder, merge, omit, or add sections.

Template instructional text (e.g. “Optional”, examples, hints)
must NOT appear in the generated TDD content.

The TDD must be detailed enough that:
- backend engineers can implement without follow-up questions
- QA can derive test cases directly
- reviewers do not need to infer intent

---

## Abbreviations & Terminology (Mandatory)

At the very beginning of the document, include a section explaining
**non-trivial or domain-specific abbreviations** used in the TDD.

Rules:
- Explain abbreviations that may be ambiguous, security-sensitive, or domain-specific.
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
- One abbreviation per bullet
- One-line explanation
- No repetition elsewhere in the document

---

## Assumptions & Open Questions (Mandatory – Meta Only)

This section exists to surface **uncertainty**, not to redefine behavior.

### Purpose
- Make missing inputs and inferred decisions explicit
- Prevent hidden assumptions
- Speed up review and confirmation

### Assumptions (Meta-level ONLY)

Include here:
- Missing inputs that were inferred to proceed
- Scope decisions inferred from context
- Defaults chosen due to missing information

Rules:
- Each assumption must be short and explicit
- Mark with `(TODO: confirm)`
- Do NOT include behavioral, policy, or domain rules here
- If an assumption is reflected later in the document, it must still appear here

Examples:
- Project is backend-only (TODO: confirm)
- MVP scope excludes anonymous users (TODO: confirm)

---

### Open Questions

Include here:
- Missing decisions required for final correctness
- Items requiring stakeholder confirmation

Rules:
- Each item must be an actionable question
- Phrase as a direct question
- No speculative or rhetorical questions

Examples:
- Should UNKNOWN consent block marketing messages for all channels?
- Is tenant default consent policy configurable or global?

---

### IMPORTANT CLASSIFICATION RULE

- This section is **NOT** a substitute for Section 2 assumptions.
- Behavioral, policy, and domain constraints MUST NOT be moved here.
- All concrete rules that affect runtime behavior MUST live in:
  **2. 🎯 Objectives & Scope → Assumptions and constraints**

No assumption may be downgraded from a concrete rule into a vague summary.

---

## Step 0 – Required Inputs

The following inputs must be provided as text:
- Technical Design Document (TDD) – Template
- PRD (full text)
- High-level Architecture document (full text)
- Relevant service documentation (including subfolders)

If any required input is missing:
- Stop
- List exactly what is missing
- Ask the user to provide it

---

## Step 1 – Context Handling & Inference Policy

### Hard-context inputs (must NOT be inferred)
- TDD author / owning team

Rules:
- Must be explicitly provided
- If missing:
  - Insert a clear TODO in the document
  - Do NOT guess
  - Do NOT block generation

---

### Soft-context inputs (may be inferred, must be confirmed)
- TDD creation date
- Last updated date
- Target phase (e.g. MVP, Phase 1, GA)

Rules:
- Infer from conversation context or current date when reasonable
- Mark as `(TODO: confirm)` if not explicit
- Do NOT block generation
- Do NOT include inference explanations in the output

---

## Step 2 – Inference Rules (Global)

Inference is **allowed and expected**, but tightly controlled.

Rules:
- Inference is forbidden for:
  - ownership
  - authority
  - approvals
- Do not mix inferred and sourced facts in the same bullet
- Use TODO only when inference would be unsafe

---

## Step 3 – Completeness & Closure Rules (Global)

Any rule, restriction, or denial must also state:
- what is allowed instead, OR
- what is explicitly out of scope

No one-sided rules.
No implicit exceptions.

---

## Global Depth & Testability Rule (Mandatory)

For ALL sections of the TDD:

- Lists of items (metrics, tests, rules, APIs, risks, etc.)
  MUST be expanded with:
  - purpose
  - scope
  - observable outcome

- Single-line bullets without context are NOT sufficient
  unless explicitly allowed by section rules.

- Every listed item MUST answer at least one of:
  - What problem does this address?
  - How is correctness or failure detected?
  - Who relies on this information?

If an item cannot be expanded due to missing information:
- It MUST be listed
- AND annotated with `(TODO: define)` rather than simplified.

This rule exists to prevent checklist-style output
and enforce implementation- and operations-grade detail.

---

## Semantic Non-Collapse Rule (Global – Mandatory)

When generating or revising any section:

- Enumerated lists MUST NOT be collapsed into summary statements.
- If detail cannot be preserved due to missing source information,
  it MUST be replaced with explicit `(TODO: define)` items.
- Loss of specificity between iterations is considered a correctness error.

This rule exists to prevent semantic thinning during refinement.

---

#### Density Preservation Rule (Global – Mandatory)

A reduction in line count or subsection count is NOT permitted
unless all of the following are true:

- No enumerated capability, restriction, or exclusion is removed
- No enforcement or trust assumption becomes implicit
- No surface (API, MQ, log, storage) is dropped from enumeration

If structural compression is applied:
- The resulting text MUST be at least as explicit as before
- Any lost detail MUST be reintroduced as `(TODO: define)`

Reviewers MUST treat semantic thinning as a correctness error,
even if formatting appears cleaner.

---

## Required Fields Enforcement Rule (Global – Mandatory)

Whenever a section defines a REQUIRED structure
(e.g. metrics, tests, APIs, risks):

- ALL required fields MUST be present for EACH item.
- Partial entries are NOT allowed.

If a required field cannot be determined:
- The field MUST still be present
- And explicitly marked as `(TODO: define)`

Omitting a required field is a correctness error,
not a formatting choice.

---

## Step 4 – Project Type

Before section 1, determine the project type:
- Backend
- Frontend
- Mobile (iOS / Android)
- DevOps / Infrastructure

Rules:
- Choose the most likely based on documents
- If uncertain, choose and mark with `(TODO: confirm)`
- Do NOT include inference commentary

---

## INTERNAL VS EXTERNAL CALL PATH RULE (CRITICAL)

When describing interactions between services:

- Presence of an API Gateway in the system does NOT imply it is used
  for internal service-to-service communication.

- Internal services MUST NOT be shown calling other internal services
  via an API Gateway unless this is explicitly stated in the
  architecture documentation.

- If the architecture is silent about the network path:
  - Default to **direct internal service-to-service communication**
  - Describe it neutrally using terms such as:
    - “internal call”
    - “service-to-service call”
    - “direct internal invocation”

- API Gateways may be referenced ONLY for:
  - external-facing traffic, OR
  - explicitly documented internal enforcement points.

Network topology MUST NOT be inferred.

---

## TRACEABILITY RULES (GLOBAL)

### Definition: Major vs Minor flows

A flow is **MAJOR** if ANY of the following apply:
- Originates from a user-facing action described in the PRD
- Crosses service boundaries
- Enforces business, legal, or compliance rules
- Emits or consumes domain events
- Incorrect behavior would cause user-visible or regulatory impact

A flow is **MINOR** if ALL of the following apply:
- Internal to a single service
- Not explicitly described in the PRD
- No policy or compliance logic
- No externally consumed events
- No user-visible impact

### Traceability requirements

- MAJOR flows → traceability REQUIRED
- MINOR flows → traceability FORBIDDEN

Traceability format:
- Flow-level only
- Add a **“Source references”** subsection
- Reference PRD sections and/or architecture document or diagram names
- Do NOT add inline references per step

---

## FORCE DIFF COMPLETENESS (CRITICAL – ADDITIVE)

The generated TDD must NOT silently drop previously derivable details.

Rules:
- Compare against:
  - PRD
  - architecture documents
  - diagrams
  - earlier surfaced assumptions, rules, and questions
- If a previously derivable item is no longer valid:
  - It MUST still be listed
  - It MUST be marked as **“Outdated / Conflicts with source”**
  - A short explanation MUST be provided explaining why it no longer applies
- Do NOT remove items solely to reduce length or perceived relevance
- Loss of detail is considered an error

This applies especially to:
- Assumptions and constraints
- Open questions
- Edge cases
- Major flows

---

## Section-by-Section Requirements

### 1. 🧭 Introduction

Purpose: context and ownership only.

Must include:
- Feature name
- Goal / purpose of this document
- Link to PRD or product spec

#### Stakeholders
Rules:
- Only directly accountable roles
- MVP → minimal ownership only

Allowed:
- Product Owner
- CRM Platform Backend Engineers
- DevOps / SRE
- DBA Engineers (only if DB changes exist)

Forbidden:
- Teams listed only because they consume data
- Hypothetical or downstream teams

If unclear:
- Insert TODO
- Do NOT infer

#### Status
- Draft / In Review / Approved
- Default: Draft

#### Dates
- Created
- Last updated
- Mark with `(TODO: confirm)` if inferred

---

### 2. 🎯 Objectives & Scope

Purpose: define intent, boundaries, applicability.

Must include:
- What is included
- What is explicitly out of scope
- **Assumptions and constraints (EXHAUSTIVE)**

#### Rules for “Assumptions and constraints” (Critical)

- List **ALL concrete behavioral, policy, and domain rules**
- Each item must be:
  - specific
  - testable
  - verifiable
- Do NOT summarise or generalise
- Abstract statements are NOT allowed unless followed by concrete rules

---

#### Platforms impacted
Allowed values only:
- Backend
- Web
- Mobile (iOS)
- Mobile (Android)

Rules:
- Infrastructure is NOT a platform
- Services are NOT platforms

---

#### Systems impacted
For each system:
- Name
- Responsibility in this feature

---

#### Multi-region / multi-country
- Explicit yes or no
- If countryCode / geo config exists → yes

Forbidden here:
- APIs
- Schemas
- Implementation details

---

### 3. 📐 Functional Overview

Purpose: describe runtime behavior precisely.

Must include:
- At least one end-to-end flow
- At least one edge case with explicit behavior

#### Major flow requirements (TRACEABILITY APPLIES)

For each MAJOR flow:
- Add a **Source references** subsection
- Then describe the flow step by step

#### Edge cases (STRICT FORMAT)

Edge cases must describe **what happens**, not just scenarios.

Required format per edge case:

**Edge case: <descriptive title>**

- Condition:
  - …
- Behavior:
  - …
- Outcome:
  - …
- Notes:
  - …

Rules:
- No arrows (→)
- No shorthand
- One semantic idea per bullet
- Avoid visual noise

---

### 4. ⚙️ System Impact Overview

Purpose: structural participation map (not behavior, not deltas).

Include, in order:
- Systems or components affected
- APIs or endpoints
- Services and domains
- Frontend views or components
- Mobile flows
- Databases / queues / jobs / third-party services

Rules:
- Descriptive only
- No business logic
- No “what changed” narratives

#### Additional Rules for Section 4 – System Impact Overview (Additive)

Section 4 MUST describe not only the list of participating systems,
but also the **structural responsibilities and trust boundaries** between them.

Allowed content in this section includes:
- Which system is responsible for:
  - tenant resolution
  - authentication / authorization
  - identity resolution
- Which systems explicitly:
  - trust upstream context
  - do NOT perform authentication or tenant resolution
- High-level trust assumptions between systems
  (e.g. “trusted internal caller”, “tenant context resolved upstream”)
- Defensive guarantees that are structural in nature
  (e.g. “may defensively validate tenant ownership at DB level”)
- Separation of concerns between systems and domains

These descriptions MUST:
- Be declarative, not procedural
- Describe **who owns a responsibility**, not **how logic executes**
- Avoid conditional or step-based behavior
- Avoid edge cases and runtime branching

Explicitly FORBIDDEN in Section 4:
- Business rules
- Validation logic
- Error handling
- Conditional behavior (“if / then”)
- Edge cases
- Change descriptions (“was / now / updated”)

Guiding question for this section:
“If this system were drawn as a box-and-arrow diagram,
what responsibilities and trust assumptions must be written on the boxes and arrows?”

#### System Listing Invariant (Section 4 – Additive)

When listing systems or components in Section 4:

- Each system MUST be listed together with its responsibilities.
- Responsibilities MUST be co-located with the system they belong to.
- Flat lists of system names without responsibilities are NOT allowed.

If responsibilities are described:
- They MUST appear under the system they apply to.
- They MUST NOT be deferred to a separate subsection.

The preferred structure is:

- **System name**
  - Responsibility 1
  - Responsibility 2
  - Trust assumption (if applicable)

This rule exists to preserve architectural clarity and prevent
responsibility diffusion across subsections.

##### Trust Boundary Explicitness Rule (Section 4 – Additive)

Section 4 MUST explicitly document trust boundaries and responsibility ownership.

Statements such as:
- which service authenticates
- which service resolves tenant context
- which services trust upstream context
- which services explicitly do NOT perform auth or tenant resolution

are REQUIRED and MUST NOT be omitted or collapsed.

If trust is assumed, it MUST be stated explicitly.

---

### 5. 🧱 Detailed Technical Design

Purpose: describe implementation-level details sufficient for direct coding, testing, and review.

General Rules:
- Describe external contracts before internal logic
- Do NOT mix external contracts and internal logic in the same paragraph
- This section MUST be self-sufficient and implementation-grade

Include where applicable:
- API / endpoint design
- Data model ownership and changes
- Business logic
- Validation rules
- Error handling and error contracts
- Failure modes

Traceability:
- OPTIONAL
- Use only when a design decision is directly derived from PRD or architecture documents

---

#### Section 5 – Authoritative Requirements

Section 5 MUST enumerate concrete behaviors and constraints.  
High-level summaries or implied behavior are NOT sufficient.

---

#### API / Endpoint Design (Mandatory)

For every new, modified, inferred, or source-defined API endpoint, the TDD MUST specify:
- Full HTTP method and path
- Resource-oriented naming
- Scope of operation (tenant-level, profile-level, destination-level)
- Required identifiers in path or body
- Source of invocation
- Idempotency expectations (if applicable)

Endpoints such as `/suppress`, `/unsuppress`, `/set`, `/check`
are NOT sufficient unless scoped to a concrete resource.

If the exact path is not finalized:
- Specify the intended resource model
- Mark the path as `(TODO: confirm)`

---

#### API Completeness & Inference Rules

All APIs that are explicitly listed in source documents
or required to support documented flows MUST be listed.

- Inferred APIs MUST be marked `(Inferred)`
- Source-defined APIs MUST be marked `(Source-defined)`
- Such APIs MUST NOT be omitted due to naming or clarity issues

---

#### Data Flow Attribution (Mandatory)

For each major API or operation, explicitly state:
- Source of input data
- Assumed contextual data
- Data stores read from
- Data stores written to

---

#### Data Model Ownership and Invariants (Mandatory)

For each table or collection:
- Owning service
- Mutating operations
- Critical invariants

This subsection MUST remain distinct and MUST NOT be collapsed.

---

#### Business Logic (Mandatory)

Business logic MUST:
- Be explicit and ordered
- State precedence rules
- Avoid abstract or summary-only descriptions

---

#### Validation Rules (Mandatory)

Validation MUST be listed explicitly and independently and MUST cover:
- Identifier existence and ownership
- State-based rejections
- Enum and schema constraints
- Idempotency correctness

---

#### Error Handling and Error Contracts (Mandatory)

For each error class, specify:
- Affected operation(s)
- Triggering condition
- Error category
- Retriable vs non-retriable
- Client-visible vs internal-only
- HTTP status or transport signal

---

#### Failure Modes (Mandatory when applicable)

List:
- Partial failures
- Retry and deduplication behavior
- Consistency impact
- Recovery or compensating actions

---

#### Subsection Preservation Rule (Critical)

The following conceptual blocks MUST remain distinct:
- API / Endpoint Design
- Data Flow Attribution
- Data Model Ownership and Invariants
- Business Logic
- Validation
- Error Handling
- Failure Modes

---

#### Section 5 – Depth Tiering Rule (Critical)

Section 5 content MUST be organized into two depth tiers:

Tier 1 — Authoritative Implementation Requirements (MANDATORY)
- API contracts and semantics
- Data model ownership and invariants
- Business logic rules and precedence
- Validation rules
- Error contracts (codes, retriability, visibility)

Tier 2 — Operational & Failure Detail (ALLOWED, COLLAPSIBLE)
- Step-by-step algorithms
- Failure modes and recovery paths
- Caching, outbox, retry behavior
- Load and scaling considerations
- Detailed channel workflows

Tier 2 content:
- MUST be explicitly labeled with subheaders
- MUST NOT redefine or contradict Tier 1
- MAY be collapsed or summarized in reviews, but MUST exist in the source

If Tier 2 content is omitted in a generated output:
- A placeholder summary + reference MUST remain
- Content MUST NOT be silently dropped

---

#### Section 5 – Navigability Rule (Additive)

If Section 5 exceeds ~300 lines:
- Major subsections MUST be anchorable and skimmable
- Each subsection MUST begin with a 1–2 line intent summary
- Long step-based logic MUST be under explicit subheaders

---

### Section 6 – Security & Privacy (Authoritative Rules)

Section 6 MUST be implementation-grade.
High-level assurances, summaries, or generic statements are NOT sufficient.

Every subsection MUST enumerate concrete responsibilities, guarantees,
and explicit exclusions.

If the feature introduces **no new security or privacy behavior**:
- This MUST be stated explicitly
- AND all subsections below MUST still be completed
  (answers such as “no change” are acceptable only when explicit)

---

### Required Subsections and Checklists

#### Data Access & Permissions

MUST explicitly enumerate:
- Each calling system and its allowed operations
  (read / write, by data category: profiles, consent, suppressions)
- Operations that are explicitly forbidden per caller
- Tenant isolation model and trust assumptions
- What access control is NOT enforced by this service

Summary statements such as “trusted internal services” are insufficient
unless backed by explicit allowed/forbidden operations.

---

#### PII Handling

MUST explicitly enumerate:
- Fields considered PII
- Where PII is stored
- Whether PII appears in:
  - API responses
  - domain events
  - message queues
  - logs
- Encryption scope:
  - at rest (field / table / platform)
  - in transit
- Redaction or masking rules
- Operations that read or write PII

If no new PII handling is introduced:
- State this explicitly
- Still list all PII touched by this feature

---

#### Compliance & Legal Considerations

MUST explicitly enumerate:
- Applicable compliance regimes (e.g. GDPR, local regulations)
- Supported user rights in this phase
- Explicitly unsupported rights (with scope or phase)
- Data retention and deletion posture
- How soft delete interacts with audit or legal obligations

If compliance is handled outside this service:
- Name the owning system or policy
- State the assumption explicitly

---

#### Audit Logging

MUST explicitly enumerate:
- Which operations generate audit records
- Which operations are explicitly excluded
- Whether failed operations are audited
- Fields captured per audit record
- Where audit logs are stored
- Immutability guarantees
- Who can access audit logs

Generic statements such as “audit logs exist” are NOT sufficient.

---

#### Enforcement Explicitness Rule (Section 6 – Additive)

Whenever an operation is marked as **Forbidden**:

- The enforcement mechanism MUST be stated explicitly
  (e.g. network isolation, DB credentials, service ownership).
- Policy-only statements without enforcement details are NOT sufficient.

---

#### Configuration Ambiguity Rule (Section 6 – Additive)

Statements containing conditional behavior such as:
- "if configured"
- "optionally"
- "may be enabled"

MUST explicitly state:
- where the configuration lives
- who owns it
- its scope (global / tenant / channel)

If unknown, mark `(TODO: confirm)` explicitly.

---

### 7. 📊 Observability & Metrics

Purpose: ensure the system is operable, debuggable, and observable in production.

#### Mandatory Structure

Section 7 MUST be divided into:

- Operational Metrics
- Business Metrics
- Events & Logs
- Alerts & Thresholds
- Explicit Non-Metrics

Each subsection MUST be present.

---

### Operational Metrics (Mandatory)

For EACH operational metric, specify:

- Metric name
- Metric type:
  - counter / gauge / histogram / timer
- Emission point:
  - which service
  - which operation or code path
- Dimensions / labels:
  - e.g. tenant_id, channel, purpose, result
- Purpose:
  - debugging / alerting / capacity planning
- Expected baseline or range (if known)
- What action is taken if the metric is abnormal

Example format:

- `consent_check_latency_ms`
  - Type: histogram
  - Emitted by: User Platform Service
  - Emission point: consent decision evaluation
  - Labels: channel, purpose, result
  - Purpose: detect latency regressions
  - Alert: p95 > 200ms for 5 minutes

---

### Business Metrics (Mandatory)

For EACH business metric, specify:

- Metric definition
- Source of truth (which event or store)
- Aggregation window
- Dimensions (e.g. channel, country)
- Business question it answers
- Known limitations or interpretation caveats

Avoid vanity metrics.

---

### Events & Logs (Mandatory)

Specify:

- Which domain events are emitted
- For each event:
  - Trigger condition
  - Payload scope (PII or non-PII)
  - Primary consumers
- Which operations MUST be logged
- Which MUST NOT be logged

---

### Alerts & Thresholds (Mandatory)

Specify:

- Which conditions trigger alerts
- Severity level (warning / critical)
- On-call or owning team
- Known false-positive risks

Generic “alerts exist” statements are NOT sufficient.

---

### Explicit Non-Metrics (Mandatory)

Explicitly list:

- Metrics that are intentionally NOT collected
- Reason for exclusion (cost, noise, handled elsewhere)

This prevents accidental observability gaps.

---

#### Metric Completeness Gate (Section 7 – Mandatory)

An operational or business metric entry is INVALID unless it includes:

- Name
- Type
- Emission point
- Labels / dimensions
- Purpose
- Baseline or SLO (or `(TODO: define)`)
- Action or consumer

Metrics missing ANY of the above MUST be expanded
or explicitly marked `(TODO: define)`.

Single-line or two-line metric entries are NOT allowed.

---

#### Metric Ownership & Actionability Rule (Section 7 – Mandatory)

For EACH metric listed:

- An owning team MUST be specified.
- A concrete action or investigation path MUST be stated
  when the metric is abnormal.

Metrics without an owner or action are NOT valid.

---

#### Event Delivery Semantics Rule (Section 7 – Mandatory)

For EACH domain event emitted:

- Delivery semantics MUST be specified:
  - at-least-once / at-most-once / exactly-once
- Ordering guarantees MUST be stated if applicable
  (e.g. per profile_id, none).

If unknown, mark `(TODO: define)`.

---

#### Logging & Sampling Rule (Section 7 – Additive)

Whenever logs are mentioned:

- Sampling policy MUST be stated
  (e.g. always, sampled, error-only).
- Explicitly state what is NEVER logged.

Silence on sampling implies ambiguity and is not allowed.

---

### 8. 🧪 Testing Strategy

Purpose: define how correctness, safety, and regressions are prevented.

#### Mandatory Structure

Section 8 MUST be divided into:

- Test Scope Overview
- Unit Tests
- Integration Tests
- Contract / API Tests
- Negative & Edge Case Tests
- Explicitly Out-of-Scope Tests

Each subsection MUST be present.

---

### Test Scope Overview (Mandatory)

Specify:

- What correctness means for this feature
- Which risks are most critical to test
- Which assumptions from Section 2 are covered by tests

---

### Unit Tests (Mandatory)

For EACH category of unit test:

- Component under test
- Input conditions
- Expected outcome
- Failure conditions
- Determinism guarantees (e.g. idempotency, merge rules)

Example:

- Consent decision engine
  - Input: UNKNOWN consent, MARKETING purpose
  - Expectation: DENY
  - Assertion: correct decision + reason code

---

### Integration Tests (Mandatory)

For EACH integration test:

- Participating services
- Triggering action
- Expected cross-service behavior
- Persistence or event side effects

Avoid generic statements like “integration works”.

---

### Contract / API Tests (Mandatory if APIs exist)

Specify:

- Which APIs are contract-tested
- Which consumers rely on the contract
- Backward compatibility guarantees
- Versioning expectations

---

### Negative & Edge Case Tests (Mandatory)

Edge cases listed in Section 3 MUST be referenced here.

For EACH edge case test:

- Scenario
- Trigger
- Expected system behavior
- Assertion criteria

---

### Explicitly Out-of-Scope Tests (Mandatory)

List tests that are intentionally NOT included, e.g.:

- Load testing
- Chaos testing
- Cross-region failover

Include reason and owning team if handled elsewhere.

This prevents false assumptions about coverage.

---

#### Test Case Explicitness Gate (Section 8 – Mandatory)

A test entry is INVALID unless it specifies:

- Component or service under test
- Triggering input or scenario
- Expected behavior
- Assertion criteria (what is verified)
- Failure condition (what would make the test fail)

Statements of intent (e.g. “ensure X works”)
are NOT sufficient.

Each test must be concrete enough
that a QA engineer could implement it without follow-up.

---

#### Test Traceability Rule (Section 8 – Mandatory)

Each test category MUST explicitly reference at least one of:
- a flow from Section 3
- an assumption or constraint from Section 2
- a risk from Section 9

Tests without traceability are considered insufficient.

---

#### Test Determinism Rule (Section 8 – Additive)

For tests involving merges, idempotency, or suppression:

- Deterministic outcome MUST be stated explicitly.
- Acceptable nondeterminism (if any) MUST be justified.

This rule exists to prevent flaky or underspecified tests.

---

### 9. ⚖️ Risks, Trade-offs & Limitations

Rules:
- For each risk:
  - state whether it is accepted or mitigated
  - explain why
- Tie trade-offs to scope (e.g. MVP decisions)

---

### 10. 📅 Timeline & Milestones

Rules:
- Include only if data exists
- If omitted, explicitly state:
  - handled elsewhere, or
  - intentionally undefined at this stage

---

### 11. 📌 Appendix

Rules:
- Reference material only
- Diagrams, schemas, links, glossary
- No new design decisions

---

## Output Formatting Rules (Output Only – Do NOT Simplify Command)

These rules apply **only to the generated TDD output**.

### General
- No generation-time meta, reasoning, or attribution
- Use `(TODO: confirm)` only when confirmation is required
- Output must be readable and human-oriented

---

## Final Output Contract

Produce:
- A complete TDD in Markdown
- With exhaustive behavioral detail
- With no summarisation loss
- With no meta leakage
- Suitable for direct implementation and review