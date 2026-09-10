# Java Development Guidelines

Java-specific development patterns applicable across projects.
Instruction files reference numbered clauses here rather than restating full text.

Shared JVM rules (Spring, Reactor, SLF4J) live in `~/Projects/.ai-playbook/jvm_guidelines.md`.
Language-agnostic rules live in `~/Projects/.ai-playbook/coding_guidelines.md`.
Language-agnostic agent workflow lessons live in `~/Projects/.ai-playbook/agent_workflow_guidelines.md`.

## 1. Spring `@ConfigurationProperties`: Constructor vs Setter Injection Validation

See `jvm_guidelines.md #1`. Java-specific: prefer constructor binding with `@ConstructorBinding`
or record-style constructors, and use JSR-303 `@Validated` with constraints on parameters.

## 2. Mockito Stubbing for Reactor / R2DBC Errors

See `jvm_guidelines.md #4`. Mockito-specific: use `thenReturn(Mono.error(...))`, never
`thenThrow()`.

## 3. Mockito `timeout()` for Fire-and-Forget Async Assertions

See `jvm_guidelines.md #5`. Mockito-specific: use `verify(collaborator, timeout(1000).times(1))`.

## 4. Config Validation Failures Must Not Be Swallowed by Infrastructure Catch Blocks

See `coding_guidelines.md #7`.

## 5. Numbered Enum Slot Reservation  -  Use an Explicit Entry

See `coding_guidelines.md #8`.

## 6. `Optional` Anti-Patterns

6.1. Never use `Optional.get()` without a preceding `isPresent()` check or an alternative
like `orElse()`, `orElseThrow()`, or `orElseThrow(Supplier)`. A bare `get()` on an empty
`Optional` throws `NoSuchElementException` with no actionable context.

6.2. Never use `Optional` as a field type or method parameter. `Optional` is designed as a
return type only. For fields, use `@Nullable` annotations and null checks. For parameters,
use overloading or `@Nullable`.

6.3. Prefer `Optional.map()` / `flatMap()` / `filter()` chains over `if (opt.isPresent())`
imperative blocks. The chain is shorter and makes the empty-case handling explicit.

## 7. Spring `@ConfigurationProperties`  -  Use `Duration` for Duration Fields

See `jvm_guidelines.md #2`.

## 8. Spring Cloud Config  -  Do Not Bundle `spring.application.name`

See `jvm_guidelines.md #3`.

## 9. Maven `.lastUpdated` Markers Block Resolution

When Maven fails to download an artifact, it writes a `.lastUpdated` marker file next to the cached
entry. Subsequent builds skip the download attempt even when the JAR is already in the local cache or
the issue has been resolved (e.g. VPN/Nexus credentials restored).

**Symptom:** `Could not resolve artifact` despite JARs visibly present under `~/.m2/repository/`.

**Fix:**
```bash
find ~/.m2/repository -name "*.lastUpdated" -delete
```

Then retry the build. If resolution still fails, the artifact is genuinely missing from the remote
repository and requires Nexus credentials or a VPN connection.

## 10. Micrometer Prometheus Name Normalisation

Micrometer's Prometheus registry normalises all metric names to **lowercase** before registration
and appends `_total` to counter metrics. Always use lowercase names when writing PromQL queries.

```
// Java code registers: "instant_virtuals_error_METRICS8002"
// Prometheus name:     "instant_virtuals_error_metrics8002_total"
```

Consequences:
- `rate(instant_virtuals_error_METRICS8002{}[5m])`  -  **does not match** (uppercase)
- `rate(instant_virtuals_error_metrics8002_total[5m])`  -  **correct**
- Gauges do **not** get the `_total` suffix; counters always do.
- Micrometer also converts camelCase segments to snake_case (e.g. `myCounter` → `my_counter_total`).

When debugging a non-matching PromQL expression, verify the actual registered name via the
Prometheus `/metrics` scrape endpoint or Grafana's metric browser before assuming the query is
logically wrong.

## 11. Collection Defensive Copy Idioms

