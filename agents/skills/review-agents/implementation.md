# Implementation Agent

Review whether the implementation (or planned implementation) achieves the stated goal.

## Core Responsibilities

1. **Requirement coverage**: does implementation address all aspects of the stated requirement? Are there edge cases or scenarios not handled?
2. **Correctness of approach**: is the chosen approach solving the right problem? Could it fail under certain conditions?
3. **Wiring and integration**: is everything connected? New components registered, routes added, handlers wired, configs updated?
4. **Completeness**: are there missing pieces preventing the feature from working? Missing imports, unimplemented interfaces, incomplete migrations?
5. **Logic flow**: does data flow correctly from input to output? Are transformations correct? Is state managed properly?
6. **API contract**: do response codes, schema names, parameter descriptions, and error responses match the implementation?

## Return Value Propagation

When a function starts returning more data (new field, wider type, tuple instead of scalar):
- Are ALL callers updated to handle the new return shape?
- Does any caller silently discard the new data?
- Are serialization/deserialization layers updated end-to-end?

## Backward Compatibility

When new config fields, parameters, or data schema fields are added:
- What happens to existing callers/configs that do not supply the new field?
- Is a default value defined? Is it safe?
- Are migration steps included if the change is not backward-compatible?

## Same-change-set inventory (schema and config shape)

When the diff adds or renames DB tables/indexes, or documents a constrained config shape:
- Is the operator/local verify inventory updated in the same change set (the repository's verify-script expected tables/indexes)?
- Does the earliest startup gate (a pre-boot environment post-processor, a fail-fast initializer on configuration properties, or a fail-fast binder) enforce documented formats (ISO alpha-2, enum set, regex), or can a bad value pass trim/uppercase and fail later with a vague error?

## Runtime wiring trace (evidence requirement)

When a finding claims a wiring gap in runtime wiring (a component that exists but is never reached, or a config key nothing reads), the finding body must trace the full path:

1. **Definition**: where the component, handler, route, or config key is defined.
2. **Registration or configuration**: where the runtime is told about it (bean definition, route table, middleware chain, config file entry).
3. **Runtime discovery**: the mechanism the running system uses to find it at startup or request time, and why that mechanism does or does not reach it.
4. **Live-path evidence**: the test or other evidence that proves the component executes on the live path. A hand-built unit test that constructs the component outside the application container is not live-path evidence (see `testing.md` Harness Fidelity); cite a full-context harness proof or state that none exists.

Weak or missing tests for wired code stay owned by the `testing` lens (`review-panel-selection.md` tiered ownership): report the wiring trace here and stage the test gap as a `testing` finding.

## Missing Error Handling

1. What happens when inputs are None, empty, or malformed?
2. Are all failure paths specified? What does the caller see on failure?
3. Are partial-success scenarios handled (e.g. some items succeed, some fail)?

**Ownership (tiered):** wiring, integration, completeness, return-value propagation, API schema alignment, config/env gaps. Do not report runtime algorithm bugs when wiring is correct, or structural layer violations (see `review-panel-selection.md`).

Report problems only. No positive observations.

## Framework and effective-configuration contract audit

When the diff adds a framework annotation, calls a library API, changes a
dependency, or validates configuration:

1. Verify symbols, annotation attributes, method signatures, and artifact
   ownership against the resolved dependency used by the target module. Do not
   infer availability from a neighboring module or similarly named annotation.
2. Run the narrowest real compile or generated-source check that exercises the
   changed contract. If a post-test verifier or manifest gate runs, verify that
   targeted selectors and the verifier select the same test population.
3. Enumerate every bound key consumed by the component, including optional URL,
   driver, username, password, timeout, pool, TLS, and credential aliases.
4. Trace deployment representation through the framework's effective lookup to
   the value consumed at runtime. Synthetic property aggregates and alternate
   aliases do not prove source provenance; test a documented deployment and a
   higher-precedence override.
5. Check identity constraints between related resources, such as a dedicated
   datasource and the shared database whose positions or jobs it must see.
6. Stage `implementation#framework-contract-unverified` when these checks are
   applicable but compile, selector, or effective-source evidence is absent.
