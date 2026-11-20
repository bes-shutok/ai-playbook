## Investigation Quality Requirements

When a plan investigates "is X handled correctly?" or "does the system correctly handle Y?", code inspection alone is INSUFFICIENT. The investigation tasks must include ACTUAL data trace verification:

1. **Trace the user's specific case:** For the exact reported scenario, verify data flows from source CSV/database through to final output. Do not rely on code inspection alone.
2. **Verify output matches source classification:** If the source report shows "Loss" and the output shows "Gain", the investigation is incomplete regardless of whether code CAN handle negatives.
3. **Use grep/compare commands:** Include tasks like `grep "specific_value" source.csv` and comparison with actual output file content
4. **Cross-report validation for multi-source systems:** When systems process data from multiple source reports, verify classifications match across ALL reports before concluding correctness. Document which report is authoritative when sources disagree.
5. **Failure consequence:** An investigation that concludes "no code changes needed" without performing data trace verification is INCOMPLETE and must be redone.

**Task ordering:** Use verification-first task ordering for investigation plans: code inspection, test execution, documentation review, and data trace verification BEFORE any implementation tasks. Skip implementation only after verification confirms correctness.

**Example:** A plan investigating whether the system correctly handles negative values must trace actual data: find a specific entry in Source Report A (shows classification "Type X"), compare it with the actual output cell value (shows conflicting classification "Type Y"), and identify why the discrepancy exists (e.g., system processes only Source Report B, ignoring Report A). Code inspection alone cannot detect this mismatch.

## TDD Task Ordering

Plan tasks MUST be ordered so that failing tests come before implementation:
1. **RED tasks first**; write failing tests for the new behavior
2. **GREEN tasks after**; implement the minimal code to pass
3. **Refactor tasks last**; DDD extraction, naming, cleanup

Never place implementation tasks before their corresponding test tasks. Group related RED/GREEN pairs when tests and implementation are tightly coupled.
When a phase plan contains multiple code changes, order tasks so earlier tasks establish prerequisites for later ones within that same phase (for example retry semantics before activating new traffic paths).

**Pure-refactoring tasks (no new behavior):** use concise `- [ ]` action items instead of RED→GREEN cycles. However, when the refactor risks breaking unstated invariants (ordering, error attribution, mutable side effects, pre-condition checks), add characterization test items in `given/expects` format. These run GREEN before the refactor and must remain GREEN after. Write them as `- [ ] Run → expect GREEN (characterization: captures existing behaviour before refactor)`, not RED→GREEN. Reference existing tests by class and method name where they cover the invariant; add a new test only for invariants with no existing coverage.

**RED fixture validity:** RED checks are execution-selected, so these obligations bind the checks execution selects, never plan-authored fixture inventory; when a plan pins a RED expectation, the pin is the observable witness, and the selected fixture must be constructible against the real base shape (build rows through the family's payload helpers, never index into a possibly-empty list), exception-contained when the probe is expected to crash today (wrap it so the harness records a FAIL instead of aborting the run), and pinned to a gate-unique assertion phrase so a pre-existing error cannot satisfy it (see user-level lessons #235). When the fixture injects a mutation or observation through a patched function, place the hook between the initial state read and the first verification on BOTH the pre-fix and post-fix trees: trace where the patched call runs after the planned fix, not only today, or the fixture can never turn GREEN (user-level lesson #258).

## DDD Extraction

When a plan modifies domain types (value objects, entities, enums) that live in a large file (>1k lines), include a task for evaluating extraction to a dedicated domain module. Specifically:
- If the affected types form a cohesive aggregate (e.g., related domain types that work together), propose extracting them to a new module under `domain/` or `application/`.
- Place the extraction task AFTER the GREEN tasks (implementation works) but BEFORE the final validation task.
- The extraction task must verify no circular imports and update all import paths in tests and production code.
