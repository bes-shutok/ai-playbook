# JVM Development Guidelines

Rules shared across JVM languages (Kotlin, Java). Language-specific syntax and examples
are shown side by side. Instruction files reference numbered clauses here rather than
restating full text.

For Kotlin-only patterns see `kotlin_guidelines.md`. For Java-only patterns see
`java_guidelines.md`. For language-agnostic rules see `coding_guidelines.md`.

## 1. Spring `@ConfigurationProperties` — Setter Injection Bypasses Constructor Validation

`@ConfigurationProperties` classes with mutable fields (setter injection) run the no-arg
constructor first with field defaults, then Spring sets properties via setters. Validation in
constructors, `init {}` blocks, or field initializers sees defaults — not the configured values.

Use JSR-303 `@Validated` with constraints on fields, or `@PostConstruct` for cross-field
validation. Never rely on constructor-time validation for setter-injected config properties.

**Kotlin:**
```kotlin
@Validated
@ConfigurationProperties(prefix = "my.feature")
class MyProps {
    @field:Min(1)                          // field: prefix required in Kotlin
    var windowHours: Long = 8
}
```

**Java:**
```java
@Validated
@ConfigurationProperties(prefix = "my.feature")
public record MyProps(@Min(1) long windowHours) {}
// Or with setter injection + @PostConstruct for cross-field validation
```

## 2. Spring `@ConfigurationProperties` — Use `Duration` for Duration Fields

Use `Duration` as the field type for any `@ConfigurationProperties` duration property — not
`Long`/`Int` with a unit suffix (e.g. `windowHours`, `maxIdleMinutes`). Spring Boot parses
human-readable strings automatically via `DurationStyle`.

| Config value | Parsed as |
|---|---|
| `8h` | `Duration.ofHours(8)` |
| `3m` | `Duration.ofMinutes(3)` |
| `30s` | `Duration.ofSeconds(30)` |
| `500ms` | `Duration.ofMillis(500)` |
| `1d` | `Duration.ofDays(1)` |
| `PT8H` | ISO-8601, also supported |