**Do not double-wrap unmodifiable copies.** `Set.copyOf()`, `List.copyOf()`, and `Map.copyOf()` already return unmodifiable copies  -  wrapping them in `Collections.unmodifiable*()` adds no protection and signals misunderstanding.

```java
// Wrong  -  redundant wrapper
this.items = Collections.unmodifiableSet(Set.copyOf(items));

// Correct
this.items = Set.copyOf(items);
```

**Let the domain method own the single defensive copy.** When a domain aggregate's mutation method calls `copyOf()` internally, the calling application service must not pre-copy the same collection before passing it in. Passing an already-copied collection wastes an allocation; more importantly, the responsibility for defensive copying should live in one place  -  the aggregate boundary.

```java
// Wrong  -  pre-copy in application service
profile.patchIdentities(List.copyOf(identities));

// Correct  -  aggregate owns the defensive copy
profile.patchIdentities(identities);  // aggregate calls List.copyOf internally
```

**Do not assert reference inequality after `copyOf` on an already-unmodifiable collection.** `List.copyOf` / `Set.copyOf` / `Map.copyOf` may return the same instance when the input is already an unmodifiable collection of that type (for example `List.copyOf(List.of(...))`). An AssertJ `isNotSameAs` (or JUnit `assertNotSame`) against that expression can fail even when content and order are correct. Prefer content/order assertions, or feed a mutable input when the production contract truly requires a distinct instance.

```java
// Fragile  -  copyOf(List.of(...)) often returns the List.of instance
assertThat(result).isNotSameAs(List.copyOf(List.of(a, b)));

// Prefer content/order
assertThat(result).containsExactly(a, b);
```

## 12. Mockito Stubs for Multi-Method Mapper Interfaces

MyBatis `@Mapper` interfaces declare multiple methods and are **not** functional interfaces. A lambda
assigned to such a type fails compilation (`incompatible types: lambda expression is not a functional
interface`).

In unit tests that inject a mapper collaborator, use explicit Mockito stubs:

```java
OrderMapper mapper = mock(OrderMapper.class);
when(mapper.findByCustomerId(customerId))
    .thenReturn(Optional.of(order));
```

Do not assign a lambda to the mapper type even when only one method is exercised in the test.

## 13. MyBatis `@Select` Methods Must Not Return `void` Without a Result Handler

An annotated MyBatis `@Select` method executes through the query result-mapping path. Do not
declare it as `void` merely because the caller wants to ignore the result. Without a
`ResultHandler`, MyBatis uses the declared return type as the result-map type and can fail while
trying to materialize a returned row as `void`.

Return a concrete scalar or domain type that matches the query, or use a result handler when
intentionally consuming rows without returning them. This is especially important for SQL
functions that perform an action but still produce a result row, such as transaction-scoped
database lock functions.

## 14. Sealed Types Cannot Permit Another Package on the Classpath

`sealed` plus `permits` across packages requires a named module (`module-info.java`). A typical
Maven classpath build is an unnamed module. `javac` then rejects a public sealed type in package A
that permits an implementation in package B.

Do not choose `sealed` as the closure mechanism for a public API type whose only allowed
implementation lives in another package unless the project already compiles as named modules.
Compile the intended package split first. If that fails, keep a public interface (or abstract type)
and enforce closure with package-private constructors, a package-private factory, and an
architecture test that the allowed implementation is the only `implements` site.

Named-module `permits` across packages remains valid when the project actually uses JPMS.

## 15. Prefer imports over fully qualified type names

See `jvm_guidelines.md` #12 (Java and Kotlin).

## 16. Review Every Changed Java Declaration for Unused Surface

When reviewing a Java change, inspect every added or modified declaration for
unused imports, fields, methods, parameters, enum constants, and helper
objects. The Java compiler does not generally report unused members, and a
public or private declaration can remain dead while the tests stay green.

Use the complete branch diff and a branch-wide reference search, not only the
changed hunk. A declaration with no caller should be removed unless the code
or an authoritative design document records a current extension point.

## 17. Preserve Nullable Boundary States

