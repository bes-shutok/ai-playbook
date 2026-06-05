# Kotlin Development Guidelines

Kotlin-specific development patterns applicable across projects.
Instruction files reference numbered clauses here rather than restating full text.

Shared JVM rules (Spring, Reactor, SLF4J) live in `~/Projects/.ai-playbook/jvm_guidelines.md`.
Language-agnostic rules live in `~/Projects/.ai-playbook/coding_guidelines.md`.
Language-agnostic agent workflow lessons live in `~/Projects/.ai-playbook/agent_workflow_guidelines.md`.

## 1. Test Method Body Style

In Kotlin, always use block body (`fun f() { ... }`) for `@Test` methods. Expression body
(`fun f() = expr`) infers the return type from the last expression: Kotest's `shouldBe`
returns its receiver (`T`), `assertThrows<T>` returns `T`. JUnit 5 silently skips
non-`void` test methods — no failure, no warning — so a broken expression-body test appears
green while never executing. The only structurally safe exception is when the last statement
is a MockK `verify`/`coVerify` call (which returns `Unit`/`void`), but prefer block body
consistently to avoid silent regressions when assertions change.

A related anti-pattern is `@Test fun f() = { body... }`. This is expression body where
the function returns a **lambda** `() -> T`; the body is never executed. The `=` and the
extra curly braces make it look like a block body but the semantics are entirely different.
Always check that a `@Test` method has `fun f() {` (no `=`) rather than `fun f() = {`.

## 2. MockK — `clearAllMocks()` and Relaxed Mocks

`clearAllMocks()` resets recorded calls and stubs; it does NOT remove the `relaxed` flag
from annotation-based mocks (`@MockK(relaxed = true)`). The `relaxed` setting is attached
to the mock object itself at creation time and survives `clearAllMocks()`. Do not report
"relaxed stubs cleared by `clearAllMocks()`" as a bug without first verifying with a
test run.

## 3. Asserting Suppressed Exceptions

When a test name claims an exception is suppressed (e.g. "exception_is_suppressed"), use
`assertDoesNotThrow { }` to actually assert it. A bare call that doesn't throw only passes
implicitly — a future regression where an exception escapes fails with a cryptic error
instead of a clear assertion message.

## 4. Coroutine Concurrency Test Determinism

Kotlin coroutine concurrency tests that use real `Dispatchers.IO` and `delay()` for overlap
detection are non-deterministic under CI load or single-thread pools. Replace real delays
with `TestCoroutineScheduler` / `UnconfinedTestDispatcher` coordination. Use
`shouldBeGreaterThan` (not `shouldBe true`) for atomic counter assertions.

## 5. `also {}` vs `let {}` in Null-Safe Chains

`also {}` returns the **receiver**, not the lambda result. A chain like
`?.also { id -> dao.findById(id) }` silently discards the `findById` result and always
continues — no null-gating occurs. Use `?.let { id -> dao.findById(id) }` when the chain
must gate on the lambda's return value (e.g. null-propagation for an existence check).

## 6. MockK Varargs Matchers

When verifying a MockK call that uses varargs, include one matcher per vararg argument.
Providing fewer matchers silently passes even when the method was not called with the
expected arguments.

For **negative assertions** (`verify(exactly = 0)`), use `*anyVararg()` rather than
fixed-arity matchers. A check like `verify(exactly = 0) { f(name, any<Double>(), any(), any()) }`
only matches calls with exactly 2 varargs; if the production call has 4 varargs it silently
passes, providing no protection. Use `verify(exactly = 0) { f(name, any<Double>(), *anyVararg()) }`
to match any call to `f` regardless of how many vararg arguments it carries.

For **stubs** (`every { }`), the same arity trap applies in reverse: a stub with a fixed
number of `any()` matchers is silently bypassed when the production code calls the function
with a different number of vararg arguments, causing the real implementation to execute.
Use `every { f(any(), any<Double>(), *anyVararg()) } just Runs` to stub a vararg function
across all call-site arities.

## 7. Spring `@ConfigurationProperties` — `init {}` Validation Bypass

See `jvm_guidelines.md #1`. Kotlin-specific note: use `@field:Min(1)` (the `field:`
prefix is required because JSR-303 annotations target field accessors, not constructor
parameters). Alternatively use `@PostConstruct` for cross-field logic.

## 8. Kotlin `forEach` Double-Brace Dead Body

`collection.forEach { elem -> { body... } }` compiles without warning but does nothing
useful. The outer lambda returns the **inner lambda as a value** and discards it; the
body is never executed. This makes assertions, side-effects, and verifications inside the
inner braces silent no-ops.

Fix: remove the inner braces so the body executes directly:

```kotlin
// Wrong — inner braces create an unevaluated lambda:
list.forEach { item -> { assertThat(item).isNotNull() } }

// Correct — body executes on each element:
list.forEach { item -> assertThat(item).isNotNull() }

// Alternatively, use a for loop for multi-statement bodies:
for (item in list) { assertThat(item).isNotNull() }
```

