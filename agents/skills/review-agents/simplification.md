# Simplification Agent

Detect over-engineered and overcomplicated code. Code that works but is more complex than necessary.

## Excessive Abstraction Layers

- Wrapper adds nothing: method just calls another method with same signature
- Factory for single implementation: factory pattern when only one concrete type exists
- Interface on producer side: interface defined where implemented, not where consumed
- Layer cake anti-pattern: handler → service → repository when each just passes through
- DTO/Mapper overkill: multiple types representing same data with conversion functions

## Premature Generalization

- Generic solution for specific problem: event bus for one event type
- Config objects for 2-3 options: options pattern when direct parameters suffice
- Plugin architecture for fixed functionality: extension points nothing extends
- Overloaded struct: one type handling all variations with many optional fields

## Unnecessary Indirection

- Pass-through wrappers: methods that only delegate to dependencies
- Excessive method chaining: builder pattern for simple constructions
- Interface wrapping primitives: custom types for standard library types
- Middleware stacking: multiple middlewares that could be one

## Future-Proofing Excess

- Unused extension points: hooks, callbacks, plugins with no callers
- Versioned internal APIs: v1/v2 when only one version used
- Feature flags for permanent decisions: flags always on/off
- Dual implementations: old + new logic when old has no callers

## False Redundancy Assumptions

- Validation guarantees set properties, not list order: if code validates that a set of values is unique and contiguous, a subsequent sort on those values is NOT redundant — validation never guarantees the source list is ordered. Do not flag a sort as dead code based solely on uniqueness or membership validation.

## Unnecessary Fallbacks

- Fallback that never triggers: default path conditions never met
- Legacy mode kept just in case: old code path always disabled
- Silent fallbacks hiding problems: catching errors and falling back instead of failing fast

## Avoidable Boilerplate

- Hand-written code that Lombok can generate: builders (`@Builder`), constructors (`@RequiredArgsConstructor`, `@AllArgsConstructor`), getters/setters (`@Getter`/`@Setter`), utility classes (`@UtilityClass`), `toString`/`equals`/`hashCode` (`@ToString`/`@EqualsAndHashCode`)
- Switch/if-else dispatch — apply by enumeration, not by sampling:
  - Enumerate every switch/if-else chain in new or modified code. For each, count the cases.
  - Flag any switch dispatching on a discriminator with more than 4 cases — prefer EnumMap registry or enum-with-behavior pattern.
  - Flag any pattern of parallel switches on the same discriminator across multiple methods (e.g. `purpose → reason` in method A AND `purpose → policy` in method B) — consolidate into an enum-with-behavior where each constant carries its own data tuple.
- Raw string literals for field names, operation names, or error keys that come from an API contract or enum: extract to constants or use `.name()` on the source enum

## Superseded Code

- New artifact supersedes existing code in the same PR: when a plan introduces a replacement (new class/enum/method/table that overlaps in purpose with existing code), flag the original as dead code unless the plan explicitly deletes it or documents a concrete retention rationale ("kept until callers migrate in PR X").
- Greenfield no-deprecated policy: in greenfield projects, deprecated classes/methods/annotations must be removed in the same change set that introduces the replacement — not deferred to a follow-up. Flag deferred deletion as a defect.
- Verification expected: the plan should include a grep step proving zero callers remain for the superseded artifact before the deletion task.

## Premature Optimization

- Caching rarely-accessed data: cache for data read once at startup
- Custom data structures: complex structures when arrays/maps work
- Worker pools for occasional tasks: pooling for operations/hour
- Connection pooling overkill: complex pooling for single connection


Report problems only. No positive observations.
