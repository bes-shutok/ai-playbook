# Quality Agent

Review for bugs, correctness issues, and quality problems.

## Correctness

1. Logic errors: off-by-one, incorrect conditionals, wrong operators
2. Edge cases: empty inputs, nil/null values, boundary conditions, concurrent access
3. Error handling: all errors checked, appropriate wrapping, no silent failures
4. Resource management: proper cleanup, no leaks, correct release order
5. Data integrity: validation, sanitization, consistent state management
6. Type safety: incorrect casts, generic type erasure issues, unchecked conversions

## Data Type and API Assumptions

1. Mutability: does code/plan assume mutable access to a frozen or immutable object?
2. Method existence: does it call or plan to call methods that do not exist on the target type?
3. Parameter types: are argument types correct at every call site?
4. Return types: are return values handled according to what the function actually returns?
5. Pipeline ordering: does the described insertion point or execution order actually produce the expected result given the real call sequence?
6. Test/implementation alignment: could a test pass even if the implementation is wrong? Does the test actually exercise the behavior it claims to cover?

## Construction-Time Validation Order

For value objects, records, structs, or commands whose constructor / init block defensively copies collections (or other inputs) and then checks emptiness or other caller-visible invariants:

1. Prefer validating null/empty (and similar input invariants) **before** reassignment when post-copy validation would turn null inputs into opaque failures from the copy helper (for example NPE from a defensive-copy API) instead of the type's documented validation error.
2. Defensive copy after successful validation remains fine.
3. Pattern: `quality#validate-after-assign`. Default **Low**; promote when it hides a reachable wrong error type on a public API.
4. Language-specific copy/validate APIs belong in the language overlay and Guideline Pack, not in this catalog.

## Naming and Structural Clarity

Structural clarity stays in this agent. Comment and doc **prose** (redundant inline comments, verbose API-documentation comments, stale task tags) is owned by `documentation.md` phase 2.

1. Naming consistency: new names follow existing codebase conventions
2. Redundant words: if a word is in the package/interface name, do not repeat it in the class name
3. Cognitive complexity: flag methods with deep nesting or multiple branching paths
4. Single responsibility: one method doing too many things

**Ownership (tiered):** runtime behavior and algorithm correctness only. Do not report missing wiring, config binding gaps, or layer placement (see `review-panel-selection.md`).

## MyBatis SqlSession local cache

When reviewing annotation MyBatis mappers:

1. Mutating SQL on `@Select` (`INSERT` / `UPDATE` / `DELETE`, including write CTEs with `RETURNING`) without `@Options(flushCache = Options.FlushCachePolicy.TRUE)` is a correctness defect: same-session retries or follow-up reads can reuse a stale `null` or prior row.
2. Prefer the same flush on `SELECT … FOR UPDATE` that gates a later write when callers re-read in the same session.
3. Do not flag ordinary `@Update` / `@Insert` / `@Delete` methods for missing `flushCache`; those already flush by default.

## Cache and TTL Operations

Before flagging cache eviction, invalidation, or fallback logic as incomplete or broken:

1. **Trace the lifecycle timing**: find the TTL calculation for the cache keys. Determine when the method is called relative to cache expiry. If the method runs after TTL expiry, eviction is a defensive no-op (DEL on non-existent keys), not a bug.
2. **Distinguish defensive no-op from incomplete code**: code that evicts already-expired keys is future-proof (works if reused pre-TTL), not broken. Do not flag it as "incomplete" or demand DB fallback.
3. **Cost/benefit for suggested fallbacks**: before suggesting "add DB fallback for the case when cache is missing", calculate the cost (e.g. N DB queries per batch tick) and verify the missing-cache scenario is reachable. If caches share the same lifecycle as the method caller, they cannot be missing.
4. **Multi-cache coherence**: when two caches (e.g. per-ID and per-user) share the same TTL anchor (like sendTime), they expire together. One being absent does not imply the other is still active.

## Scalability

