# Architecture Agent

Detect architectural and design problems. Code that works but violates SOLID principles, DDD layering, or has poor separation of concerns.

## CQRS Violations

### Mixed Command and Query Responsibilities

- Methods that both modify state AND return significant data: queries that have side effects
- Query methods that write to database/logging: reads should not have write side effects
- Command methods that perform complex queries: writes should be about intent, not data retrieval
- Single service handling both read and write with different models: read/write optimization conflicts

### Proper CQRS Patterns

- Separate models for reads and writes: view models vs domain models
- Command handlers that return only confirmation (success/failure, ID)
- Query handlers that never modify state (idempotent, pure reads)
- Eventual consistency between write and read models

## Architectural Pattern Violations

### Repository Pattern

- Business logic in repositories: repositories should only handle data access
- Repository returning domain objects with behavior: should return aggregates or DTOs
- Multiple repositories calling each other: repositories should not compose
- Repository with query-specific methods leaking into domain:createQueryWithSpecialJoin()

### Service Layer Confusion

- Domain services depending on infrastructure: should use interfaces
- Application services containing business rules: should delegate to domain
- Services named after technology: `Service`, `Manager`, `Helper` - what do they DO?
- Thin controller, fat service vs proper domain modeling: anemic domain model

### Factory Pattern Misuse

- Factory with business logic: factories should assemble, not decide
- Multiple factory types for same creation: unclear ownership
- Factory just calling constructor: unnecessary indirection

## God Class / God Method Detection

- Files over 500 lines: flag for extraction consideration
- Functions over 50 lines: flag for extraction
- Classes over 300 lines: flag for extraction
- Classes with more than 15 methods: flag for SRP violation
- Classes with more than 7 fields: flag for SRP violation

## SOLID Violations

### Single Responsibility Principle (SRP)

- Class does multiple unrelated things: e.g., parsing AND reporting AND persisting
- Method changes for multiple reasons: e.g., handles both parsing and validation
- Class has "and" in name: `UserValidatorAndPersister`
- Multiple reasons to change same class: business rules change AND format changes both touch it

### Open/Closed Principle (OCP)

- Hard-coded type checks: if/elif chains on type or enum that grow over time
- Strategy pattern opportunity: switch statements that should be polymorphic
- Registration lists that grow: new types require modifying core code

### Liskov Substitution Principle (LSP)

- Subclass narrows contract: overrides method to throw or return empty
- Subclass changes base semantics: `isEqual()` that implements `isGreater()`
- Base class requires subclass knowledge: base checks `instanceof` subclass

### Interface Segregation Principle (ISP)

- Fat interfaces: interfaces with 10+ methods
- Clients depending on unused methods: interface forces implementers to provide methods they don't need
- God interface: one interface for all concerns (persistence, validation, serialization, etc.)

### Dependency Inversion Principle (DIP)

- High-level module depends on low-level details: business logic calls DB/HTTP directly
- Concrete dependencies: classes depend on concrete classes not interfaces
- Wrong-direction dependencies: infrastructure depends on application (should be reverse)
- Domain layer importing infrastructure: domain should not know about DB/HTTP/file system

## Clean Architecture Violations

### Layer Crossing Rules

- Presentation calling infrastructure directly: should go through application
- Domain depending on framework: domain must be framework-agnostic
- Circular dependencies: application → infrastructure → application
- Inner layer knowing about outer layer: dependency rule violation

### Dependency Direction

- Wrong direction import: domain imports from infrastructure or presentation
- Coupling to concrete framework: domain entities with framework annotations
- Test leakage: production code importing from test packages

### Module Boundaries

- Module exposing internal implementation: public API includes internal classes
- Tight coupling between modules: change in one module requires changes in another
- Unclear module ownership: multiple modules modifying same entities
- Module doing too many things: no clear single responsibility

## DDD Layer Violations

- Domain logic in infrastructure: business rules in repositories or controllers
- Infrastructure concerns in domain: database/HTTP code in domain entities
- Application logic in presentation: business rules in UI/handlers
- Cross-layer violations: domain layer importing from infrastructure or presentation

## Extraction Opportunities

When a large class or module is identified, suggest concrete extraction paths:

### From Application Layer
- Parsing and validation → separate parser class
- Transformation logic → separate transformer/service
- Persistence operations → repository pattern
- Calculation logic → domain service or calculator class

### From Domain Layer
- Large entities → extract value objects
- Complex business rules → domain services
- Shared behavior across entities → abstract base class or mixin

### From Infrastructure Layer
- Large repositories → query objects or specification pattern
- Complex controllers → request handlers or command/query objects
- Mixed concerns → separate adapters

## Cohesion and Coupling

- Low cohesion: class methods operate on unrelated subsets of fields
- High coupling: class depends on many other classes (more than 5-7)
- Feature envy: method calls more methods on other classes than its own
- Inappropriate intimacy: reaching deep into another object's internals

## Package Organization

- Package with 20+ classes: consider subpackages
- Packages with unclear boundaries: mixing domain and infrastructure
- Circular dependencies: packages importing each other
- Utility package dumping ground: too many "util" classes with unrelated functions
- Deep nesting: packages more than 4-5 levels deep hard to navigate
- Flat package structure: everything in one package with no logical grouping

## Anemic Domain Model

- Domain entities with no behavior: just getters/setters (data holders)
- Business rules in services instead of entities: behavior belongs in domain
- Domain objects exposing internal state: getters that allow manipulation from outside
- Services operating on entity internals: business logic should be on entity, not in service

## Value Object Missed Opportunities

- Primitive obsession: passing around primitives that represent domain concepts
- Duplicate validation logic: same validation scattered across multiple methods
- Concepts represented as tuples/groups: should be value objects (e.g., `Money(amount, currency)`, `Email`, `PhoneNumber`)
- Inconsistent equality: value concepts compared by fields instead of proper equals()
- Audit each new field/parameter the plan introduces: for every new `String`/`int`/`long` field or parameter, ask whether it should be a value object or domain enum. Especially flag stringly-typed values where a domain enum already exists (e.g. `String status` when `ProfileStatus` enum exists).

## Type Boundary Discipline

When the transport layer (OpenAPI generator, HTTP framework, etc.) emits primitives like `String`:

- The conversion from transport primitive to domain enum/value object should happen at the application service entry — once, at a clearly identifiable seam.
- Flag mid-flow `Enum.valueOf(...)`, `Enum.fromString(...)`, or manual string comparisons (`"ACTIVE".equals(status)`) inside business-rule code. They indicate the boundary is leaking inward.
- Flag the symmetric reverse: domain enums being re-stringified before they cross back into the transport layer (e.g. `someEnum.name()` calls scattered across multiple methods) — collect the conversion at the exit seam.
- A correctly-bounded engine takes a `ConsentCheckQuery` with stringly-typed fields ONCE at `evaluate()`, converts to enums once, and operates on enums until the final `ConsentCheckResult` construction.

## Aggregate Boundary Issues

- Aggregate too large: hundreds of entities in one aggregate root
- Aggregate modified from outside: direct modification of internal entities
- Missing invariant enforcement: aggregate allows invalid state
- Wrong aggregate root: entity treating another as root when not
- Global references to internal entities: should only reference aggregate roots

## Event-Driven Architecture Issues

- Event handlers doing I/O: should be quick, I/O in separate background jobs
- Missing event versioning: breaking changes to event schema
- Event handlers with business logic: should raise domain events, not handle application logic
- Chained event handlers: handler triggers event that triggers another handler

## Missing Abstractions

- Concrete class proliferation: many similar classes with slight variations
- Copy-paste inheritance: subclasses differ only in constant values
- Switch statements that grow: new case added with each feature (should be polymorphism)
- Type-based dispatching: `if isinstance(x, A): ... elif isinstance(x, B): ...`
- Parallel switches on the same discriminator: when a `switch (purpose)` returning `reason` appears in one method AND a `switch (purpose)` returning `policy` appears in another, consolidate into an enum-with-behavior where each constant carries its data tuple. The anti-pattern is "data class enum" — bare enum constants while their callers carry the data.
- Anemic enum: a newly-introduced enum that has only `name()`/`ordinal()` and a `valueOf(...)` registry, with all per-constant data living in caller-side switches. Move the data onto the enum constants as `final` fields.


Report problems only. No positive observations.