At request and response boundaries, distinguish omitted, explicit `null`,
empty, and present values whenever the contract gives them different meaning.
For generated request models, inspect the actual nullable wrapper behavior and
test each state through the converter or mapper that production uses.

Guard nullable map keys, property names, and collection elements before lookup,
dereference, or validation. A null-safe test must prove the resulting public
outcome and must fail when the guard is removed.

## 18. Treat Downstream Error Payloads as Untrusted Input

An HTTP client must not pass a downstream error message or arbitrary details
directly to an external response or log. Map status and error codes through a
bounded vocabulary, keep only explicitly safe structured fields, and replace
free-form text with a service-owned message.

Add a test with a unique marker in both message and details and assert that the
marker cannot reach the response or logs. Apply the same rule to single-item
and batch converters.

## 19. Audit Changed Dependency Coordinates

When a Maven or Gradle dependency is added or its version changes, check the
coordinate against a current vulnerability source and verify compatibility with
the Java and framework versions in use. Do not limit the audit to newly added
artifacts; a version change can expose a new advisory or API incompatibility.

Run the relevant compile, unit, and integration checks for direct API usages.
When a dependency reserves a name or changes serialization behavior, update
fixtures through the dependency's supported API and add a regression test.

## 20. Enforce Required TLS at the Outbound Configuration Boundary

When the application directly creates outbound HTTP clients and accepts a
service URL from configuration, validate the URL scheme at configuration
binding time when the service contract requires encryption. A local loopback
exception must be explicit and limited to local or test use. Infrastructure
TLS does not replace validation when the application can otherwise be pointed
at plaintext transport.

## 21. Preserve the Raise-versus-Degrade Policy of Every Caller in Shared Helpers

Trace every shared conversion, mapping, or persistence helper to every caller in the changed branch. Each caller keeps its own raise-versus-degrade policy: infrastructure failures stay top-level failures, and only explicitly row-local problems may degrade to per-item results. When a helper is reused by a new caller, verify the reuse does not silently change an existing caller outcome from raise to degrade or the reverse. Add or verify a test per caller that proves a malformed infrastructure input fails the whole request where the caller raises, and only the offending item where the caller degrades.

```java
// Generic example for rule 21: one shared helper, two callers, different policies.
class OrderImportJob {
  // Single-item route: raises; the whole request fails on infrastructure errors.
  void importOne(Row row) {
    persist(mapRow(row));
  }

  // Batch route: degrades; only the offending item is recorded as skipped.
  BatchResult importBatch(List<Row> rows) {
    BatchResult result = new BatchResult();
    for (Row row : rows) {
      try {
        result.add(mapRow(row));
      } catch (RowLocalException e) {
        result.skipped(row, e);
      }
    }
    return result;
  }

  MappedRow mapRow(Row row) { /* shared conversion helper */ }
}
```

## 22. Exercise the Feature-Flag and Configuration Matrix for Independent Readiness

When a change touches a rollout flag or its configuration, review the complete flag and configuration matrix, not only the default deployment mode. Enumerate the flag values and configuration profiles the changed scope can combine, and require a discriminating assertion per combination that matters for readiness. An independent capability must not become ready or unavailable through an unrelated flag.

```java
// Generic example for rule 22: an unrelated flag combination flips capability readiness.
// Readiness check couples two independent flags:
boolean isExportReady() {
  return exportFlag.isEnabled() && importFlag.isEnabled();  // export readiness must not depend on importFlag
}

// Review finding: with exportFlag enabled and importFlag disabled, isExportReady()
// returns false even though export has all its own dependencies in place.
// Required matrix assertions (one per combination that matters for readiness):
//   exportFlag=on,  importFlag=on  -> isExportReady() == true
//   exportFlag=on,  importFlag=off -> isExportReady() == true  (fails before the fix)
//   exportFlag=off, importFlag=on  -> isExportReady() == false
```

## 23. Enforce Time Budgets at the Last Transport Boundary and Audit Timeout Resource Lifecycles

