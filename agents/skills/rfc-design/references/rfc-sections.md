# RFC Section Template and Editing Rules

Read this file when drafting or editing RFC sections (Step 1 and substantial edits).

## Document order (must follow exactly)

1. `# Terminology` (or `# Dictionary`)  -  **only** content before numbered sections
2. `### 1. Header` through `### 8. Testing & Rollout`
3. Optional `### Addendum A.` … (supplementary matrices, naming notes; not glossary entries)

Do not place catalog tables, operator matrices, or writer instructions in Terminology. See **Terminology** rules in `SKILL.md`.

## Heading levels

| Markdown | Role |
|----------|------|
| `# Terminology` | Reader glossary at document top |
| `### N. Title` | Main sections 1–8 and Addendum |
| `#### Title` | Subsections (Problem statement, Goals, In-scope, Contract notes, …) |
| `##### METHOD /path` | Per-endpoint or per-event contract examples under §5 |

**Subsection formatting (required):** Use `#### Subsection title`, blank line, then content. Forbidden as subsection headers:

- Nested list labels: `- Problem statement:` with indented child bullets
- Bold inline labels: `Goals:` followed by bullets on the same or next lines
- Bold paragraphs used instead of headings

**Bold (required):** Only glossary term labels in `# Terminology`. §1–8 and Addendum use headings and backticks, not bold emphasis.

Applies to §2 (Problem statement, Goals, Non-goals), §3 (In-scope, Dependencies, Assumptions), §4 (flow titles and `#####` edge-case titles), §5 (Contract notes, Authority, Topic, …), §7 (Alerts), §8 (Critical tests, Phases, Accepted risks), and Addendum subsections.

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

Keep this section compact. Metadata bullets live under `### 1. Header`; use `####` for sub-blocks such as **Scope of this document** when they need visual separation from the link list.

---

### 2. Problem, Goals, Non-goals
Purpose: clarify why we are doing this, what success means, and where the hard boundaries are.

Structure: use **`#### Problem statement`**, **`#### Goals`**, **`#### Non-goals`** (each followed by a blank line, then bullets). Do not nest these as list item labels.

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

Structure: use **`#### In-scope`**, **`#### Dependencies`**, **`#### Assumptions`** (and additional `####` blocks for cross-cutting notes such as storage boundaries). Blank line after each heading before bullets.

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
- Do NOT include negative-scope statements such as "X does not apply to this feature" or "X is handled elsewhere". If something is not relevant to this service, omit it; documenting its absence adds noise.

---

### 4. Functional Overview
Purpose: describe runtime behavior precisely.

Must include:
- At least one end-to-end MVP flow (step-by-step, numbered)
- Edge cases (only the important ones) using the format:

**Edge case: \<title\>**

- Condition:
- Behavior:
- Outcome:
- Notes: (optional; use for accepted lag, decision refs, or pointers to §7)

Rules:
- Keep flows readable. Numbered steps remain normative; any diagrams are visual aids, not a substitute for the numbered steps.
- Diagrams (required when applicable): add a fenced Mermaid `flowchart` or `sequenceDiagram` when **any** of these hold:
  - a §4 flow has three or more decision branches, **or**
  - concurrent actors race on shared state (for example two app instances plus an external service contending for a lock), **or**
  - a cross-trust-boundary handoff that readers routinely mis-order (for example initialize → release → remote call → re-lock with winner/loser branches), **or**
  - the design includes an API gateway and/or platform authorization (or equivalent edge-auth) hop with encrypted client or service traffic: add one diagram that shows expected encrypted communication directions (who encrypts, who decrypts, which hops carry ciphertext vs cleartext inside a trust zone). Prefer §3 when it is a static trust map; prefer §4 when it is one request lifecycle.
