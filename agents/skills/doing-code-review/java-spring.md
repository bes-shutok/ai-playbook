# Language Overlay: Java + Spring

Additional review context for Java/Spring projects. Append to each sub-agent prompt.

## Framework Lifecycle Awareness

- For every changed implementation class, identify its parent class, implemented interfaces, annotations, and framework lifecycle hooks.
- Check for non-obvious inherited behavior:
  - Default methods that compile but are unsafe for this implementation
  - Optional lifecycle/error hooks that should be overridden
  - Parent/interface contracts that require exceptions to be swallowed, rethrown, or converted
  - Methods added to an interface where existing implementations silently inherit a generic default
- `@ExceptionHandler` methods silently consume exceptions. No log is created unless written explicitly. For 400 client errors suggest DEBUG-level logging at most; for unexpected server errors suggest WARN/ERROR.

## Spring-Specific Concerns

- `@Transactional` propagation: verify scope covers the full logical unit. Watch for self-invocation bypassing the proxy.
- `@Async` methods must return `void` or `Future`. Exceptions in async methods are lost unless a custom `AsyncUncaughtExceptionHandler` is configured.
- `@Scheduled` methods: verify thread pool sizing. Default is single-threaded: one slow task blocks all others.
- Bean lifecycle: `@PostConstruct` runs before the application is fully wired. Do not call other beans that depend on late initialization.
- Profile-conditional beans: verify test profiles wire the correct implementations.

## Java-Specific Concerns

- Enum-to-enum mapping: flag `OtherEnum.valueOf(sourceEnum.name())` in factory methods as a compile-time safety risk. Prefer exhaustive `switch` expressions: they fail at compile time when enum constants drift, while `valueOf` throws `IllegalArgumentException` at runtime. The `valueOf` shortcut can look like a valid simplification when enum names currently match, but it removes the coverage guarantee silently.
- Null safety: prefer `Optional` return types for query methods. Never return null from a method declared to return a collection.
- Stream API: streams are single-use. Reusing a closed stream throws `IllegalStateException`.
- Checked exceptions: verify exception handling contracts match interface declarations. Wrapping checked exceptions in `RuntimeException` loses the contract.
- Generics and type erasure: verify runtime type checks account for erasure. `instanceof` on generic types is always unchecked.
- `equals`/`hashCode` contract: if one is overridden, both must be. Mutable fields in `hashCode` break `HashMap` behavior.
- Resource management: use try-with-resources for `AutoCloseable`. Verify `finally` blocks do not swallow original exceptions.

## Transport Exception Mapping

- In transport converters, registries, and dispatchers: verify that ALL client-caused error paths (unsupported enum values, null discriminators from Jackson unknown-value handling, unknown operation types) throw typed domain exceptions mapped to 4xx, never generic `IllegalArgumentException`/`IllegalStateException` that fall through to the 500 handler.
- When a `Map.get()` or `EnumMap.get()` returns null for a client-supplied key, the resulting error must surface as 400, not 500.
- **Endpoint-owned error taxonomy:** a typed 4xx is not enough when the exception maps to the **wrong module error code** for that route. Match structural request-shape failures to the endpoint's owning module (example: null elements or missing discriminators on `/v1/user-updates` use profile-owned `InvalidPropertyValueException` / profile `ApiError` codes, consistent with `OperationConverterRegistry`, not consent-updates `InvalidConsentUpdateRequestException`). Field validation that is clearly consent-op-specific may still use consent-owned exceptions. Flag `architecture#exception-ownership` or `quality#wrong-endpoint-error-code` when HTTP status is 400 but the wire `code` / handler ownership is wrong for the path.

## Collection Invariants in Records/Commands

- Domain records, commands, and DTOs with collection parameters: verify compact constructors check for null elements (not just null/empty). A missing `stream().anyMatch(Objects::isNull)` guard allows NPEs to surface later at runtime in hard-to-diagnose locations.
- OpenAPI Generator optional array properties on request models often default to `new ArrayList<>()`. When the client omits the field from JSON, Jackson leaves the empty list in place (not `null`). Partial-update handlers that only check `steps == null` will still forward `[]` upstream. Treat omitted and empty collections as "no change" when the upstream contract distinguishes `null` from empty.
- Maps abstract `quality#validate-after-assign`: when a compact constructor does `List.copyOf(...)` (or similar) and only then checks emptiness, prefer null/empty checks on the inputs before the copy so null lists fail with the type's validation error instead of NPE from `copyOf`.

## Request-boundary harness fidelity (Spring)

Maps abstract `testing#harness-fidelity-gap` / `testing#coverage-claim-unchecked` to Spring MVC:

- New `@Component` / `@WebFilter` `OncePerRequestFilter`, `HandlerInterceptor`, or `FilterRegistrationBean` needs a test that exercises the **Spring-registered** filter/interceptor chain (for example `@SpringBootTest` with `@AutoConfigureMockMvc`, `MockMvcBuilders.webAppContextSetup`, or a slice that loads the production filter beans).
- `MockMvcBuilders.standaloneSetup(controller)` without explicitly adding the production filters does **not** close harness fidelity for a production `@Component` filter.
- Manually `new MyFilter(...)` unit tests are useful for branch logic but do not prove dispatcher registration or path matching.
- Resolve test class naming and Surefire vs Failsafe placement from the Guideline Pack: when company-scoped, read **company guidelines together with project guidelines** (and sibling tests in-repo). Prefer `company_guidelines_master` over a repo mirror. This overlay does not require any particular class-name suffix.

## Observability

