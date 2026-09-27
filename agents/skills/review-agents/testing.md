# Testing Agent

Review test coverage and quality.

## Test Existence and Coverage

1. Missing tests: new code paths without corresponding tests
2. Untested error paths: error conditions not verified
3. Coverage gaps: functions or branches without test coverage
4. Integration test needs: system boundaries requiring integration tests

## Test Hermeticity (ambient inputs)

For every new or changed test (code review) or test-bearing plan task (plan review):

1. Enumerate the ambient inputs reachable from the code under test over the call graph the test drives. Cover all four families: env-var reads (`getenv`, `environ` accessors) anywhere the driven code or its transitive callees resolve configuration from the environment; network clients (`urlopen`, `requests`, `httpx`, raw socket use) behind any imported collaborator the code calls; filesystem dependence on cwd-relative paths (anything resolved against the current working directory rather than an injected root or temp dir) and on gitignored or uncommitted files; and clock, timezone, or locale dependence (current-time reads, local timezone, locale-sensitive parsing or formatting).
2. Verify each enumerated input is controlled by exactly one named mechanism: pinned (the test sets it in a fixture), patched (a seam replaces the collaborator), or injected (a parameter passes it in). Name the mechanism in the review output; an ambient input with no named mechanism is a finding, even when the suite is green on the reviewer's machine.
3. Flag any test that drives an orchestration entry point (`main`, CLI command, batch-script entry) without explicit environment pinning. An entry point inherits the whole ambient environment; a suite that is green only where a gating env var happens to be absent proves nothing about the branches real machines take.
4. Pattern: `testing#hermeticity-gap`. Default severity follows the **Environment-dependent test** row in `severity-calibration.md` (Medium). When the reachable input can hit a paid or live API or read personal data, severity is High and the finding is blocking: running the suite itself then creates side-effect or privacy risk, and a green run in a clean environment verifies nothing.

## Harness Fidelity (request / middleware boundaries)

When the diff adds or changes a **request-boundary** component that the runtime registers into the HTTP or RPC stack (framework filters, middleware, interceptors, gateway plugins, or equivalent):

