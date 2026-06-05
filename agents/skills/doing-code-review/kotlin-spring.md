# Language Overlay: Kotlin + Spring

Additional review context for Kotlin/Spring projects. Append to each sub-agent prompt.

## Kotlin-Specific Concerns

- **Null safety**: Kotlin's type system distinguishes nullable (`T?`) from non-nullable (`T`). Flag:
  - Unnecessary `!!` (non-null assertion) when safe call (`?.`) or `let` would work
  - Platform types from Java interop used without null checks
  - Nullable return types where the caller always does `!!` — consider making non-nullable
- **Data classes**: verify `copy()` usage does not accidentally preserve stale state. If a data class has mutable internal state, `copy()` is shallow.
- **Coroutines**:
  - Verify `suspend` functions are called within proper coroutine scope
  - `GlobalScope.launch` leaks coroutines — use structured concurrency (`coroutineScope`, `supervisorScope`)
  - Exception handling: `launch` vs `async` have different exception propagation. `async` stores exceptions in `Deferred`; uncaught until `.await()`.
  - `Dispatchers.IO` for blocking calls; never block `Dispatchers.Default`
- **Extension functions**: verify they do not shadow member functions. Member functions always win in resolution.
- **Sealed classes/interfaces**: verify `when` expressions are exhaustive. Non-exhaustive `when` on sealed types compiles but misses future additions.
- **Companion object**: avoid putting heavy initialization in companion. It runs at class-load time and cannot be injected/mocked.

## Spring + Kotlin Integration

- **Constructor injection**: Kotlin classes with single constructor do not need `@Autowired`. Multiple constructors need explicit annotation.
- **`@Transactional` on suspend functions**: Spring's `@Transactional` does NOT work with coroutines by default. Use `TransactionalOperator` for reactive/coroutine transactions.
- **`open` classes**: Spring requires classes and methods to be `open` for proxying. The `kotlin-spring` plugin handles this for `@Component`, `@Service`, etc. — but verify custom annotations are covered.
- **Jackson + Kotlin**: use `jackson-module-kotlin`. Without it, deserialization of data classes fails at runtime (no default constructor). Default parameter values only work with this module.
- **`lateinit var`**: acceptable for Spring-injected fields. Do not use for fields that might be accessed before injection completes (e.g. in `init {}` blocks).

## Observability

- Structured logging: use `KotlinLogging.logger {}` or SLF4J. Avoid string templates in log calls at disabled levels — use lambda-based logging.
- Coroutine context: verify `MDC` (Mapped Diagnostic Context) propagates across coroutine boundaries. Use `MDCContext()` dispatcher element.
- No PII in logs. System identifiers are not PII.

## Testing

- **MockK** over Mockito for Kotlin: Mockito struggles with final classes, companion objects, and coroutines.
- **`runTest`** for coroutine tests: ensures proper virtual time advancement and structured concurrency.
- Verify `@SpringBootTest` tests do not accidentally load the full context when a slice (`@WebMvcTest`, `@DataJpaTest`) suffices.

## Transport Exception Mapping

- In transport converters, registries, and dispatchers: verify that ALL client-caused error paths (unsupported enum values, null discriminators, unknown operation types) throw typed domain exceptions mapped to 4xx — never generic `IllegalArgumentException`/`IllegalStateException` that fall through to the 500 handler.
- When a `Map[key]` or `enumValues` lookup returns null for a client-supplied key, the resulting error must surface as 400, not 500.

## Collection Invariants in Data Classes/Commands

- Data classes and command objects with collection parameters: verify constructors or `init {}` blocks check for null elements (relevant for Java-interop collections where `List<T>` can still contain nulls at runtime despite non-nullable type parameter). A missing guard allows NPEs to surface later in hard-to-diagnose locations.
