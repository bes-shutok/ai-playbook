# Generic Coding Guidelines

Language-agnostic software engineering rules applicable across all projects and stacks.
Instruction files reference numbered clauses here rather than restating full text.

JVM/Spring-specific rules live in `~/Projects/.ai-playbook/jvm_guidelines.md`.
Language-specific rules live in `~/Projects/.ai-playbook/kotlin_guidelines.md`,
`~/Projects/.ai-playbook/java_guidelines.md`, and `~/Projects/.ai-playbook/python_guidelines.md`.

## 1. Merge Tests That Share Identical Setup

When two test methods use identical setup (same fixture, same stubs or mocks) and differ
only in **which side-effects they assert on the same single method invocation**, merge them
into one test. Name the merged test to enumerate both verified behaviors, e.g.
`given_X_when_Y_then_A_and_B` (or the equivalent convention used in the codebase).

Keeping them separate creates:
- Duplicated arrange/act code that drifts independently
- A misleading appearance that the two behaviors are independently testable
- A stub-without-verify smell: one test stubs a collaborator but never verifies it; the
  other verifies it but duplicates all the setup — split tests conceal that both
  assertions belong to a single invocation

**Exception:** keep tests separate when they require genuinely different setups (different
failure conditions, different fixture values, different mock responses) or when each test
exercises a distinct code path.

## 2. Narrow try-catch blocks to the intended operation

Wrap only the specific operation that can throw the expected exception in `try`. When multiple operations share one `try` block, an exception from a different operation is caught, producing a misleading error message and triggering fallback logic that was not intended for that failure.

**Example:** A cache read with a fallback — if the fallback call is inside the same `try` as the cache read, a fallback exception fires the catch block, logs "cache failed" (wrong), and retries the fallback a second time.

Each distinct failure mode should have its own narrowly-scoped try-catch.

## 3. Do not use test/staging environment measurements as production capacity baselines

Load test results, throughput numbers, latency observations, and fan-out ratios measured in non-production environments (UAT, staging, STG, dev) are not representative of production capacity. Key reasons:

- **Rule / data volume differs** — STG typically has far fewer configured rules, users, or records than PROD. A fan-out ratio of 13× on STG tells you nothing about the PROD multiplier.
- **Traffic is synthetic** — GoReplay replays, JMeter scripts, and similar tools produce artificial traffic patterns that don't match real user behaviour distributions.
- **Infrastructure differs** — resource limits, pod counts, DB instance sizes, and network topology are usually smaller in non-prod environments.

When documenting load test findings:
- Always label observed numbers with the environment and the traffic source (e.g. "STG, GoReplay replay of March 28 capture").
- Do not embed test-env-derived formulas (e.g. `~300 × ~13 ≈ ~4k`) in canonical capacity docs — they imply generality that doesn't exist.
- If numbers must be recorded for historical reference, place them in a clearly scoped section (e.g. "STG-only / artificial load") and explicitly state they are not production guidance.

## 4. Safe Sentinel for Absent Optional Fields

When an optional field from external input is absent, use a type-safe sentinel value
(e.g. `"0"` for numeric fields, empty collection for lists) rather than an empty string
that may cause downstream parse errors. The sentinel should be chosen so that downstream
parsing and arithmetic treat the absent field as a no-op.

## 5. Data-Loss Conditions Must Be Logged at Warning Level or Higher

When a matching, aggregation, or transformation step discards or fails to match data,
the condition must be logged at `warning` level or higher — never `debug`. Data-loss
conditions are always production-visible and must not be hidden behind debug-level
filtering.

## 6. Descriptive Output Labels for User-Facing Surfaces

User-facing output labels (column headers, report section titles, API field names,
error messages) should use self-explanatory terminology, not terse names inherited from
upstream source formats or internal abbreviations. When labels are clear on their own,
no separate terminology legend is needed.

## 7. Config Validation Failures Must Not Be Swallowed by Infrastructure Catch Blocks

When a property getter or guard throws a validation exception (`require()`,
`checkArgument()`, `Preconditions.checkArgument()`), calling it inside a `try-catch` that
broadly catches `RuntimeException` or `Exception` swallows the config error and masks a
startup misconfiguration as a transient infrastructure error.

Resolve the config value **before** entering the try-catch block so that config validation
failures propagate immediately.

## 8. Numbered Enum Slot Reservation — Use Explicit Entries