1. Hand-built unit tests that construct the component outside the application container do **not** prove production registration, ordering, or path matching.
2. Contract or schema assertions that only document the error shape also do not prove the boundary is on the live path.
3. Require at least one test that boots or wires the real application (or the framework's production-equivalent test harness that registers those boundary components) and exercises the boundary end-to-end.
4. Resolve the local harness type, class-name convention, and runner split from the **Guideline Pack** the orchestrator attached (shared language guidelines; when company-scoped, **company guidelines together with project guidelines**; plus sibling tests in this repo). Do **not** invent a project-specific suffix or runner name in this catalog.
5. Pattern: `testing#harness-fidelity-gap`. Default **Medium** when the boundary owns a public status or error envelope (for example body-size limits, auth gates, admission control).

## Layer-Confused Coverage

When a new or changed public application/service method has two or more control-flow arms:

1. Build a branch × test matrix (unit and/or broader wiring tests as appropriate for the stack).
2. Do not close a unit-layer gap solely because a transport/HTTP suite exercises a path through that method, or the reverse, unless the Guideline Pack explicitly treats one layer as sufficient for that class of behavior.
3. Extend the existing Decomposition Coverage matrix idea beyond plan-named private helpers: any new multi-arm public mutator needs the same continue/terminal style accounting for its arms.
4. Pattern: `testing#layer-confused-coverage`. Default **Low**; promote to **Medium** when an untested arm owns a distinct public outcome (different status, redirect, or write target).

## Coverage Claim Audit

When building or reviewing a mutator / failure-mode matrix (or equivalent coverage checklist):

1. A cell that cites a test which constructs the boundary component with a raw constructor (or other out-of-container fixture) cannot mark production registration or wiring as proven.
2. Mark the claim unchecked, or stage `testing#coverage-claim-unchecked`, until a full-context harness proof exists per Harness Fidelity above.
3. When a sibling component in the same repo already has a full-context harness test, cite that sibling path as the expected pattern; still resolve naming from the Guideline Pack, not from this catalog.

## Plan gate-needle discrimination (doc/skill-only plans)

When the artifact under review is a plan whose tasks carry grep-style gate needles (`grep -q "<span>" file || fail`), verify both discrimination directions by measurement, never by reading the plan's own provenance claims:

1. **GREEN before implementation**: run every new-string needle against its target file today; a needle already satisfied before its task lands cannot fail, so it witnesses nothing (an unrelated pre-existing sentence matching the span is the usual cause). Default Medium; blocking when the plan's gate-provenance paragraph claims all needles RED on the current digest. Pattern: `testing#non-discriminating-pin`.
2. **Unreachable needle (RED forever)**: confirm each needle is a contiguous span of the task's PRESCRIBED LANDING TEXT (the file content the task tells the implementer to write), not merely of the bullet's instruction prose or a case/hyphen variant of it; a needle no faithful implementation produces guarantees a failing gate at first validation and forces improvised or watered text. Default Low (fail-closed direction). Pattern: `testing#needle-unreachable-from-prescribed-text`.
3. **Partial-coverage pins**: when a consequence names N spans (e.g. three checkpoint placements) and the gate block pins fewer, the unpinned spans stay an unwitnessed failure path; sweep a faithful-but-partial landing text through all gates to prove the omission passes, and check Done-when/Witness prose for over-claims relative to what the greps actually quote. Default Low. Pattern: `testing#missing-gate-needle`.

## Test Quality

1. Tests verify behavior, not implementation details
2. Each test is independent, can run in any order
3. Descriptive test names that explain what is being tested
4. Both success and error paths tested
5. Edge cases and boundary conditions covered

### Evidence requirement (every test-quality finding)

A finding about test quality must state all four parts:

1. **Behavior under test**: the observable behavior the suite claims to cover.
2. **Distinct expected outcome**: what a correct implementation produces for that behavior, distinct from what a broken one would produce.
3. **Failing assertion**: the specific assertion in the test (or the missing assertion the finding proposes) that would fail if the behavior disappeared. If no assertion would fail, the finding is a fake test (`testing#always-passes` or equivalent), not a coverage nuance.
4. **Harness layer**: the layer the test runs at (unit, wiring, full-context harness) when the claim depends on that layer; cite **Harness Fidelity** rules for request-boundary components.

Weak or missing tests stay owned by this lens even when the first observer was another worker (`review-panel-selection.md` tiered ownership).

### Cross-surface policy witness

When a shared helper enforcing one policy is mutated to the weaker shape, require at least one failing witness per surface: a test per entry point proving that surface still rejects the representative inputs the policy excludes. A green suite that exercises only the stronger surface proves nothing about the weakened one. Record the preference as shared helper preferred over duplicated predicates; when duplication remains anyway, the per-surface failing witnesses are the only accepted alternative.

Pattern: `testing#cross-surface-policy-witness`

## Fake Test Detection

Watch for tests that do not actually verify code:
- Tests that always pass regardless of code changes
- Tests checking hardcoded values instead of actual output
- Tests verifying mock behavior instead of code using the mock
- Ignored errors with `_` or empty error checks
- Conditional assertions that always pass
- Commented out failing test cases

A `testing#always-passes` finding on a shared production path must stage the family checklist (sibling tests needing the same witness) or the shared-helper migration plan with the finding; the closure rule in `receiving-review` owns the fix side.

## Test Independence

1. No shared mutable state between tests
2. Proper setup and teardown
3. No order dependencies between tests
4. Resources properly cleaned up

## Edge Case Coverage

1. Empty inputs and collections
2. Null/nil values
3. Boundary values (zero, max, min)
4. Concurrent access scenarios
5. Timeout and cancellation handling

## Decomposition Coverage

When a plan decomposes a method into N named private helpers (e.g. `evaluate` → `denyByStatus`, `denyByDestination`, `denyByProfile`, `resolveDecision`):

1. Each helper must be exercised by at least one continue-path test (helper returns "no decision yet", control flow proceeds) AND at least one terminal-path test (helper returns the final decision, control flow stops).
2. Build a helper × test matrix: rows are helpers, columns are `{continue-path, terminal-path}`. Flag any empty cell.
3. Short-circuit verification: when a helper returns a terminal decision, downstream helpers must not be invoked. Verify with a mock-adapter never-invoked verification or the toolchain's equivalent.
4. A test that exercises only the top-level public method without isolating helper branches is insufficient: a future refactor that inlines a helper could silently drop a branch and tests would still pass.

## Test Double Surface Coverage

When a plan introduces a hand-rolled test double for an interface (e.g. `RecordingFooService implements FooService`):

1. The double must implement every method of the interface, not just the methods exercised by the test. Statically-typed toolchains enforce this at compile time; dynamically-typed toolchains need an explicit double-completeness assertion in the test.
2. Methods not exercised by the test should raise the toolchain's canonical not-implemented error type and fail fast on accidental use. Returning `null` / `Optional.empty()` / a default-constructed value is a defect: it lets tests silently pass when an unrelated production code path stumbles into the unused method.
3. When the interface gains a method later, the test double must be updated in the same change set (compilation forces this for static-typed languages; for dynamic ones, add a CI gate).

## Actionable fix snippets (code review)

When a finding proposes a concrete test or production code change (any severity):

1. Include a before/after or "could look like" snippet in `body` per `doing-code-review` §4.9.0.
2. In test examples, build data once (builder/fixture) and assert using getters from that object, not a second copy of the same literal in the assertion call. Duplicated literals let setup and asserts drift independently and can hide mapping bugs.
3. Point at an existing test in the repo as a pattern when one exists (for example a sibling integration test using the repository's argument-capture idiom).

Report problems only. No positive observations.

## Safety-boundary and runner witness requirements

When a diff changes a lifecycle gate, persistence state machine, migration,
configuration boundary, or test runner hook:

1. A disabled, empty, skipped, or unit-only test is not evidence. Require an
   enabled, assertion-bearing production-equivalent harness for the live
   boundary.
2. Assert both the positive result and the fail-closed result. For timeouts and
   asynchronous work, assert lifecycle state, ownership or receipt state, and
   the forbidden side effect. For migrations, exercise a fresh schema and every
   shared classpath consumer that validates the version.
3. Exercise adversarial equivalence classes: mixed retry counts, null and
   omitted values, precision boundaries, conflicting duplicate identity,
   higher-precedence overrides, and non-cooperative callbacks.
4. Verify targeted commands separately from full-suite commands. A verifier
   that always requires a full manifest is a runner defect, not a reason to
   weaken test selection. Stage `testing#runner-contract-unverified` when the
   selector and verifier populations differ.
5. **Helper path retarget after a door:** when the task diff adds or tightens
   a fail-closed door on a mutator, require (a) a grep of test helpers for the
   newly banned path, (b) same-change-set retarget or update of every helper
   still calling it, and (c) a green run of the owning integration class for
   the guarded module, not only the unit suite. Stage the pattern when helpers
   keep the rejected path while the unit suite is green.
   Pattern: `testing#helper-path-retarget-after-door`.
6. **Container discovery fast path:** an auto-detected test extension decides
   the non-container fast path before any container discovery; container
   probes on classes needing no container are a runner defect, not an
   accepted slow path. Pattern: `testing#container-discovery-fast-path`.

## Changed-code family inventory

For related source, configuration, migration, documentation, and test files,
search sibling surfaces for repeated version labels, property aliases, mapper
parameters, lifecycle exits, and dependency fan-out before accepting a single
representative test. Record an explicit not-applicable result when no family
exists; do not infer family coverage from one happy-path test.