1. N+1 calls: loops issuing individual queries instead of batch operations
2. Memory loading: unbounded collections loaded entirely into memory
3. Missing batch APIs: repeated single-item calls where batch alternatives exist
4. No resilience contract: missing timeouts, retries, or circuit breakers for external calls
5. **Catalog / config-list loops:** a `for` over allowlist, catalog, deny-keys, feature flags, or similar config that calls a single-key repository/persistence method per iteration is reportable **even when the list size is 1 today**, when a bulk/batch read already exists on the same repository port or mapper (or an equivalent load-all-by-user/by-parent method is one adapter call away). Prefer one load then in-memory filter. Pattern: `quality#catalog-loop-n-plus-one`. Skip the DB load entirely when the catalog returns an empty key list for this request. Do not dismiss solely because current N is small; note Low severity when blast radius is still local and N is tiny.

## Hermeticity cross-check

When tracing call graphs or data flows, note ambient-input reads reachable from tests in the diff or plan: env vars, network clients, cwd-relative or gitignored paths, and clock/timezone/locale dependence. Raise with a `quality#` prefix when visible. The `testing` worker leads the dedup group per `review-panel-selection.md`; the enumeration procedure lives in `testing.md`.

Report problems only. No positive observations.

## Representation precision and fan-out completeness

When a value crosses a framework, database, serializer, or mapper boundary:

1. Compare the accepted domain with the emitted representation. Check unit
   conversion, timestamp precision, null versus empty JSON, and binary or text
   JDBC binding. A positive duration that becomes zero is not a valid timeout.
2. For paired records, normalize each record from its own source fields before
   comparing them. Do not rebuild one record from the other and then claim the
   pair was validated.
3. Require boundary tests for the smallest value, precision edge, null, empty,
   and mismatched-pair cases when reachable.
4. **Addressable domain narrowing:** when a port accepts `long` / `BIGINT` but
   SQL, `set_bit`, byte[] capacity, or a cast narrows to 32-bit / `Integer`
   domain, require one shared guard at every write and size path (materialize,
   grow, capacity, poison, set-bit). Parallel ad-hoc checks that miss one
   caller are incomplete. Pattern: `quality#addressable-domain-door`.
5. **Numeric overflow on range math:** unchecked `long` addition for range
   ends, bit lengths, or pad sizes near `MAX_VALUE` must fail closed before
   persistence. Pattern: `quality#range-overflow`.
6. **Typed catalog enumeration door:** when a loop materializes, floors, or
   enqueues from a catalog, require the key source to be the typed or
   published definition set, never a wider all-keys helper, unless the plan
   explicitly documents the wider set. The finding body names both enumeration
   APIs and cites one illegal key the wide API admits and the typed API
   excludes. Pattern: `quality#typed-catalog-enumeration-door`.

When a change persists multiple facts or updates dependency-driven state,
enumerate every changed fact, published predicate, downstream job source, and
dependency key. Compare the persisted set with the fan-out set passed to
coordinators or queues; a successful write with an incomplete fan-out is a
stale-derived-state bug.

## Port API truth

When a persistence port method's name or parameters imply a scope (per user,
per seat, per key), verify the SQL predicates match that scope. A finder that
ignores a parameter or returns sibling-range history under a per-seat API is a
correctness defect, not a naming nit. Pattern: `quality#port-api-truth`.

## Opaque identifier parsing

When parsing catalog keys, event names, or dotted identifiers:

1. Do not truncate opaque names at the last `.` unless the contract defines a
   namespace separator and validates that shape.
2. Prefer family-aware token search (`lastIndexOf` of the operator family)
   after the family is known; whole-key `indexOf` of operator tokens misparses
   when identifiers embed the same substring.
3. Pattern: `quality#opaque-key-parse`.

## MyBatis side-effect SELECT

A `@Select` used only for a side effect (for example `pg_advisory_xact_lock`)
must not declare a mapped `void` return that still consumes a JDBC
result. Prefer `@Update` / `@Select` with an explicit ignore mapping pattern
already used in the repo, or a non-void type the driver can discard safely.
Pattern: `quality#mybatis-void-select`.