- Cap the RFC at the three to five highest-value diagrams (the encrypted-direction map counts toward the cap). Do not diagram every linear happy path.
- Do not put secrets, sample ciphertext, or real credentials in diagrams.
- Mermaid `sequenceDiagram` message text must not contain `;` (it ends the statement and leaves the next line as a parse error). Use a comma, or put multi-line text in quotes with `\n`. Semicolons inside quoted `flowchart` node labels are fine.
- If no trigger applies, state one line under §3 Assumptions: `No workflow diagrams: all §4 flows are linear single-actor paths and no encrypted edge-auth hop is in scope.`
- No arrows (→) in prose. No shorthand. (Arrows inside a fenced Mermaid diagram are fine.)
- **Edge cases must be readable standalone:** each field is one or more complete sentences. Do not use telegraphic clause chains (`do X; alert if ≥3 in 24h`) or jargon-only bullets that assume Terminology was read first. Name tables/columns when they disambiguate (e.g. `segment_batch_watermark.last_processed_at`).
- Include only edge cases that impact business correctness, money, user experience, or support load.
- **Multi-flow structure**: when multiple flows share most steps, structure as a base flow covering the shared path, plus derived flows that document only their divergences. Each derived flow must open with "Flow X applies with one divergence at step N" (or "Flow X applies in full") and close with "All other steps identical to Flow X."
- **Metrics placement**: metrics that fire on the base/shared path belong in the base flow step where they fire. Do not repeat them in derived flows; derived flows document only metrics specific to their divergence (e.g. a suppression-hit counter that never fires in the base path).
- **Error propagation scope**: error propagation notes must explicitly state the unit of failure; per-message, per-thread, or per-batch; and explain the isolation boundary (e.g. "returns RECONSUME_LATER for that one message only; other consumer threads ACK their own messages independently").

---

### 5. Contracts (API, Events, Data)
Purpose: provide **implementation-ready** external and persistence contracts. This section is blueprint-first: concrete JSON/SQL examples carry the contract; prose only annotates them.

**Minimum detail bar:** `contract-blueprint-example.md` in this directory. Match that depth for every in-scope API, event, and persistence surface. When the repo already has RFCs under `{rfcs_dir}`, read one as a style reference before drafting §5 (do not copy employer-specific values into new RFCs).

Include only what is in scope per confirmed coverage:
- APIs (HTTP endpoints)
- Domain events / message queues (if any)
- Database schema changes (if any)

#### 5.1 APIs

**Blueprint-first rule:** A paragraph describing an API is not a contract. Each in-scope endpoint must appear in **§5.1.1 Example request / response bodies** with fenced JSON (or `Request body: none` for bodyless reads). Error responses with domain `code` values belong in §5 when they affect implementation or tests.

**Required structure (in order):**

1. **Endpoint inventory:** table with columns `Method`, `Path`, `Priority`, `Description` for every in-scope endpoint. One row per HTTP method (do not combine `POST` and `PATCH` on one row). The Description cell is the OpenAPI `summary` source (one short sentence).
2. **MVP priority labels** (when multiple endpoints): `Must` / `Optional` / `Later` in the inventory table.
3. **Contract notes:** short bullets (idempotency, headers, enum constraints, conflict codes); no multi-sentence narratives where a JSON field or status code suffices.
4. **§5.1.1 Example request / response bodies:** one `##### METHOD /path` subsection per endpoint (no `(example)` suffix):
   - Repeat the inventory Description as the first prose line under the heading (OpenAPI `summary` parity).
   - Request body (JSON fence, or `none`)
   - Response body (JSON fence, happy path)
   - Error bodies for write endpoints and non-obvious failures (`4xx`/`5xx` with `code`, `message`, and relevant `details`)
   - Use realistic field names, enums, nesting, and timestamps; `(TODO: define)` only inside JSON for unknown fields, not instead of the fence

**Per-endpoint checklist (§5.1.1):**

| Item | Required when |
|------|----------------|
| Method + path in heading | Always |
| Request JSON (or `none`) | Always |
| Success response JSON | Always |
| At least one error JSON | Write endpoints; read endpoints with domain-specific `404`/`409` semantics |
| Status code on response line | When not obvious from context |
| Authn/authz, idempotency headers | Only when non-default; state in contract notes or above the fence |