When reserving a gap in a numbered enum (e.g. `METRICS0007` reserved for an upcoming feature
while `METRICS0008` already exists), add the entry as an actual (unused) enum constant rather
than only a comment. The explicit entry ensures that any future PR introducing a second
`METRICS0007` fails to compile instead of silently overriding the reservation.

## 9. Slim Projection Types for Batch Read Paths

When a batch read path only needs a subset of a domain entity's fields, define a dedicated
slim projection type rather than returning the full entity. Returning the full entity forces
the query to fetch unused columns and tempts callers to use fields that were not the intent
of the operation.

Name the projection after what it represents, not after what it omits (e.g.
`UserNotificationTypeSwitch`, not `UserNotificationTypeSettingWithoutTimestamps`).

The slim type is backed by a separate query method with a narrower `SELECT` clause. This
pattern is especially valuable on high-frequency batch paths where reduced payload multiplies
across many rows.

## 10. Hoist Batch-Invariant Checks Outside Loops

When a flag, config value, or feature-gate is the same for every item in a batch, compute it
once before the loop — not inside the loop body. This avoids redundant work and makes the
invariant intent explicit.

## 11. Use Lifecycle-Specific Names for Fields That Hold Different Life Phases

When a class holds two or more fields that represent the same kind of entity at different
lifecycle phases, name each field after its specific phase — not a relative or positional term.

Relative terms like "current" and "latest" feel interchangeable and force the reader to trace
all usages to understand which phase each field holds.

**Bad:** `currentRevisionId` vs `latestRevisionId` — both sound like "the most recent one".
Reading `archiveCurrentRevisionIfNeeded()` right before activating `latestRevisionId` looks
contradictory until you trace both field meanings.

**Good:** `activeRevisionId` (published) vs `draftRevisionId` (pending activation) — the phase
is encoded in the name; the flow reads as "archive the active one, promote the draft".

## 12. PII Redaction Before Committing Personal Docs to Shared Repos

When copying personal reference documents (team notes, onboarding facts, project inventories) from a private location into a shared or team repository, redact all third-party PII before committing:

- **Colleagues' full names** → replace with role descriptors: `[tech-lead]`, `[product-manager]`, `[onboarding-buddy]`
- **AWS/cloud account IDs** → replace with `<AWS_ACCOUNT_ID>`
- **Internal credentials, tokens, passwords** → replace with `<REDACTED>` or remove entirely
- **Personal email addresses** → acceptable in MIT/Apache LICENSE copyright headers regardless of folder (this is standard copyright attribution, not PII); remove from all other contexts (facts files, team notes, configuration, docs)

The author's own name is acceptable in their own profile folder. Everything else that identifies a specific individual must be replaced with a role or placeholder before the first commit. Redaction is easier before the content enters version history than after.

## 13. Filter Before Aggregation to Avoid Overfiltering

When a filter removes entries by a key that unrelated entries may also share (e.g., date+asset+platform), apply the filter to individual items before they are aggregated into groups. Filtering after aggregation removes entire groups including unrelated entries that happened to share the group key. Pre-aggregation filtering preserves unrelated entries while still removing the targeted ones.

## 14. Self-Documenting Config Property Names

Config keys should name what they guard or control, not just that they configure something. Prefer `ZERO_BASIS_REVIEW_THRESHOLD` (names the condition: zero cost basis) over `REVIEW_THRESHOLD` (ambiguous: review of what?). A reader should understand the property's purpose from the name alone, without looking up its usage.

## 15. Test Exact Boundary Values

When testing conditional logic that uses threshold comparisons (`>=`, `<=`, `>`), always include a test case at the exact boundary value. Off-by-one errors at boundaries are a common source of incorrect behavior.

**Examples:**
- Holding period thresholds: test exactly 365 days (not just 364 and 366)
- Zero-basis review thresholds: test exactly `threshold` value
- Pagination limits: test exactly `page_size` items

The boundary value itself is where the bug most often lives — one direction wrong and the classification flips.

## 16. Use Exact Equality for Known Counts

When the expected count of items is known (not just "at least one"), use exact equality (`==`) in assertions rather than inequalities (`>=`, `<=`).

**Why:** `assert len(entries) >= 1` accepts any positive count, hiding duplications and partial failures. If the test scenario produces exactly one entry, the assertion should be `assert len(entries) == 1` so that unexpected extras or splits fail visibly.
