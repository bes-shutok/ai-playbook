## Universal Patterns

Core plan quality principles applicable across all projects and languages:

- **Gist & Examples section**: Every plan must include a human-readable "Gist & Examples" section directly after `## Why` and before `## Outcome` that explains: what changes (plain language), why the change is needed (problem statement or context), concrete input/output examples showing before/after behavior, and edge cases that motivated design decisions. This serves as the on-ramp for both implementers and reviewers who need context before diving into tasks. The Gist is the main user-readable part of the plan: walk at least the happy path as a concrete scenario with clearly separated **Before (today)** and **After (this plan)** paragraphs that name the same trigger and show the different outcome; a terse one-sentence before/after pair is not enough (user correction 2026-09-05).

- **Evaluation Criteria section**: Every plan must include an "Evaluation Criteria" section that defines how quality will be assessed for the final product. This includes quality dimensions (correctness, performance, maintainability, security, test coverage, observability) with specific checks or metrics for each, **Done when** criteria for repository implementation, and **Ship when** conditions for deployed, cross-team, or human-owned evidence. Criteria must be precise and verifiable; not vague statements like "it should work" but concrete tests, commands, metrics, or named release conditions.

- **Core concepts**: Edge cases (boundary conditions requiring explicit handling), negative requirements (what must NOT be done), acceptance criteria (definition of done), validation sequence (ordered steps in which processing must occur).

- **Pattern-specific specifications**: Use exact pattern matching with start/end anchors (not `startswith()` or broad regex), include examples of what NOT to match, explicitly state what is out of scope.

- **Data classification specifications**: Define the source of truth, list explicit exclusions with reasons, handle edge cases (collisions, ambiguous values), specify fallback behavior.

- **Error handling specifications**: State what exception type to raise, what cleanup must occur before re-raising, what must NOT happen (silent continuation, partial output).

- **Pre-computation bug pattern checks**: Before finalizing tasks involving data processing, verify: unit verification (correct units), temporal gating (earlier events cannot consume later state), empty string handling (aggregation min/max filters), boundary values (tests at exact threshold), zero-cost propagation (flagged with review reason), fee/completeness (all components included), error scope (row-level parse errors caught per-row).

- **Stateful helper contracts:** when specifying a helper function that mutates shared state (dict, set, deque passed by reference), list ALL mutated parameters in the function signature spec; including those mutated as side effects that do not appear in the return type. A helper signature that omits a mutated parameter is an incomplete contract and will produce incorrect extraction.

- **Observable witness format**: Every behavior or safety claim a task owns uses the `given/expects` witness format: given <scenario/inputs>, expects <observable outcome>. Include the happy path, negative outcomes (what must NOT happen), edge case outcomes (boundary conditions), and error path outcomes (exception handling and cleanup). The witness names observable behavior, never test identities: which tests, fixtures, and commands verify it is selected at execution from repository evidence, and a plan that guesses them carries inventory review finds without improving the witness; the plan must be readable without opening any test file.

- **Boolean / Optional multi-row mutators:** When specifying a port or adapter method that returns success/failure from a CTE or multi-statement write, always add a negative `given/expects` IT: call fails (wrong id, wrong status, stale token) **and** persisted state for other rows is unchanged. See **Validation Commands (authoring rules)** item 5. Incident reference: `promoteToActive` superseded ACTIVE while returning `false` on a missing BUILDING target.

- **Integration testing requirements**: For multi-step pipelines, include integration tests that exercise the full flow, not just unit tests for individual components.

- **Boundary test checklist**: When implementing threshold-based logic (>=, <=, >, <), always include tests at the exact boundary value. Off-by-one errors at boundaries are common sources of incorrect behavior.

Projects with detailed plan quality guidelines should document them in `{guidelines_path}` or a named architecture/maintenance doc; not `docs/domain/` or `docs/<module>/` on migration-complete company services. The generic skill provides only the universal patterns above.