Rules:
- If an endpoint exists but details are missing, still add the `#####` subsection and use `(TODO: define)` **inside** JSON fields, not as a substitute for the subsection.
- No generic "standard errors" statements without an example body.
- Prefer unambiguous field names (for example `consent_state` instead of ambiguous qualifiers) when terms affect decision interpretation.
- OpenAPI or schema links may supplement §5; they do **not** replace in-RFC JSON bodies.

#### 5.2 Events / Messaging (if applicable)

Blueprint-first: lead with a **payload JSON fence** per event, then metadata bullets.

For each event/message:
- Name (as `#####` heading)
- **Payload** (code fence, JSON) with PII fields clearly marked
- Producer
- Consumers (if known)
  - **Always include this field** - it documents the integration contract and what downstream services expect from THIS service
  - List known services that subscribe to or consume this event
  - This is different from Section 3 dependencies (what THIS service requires); this documents what THIS service provides to others
- When emitted
- Delivery semantics: at-least-once / at-most-once / exactly-once (or `(TODO: define)`)
- Ordering guarantee (or state none)

#### 5.3 Database (if applicable)

Blueprint-first: lead with **DDL** or **full hot-path SQL**, not table descriptions in prose.

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

**Less obvious tables (multi-table or async pipelines):** add three layers, not prose-only summaries:
1. **Table inventory** (`##### 5.3.0` or equivalent): one-line purpose per table, grouped by role.
2. **SQL `--` comments** on each `CREATE TABLE` and on non-obvious columns (watermarks, polymorphic FKs, catalog tokens).
3. **Column notes** after DDL: example rows and disambiguation (e.g. surrogate PK in another module vs catalog dimension in this DB).

Obvious tables (single-purpose CRUD) need only a short block comment above `CREATE TABLE`.

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
- **RFC-owned operational deliverables**: if the feature requires a BO operator to create configuration records, templates, or flags in a downstream service before activation (e.g. a `t_notification_setting` row, a template record), treat these as tracked RFC deliverables; not "prerequisites another team owns". Document them here with the full BO → management → service call chain if applicable (never reference internal `/inner/` endpoints for operator-facing steps), state what error occurs if the records are absent (error type, retry behavior), and track them in §8 Rollout phases.
- Clearly distinguish: (a) **source-code changes** in the downstream service (developer work, scoped to this RFC if needed) vs (b) **BO/operator configuration actions** (no code change, but still RFC-scoped deliverables). A statement "no code changes needed in service X" is incomplete when BO setup actions are also required.

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
- **"When abnormal" must be self-explanatory:** name the counted signal, threshold, and time window (e.g. "page on-call when PARTIAL run count ≥ 3 in rolling 24h"), not bare thresholds (`≥3 in 24h`).
- If nothing meaningful is stated in inputs, write:
  - `Not applicable for MVP: observability handled elsewhere` (only if supported by inputs) OR
  - provide minimal metrics anyway (preferred).

---

### 8. Testing & Rollout
Purpose: only the critical tests and rollout steps that prevent expensive failures.

Structure: use **`#### Critical tests`**, **`#### Phases`** (or rollout steps), **`#### Accepted risks`** when each block has multiple bullets or paragraphs. Blank line after each heading.

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

## Addendum (optional, after §8)

Use `### Addendum A. <title>`, `### Addendum B. <title>`, … for supplementary reference material that is not a glossary term:

- Operator or filter matrices (e.g. MVP catalog operators)
- Naming or design comparisons too long for Terminology
- Overflow accepted risks when §8 is already dense
- Throughput or storage footprint calculations (required when applicable, see triggers below).
  - **Triggers (add a `### Addendum <letter>. Throughput and storage footprint` when any hold):**
    1. The design adds or changes CPU-costly work on a hot API path (crypto, compression, large validation).
    2. Request or response encoding expands payload size against existing body or field caps.
    3. Persistence grows per-entity storage, adds indexes, or carries rewrite/backfill risk.
    4. The deployable shares one database instance across modules or workloads that will run concurrently with the new path.
    5. Baseline/import or burst traffic can contend with steady sync traffic.
  - **When applicable, the addendum MUST include:** demand × size bands (active entities, sync RPS ceiling, burst/import posture) with labels `established` | `planning assumption` | `illustrative`; a sources-of-truth table when planning inputs override an older ADR; API fit-check against existing latency/admission budgets (not new hard SLOs unless product asks); storage bands for **every** logical database on a shared instance, not only the module owning the feature delta; a worked body-size example when encoding expands requests; and measurement gates (idle-box success is not capacity truth under shared load; stretch concurrency is opt-in with abort alerts).
  - **If none of the triggers apply**, state one line under §3 Assumptions: `No capacity addendum: no material API CPU, payload, or shared-storage change.` The existing §8 rule still holds: net-new downstream volume needs an explicit capacity review gate before go-live.

Addendum sections follow the same `####` subsection rules as §1–8. Do not duplicate Terminology definitions in Addendum prose without a one-line pointer from Terminology (e.g. "See Addendum A").

---

## Technical Decision Notes (Non-obvious Choices)

When the RFC makes a non-obvious implementation choice where multiple approaches exist and constraints drive the selection, document it as a named subsection within the relevant RFC section (e.g., "Concurrency Design Note", "Cache Strategy Note"). Structure it as:

1. **Constraints** (non-negotiable inputs that bound the option space; label C1, C2, …)
2. **Options considered**; comparison table with each constraint as a column; mark ✅ / ❌ per cell
3. **Elimination trail**; one sentence per eliminated option explaining which constraint it violates
4. **Recommendation**; state the chosen option and the decision trail: a numbered sequence that maps each constraint to the option's property that satisfies it
5. **Reversibility note**; one sentence per constraint: which input would need to change to make a previously eliminated option viable again

Rules:
- The decision trail must be written so a reader who did not attend the discussion can independently verify or challenge the choice using only the RFC.
- Keep constraints concrete and verifiable (e.g., "`handleMessage()` throws → retry; any early return = silent ack" not "correctness concerns").
- Do NOT list options that were never seriously considered. Only include options that would be valid if one or more constraints were relaxed.
- Place the note in the section closest to the implementation detail it justifies; typically Section 3 (Core Concepts/Assumptions) for cross-cutting decisions, or Section 4 (Functional Overview) for flow-specific ones.
- **Subsection-local terms**: when a Technical Decision Note (or similar analytical subsection) introduces local variables (e.g. N), notation shorthands (e.g. ~10 ms), or abbreviated concepts not defined in the global Terminology, add a "Terms used in this section" table immediately after the subsection heading, before the Constraints block. One row per term; columns: Term | Meaning.
- **Dimension-specific variable naming**: when an analytical subsection discusses more than one related boundary or cardinality (for example activity-level fan-out vs per-user + task concurrency), do not use a bare single-letter variable like `N` as the primary term. Name the variable after the counted dimension (`fanOut`, `matchedRules`, `distinctTasks`) and state the other boundaries explicitly so the formula cannot be misread as applying to the wrong scope.
- **Formula clarity**: mathematical formulas with ambiguous operator precedence must use explicit parentheses (e.g. `1 000 ms / (N × 10 ms)`, not `1 000 ms / N × 10 ms`).
- **PROD verification query for unbounded/configurable variables**: when a constraint documents a variable that is BO-configurable or unbounded at runtime (e.g. "N rules per activity, no code gate"), include a PROD-runnable SQL query immediately below the constraint so engineers can verify the real current value without digging through the codebase. The query must mirror the exact WHERE clause the application uses (same predicates, evaluated at `NOW()`), group by the dimension being counted, and order by count descending so the maximum is the first row. Always qualify table names with the database name (e.g. `example_db.example_trigger_table`).
- **Zero-row observations**: if the verification query returns zero rows or the inspected table is empty, record that as a point-in-time environment observation only. Do not present it as proof of an upper bound, intended limit, or enforced invariant; pair it with product/source clarification if the design still needs a target boundary.

