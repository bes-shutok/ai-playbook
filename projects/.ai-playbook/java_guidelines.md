# Java Development Guidelines

Java-specific development patterns applicable across projects.
Instruction files reference numbered clauses here rather than restating full text.

Shared JVM rules (Spring, Reactor, SLF4J) live in `~/Projects/.ai-playbook/jvm_guidelines.md`.
Language-agnostic rules live in `~/Projects/.ai-playbook/coding_guidelines.md`.
Language-agnostic agent workflow lessons live in `~/Projects/.ai-playbook/agent_workflow_guidelines.md`.

## 1. Spring `@ConfigurationProperties` — Constructor vs Setter Injection Validation

See `jvm_guidelines.md #1`. Java-specific: prefer constructor binding with `@ConstructorBinding`
or record-style constructors, and use JSR-303 `@Validated` with constraints on parameters.

## 2. Mockito Stubbing for Reactor / R2DBC Errors

See `jvm_guidelines.md #4`. Mockito-specific: use `thenReturn(Mono.error(...))` — never
`thenThrow()`.

## 3. Mockito `timeout()` for Fire-and-Forget Async Assertions

See `jvm_guidelines.md #5`. Mockito-specific: use `verify(collaborator, timeout(1000).times(1))`.

## 4. Config Validation Failures Must Not Be Swallowed by Infrastructure Catch Blocks

See `coding_guidelines.md #7`.

## 5. Numbered Enum Slot Reservation — Use an Explicit Entry

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

## 7. Spring `@ConfigurationProperties` — Use `Duration` for Duration Fields

See `jvm_guidelines.md #2`.

## 8. Spring Cloud Config — Do Not Bundle `spring.application.name`

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
- `rate(instant_virtuals_error_METRICS8002{}[5m])` — **does not match** (uppercase)
- `rate(instant_virtuals_error_metrics8002_total[5m])` — **correct**
- Gauges do **not** get the `_total` suffix; counters always do.
- Micrometer also converts camelCase segments to snake_case (e.g. `myCounter` → `my_counter_total`).

When debugging a non-matching PromQL expression, verify the actual registered name via the
Prometheus `/metrics` scrape endpoint or Grafana's metric browser before assuming the query is
logically wrong.

## 11. Collection Defensive Copy Idioms

**Do not double-wrap unmodifiable copies.** `Set.copyOf()`, `List.copyOf()`, and `Map.copyOf()` already return unmodifiable copies — wrapping them in `Collections.unmodifiable*()` adds no protection and signals misunderstanding.

```java
// Wrong — redundant wrapper
this.items = Collections.unmodifiableSet(Set.copyOf(items));

// Correct
this.items = Set.copyOf(items);
```

**Let the domain method own the single defensive copy.** When a domain aggregate's mutation method calls `copyOf()` internally, the calling application service must not pre-copy the same collection before passing it in. Passing an already-copied collection wastes an allocation; more importantly, the responsibility for defensive copying should live in one place — the aggregate boundary.

```java
// Wrong — pre-copy in application service
profile.patchIdentities(List.copyOf(identities));

// Correct — aggregate owns the defensive copy
profile.patchIdentities(identities);  // aggregate calls List.copyOf internally
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