Verify time-budget enforcement at the last transport boundary: a budget can expire after the controller returns but before the serialized response is emitted, so the check must cover the final write to the client, not only the handler method (directly when the application owns serialization, or at the outermost application-owned boundary per the framework case below). Inspect scheduled executors, callbacks, and cleanup paths for per-request resources that outlive the request after a timeout, and require evidence they are released or bounded. When the application owns serialization or streaming, the budget check must cover the final write. When the framework performs serialization, require evidence that budget enforcement sits at the outermost application-owned boundary, such as a filter or interceptor, and record the framework-owned final write as an accepted residual with its rationale in the review's durable record, such as the staging doc's Release-gate ledger or a backlog item with an owner.

```java
// Generic example for rule 23: the budget expires between handler return and serialization.
ResponseEntity<Report> getReport(Request req) {
  Deadline budget = Deadline.from(req);           // 5s budget for the whole request
  Report report = reportService.build(req, budget);
  return ResponseEntity.ok(report);               // handler returns within budget
}

// The serializer runs after the handler returns; the budget is not checked there:
void writeResponse(ResponseEntity<Report> response, OutputStream out) {
  byte[] body = serialize(response.getBody());    // slow serialization, budget already expired
  out.write(body);                                // final write to the client is unbounded
}

// Review finding: budget.remaining() must be checked before the final client write, and any
// per-request executor or callback scheduled by reportService must be cancelled or bounded
// when the budget expires, not left running past the request lifetime.
```

## 24. Add an Executable Compatibility Witness for Changed Direct API Usage

For every value shape that a changed direct call to a dependency API relies on, add a small executable compatibility witness: a test or scratch check that invokes the changed call against the upgraded dependency version. Compilation is not compatibility: a dependency can compile cleanly while rejecting a value at runtime because of reserved names, added validation, or changed default behavior. The witness must exercise the value shapes the change relies on and record the observed behavior. The witness must run hermetically: no live services and no paid APIs. When a dependency API cannot be exercised without real infrastructure, record a static compatibility analysis of the changed call, such as the upgraded artifact's source or changelog and rejection-path reading, as the evidence and note the residual runtime risk in the review's durable record, such as the Release-gate ledger or a backlog item with an owner. When a coordinate change alters many direct call sites, prioritize the value shapes the change relies on rather than every call site. See also #19 for the advisory audit.

```java
// Generic example for rule 24: a reserved name accepted at compile time, rejected at runtime.
// Upgraded dependency declares a name validator; this compiles cleanly:
registry.register("order", handler);          // fine
registry.register("new", otherHandler);       // compiles, but "new" is reserved in v2

// Executable compatibility witness (a test against the upgraded version):
@Test
void witnessReservedNameRejection() {
  Registry registry = new Registry();
  registry.register("order", handler);        // passes: value shape the change relies on
  assertThatThrownBy(() -> registry.register("new", otherHandler))
      .isInstanceOf(ReservedNameException.class)
      .hasMessageContaining("reserved");      // observed behavior recorded in the test
}
```

## 25. Reconcile Living-Documentation Status Claims with Implementation Evidence

Reconcile every changed living-documentation status claim with implementation evidence: an integration described as active needs an executable consumer or producer, configuration, or an integration witness in the changed branch. When a status claim cannot be evidenced because scope is intentionally deferred, require a durable backlog item with an explicit owner and handoff instead of leaving the deferral only in review notes.

```
Generic example for rule 25: an active claim without an executable consumer.

Living doc (changed paragraph):
  "The notification integration is active and consumes events from the order stream."

Reconciliation in the changed branch:
  - Consumer class: none found (no listener annotation, no scheduler, no inbound adapter).
  - Configuration: notification.consumer.* keys exist but no code reads them.
  - Test witness: no test starts a consumer or asserts a consumed event.

Review finding: the claim cannot stay "active". Either restore an executable consumer
or correct the claim, and because the consumer is intentionally deferred this quarter,
record a durable backlog item:

  Backlog item: "Restore notification stream consumer"
  Owner: feature team lead (named in the ticket, not in review notes)
  Handoff: configuration keys documented as dormant; revisit before the next release note.
```
