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
- `@Scheduled` methods: verify thread pool sizing. Default is single-threaded — one slow task blocks all others.
- Bean lifecycle: `@PostConstruct` runs before the application is fully wired. Do not call other beans that depend on late initialization.
- Profile-conditional beans: verify test profiles wire the correct implementations.

## Java-Specific Concerns

- Enum-to-enum mapping: flag `OtherEnum.valueOf(sourceEnum.name())` in factory methods as a compile-time safety risk. Prefer exhaustive `switch` expressions — they fail at compile time when enum constants drift, while `valueOf` throws `IllegalArgumentException` at runtime. The `valueOf` shortcut can look like a valid simplification when enum names currently match, but it removes the coverage guarantee silently.
- Null safety: prefer `Optional` return types for query methods. Never return null from a method declared to return a collection.
- Stream API: streams are single-use. Reusing a closed stream throws `IllegalStateException`.
- Checked exceptions: verify exception handling contracts match interface declarations. Wrapping checked exceptions in `RuntimeException` loses the contract.
- Generics and type erasure: verify runtime type checks account for erasure. `instanceof` on generic types is always unchecked.
- `equals`/`hashCode` contract: if one is overridden, both must be. Mutable fields in `hashCode` break `HashMap` behavior.
- Resource management: use try-with-resources for `AutoCloseable`. Verify `finally` blocks do not swallow original exceptions.

## Transport Exception Mapping

- In transport converters, registries, and dispatchers: verify that ALL client-caused error paths (unsupported enum values, null discriminators from Jackson unknown-value handling, unknown operation types) throw typed domain exceptions mapped to 4xx — never generic `IllegalArgumentException`/`IllegalStateException` that fall through to the 500 handler.
- When a `Map.get()` or `EnumMap.get()` returns null for a client-supplied key, the resulting error must surface as 400, not 500.

## Collection Invariants in Records/Commands

- Domain records, commands, and DTOs with collection parameters: verify compact constructors check for null elements (not just null/empty). A missing `stream().anyMatch(Objects::isNull)` guard allows NPEs to surface later at runtime in hard-to-diagnose locations.

## Observability

- Structured logging: use SLF4J placeholders (`log.info("msg {}", var)`) not string concatenation.
- No PII in logs. System identifiers are not PII.
- Micrometer metrics: counters, timers, and gauges for key operations.
- Trace context propagation across async boundaries.
- Error counters for catch blocks that swallow exceptions.

## Build and Dependency

- Dependency versions: check for known CVEs in newly added dependencies.
- Maven/Gradle plugin versions: verify compatibility with Java version.
- Test scope: test utilities must use `test` scope, not `compile`.
