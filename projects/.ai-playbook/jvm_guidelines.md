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