---

## Editing an Existing RFC

When modifying an existing RFC document (adding sections, updating decisions, restructuring content), apply the same structural contract as creation. Do **not** skip this because the skill was not explicitly invoked for the edit.

### Checklist before committing any RFC change

1. **Section order**  -  Terminology → `### 1` Header → … → `### 8` Testing & Rollout → optional Addendum(es). Do not add, rename, reorder, merge, or omit numbered sections 1–8.

2. **Terminology**  -  Flat A–Z glossary only before §1; no topic subsections, writer meta, or operator matrices. New terms in the edit must be added to Terminology (alphabetically). Prefer plain BE-readable wording for uncommon metaphors; if jargon stays for concision, it must be defined here. Supplementary tables go in Addendum. Body: no ambiguous **eval** catch-alls; name the specific operation.

3. **Subsection headings**  -  Use `####` for Problem statement, Goals, In-scope, Contract notes, Critical tests, etc. Use `#####` for edge-case titles and per-endpoint blocks under §5.1.1. Replace nested `- Label:` list items and bold pseudo-headings when touching a section.

4. **Bold**  -  Glossary term labels only in Terminology. Body uses headings and backticks, not bold for emphasis or re-defined terms.

5. **Placement of new content**  -  Place new content in the section closest to the detail it justifies:
   - Cross-cutting decisions → Section 3 (Scope & Dependencies)
   - Flow-specific decisions → Section 4 (Functional Overview)
   - Closed decisions (no open alternatives) → inline rationale in the relevant section or a named appendix subsection; do NOT present them as open option comparisons.

6. **Technical Decision Notes**  -  Any non-obvious technical choice added or substantially revised must follow the full structure defined in §Technical Decision Notes: Constraints → Options table (constraints as columns) → Elimination trail (one sentence per eliminated option) → Recommendation with decision trail → Reversibility note (one sentence per constraint). Partial structures (e.g. recommendation without elimination trail, or options table without reversibility note) are not compliant.

7. **Closed decisions**  -  When a decision has been made, collapse any options-comparison content to a single named subsection containing: the decision, who made it, when, and the rationale. Remove pros/cons tables for eliminated options; they add noise to a reader trying to understand what will be built.

8. **Process-tense labels**  -  Do not use labels that were only meaningful during the review/drafting stage. Replace "(current)" with "(existing)" or "(pre-RFC)", remove "(new)" from stable flow/section headings, and avoid "Refactored" in stable section titles. Use stable descriptive names that remain accurate after the RFC is implemented.

9. **Open question resolution propagation**  -  When resolving an RFC open question (changing status from "defer" or "open" to decided), grep the entire document for all references to the old state; assumptions, edge cases, flow descriptions, rules, and inline mentions. Update every reference in the same changeset. A resolved question with stale references elsewhere in the RFC is worse than an open question because it creates contradictions.

10. **Substantial edits**  -  When the edit changes contracts (§5), flows (§4), business rules (§6), or rollout (§8), run **Step 2 – Review pass** before presenting the updated RFC. Skip Step 2 for typo-only or single-bullet clarifications unless the user requests a full review.

11. **Readable-not-telegraphic**  -  §4 edge cases use the **Edge case: \<title\>** + Condition/Behavior/Outcome format (not one-line shorthand). §6 rules and §7 metric/alert rows state **who/what/when** in plain language; Terminology defines terms once, body sections restate behavior where a mid-doc reader needs it. Thresholds include subject and window (not `≥3 in 24h` alone).

12. **Diagrams**  -  If any edited flow or edge-auth/crypto path meets a complexity or encrypted-direction trigger, ensure a diagram exists or the §3 N/A one-liner is present. After editing Mermaid `sequenceDiagram` blocks, reject message text that contains `;`.

13. **Capacity addendum**  -  If any capacity trigger applies (API CPU / payload expansion / shared DB / import contention), ensure the footprint Addendum or the §3 N/A one-liner is present.
