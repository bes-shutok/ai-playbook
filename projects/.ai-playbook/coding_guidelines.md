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
  other verifies it but duplicates all the setup; split tests conceal that both
  assertions belong to a single invocation

**Exception:** keep tests separate when they require genuinely different setups (different
failure conditions, different fixture values, different mock responses) or when each test
exercises a distinct code path.

## 2. Narrow try-catch blocks to the intended operation

Wrap only the specific operation that can throw the expected exception in `try`. When multiple operations share one `try` block, an exception from a different operation is caught, producing a misleading error message and triggering fallback logic that was not intended for that failure.

**Example:** A cache read with a fallback: if the fallback call is inside the same `try` as the cache read, a fallback exception fires the catch block, logs "cache failed" (wrong), and retries the fallback a second time.

Each distinct failure mode should have its own narrowly-scoped try-catch.

## 3. Do not use test/staging environment measurements as production capacity baselines

Load test results, throughput numbers, latency observations, and fan-out ratios measured in non-production environments (UAT, staging, STG, dev) are not representative of production capacity. Key reasons:

- **Rule / data volume differs**: STG typically has far fewer configured rules, users, or records than PROD. A fan-out ratio of 13× on STG tells you nothing about the PROD multiplier.
- **Traffic is synthetic**: GoReplay replays, JMeter scripts, and similar tools produce artificial traffic patterns that don't match real user behaviour distributions.
- **Infrastructure differs**: resource limits, pod counts, DB instance sizes, and network topology are usually smaller in non-prod environments.

When documenting load test findings:
- Always label observed numbers with the environment and the traffic source (e.g. "STG, GoReplay replay of March 28 capture").
- Do not embed test-env-derived formulas (e.g. `~300 × ~13 ≈ ~4k`) in canonical capacity docs; they imply generality that doesn't exist.
- If numbers must be recorded for historical reference, place them in a clearly scoped section (e.g. "STG-only / artificial load") and explicitly state they are not production guidance.

## 4. Safe Sentinel for Absent Optional Fields

When an optional field from external input is absent, use a type-safe sentinel value
(e.g. `"0"` for numeric fields, empty collection for lists) rather than an empty string
that may cause downstream parse errors. The sentinel should be chosen so that downstream
parsing and arithmetic treat the absent field as a no-op.

## 5. Data-Loss Conditions Must Be Logged at Warning Level or Higher

When a matching, aggregation, or transformation step discards or fails to match data,
the condition must be logged at `warning` level or higher, never `debug`. Data-loss
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

## 8. Numbered Enum Slot Reservation: Use Explicit Entries

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
once before the loop, not inside the loop body. This avoids redundant work and makes the
invariant intent explicit.

## 11. Use Lifecycle-Specific Names for Fields That Hold Different Life Phases

When a class holds two or more fields that represent the same kind of entity at different
lifecycle phases, name each field after its specific phase, not a relative or positional term.

Relative terms like "current" and "latest" feel interchangeable and force the reader to trace
all usages to understand which phase each field holds.

**Bad:** `currentRevisionId` vs `latestRevisionId`: both sound like "the most recent one".
Reading `archiveCurrentRevisionIfNeeded()` right before activating `latestRevisionId` looks
contradictory until you trace both field meanings.

**Good:** `activeRevisionId` (published) vs `draftRevisionId` (pending activation): the phase
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

The boundary value itself is where the bug most often lives: one direction wrong and the classification flips.

## 16. Use Exact Equality for Known Counts

When the expected count of items is known (not just "at least one"), use exact equality (`==`) in assertions rather than inequalities (`>=`, `<=`).

**Why:** `assert len(entries) >= 1` accepts any positive count, hiding duplications and partial failures. If the test scenario produces exactly one entry, the assertion should be `assert len(entries) == 1` so that unexpected extras or splits fail visibly.

## 17. Root-Cause Principle Catalog (Recall by Problem Shape)

This catalog is **finalized** by the `generalize audit` (see the `generalize` skill). The
anchor sets below are the authoritative illustrative subset drawn from the audit; the
complete per-repo lesson map is greppable in each repo's `development_lessons.md`
(`grep -nE '^\*\*Principle:\*\* Family X'`), and cross-project lessons live in the
user-level `development_lessons.md` (strict, gated). Shape triggers may be revised by a
future audit run, but the family set (A to H) is stable.