The pattern is especially dangerous in test code where it makes all assertions
pass trivially, producing a permanently-green test that verifies nothing.

## 9. MockK Stubs for Reactor / R2DBC Errors

See `jvm_guidelines.md #4`. MockK-specific: use `returns Mono.error(...)` /
`returns Flux.error(...)` — never `throws`.

```kotlin
// Wrong — bypasses reactive pipeline:
every { redisOps.get(key) } throws RuntimeException("redis error")
// Correct — error arrives as reactive signal:
every { redisOps.get(key) } returns Mono.error(RuntimeException("redis error"))
```

## 10. Config Validation Failures Must Not Be Swallowed by Infrastructure Catch Blocks

See `coding_guidelines.md #7`. Kotlin-specific note: this is distinct from rule #7
(Spring ConfigProps `init {}` validation bypass), which concerns *when* validation runs.
This rule concerns *which catch block* absorbs the failure when validation does run.

## 11. MockK `coVerify(timeout = T)` for Fire-and-Forget Async Assertions

See `jvm_guidelines.md #5`. MockK-specific: use `coVerify(timeout = T, exactly = N)`.
This rule complements rule #4 (which covers controllable test dispatchers). Use the
injectable-dispatcher approach when the production code allows it; use `coVerify(timeout)`
when it does not.

## 12. Numbered Enum Slot Reservation — Use an Explicit Entry

See `coding_guidelines.md #8`.

## 13. Prometheus / Micrometer Metric Tag Values — No Boolean Type

Prometheus (and Micrometer) store all label/tag values as strings. There is no boolean
label type. When a tag represents a boolean condition, convert explicitly via `.toString()`:

```kotlin
// Wrong — does not compile; tag value must be String, not Boolean:
METRICS0001.metrics(TAG_ACTIVITY, dto.activityType.name, TAG_CANCELED, canceled)

// Correct — "true" / "false" string values work in PromQL label selectors:
METRICS0001.metrics(TAG_ACTIVITY, dto.activityType.name, TAG_CANCELED, canceled.toString())
```

Grafana and PromQL treat these as ordinary string label values and support equality
filtering (`{canceled="true"}`) and `label_values()` without any special handling.

## 14. Spring `@ConfigurationProperties` — Use `Duration` for Duration Fields

See `jvm_guidelines.md #2`. Kotlin-specific: use `data class` with `var` Duration field.
Validate in `SmartInitializingSingleton`, not `init {}` (see rule #7).

## 15. Spring Cloud Config — Do Not Bundle `spring.application.name`

See `jvm_guidelines.md #3`.

## 16. `CancellationException` Must Be Rethrown in Fail-Open Catch Blocks

Every `catch (e: Exception)` inside a `suspend` function must rethrow
`CancellationException` before any fail-open handling. Swallowing it prevents the
coroutine scope from cancelling, which causes hangs and resource leaks.

```kotlin
// Correct — fail-open but cancellation-safe
} catch (e: Exception) {
    if (e is CancellationException) throw e
    log.error("Operation failed, defaulting", e)
    defaultValue
}
```

A common missed case is a service method that is suspend, fail-open, and called from a
`runBlocking {}` consumer: the consumer cannot cancel in-flight work if the inner suspend
function swallows the cancellation signal.

## 17. SLF4J Logging — Always Pass the Exception Object, Not `e.message`

See `jvm_guidelines.md #6`.

## 18. Merge Duplicate Tests That Share Identical Setup

See `coding_guidelines.md #1` for the general rule. Kotlin-specific note: follow the
`given_X_when_Y_then_A_and_B` naming convention, and watch for the stub-without-verify
smell — if the first test stubs `Metrics` but only asserts on the log while the second
asserts on `Metrics`, the split conceals that both assertions belong to one invocation and
both stubs should be active in the same test.

## 20. Slim Projection Types for Batch Read Paths

See `coding_guidelines.md #9`. See also: `project-guidelines.md #23`.

## 19. Terminal Handlers Must Not Throw

A "terminal handler" is a method that must never throw (e.g. `handleMaxRetriesExceeded`,
an error-page renderer, a last-resort fallback). If such a method is invoked inside the
base class's try-catch, an uncaught exception propagates to the catch block's handler
(e.g. `handleException`), which may rethrow and incorrectly re-queue a permanently dead
message.

For every terminal handler that parses or processes input (e.g. deserialises a `MQMessage`
payload), add a test that passes a malformed/unparseable input and asserts:
1. No exception escapes the handler.
2. The fallback / default path produces the expected metric/log with `"unknown"` values
   where the parse failed.

## 21. Hoist Batch-Invariant Checks Outside Loops

See `coding_guidelines.md #10`.