- Structured logging: use SLF4J placeholders (`log.info("msg {}", var)`) not string concatenation.
- No PII in logs. System identifiers are not PII.
- Micrometer metrics: counters, timers, and gauges for key operations.
- Trace context propagation across async boundaries.
- Error counters for catch blocks that swallow exceptions.

## Spring Cloud Config / per-workspace overlays

- For active `spring.application.name` (and similar identity keys) in config-repo `.properties`, compare to the **target service** packaged `application.yml`. Do not copy a sibling service's name pattern (for example a long prefixed name `example-crm-*` vs a short unprefixed `crm-*`) from ADR comments or filenames alone.
- Before requiring a key because a sibling overlay has it, confirm this service has a consumer (binding, post-processor, or fail-fast validator).
- Before treating a missing overlay key as a boot crash, check whether the JAR already supplies a non-empty default; if it does, prefer a Low go-live checklist note.

## MyBatis (annotation mappers)

- Mutating SQL mapped as `@Select` (`INSERT` / `UPDATE` / `DELETE`, including write CTEs with `RETURNING`) must declare `@Options(flushCache = Options.FlushCachePolicy.TRUE)`. Default SELECT cache policy leaves SqlSession local cache stale across same-transaction retries or follow-up reads.
- Prefer the same `@Options(flushCache = …)` on `SELECT … FOR UPDATE` that gates a later write when callers re-read in the same session.
- When a migration adds or renames tables/indexes that local bootstrap checks, flag missing updates to operator verify scripts (for example `docker/verify-local-schema.sh` `EXPECTED_TABLES` / `EXPECTED_INDEXES`) in the same change set.
- Documented config shapes (ISO alpha-2, enum sets, regex) must fail at the earliest startup gate (`EnvironmentPostProcessor`, `@PostConstruct` on `@ConfigurationProperties`, or fail-fast binder), not only via trim/uppercase or a later binder error.

## Build and Dependency

- Dependency coordinates: apply `java_guidelines.md` #19 to every added or
  version-changed dependency, including managed versions. Check current
  advisories and compile/test direct API usages after the change.
- Maven/Gradle plugin versions: verify compatibility with Java version.
- Test scope: test utilities must use `test` scope, not `compile`.

## Review-wide Java checks

For every Java/Spring review, the orchestrator must include the shared
`java_guidelines.md` and `jvm_guidelines.md` in the Guideline Pack and record
the applied rule hints in staging metadata. Workers must apply these checks to
the complete branch diff, not only to the highlighted line:

- `java_guidelines.md` #16: unused imports and unused declarations, including
  fields, methods, parameters, enum constants, and helpers.
- `java_guidelines.md` #17: omitted, explicit-null, empty, and present input
  states at generated-model and mapper boundaries.
- `java_guidelines.md` #18: downstream error messages and details treated as
  untrusted before response or log mapping.
- `java_guidelines.md` #19: advisory and API-compatibility checks for changed
  dependency coordinates.
- `java_guidelines.md` #20: required outbound TLS validation at configuration
  binding, with only an explicit loopback exception.
- `java_guidelines.md` #21: raise-versus-degrade policy of every caller at
  shared conversion and persistence helpers.
- `java_guidelines.md` #22: flag and configuration matrix coverage for
  independent capability readiness.
- `java_guidelines.md` #23: time budgets at the last transport boundary and
  scheduled timeout resource lifecycles.
- `java_guidelines.md` #24: executable compatibility witness for changed
  direct API usage.
- `java_guidelines.md` #25: living-documentation status claims reconciled
  with implementation evidence.

Assign findings to the normal owners: unused surface to simplification,
boundary behavior to quality or testing, error leakage and transport security
to risk, and dependency wiring or compatibility to implementation or risk.
Shared-helper raise-versus-degrade tracing belongs to quality;
the flag and configuration matrix and timeout lifecycle to risk;
the compatibility witness to implementation;
living-documentation reconciliation to documentation.

## Rollout, timeout, and shared-helper triggers (Spring)

- Shared `@Component` converters, mappers, or persistence helpers reused by a
  new caller: apply #21 to every caller.
- Rollout flags, `@ConditionalOnProperty` wiring, or profile-specific
  configuration: apply #22 to the flag and configuration matrix.
- Per-request time budgets, resilience timeout annotations, or `@Scheduled`
  cleanup: apply #23 at the last serialization and transport boundary and to
  scheduled resource lifecycles.
- Changed direct dependency API usage, especially after a coordinate change:
  apply #24 alongside #19.
- Changed living docs claiming an integration is active:
  apply #25 and reconcile with an executable consumer, producer, or witness.

## Message-driven handlers (Spring Kafka)

- **Framework defaults vs docs:** Before flagging a doc/code mismatch on broker or error-handler naming (DLT topic suffix, retry topic names), confirm the default for the dependency version on the classpath. Major-version upgrades often change suffixes and resolver behavior; stale ops docs or prior review threads may cite an older default.
- **Caught exceptions vs container retry:** When a `@KafkaListener` catches exceptions inside a per-item loop, the method can return successfully and the container commits the offset without invoking `DefaultErrorHandler` retry/DLT. Narrow catches to expected domain outcomes; let infrastructure failures propagate unless idempotency makes full-message retry safe.
- **Validation bounds vs persistence:** Inbound record validation (`@Valid`, Bean Validation) must fit the tightest downstream storage limit (column length, composite unique key size, lookup key width). Persistence overflow surfaces as a different exception type than `ConstraintViolationException` and may not follow the fast non-retryable DLT path.