The rest of this file (clauses #1 to #16) is incident-anchored: a rule is recalled by the code location
or the incident surface that produced it. That helps prevent the same bug in the same place, but it
under-helps when the same root cause reappears in a new module under a different surface, because no
cross-ref points there and the headline does not match. This catalog re-anchors recurring lessons to the
underlying root-cause *family* and to a *shape trigger* (the situation, independent of file or module,
that should make you suspect the family). Recall then works by problem shape, not by where the last bug
bit.

**How to use it.** When you capture a lesson (via the `learn` skill's Generalization pass) or review one,
name its family from #18 onward and write a shape trigger that a reader in a different module would
recognize. Use the `generalize` skill's `map` mode for a single incident and its `audit` mode to cluster
a whole corpus. The catalog is the family authority; the concrete incident is always kept as the witness
(a bare precept with no failure mode is unfalsifiable and forgettable).

**Family map (A to H).** Each family below links to its section:

- A. Equivalence-class coverage: a passing test pins one cell; fix the class, not the cell. See #18.
- B. Error-policy propagation: a centralized fallible op must carry each call site's raise/degrade policy. See #19.
- C. Representation: sentinel vs None vs exception: each carries distinct recoverability; do not conflate. See #20.
- D. Single source of truth: two authoritative copies drift; one source, the rest are views. See #21.
- E. Temporal / ordering invariants: earlier events cannot consume later state; recompute preconditions after each input change. See #22.
- F. Layering / dependency direction: dependencies point one way; logic lives at the layer that owns it. See #23.
- G. Data-loss observability: unmatched or dropped records must surface; never silent discard. See #24.
- H. Verify the real thing, not the abstraction: do not trust names, summaries, or mocks; trace actual data and behavior. See #25.

Inline anchors in each family are an illustrative subset; grep each repo's
`development_lessons.md` (`grep -nE '^\*\*Principle:\*\* Family X'`) for the full project-tier
lesson map per family, and the user-level `development_lessons.md` for cross-project lessons.

### Lesson tag format

Every catalogued lesson carries exactly one family tag as the **first body line** of the
lesson, in the form:

```
**Principle:** Family <X> (<free-text reason>)
```

- `<X>` is one of the family letters in #18-#25 (currently A-H), or the literal `excluded`
  (a process-only or out-of-catalog lesson, kept for history but not recalled by shape), or
  `unclassified` (the lesson has not yet been routed through the `generalize` audit). Do NOT
  invent letters outside the catalog; growing the family set means adding the #18-#25 section
  AND the gate's `VALID_FAMILIES` together.
- The parenthetical `(<free-text reason>)` is **mandatory**: a short, specific phrase naming
  the failure mode or shape (e.g. `Family H (verify the real thing, not the abstraction)`).
  A bare `Family H` with no reason is rejected; the reason is what makes recall by shape work.
- Exactly one tag per lesson. A lesson spanning two families is split into two lessons (the
  audit exists to force that decision), not double-tagged.

**Strictness split.** The tag is enforced at two different strengths:

- **User level** (`shared_docs_dir`/`development_lessons.md`, the cross-project corpus): the
  tag is **mandatory and enforced**. `lessons_index.py` rejects any `UL#N` lesson that has
  zero tags, more than one, or a tag outside `VALID_FAMILIES`; a catalog change that adds a
  family surfaces as a visible `invalid-family` failure until `VALID_FAMILIES` and the #18-#25
  section are updated together. The `learn` Step 6.6 gate hard-blocks on a violation.
- **Project level** (each repo's `docs/maintenance/development_lessons.md`): the tag is a
  **convention**, written by `learn`/`generalize` for best-effort in-project AI recall. Project
  files are plain markdown, valid standalone with NO skill, gate, or user-corpus dependency;
  nothing enforces the tag and a missing/malformed tag does not break the project. A project
  that wants strictness can opt into a project-local gate later.

Cross-project lessons live in the user-level `development_lessons.md` (strict, gated);
repo-specific lessons live in each repo's `development_lessons.md` (convention). Both layers
load on demand, so recall works from either.

## 18. Equivalence-class coverage (A)

A passing test pins one cell of an N-dimensional input space; the fix belongs at the partition class,
not at the cell the test happened to exercise.

**Failure signature:** A bug is fixed with a test for the specific failing case, yet a sibling case that
shares the same partition (different caller, different branch of the same condition, different config
arm) still fails silently. The regression suite grows, but coverage of the *class* does not.

**Shape trigger:** You just added a test or guard after extracting a shared helper, centralizing a policy,
or widening a conditional to cover more callers/branches. Ask: of the equivalence classes that now flow
through the changed code (each caller, each raise-vs-degrade arm, each value partition), is there a test
that would fail if the implementation were wrong for *that* class specifically? If two classes could be
wrong independently, they need independent assertions, not one OR'd case.

**Example:** A shared helper normalizes a value and raises on malformed input. It is extracted from three
callers: one that must raise hard, one that must warn-and-degrade, and one that must skip the row. A test
is written for the raising caller and passes. The warn-and-degrade caller, with a different exception
policy, still swallows the malformed value and produces a wrong output, because the centralized helper
was not taught each caller's policy and no test exercised the degrade arm. The class is "centralized
fallible op across callers with distinct policies"; the cell is "the one caller the test pinned."
(Illustrative anchors: tax-reporting #91, #111, #117, #119, #125, #133, #136.)

**Exception:** When the changed code genuinely has exactly one equivalence class (a single caller, a
single branch, a total function with no partition), one test suffices. The family bites when N > 1.

## 19. Error-policy propagation (B)

A centralized fallible operation must carry each call site's raise-vs-degrade policy; a single hard-coded
policy in the shared code serves only the call site whose policy happens to match.

**Failure signature:** Reusing a validated security or parsing pattern (symlink rejection, size limit,
rate lookup, parse) at a new call site fixes the *primary* failure but leaks the original site's error
handling, which is calibrated to that site's cost of silent failure. The new site either raises where it
should degrade, or degrades where it should raise.

**Shape trigger:** You are centralizing a fallible op (rate lookup, parse, resolve, guard) that more than
one caller now invokes, or you are reusing an existing validation/security pattern at a new location.
For each caller, ask: what is the cost of a silent failure here, and does the centralized code's raise or
degrade match that cost? If the cost differs across callers, the policy is a per-call argument, not a
constant in the helper.

**Example:** A rate-lookup helper returns a sentinel on failure, and one caller multiplies that sentinel
through and raises an uncaught type error at a different layer, because the helper's "return None on
miss" policy was right for the original caller (which checked the result) but wrong for the new caller
(which used the result unconditionally). The fix is not to make the helper raise; it is to make the
policy explicit per call site (raise inside the per-row boundary that catches it, or degrade explicitly)
so each caller's recoverability is honored. (Illustrative anchors: tax-reporting #9, #105, #124, #130,
#135.)

**Exception:** When every caller shares the same recoverability and the same cost of silent failure, a
single hard-coded policy in the shared code is correct and a per-call argument is over-engineering.

## 20. Representation: sentinel vs None vs exception (C)

The representation chosen for "this value is absent or invalid" (a sentinel value, a null/None, or a
thrown exception) carries a distinct recoverability contract; conflating them produces wrong downstream
behavior that looks like a valid result.

**Failure signature:** A field that can be absent, unknown, or invalid is represented one way internally
(e.g. a sentinel string) but rendered or consumed as if it were a different representation (None, an
empty string, a thrown exception). The output either crashes on an unexpected type, or worse, renders a
plausible-but-wrong value with no signal that anything was missing.

**Shape trigger:** You are choosing how to represent an absent/unknown/invalid value, or you are passing
such a value across a boundary (internal resolver to user-facing output, one layer to another, a string
format that interpolates it). Ask three questions: is this representation recoverable by the receiver
(caught exception vs uncaught), is it distinguishable from a legitimate value (sentinel vs bare empty),
and does it degrade explicitly when the field is reachable via a warn-only path? If the answers differ
across boundaries, convert at the boundary rather than letting the internal representation leak.

**Example:** An internal resolver marks an unresolved origin with a review-sentinel string. Downstream, a
user-facing cell interpolates that sentinel into prose, so the review-required flag is silently rendered
as if it were a real value. The fix is to convert: the sentinel is internal-only; the user-facing field
uses the raw input value (or an explicit "unknown" token), and any f-string that interpolates a possibly
null field degrades explicitly rather than printing "None". (Illustrative anchors:
tax-reporting #113, #114, #131.)

**Exception:** Within a single layer where one representation is used consistently and never crosses a
boundary, no conversion is needed. The family bites at the boundary or when the null-path is reachable.

## 21. Single source of truth (D)

When the same fact is authoritative in two places, the two copies drift; designate one source and make
the rest views (or recompute), never a second independent authority.

**Failure signature:** A total, a derived value, or a classification exists in two places that are each
treated as authoritative. One is updated (the merge applies a fix, an override corrects a row); the other
is not. The two disagree, and downstream code trusts the stale copy.

**Shape trigger:** You are about to write a second authoritative copy of a fact that already has a home
(a duplicate key in an index, a derived total that is also summed elsewhere, an override applied before
an aggregation that recomputes the same field). Ask: is there already one source for this value, and is
the new copy a view over it or a second authority? If two authorities exist, one must be demoted to a
view, or the duplicate-key case must sum rather than overwrite.

**Example:** An aggregation sums FIFO lots into per-disposal totals, and a separate override report also
holds the per-disposal total. The override is applied, but the aggregation recomputes from the lots
afterward and clobbers the override, because both were authoritative for the same field. The fix is
ordering plus demotion: the override is the authority and is applied before aggregation, and aggregation
treats the overridden total as the source of truth rather than recomputing it. (Illustrative anchors:
tax-reporting #59, #75, #77, #85, #103.)

**Exception:** A genuinely independent second copy that is never consumed as authoritative (a cache that
is always validated against the source, a display snapshot) does not drift dangerously. The family bites
when both copies are read as the answer.

## 22. Temporal / ordering invariants (E)

An earlier event cannot consume state that only a later event establishes; when inputs change the
preconditions, recompute them after each change rather than once at the start.

**Failure signature:** Logic computed a precondition (a tolerance, a candidate set, a parsed value) once,
then mutated the inputs (shrank a window, removed matched items, advanced a cursor), and reused the stale
precondition against the new state. The result admits an invalid candidate, or rejects a valid one, or
consumes a second value from a now-exhausted source.

**Shape trigger:** You are writing a multi-phase or sliding-window matcher, a loop that mutates a shared
structure, or code that parses a value inside a try block and then derives a second value from it
outside the block. Ask: after each mutation, are the preconditions (window tolerance, candidate count,
parsed object, cursor position) still valid for the remaining state? If the mutation changes what would
be admissible, recompute before the next step. Prefer an ordered structure (a deque popped once per
event) over a dict keyed by a non-unique tuple, which silently overwrites on collision.

**Example:** A two-pointer sliding-window matcher computes a tolerance proportional to the current window
size, then shrinks the window from the left but reuses the stale tolerance, so the shrunken window admits
a candidate that is invalid for its new size. Or: phase 1 of a matcher removes exact matches, and phase 2
brute-force-checks the fallback against the original full set rather than the post-phase-1 remainder, so
its feasibility prediction is wrong because the candidate count changed. The fix in both is to recompute
the precondition after every state change. (Illustrative anchors: tax-reporting #106, #107,
#108, #110.)

**Exception:** When preconditions are genuinely invariant across all mutations (a constant tolerance, a
monotonically growing candidate set), recomputing is redundant. The family bites when the mutation can
change admissibility.

## 23. Layering / dependency direction (F)

Dependencies point one way; logic that depends on a lower layer's detail does not belong at a higher
layer, and a lower layer must not reach up for a constant or type owned above it.

**Failure signature:** An orchestration layer accumulates domain logic until it is both the coordinator
and the rule book, or a lower layer imports a constant or type from a higher layer and creates a cycle.
The module grows past its size budget, or an extraction fails with a circular import.

**Shape trigger:** You are adding logic to an orchestration layer, extracting a helper to a new module,
or splitting responsibilities. Ask: does this logic belong to the layer that owns the data or rule it
operates on, or has it accreted in the orchestrator by convenience? And does the extracted module depend
only on lower layers, or does it reach back up for a constant from its source module? Move domain logic
to a dedicated service when coordination grows; resolve constants downward.

**Example:** A thin orchestrator grows past its size budget because each new rule was added there for
convenience. Extracting the rules into a dedicated service reveals that the service needs a constant
still owned by the orchestrator, so a naive extraction creates a circular import. The fix is to move the
constant to the layer that owns it (downward) so the extracted service depends only on lower layers, and
to keep the orchestrator as coordination only. (Illustrative anchors: tax-reporting #28, #49,
#86, #87, #88, #121.)

**Exception:** A genuinely cross-cutting concern (logging, telemetry) that is intentionally allowed to
appear at every layer does not violate directionality. The family bites when domain rules or owned
constants flow the wrong way.

## 24. Data-loss observability (G)

When a matching, aggregation, dedup, or transformation step drops or fails to match a record, the drop
must surface visibly; a silent discard is a data-loss bug even when the program exits zero.

**Failure signature:** Records that should have been matched, paired, or carried through are absent from
the output, and nothing in the logs at warning or above explains where they went. The output looks
complete and valid; it is not.

**Shape trigger:** You are writing or reusing a matcher (FIFO pairing, key join), a dedup step, a
filter-before-aggregation, or any guard that reads a manifest or patterns file. Ask: for every input
record that is not carried to the output, is there an explicit fallback and a warning? And for every
guard that depends on a file (a manifest, a patterns list), does it fail closed when the file is absent
(a missing grep target exits non-zero, so a naive "cmd and echo BAD or echo GOOD" reports GOOD exactly
when the guard cannot run)? Matched-target counts should warn when one source event matches more than one
target item, to surface amount collisions without blocking splits.

**Example:** A matcher pairs source events to target items by a key tuple, and unmatched source events
are simply not emitted, with no warning. Or a hygiene guard runs "grep -f patterns && echo BAD || echo
GOOD", but the patterns file is gitignored and absent in CI, so grep exits non-zero and the guard prints
GOOD, a false pass, exactly when it cannot run. The fix is an explicit fallback for every unmatched
record logged at warning or higher, and a fail-closed guard that distinguishes "could not run" from
"ran clean". (Illustrative anchors: tax-reporting #40, #51, #73, #102, #126.)

**Exception:** A drop that is intentional and documented by the domain (a materiality filter, a known
suppression) does not need a warning, provided the suppression is itself visible elsewhere (a stated
threshold, a logged count). The family bites when the drop is silent and unintentional.

## 25. Verify the real thing, not the abstraction (H)

Do not trust names, summaries, mocks, or plan pseudocode; trace the actual data from source to output
and confirm the behavior against the real implementation.

**Failure signature:** A claim about production code (a field's semantics, a file path, a line number, a
function's return shape, an enumeration's cases) is asserted from a name, a docstring, or a plan's
pseudocode, and the assertion is wrong. A test passes against a mock that does not match the real
collaborator, or a plan task is built on a field-name conflation that the real data contradicts.

**Shape trigger:** You are about to assert that something is "handled correctly", write a plan task that
claims a fact about production code, or trust a summary (a docstring, a headline, a reviewer's gloss).
Code inspection alone is insufficient. Ask: have I traced the actual data from the source to the output,
and have I read the function's implementation (not just its name) to learn what patterns it really
supports? For plan pseudocode that compares two same-named fields across objects, trace the fixture to
confirm the two names denote the same economic quantity before implementing. For an enumeration claimed
as N-case, count the implemented branches.

**Example:** A plan compares two fields by name across two domain objects and assumes they are the same
quantity, but the objects name two different economic values that happen to share a label, so the
comparison is meaningless. Or a test verifies "YES/NO" rendering against a flag the fixture sets via a
nested object, but the real renderer reads a different field, so the test passes against a mock and the
production path is untested. The fix is a data trace: read the implementation, set the fixture fields to
different-but-realistic values so a conflation fails visibly, and assert against the real collaborator.
(Illustrative anchors: tax-reporting #71, #72, #99, #100, #101, #116, #120, #123, #132.)

**Exception:** A purely structural claim (a file exists, a function is exported) can be settled by
inspection alone. The family bites for any claim about semantics, behavior, or data identity.

## 26. Tests Must Not Depend on Gitignored Data

Test data that a test reads at runtime must be committed to version control, inlined in the test, or
generated deterministically at test time. It must never live in a gitignored path. A test that opens a
gitignored fixture (a local snapshot, a scratch JSON, a personal data file) passes on the machine that
happens to have the file and errors at setup on every fresh clone and CI run, because the file is absent
there. Such a test is not a portable contract; it is a latent CI failure that surfaces only when someone
else runs the suite.

This applies to characterization/golden-snapshot tests in particular: capturing a "golden" value into a
gitignored file and asserting against it from a test re-creates this failure mode by design. Inline the
expected value as a literal in the test, or commit the snapshot to the repo.

**Failure signature:** A test's `setup_method` / fixture loader calls `pytest.fail` (or raises) when a
data file is missing, and that file lives under a gitignored directory (`docs/tmp/`, a personal data
folder, a machine-local scratch path). The suite is green locally and red on CI or a fresh clone.

**Shape trigger:** You are about to read a data file from within a test, or to capture pipeline output
into a snapshot file for a characterization test. Ask: is this path version-controlled? Run
`git check-ignore <path>`. If it returns the path, the test depends on data that does not exist on a clean
checkout. Either inline the value, commit the fixture, or generate it deterministically in the test.

**Example:** A characterization test captures two aggregated gain values into
`docs/tmp/derivatives-characterization-golden.json` (gitignored) and reads them in `setup_method`,
calling `pytest.fail` when the file is absent. The test passes on the author's machine and errors at
setup everywhere else. The fix is to inline `Decimal("136.01")` and `Decimal("-1.00")` directly in the
test methods and delete the snapshot file, so the contract holds on any checkout.
(Illustrative anchors: tax-reporting #189.)

## 27. Prefer Safe-Default Autodiscovery Over Operator-Supplied Parameters When Generalizing a Tool

When generalizing a tool that was hardcoded to one context (one repo, one domain, one config), the
first instinct is to **parameterize** the hardcoded values: turn the embedded keyword list, magic
constant, or fixed ordering into a CLI flag or config file the operator supplies per run. This
relocates the bespoke knowledge from the engine to a per-run file but does not remove the manual
step; the tool is technically context-agnostic yet practically bespoke-per-run.

Before parameterizing, ask whether the parameter is needed at all. If the tool performs a
classification or routing where the buckets have **asymmetric cost** (mis-assigning to one bucket is
costly, e.g. promoting a project-specific record into a shared cross-project store where it pollutes
every consumer; mis-assigning to the other is harmless, e.g. keeping a genuinely-shared record local
just loses some reuse), then identify only the **costly bucket** via stable, context-independent
signals and default everything else to the **safe (harmless) bucket**. The safe default makes the
costly error impossible by construction, so the classifier never needs to recognize the safe-bucket
inputs precisely and therefore never needs the operator to supply the domain vocabulary that would
let it do so. The result is zero-config; keep the parameter only as an optional override.

**Failure signature:** A "generalized" tool ships with a required `--<domain>-keywords <file>` flag
(or equivalent) and the run book instructs the operator to curate the repo's domain terms by hand
before each run. The manual step is the symptom of a parameter that safe-default autodiscovery could
have eliminated.

**Shape trigger:** You are converting a hardcoded value into a parameter (adding a CLI flag, a config
key, or a "curate this file per repo" instruction) so a tool built for one context can run elsewhere.
Pause and ask: is there a bucket whose correct identification lets me default every other input
safely? If yes, detect that bucket from stable signals and drop the parameter.

**Example:** A migration tool classifies each legacy lesson as project-specific or cross-project. The
first generalization extracted the hardcoded domain keywords into a `--domain-keywords <file>` flag
the operator curates per repo. The better design recognizes the asymmetry: mis-promoting a
project-specific lesson into the shared cross-project corpus is costly; keeping a cross-project
lesson local is harmless. So the classifier identifies the cross-project bucket only, via a stable
family tag or a generic engineering-shape vocabulary drawn from a shared catalog, and defaults
everything else to project-specific. No domain keywords are needed; the tool runs zero-config.
(Illustrative anchors: tax-reporting lessons-corpus plan, 2026-06-29.)

## 28. Minimal Solution Ladder (Before Writing Code)

Climb this ladder **after** reading the task and tracing the code the change touches. The ladder shortens the solution, not the understanding. Lazy about implementation, never about comprehension.

Stop at the first rung that holds:

1. **Does this need to exist?** Speculative or "for later" work: skip it and say so in one line (YAGNI).
2. **Already in this codebase?** Reuse existing helper, util, type, or pattern; re-implementing nearby code is the most common slop.
3. **Standard library does it?** Use it.
4. **Native platform feature covers it?** Prefer built-ins (HTML input types, CSS, DB constraints) over custom code or new dependencies.
5. **Already-installed dependency solves it?** Use it; do not add a dependency for what a few lines can do.
6. **Can it be one line?** One line.
7. **Only then:** the minimum code that works.

**Bug fixes:** a ticket names a symptom. Before editing, grep callers of the function you will touch. Fix at the shared choke point where all callers route through; patching only the reported path leaves sibling callers broken.

**Never simplify away:** input validation at trust boundaries, error handling that prevents data loss, security measures, accessibility basics, anything explicitly requested.

**Deliberate simplifications** with a known ceiling (global lock, O(n²) scan, naive heuristic): leave a short comment naming the ceiling and the trigger to revisit (for example throughput threshold, second implementation needed).

**Tests:** non-trivial logic (branch, loop, parser, money/security path) deserves one runnable check (smallest `test_*` or self-check); trivial one-liners need no test (YAGNI applies to tests too).

**Upstream pattern:** adapted from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail); deep links in `skill-upstream-catalog.md` **Merged pattern index**. Merged here instead of a persistent session-mode skill. Complexity review tags live in `review-agents/simplification.md`.