Validate positivity in a startup `SmartInitializingSingleton` — not in `init {}` or
constructors (see rule #1).

**Kotlin:**
```kotlin
data class MyProperties(var window: Duration = Duration.ofHours(8))
```

**Java:**
```java
@ConfigurationProperties("my.feature")
public class MyProperties {
    private Duration window = Duration.ofHours(8);
    // getter/setter
}
```

**Startup validation (both languages):**
```kotlin
@Bean
fun myPropertiesValidator(props: MyProperties): SmartInitializingSingleton =
    SmartInitializingSingleton {
        require(props.window > Duration.ZERO) { "window must be positive, got ${props.window}" }
    }
```

## 3. Spring Cloud Config — Do Not Bundle `spring.application.name`

In any Spring Boot service that uses Spring Cloud Config, do not set
`spring.application.name` in the bundled `application.yml` (or any resource file packaged in
the jar). The bundled value takes precedence over `bootstrap.properties` and environment
variables in Spring Boot's property-source ordering, causing the service to load the wrong
profile and silently drop deployment-supplied overrides (Feign URL mappings, circuit-breaker
settings, namespace-scoped service discovery entries).

Supply the name externally only (K8s env var, Helm values, `bootstrap.properties`).

**Observed failure:** `my-service` on UAT — Feign URL override for `my-dependency`
was dropped, causing `UnknownHostException` (wrong K8s namespace) and bet placement timeouts.

**Correct pattern (both languages):**
```yaml
# application.yml — do NOT add spring.application.name here
your-company:
  deployment:
    app-id: my-service
```
```properties
# bootstrap.properties / K8s SPRING_APPLICATION_NAME env var — correct location
spring.application.name=my-service-tz
```

**Exception:** Services that do **not** use Spring Cloud Config may set the name freely in
`application.yml`.

See also: `company-guidelines.md #46`.

## 4. Mocking Reactive Types (Mono/Flux) — Return Error Signals, Don't Throw

When stubbing a method that returns `Mono<T>` or `Flux<T>` (R2DBC repository,
Redis/Lettuce operation, WebClient call), return the error as a reactive signal
(`Mono.error(...)`, `Flux.error(...)`) — never throw synchronously.

A synchronous throw propagates before returning any reactive type, bypassing all reactive
error handlers (`onErrorResume`, `onErrorReturn`, `.catch {}`).

**Kotlin (MockK):**
```kotlin
// Wrong — bypasses reactive pipeline:
every { redisOps.get(key) } throws RuntimeException("redis error")
// Correct — error arrives as reactive signal:
every { redisOps.get(key) } returns Mono.error(RuntimeException("redis error"))
```

**Java (Mockito):**
```java
// Wrong — throws synchronously, bypasses reactive pipeline:
when(repository.findById(id)).thenThrow(new RuntimeException("db error"));
// Correct — error arrives as reactive signal:
when(repository.findById(id)).thenReturn(Mono.error(new RuntimeException("db error")));
```

## 5. Async Fire-and-Forget Test Assertions — Poll, Don't Sleep

When testing a production method that delegates to an async executor or fire-and-forget
coroutine, do not use fixed sleeps (`Thread.sleep(N)`, `delay(N)`) before verifying.
Fixed sleeps are non-deterministic under CI load and inflate test duration.

Use the mocking framework's polling verification instead. The framework polls the interaction
registry until the expected call count is recorded or the timeout expires.

**Kotlin (MockK):**
```kotlin
// Wrong — timing-dependent:
runBlocking { sut.publishAsync(event); delay(200) }
coVerify(exactly = 1) { collaborator.doWork(any()) }

// Correct — deterministic polling:
runBlocking { sut.publishAsync(event) }
coVerify(timeout = 1000, exactly = 1) { collaborator.doWork(any()) }
```

**Java (Mockito):**
```java
// Wrong — timing-dependent:
sut.publishAsync(event);
Thread.sleep(200);
verify(collaborator, times(1)).doWork(any());

// Correct — deterministic polling:
sut.publishAsync(event);
verify(collaborator, timeout(1000).times(1)).doWork(any());
```

For **zero-call assertions** (`exactly = 0` / `times(0)`), distinguish two cases:

- **Structurally guaranteed non-call**: the production code path provably never invokes the
  method regardless of async state. Assert immediately — no wait needed.
- **Timing-uncertain non-call**: the async work *might* call the method. A fixed sleep is
  imperfect but acceptable. Polling `timeout(T).times(0)` is **not** a substitute — it passes
  immediately because zero calls exist at check time.

## 6. SLF4J Logging — Always Pass the Exception Object, Not `e.message`

Pass the exception object (`Throwable`) as the **last** argument to `log.error(...)` /
`log.warn(...)`. SLF4J detects a trailing `Throwable` and appends the full stack trace.
Passing `e.message` (a `String`) loses the stack trace entirely — diagnosing the failure
then requires reproducing it.

**Both Kotlin and Java:**
```kotlin
// Wrong — stack trace lost
log.error("Failed for userId={}: {}", userId, e.message)

// Correct — full stack trace preserved
log.error("Failed for userId={}", userId, e)
```

This applies even in intentionally fail-open catch blocks: an infrastructure error is still
an ERROR, and the stack trace is the primary debugging signal.

## 7. Request DTO Validation — Do Not Duplicate Bean Validation Constraints

When Jakarta Bean Validation annotations on a request DTO already express a constraint
(`@NotNull`, `@Size`, `@Pattern`, etc.), do not re-implement the same check in a controller,
mapper, or transport converter.

In company-scoped repos see `company-guidelines.md` #12. In contract-first OpenAPI CRM
services see the owning repo's `project-guidelines.md` input validation trust boundary rule
for schema-as-source and test guardrails.

## 8. Spring Boot 3.5 — Register `EnvironmentPostProcessor` in `spring.factories`

On Spring Boot 3.5, `META-INF/spring/org.springframework.boot.env.EnvironmentPostProcessor`
alone does **not** load custom `EnvironmentPostProcessor` implementations. Boot still discovers
EPPs via `META-INF/spring.factories` (`EnvironmentPostProcessorsFactory.fromSpringFactories`).

Register both when migrating forward-compatible:

```properties
# META-INF/spring.factories
org.springframework.boot.env.EnvironmentPostProcessor=com.example.MyEnvironmentPostProcessor
```

**Observed failure:** full `@SpringBootTest` contexts failed during `@ConfigurationProperties`
`@PostConstruct` validation because deploy-time defaults never ran; unit tests against an
isolated `ConfigurableEnvironment` still passed.

Before relying on a new EPP in integration tests, confirm discovery with a full-context boot
test or inspect `EnvironmentPostProcessor` loading for your Boot version.

## 9. Spring Boot 3.4+: prefer `@MockitoBean` / `@MockitoSpyBean` over `@MockBean` / `@SpyBean`

On Spring Boot 3.4+, `org.springframework.boot.test.mock.mockito.MockBean` and
`SpyBean` are deprecated for removal in Boot 4.0. Use Spring Framework bean overrides instead:

| Deprecated (Boot) | Replacement (Framework) | Import |
|---|---|---|
| `@MockBean` | `@MockitoBean` | `org.springframework.test.context.bean.override.mockito.MockitoBean` |
| `@SpyBean` | `@MockitoSpyBean` | `org.springframework.test.context.bean.override.mockito.MockitoSpyBean` |

**Do not** introduce new `@MockBean` / `@SpyBean` usages on Boot 3.4+ projects. When touching a
test that still uses the deprecated annotations, migrate that test (or the whole suite in the
same change set when the touch is small).

**Behavioral note:** `@MockitoSpyBean` requires an existing bean of that type in the context
(it wraps the real instance). Unlike legacy `@SpyBean`, it does not silently create a missing
bean. Prefer a real `@SpringBootTest` / slice context bean, or use
`@MockitoBean(answers = Answers.CALLS_REAL_METHODS)` only when a spy-without-existing-bean is
intentional.

**Java:**
```java
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;

@SpringBootTest
class ExampleIT {
    @MockitoSpyBean
    private SomeMapper someMapper;
}
```

## 10. `@ConditionalOnMissingBean` on `@Component` can self-skip

Do not put `@ConditionalOnMissingBean(OwnType.class)` (or the same type via
`@ConditionalOnMissingBean`) on a class that is itself a `@Component` /
`@Service` of `OwnType`. During condition evaluation Spring may already see
that candidate bean definition, so `OnBeanCondition` treats the type as
present and skips registration. Neutral or fallback beans then never appear.

**Required pattern:** register defaults from a `@Configuration` class with
`@Bean` methods annotated `@ConditionalOnMissingBean(OwnType.class)`. The
condition then checks for other beans of that type, not the defining method's
own candidate in a way that vacuously skips.

**Verify:** after wiring a missing-bean fallback, assert the bean exists in a
full application context (or a slice that loads that `@Configuration`), not
only that the class compiles.

## 11. Primary Actuator health includes every contributor

Spring Boot's primary `/actuator/health` group always includes every
`HealthIndicator` / `HealthContributor`. Setting
`management.health.group.<name>.exclude` (including a group named `default`)
does **not** remove a contributor from that primary aggregation. A
readiness-only indicator that is DOWN will still fail primary health and can
make integration tests or orchestrators treat the process as unhealthy.

**Required pattern:** register a `HealthEndpointGroupsPostProcessor` bean that
wraps `groups.getPrimary()` and returns `false` from `isMember` for the
contributor that must stay off primary health. Keep a separate named group
(and path) for the readiness-only probe.

**Verify:** assert primary `/actuator/health` stays UP when the excluded
contributor is OUT_OF_SERVICE, and assert the named group path still reports
that contributor's status.

## 12. Prefer imports over fully qualified type names

Use a normal `import` (or Kotlin import) and the simple name for annotations and
constructor or type references in production and test code. Do not write
`@org.springframework.stereotype.Component`, `@lombok.RequiredArgsConstructor`,
or `new com.example.Foo(...)` when a simple-name import is possible.

When review or self-check fixes one fully qualified name, scan every **PR-touched**
source file for the same pattern (FQN annotations and FQN `new` / type uses for
types this change introduced or already imports elsewhere) and fix them in the
same change set.

Keep fully qualified names only when intentional: `package-info` / module
metadata, or avoiding a simple-name clash (for example generated wire enums vs
domain enums with the same short name). Do not rewrite pre-existing FQN style
outside the PR diff just for uniformity.

Unused-import scanners do not catch this: both forms compile. Treat it as style
hygiene next to unused-import cleanup, not as the same check.

## 13. Classify sibling HTTP I/O at the adapter boundary

When a Spring `RestTemplate` / `RestClient` / `WebClient` call fails with
`ResourceAccessException`, catch it at the outbound adapter and map to an
explicit domain transport outcome before the error mapper runs. Do not let the
exception escape as an unhandled 500.

**Required pattern:**
1. Treat connect refused, DNS failure, and `HttpConnectTimeoutException` as
   **not-sent** (the request never reached the sibling).
2. Treat read timeout and other I/O after the request may have left as
   **unknown-commit** (or the project's equivalent).
3. Feed those outcomes into the same retry / client-error policy as HTTP status
   mapping. Do not emit caller `Retry-After` for not-sent or unknown-commit
   unless the project contract explicitly says otherwise.

**Verify:** unit tests for connect-refused and read-timeout paths; an
integration test that the published status and retry header match the outcome
class (including omit-`Retry-After` when required).

## 14. Selected Failsafe after reactor install: avoid `-am` when no-match fails hard

When selecting one IT (including a nested class) after `mvn -pl <module> -am ... install`,
run the Failsafe goal with `-pl <module>` only, **or** keep `-am` and set
`-Dfailsafe.failIfNoSpecifiedTests=false`.

`-am` is correct for compiling dependencies. It is the wrong Failsafe scope when
`failIfNoSpecifiedTests` stays true (Maven default): sibling reactor modules with
no matching IT fail before the target class runs.

After editing nested IT annotations or `@SpringBootTest(properties=...)`, run
`test-compile` (or install) before Failsafe so the selector does not load stale
classes.

When a plan Validation block must prove only Failsafe selectors, use this Failsafe
path after install. Do not treat a full reactor `verify` that fails on unrelated
Surefire outside the allowlist as a Failsafe regression.

## 15. Optional empty JSON columns: accept SQL NULL and `{}`

When an IT asserts an optional empty JSON/jsonb (or properties) column after a
write that omitted the map, accept both SQL `NULL` and empty-object forms
(`{}` / equivalent binder output) unless the production contract pins one
representation. Do not fail the suite on binder null-vs-empty drift for the
same semantic empty value.

## 16. Do not nest a blocking Awaitility await inside `untilAsserted`

`Awaitility.untilAsserted` already retries its assertion lambda on a poll
interval. Nesting another timed blocking await (for example a collection helper
that waits up to `Duration.ofSeconds(N)` for a minimum count) inside that
lambda multiplies timeouts, can return a partial snapshot mid-retry, and hides
which condition actually failed.

**Required pattern:**
1. Use `untilAsserted` only for a cheap, idempotent predicate (for example
   `assertThat(collector.count()).isGreaterThanOrEqualTo(1)`).
2. After the outer await succeeds, call the blocking snapshot or content await
   once outside the lambda (for example `awaitAtLeast(1, timeout)` then assert
   payload).
3. Prefer exact equality for expected signal counts when the scenario under test
   is deterministic; reserve `isGreaterThanOrEqualTo` for intentionally open
   lower bounds.

**Verify:** a Failsafe or unit selector that previously nested a collection
`awaitAtLeast` inside `untilAsserted` should fail-fast on the count predicate
alone when empty, and should assert body or ledger content only after the count
gate passes.

## 17. Retarget migration-resource tests when DDL moves across versions

When a change splits, renames, or relocates DDL from one Flyway script to
another (for example `V3__...` to `V4__...`), every test that loads migration
SQL via classpath resource path and asserts snippet content must be updated in
the same change set.

**Required pattern:**
1. Point `getResourceAsStream` / resource constants at the file that now owns
   the asserted objects (table, CHECK, column).
2. Refresh expected snippets for the new file's whitespace and formatting; do
   not keep padded column layouts from the previous script.
3. When a guardrail must cover an entire module schema that spans multiple
   scripts, load and assert each relevant migration (or concatenate explicitly),
   not only the historically first file.

**Failure mode:** AssertJ fails with the wrong file's header comments as
"actual" while the expected CHECK or column lives in a later version. Module
Surefire can stay green for adapters that never touch the stale resource until
the schema-resource test runs.

## 18. Floor `Duration.toMillis()` before PostgreSQL `SET LOCAL …_timeout`

When a config `Duration` is rendered into PostgreSQL `SET LOCAL lock_timeout` /
`statement_timeout` (or similar) as `'Nms'`, reject values whose
`toMillis()` is less than `1`.

`Duration.toMillis()` truncates toward zero. A positive sub-millisecond value
(for example `1ns`) passes `isZero()` / `isNegative()` checks but becomes
`0ms`. PostgreSQL treats `0` as unlimited for these settings, so the bound
disappears silently.

Apply the same floor to any other sink that only understands whole milliseconds
(for example Hikari `setConnectionTimeout(long)`).

**Verify:** a unit that sets `Duration.ofNanos(1)` (or any value with
`toMillis() == 0`) must fail validation before the session opens.

## 19. `-DskipTests` skips Failsafe; use `-Dsurefire.skip=true` for IT-only runs

Maven's `-DskipTests` skips both Surefire and Failsafe. A command that intends
to run only integration tests must not use `-DskipTests`.

**Required pattern:**
- Unit tests only: `mvn test` (or `-DskipITs` when verify is in the lifecycle)
- Integration tests only after compile: `-Dsurefire.skip=true` with Failsafe
  `-Dit.test=... verify`
- Skip everything: `-DskipTests` (both plugins)

**Failure mode:** `verify` reports `BUILD SUCCESS` with `Tests are skipped`
under Failsafe while the selected `*IT` classes never ran.

## 20. Drop perpetual "old migration path is null" asserts after a rename

Extends #17. After a Flyway script is renamed or removed, a one-time
`assertThat(getClass().getResource("/db/migration/Vold__…")).isNull()` check
proves the rename for that PR. Leaving it in the suite forever only re-checks
classpath absence on every Failsafe run and does not protect future renames.

**Required pattern:** update applied-version and live-resource assertions in the
same change set (#17). Do not keep absent-path null asserts as standing
coverage.

**Verify:** `FlywayIT` (or equivalent) asserts current applied versions and
loads only live migration resources.
