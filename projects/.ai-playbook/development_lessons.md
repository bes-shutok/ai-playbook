## 1. Code Quality and Duplication

**Principle:** Family D (Single source of truth)


- Always check for duplicate test methods or functions before adding new code.
- Command: `grep -n "def method_name" . -r`

**See also (principle cluster D):** #42 (same family, distinct angle: general duplicate-detection seed (#1) vs frozenset cross-section (#42)).


## 2. Dependencies and Imports

**Principle:** Family F (Layering / dependency direction)


- Check all imports against declared dependencies before submitting.
- Import from public `__all__` exports; avoid `_private` imports in tests unless necessary.
- Run tests early to catch missing imports.

**See also (principle cluster F):** #24 (same family, distinct angle: broad import-hygiene seed (#5) vs focused private-boundary principle with remediation (#24). Cross-link. (If the fresh-agent finds #5's other bullets irrelevant and only the private-import bullet matters, this could tighten to a true-duplicate; default is overlapping.)).


## 3. Testing Best Practices

**Principle:** Family A (Equivalence-class coverage)


- 3-tier structure: unit (`tests/unit/`) → integration (`tests/integration/`) → e2e (`tests/end_to_end/`).
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`.
- Unit tests may access internal functions; integration/e2e use only public APIs.
- Edge case coverage: When testing string sanitization, validation, or parsing functions, explicitly test edge cases:
  - Empty strings and whitespace-only inputs
  - Multi-byte UTF-8 characters
  - Control characters (null, newline, carriage return)
  - Multi-character prefixes (e.g., `==`, `++` vs single `=`, `+`)
  - Padded inputs (leading/trailing whitespace)
- Error path coverage: Test double-failure scenarios where multiple error conditions occur together (e.g., aggregation fails AND workbook.close fails).


## 4. Excel Output Security

**Principle:** Family A (Equivalence-class coverage)


- All external data string fields (from any upstream data source: CSV/Excel importers, API responses, third-party feeds, etc.) must be wrapped with `safe_cell_value()` before writing to Excel cells. Formula injection vulnerabilities exist if even one field is unprotected.
- Check consistency: if most fields in a section use `safe_cell_value()`, any unprotected field is likely a bug.
- Common unprotected fields to watch: free-text `description`, `notes`, customer/account labels, supplier names, user-entered reason text.


## 5. Exception Handler Specificity

**Principle:** Family B (Error-policy propagation)


- Catch specific exception types (`FileProcessingError`, `ValueError`) instead of broad `Exception`.
- Broad exception handlers mask programming errors and make debugging harder.
- When a function documents raising a specific exception, catch that exact type in callers.

**See also (principle cluster B):** #27 (same family, distinct angle: write-side (catch specific not broad, tax-reporting "Operator Mapping Field Semantics (`service_start_date` / `valid_from`)") vs escape-side (convert the specific type so it evades the broad handler, #27)).


## 6. API Design for Production vs Testing

**Principle:** Family H (Verify the real thing, not the abstraction)


- Do not add features or parameters solely to satisfy tests; adjust tests to match production patterns instead.
- When tests need special handling, first try to make tests reflect real usage before adding complexity to production code.


## 7. Test Real Behavior, Not Implementation Details

**Principle:** Family H (Verify the real thing, not the abstraction)


- Verify that a feature works end-to-end, not just that it returns a certain value.
- Use realistic test data; check that integrated components produce correct outputs.


## 8. Aggregation Logic: Test Both Directions

**Principle:** Family A (Equivalence-class coverage)


See `~/Projects/.ai-playbook/agent_workflow_guidelines.md` #1.
Repo context: LP liquidity operations; fixing "in" direction broke "out" because liquidity out produces multiple outputs from one input.


## 9. Descriptive Output Labels

**Principle:** Family C (Representation: sentinel vs None vs exception)


See `~/Projects/.ai-playbook/coding_guidelines.md` #9 for the canonical rule.
Repo context: output table headers renamed from terse upstream CSV column names to self-explanatory terms (e.g. "Quantity" not "Qty", "Unit Price (EUR)" not "Price", "Customer Reference" not "Ref").


## 10. Date Comparison Must Use Date Objects, Not Strings

**Principle:** Family H (Verify the real thing, not the abstraction)


Comparing ISO date strings with `<` / `>=` works for same-length same-format strings but silently produces wrong results when formats differ (e.g. `"2025-3-5" < "2025-12-01"` is `True` but `"2025-3-5" < "2025-10-01"` is `False` because `"3"` > `"1"`). Always parse to `date` objects before comparison.

**See also (principle cluster H):** #98 (same family, distinct angle: datetime representation traps.).


## 11. ISO Date Validation Must Enforce Zero-Padding

**Principle:** Family A (Equivalence-class coverage)


`map(int, "2025-3-5".split("-"))` succeeds, but `YYYY-MM-DD` requires two-digit month and day. Validate each component's string length: year 4 digits, month 2 digits, day 2 digits. Same applies to `HH:MM:SS` time components.


## 12. Three-Way Doc Sync: Code, Registry, Decision Log

**Principle:** Family D (Single source of truth)


When a feature uses both code-based mappings and canonical documentation (e.g. operator origin registry, mapping decision log), any field change must be applied to all three in the same commit. Code review consistently catches doc drift as a finding. Add a verification step to the plan: "grep for changed field names in registry and decision log."

**See also (principle cluster D):** #41, #51, #67 (same family, distinct angle: multi-authority synchronization; #67 is the test-enforced variant of #21's manual grep.).


## 13. Integration Test Fixture Consistency for Computed Fields

**Principle:** Family D (Single source of truth)


When adding a computed field to a data class used in integration tests, update ALL construction sites to compute the field from actual test data, not from a zero-valued or empty placeholder. Using `StatsClass.from_entries([])` while the entries list has real data produces inconsistent output (statistics section shows all zeros next to non-zero aggregated values). Search for all construction sites with `grep -n "DataClass("` before committing; each site must derive the new field from its own test data.


## 14. Atomic File Replacement: No Pre-Deletion

**Principle:** Family E (Temporal / ordering invariants)


Never call `safe_remove_file(target)` before `temp_path.replace(target)`. On POSIX, `Path.replace()` atomically replaces the target file. The "remove then replace" sequence breaks atomicity: if `replace()` fails after the removal, the old report is permanently lost and the new file is stranded in `.tmp`. Correct pattern:

```python
# ✅ CORRECT: atomic on POSIX
workbook.save(temp_path)
temp_path.replace(target)  # replaces atomically; no pre-deletion needed

# ❌ WRONG: data loss window between these two lines
safe_remove_file(target)
temp_path.replace(target)
```


## 15. Default Value Assignment Before Derived Computation

**Principle:** Family E (Temporal / ordering invariants)


Always apply defaults to source variables before computing derived values from them. Anti-pattern:

```python
# ❌ WRONG: log_file computed from None even when output_dir has a default
log_file = output_dir / "report.log" if output_dir else None
output_dir = output_dir or DEFAULT_OUTPUT_DIR

# ✅ CORRECT: apply default first, then compute derived values
output_dir = output_dir or DEFAULT_OUTPUT_DIR
log_file = output_dir / "report.log"
```

Any variable that depends on another must be computed after all defaults are applied to its source.


## 16. Don't Use `_private` Constants Across Module Boundaries

**Principle:** Family F (Layering / dependency direction)


Constants prefixed with `_` are module-private by convention. When a constant is needed in another module (e.g., the production module needs `_DEFAULT_ZERO_BASIS_REVIEW_THRESHOLD` from the config module), rename it to a public name first. Importing private names across modules violates the API boundary and creates hidden coupling. Apply the same rule that lesson #5 states for tests.


## 17. Plan Edge Case Behavior Must Be Traced to Correctness Outcome

**Principle:** Family H (Verify the real thing, not the abstraction)


When writing a plan's Gist & Examples section, trace every described "edge case" or "behavior change" outcome to its user-facing result and verify it satisfies the project's correctness requirements, not just that it differs from the previous behavior.

A common failure mode: comparing the new behavior to the old one ("better than X") without verifying the new behavior is itself correct. Example from this project: "an absent filter input → `frozenset()` → contaminated upstream rows pass through" was initially described as an improvement over "an absent filter input → rows silently dropped". Both behaviors produce wrong figures. The correct behavior is to raise `FileProcessingError` immediately; the improvement is the explicit failure, not acceptance of contaminated data.

**Test:** For every edge case in a plan, ask "what does the user see in the output?" and verify that output is either correct, or flagged as requiring review with a specific reason. Contaminated financial data presented without a flag is never acceptable.

**Cross-check:** Verify that described edge case behavior is consistent with existing `CLAUDE.md` constraints (e.g. "Optional source-data ingestion must be non-blocking" does not mean wrong data should silently substitute for missing correct data).

---


## 18. Verify Warning/Guard Path Reachability Before Writing Tests

**Principle:** Family H (Verify the real thing, not the abstraction)


Before writing a test for an existing warning, guard, or defensive code path, verify that the path can actually be triggered with current production code. Trace every condition that must be true simultaneously for the code to reach that branch.

If the path is unreachable via real data (e.g., a placeholder mechanism always fires before the guard condition can be met), the test must either: (a) use a mock/patch to inject the edge case directly, or (b) first amend the implementation to make the path reachable.

Claiming "implementation is already complete" for an untested path without first proving it is reachable leads to tests that can never go RED → the TDD cycle is broken and the coverage is false.


## 19. Read Full Dataclass Definition Before Describing Fields in a Plan

**Principle:** Family H (Verify the real thing, not the abstraction)


When a plan task describes the fields of a dataclass (e.g., listing fields to be moved or created), always read the actual class definition in source code to obtain the complete, current field list, including fields with default values that are easy to miss.

Omitting a field from a plan that is then used downstream (e.g., a `carryover_keys` field consumed by `resolve_split_events`) silently changes behaviour and is not caught until runtime.


## 20. Distinguish Code Comments from Observed Data

**Principle:** Family H (Verify the real thing, not the abstraction)


When describing data behaviours (e.g., "this swap direction occurs"), explicitly distinguish between: (a) a behaviour observed in actual source data files, and (b) a behaviour described in a code comment or docstring.

Code comments reflect developer intent or known edge cases at the time of writing; they are not evidence that the behaviour has occurred in real data. For data-driven claims, check actual input files in `resources/source/` before asserting the behaviour is present.


## 21. Monkeypatch Module-Level Path Constants in Unit Tests

**Principle:** Family H (Verify the real thing, not the abstraction)


See `~/Projects/.ai-playbook/python_guidelines.md` #4 for the canonical rule.
Repo context: `_RULES_DIR = _REPO_ROOT / "docs/maintenance/rules"` in `config.py` is resolved at import time. Tests in `TestLoadRuleConfig` that called `_load_rule_config()` without patching this constant silently read the real `rules.toml` from the working tree. They passed because the real file existed and had the expected active flag; any rename, move, or config edit would cause a cryptic `FileNotFoundError` rather than a meaningful test failure.
Fix: monkeypatch `_RULES_DIR` to a `tmp_path`-based directory with a minimal TOML fixture, identical to the pattern in `TestLoadRuleFlags`.


## 22. Resource-Release Flag Must Be Set After Successful Release Only

**Principle:** Family E (Temporal / ordering invariants)


See `~/Projects/.ai-playbook/python_guidelines.md` #5 for the canonical rule.
Repo context: `workbook_builder.py` set `workbook_closed = True` unconditionally after a `try/except` that swallowed `workbook.close()` exceptions. The `finally` block then skipped the fallback `workbook.close()` call because the flag was already `True`, leaking the file handle whenever both the data-sheet rendering and the subsequent close both raised.


## 23. Extracted Helpers Need Direct Unit Tests for Key Invariants

**Principle:** Family A (Equivalence-class coverage)


When refactoring extracts a private helper from a large orchestrator, add direct unit tests covering the key behavioral invariants (exact-match, partial consume, exhaustion, empty input, no-op/early-return path). Relying only on orchestrator-level coverage means a future regression in the helper requires tracing through the orchestrator before the failure is localized.

Example: extracting the matching helper from the matching-queue orchestrator prompted adding six focused tests in the matching-helper test class, reducing the blast-radius of future regressions to a single function.

**See also (principle cluster A):** tax-reporting "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag" (same family, distinct angle: the audit's only true-duplicate candidate, overturned to OVERLAPPING by the fresh-agent challenge. Canonical = tax-reporting "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag" (domain-neutral control-flow taxonomy), See-also #30 (incident-anchored FIFO witness). Full record in `### true-duplicate candidates` and `## Precision gate`.).


## 24. Failing Tests: Distinguish Stale Expectation from Production Bug

**Principle:** Family H (Verify the real thing, not the abstraction)


When a test fails, first determine whether the test expectation became stale (design changed) or whether production code regressed. Changing production code to make a stale test pass is the wrong fix; it re-introduces the removed behavior.

Indicator: the test reads live state from the system under test (e.g. `review_required=row.review_required`) instead of an explicit hardcoded fixture value. If the underlying mapping changed for valid reasons, the test silently tracks the wrong behavior.

Rule: tests that verify rendering or display behavior (e.g. "REVIEW" vs "OK" in an Excel cell) must use explicit hardcoded fixture values, not values delegated to `row.some_field`. Hardcoding makes the test's intent clear and decouples it from unrelated mapping changes.


## 25. Summary Sheets Should Be Complete Manifests, Not Filtered Lists

**Principle:** Family G (Data-loss observability)


A summary/manifest sheet (e.g. Platform Assumptions) should list ALL items in the dataset with metadata columns, not only items that satisfy a filter condition. Filtering by flag omits clean items that a reviewer may still want to audit, and hides the total scope of the data.

Use flag columns (e.g. "Review Required = YES/NO", sort review-required first) to draw attention to items needing action, while preserving the complete manifest for auditability. Apply red row fill only to the flagged rows.


## 26. Inlining Helpers That Use `defaultdict`: Update Tests That Pass Plain Dicts

**Principle:** Family C (Representation: sentinel vs None vs exception)


When inlining a helper that switches internal state from `{}` to `defaultdict(list)`, any test that directly calls the helper with a plain dict `{}` will silently get a `KeyError` on first missing key. Update such tests to pass `defaultdict(list)` directly, or update the inlined code to use `.setdefault(key, [])` instead of relying on defaultdict auto-init so plain-dict callers still work.


## 27. Verify Staged Diff Matches Implementation Before Finalizing

**Principle:** Family H (Verify the real thing, not the abstraction)


When finalizing work for code review or commit, the staged diff (`git diff master...HEAD`) must match the actual implementation in the working directory. Untracked files that are part of the implementation create a discrepancy; reviewers evaluate stale code while the working directory has different logic.

**Check before finalizing**: Run `git status` and verify no files that are part of the implementation appear as untracked (`??`). If a new source file or test exists in the working directory but is not staged, add it with `git add <file>` before considering the work ready for review.

**Why**: Code reviews evaluate staged changes. If staged code differs from working directory, review findings may be obsolete or the review may miss issues that exist only in untracked files.

**See also (principle cluster H):** #88, #93, #94, #95 (same family, distinct angle: the git/docs-state verification cluster.).


## 28. Try/Finally Resource-Cleanup Scope Must Cover All Raising Operations

**Principle:** Family E (Temporal / ordering invariants)


When using try/finally for resource cleanup (e.g., `workbook.close()`, `file.close()`), ensure all operations that can raise exceptions before the finally block are covered by the same try block. If an operation outside the try/finally raises, the cleanup never runs.

**Fix by**: Either (1) start the try block early enough to cover all operations that can raise, or (2) wrap early operations in their own try/except with explicit cleanup before re-raising.

**Example**: In workbook_builder.py, `aggregate_summary_totals()` was called before the try/finally that closes the workbook. If aggregation raised, the workbook was never closed. Fixed by moving aggregation inside the try block so any exception triggers workbook cleanup.

**See also (principle cluster E):** #78 (same family, distinct angle: try/finally cleanup scope (#39) vs reuse-parsed-value-in-try (#78)).


## 29. Update Documentation When Code Structure Changes

**Principle:** Family D (Single source of truth)


When restructuring code (changing sheet layouts, renaming components, merging or splitting modules), update all documentation that describes the structure in the same session. README files, walkthough documents, and project overviews that describe the old structure become misleading and cause confusion.

**Scope**: Check README.md, any walkthrough or presentation docs, and any architectural decision documents that mention the changed components.

**See also (principle cluster D):** #21, #51, #67 (same family, distinct angle: multi-authority synchronization; #67 is the test-enforced variant of #21's manual grep.).


## 30. Hardcoded Set Maintenance: Check Across All Sections for Duplicates

**Principle:** Family D (Single source of truth)


When maintaining multi-section hardcoded collections (like `_SUPPORTED_FORMATS`, `_STATUS_CODE_DESCRIPTIONS`), items can legitimately belong to multiple categories. Before adding an item to one section, grep across all sections to verify it doesn't already exist elsewhere in the same collection.

**Problem**: Frozensets and dicts silently deduplicate, so duplicate entries don't cause runtime errors but create confusion for maintenance and can mislead readers about category boundaries.

**Check pattern**: `grep -n '"ITEM_NAME"'` in the production module that owns the set, before adding a new entry.

**Example**: "XML", "YAML", "CSV" appeared in both "Active formats" and "Deprecated formats" sections; keep each entry in its most appropriate category only.

**See also (principle cluster D):** #1 (same family, distinct angle: general duplicate-detection seed (#1) vs frozenset cross-section (#42)).


## 31. Add Logging to Silent Exception Handlers

**Principle:** Family G (Data-loss observability)


When using `except Exception: continue` or similar graceful degradation patterns, add warning-level logging before continuing. Silent failures hide real issues (file corruption, permission problems, malformed data) and make debugging impossible.

**What to log**: At minimum, log the file path, exception type, and message so the degradation is observable in logs.

**Pattern**:
```python
# ❌ WRONG: silent failure hides the problem
try:
    rows = read_source_rows(file_path)
    # ... process rows ...
except Exception:
    continue  # No visibility into what failed

# ✅ CORRECT: observable degradation
try:
    rows = read_source_rows(file_path)
    # ... process rows ...
except Exception as e:
    logger.warning("Failed to scan %s: %s. Continuing with empty set.", file_path, e)
    continue
```

**Why**: When the function fails silently, you can't tell whether the empty result is correct (no data) or caused by a bug (file couldn't be read). Logging makes the difference visible.

**See also (principle cluster G):** #29 (same family, distinct angle: structure-recording (#29) vs baseline log-it (#44)).


## 32. Fail Fast for Data-Completeness Operations

**Principle:** Family G (Data-loss observability)


For scan/aggregation functions that populate lookup sets used for validation or classification, fail fast when ALL inputs fail rather than returning empty results that cause incorrect downstream behavior. Partial success with warning is acceptable; total failure should raise an error.

**Pattern**:
```python
# ❌ WRONG - Silent degradation causes incorrect behavior
def _collect_known_entries(files):
    known = set()
    for f in files:
        try:
            known.update(parse(f))
        except Exception:
            pass  # Silently return empty set if all files fail
    return frozenset(known)

# ✅ CORRECT - Fail fast when all inputs fail
def _collect_known_entries(files):
    known = set()
    failures = []
    for f in files:
        try:
            known.update(parse(f))
        except Exception as e:
            failures.append((f, e))

    if files and len(failures) == len(files):
        raise FileProcessingError(f"All files failed: {failures}")
    return frozenset(known)
```

**Why**: When the function returns empty due to total failure, downstream code incorrectly treats valid known entries as unknown, causing data loss. Raising an error surfaces the root cause (file format/parse errors) prominently.

**See also (principle cluster G):** tax-reporting "Cross-Module Function Dependencies Require Complete Imports" (same family, distinct angle: total-failure fail-fast (#46) vs partial-file-set fail-fast (tax-reporting "Cross-Module Function Dependencies Require Complete Imports")).


## 33. Externalize Frequently-Changing Lists

**Principle:** Family D (Single source of truth)


Hardcoded lists that change frequently (frequently-updated identifiers: supported formats, status codes, category labels) should be externalized to data files, not embedded in source code. Use cached loading for performance.

**Pattern**:
```python
# ❌ WRONG - Requires code change for every new format
_SUPPORTED_FORMATS = frozenset(("XML", "JSON", "CSV", ...))  # many items

# ✅ CORRECT - External data file, cached in memory
@lru_cache(maxsize=1)
def _load_supported_formats() -> frozenset[str]:
    with open("the known-formats file") as f:
        return frozenset(json.load(f)["formats"])
```

**Why**: Lists representing external reality (the known-format set, format support, compliance lists) change independently of code. Externalizing allows updates without code changes and separates configuration from logic.


## 34. Excel Output Visual Structure Tests

**Principle:** Family A (Equivalence-class coverage)


When adding or modifying Excel report layouts, add visual structure tests to verify row placement, cell merging, blank rows, and header structure, not just data values. This prevents regressions where structural changes accidentally modify layout.

**What to test:**
- **Row placement**: Section title row, blank row count (exactly one vs double), header row positions, data start row
- **Cell coordinates**: Verify specific values at expected positions (e.g., the report title at A1, "Day" at B4)
- **Cell merging**: Verify merged cell ranges using `sheet.merged_cells.ranges` (e.g., SALE header spans B3:E3)
- **Cell formatting**: Verify bold fonts, red fills, and other visual indicators
- **Column positions**: Regression guard against column index changes (e.g., "Country" at col 1, "Settlement Date" at col 2)

**Pattern:**
```python
# Test section title placement and formatting
def test_section_title_at_row_1(self, sheet):
    assert sheet["A1"].value == "REPORT TITLE"
    assert sheet["A1"].font.bold

# Test blank row count (not double-spaced)
def test_single_blank_row_after_title(self, sheet):
    assert sheet["A2"].value is None  # Row 2 is blank
    assert sheet["A3"].value is not None  # Row 3 has header

# Test cell merging
def test_sales_header_merged_across_4_columns(self, sheet):
    assert "B3:E3" in {r.coord for r in sheet.merged_cells.ranges}
```

**Why**: Data-value tests alone cannot detect layout regressions. A structural change like modifying `start_column` from 2 to 1 would misalign data columns without breaking data-value assertions. Visual structure tests catch these regressions by explicitly verifying the expected layout geometry.

**See also**: `tests/unit/application/persisting/test_report_sheet.py::TestWriteReportSheetTotals` for example visual structure tests


## 35. Structural Change Verification for Absolute-Position Code

**Principle:** Family A (Equivalence-class coverage)


When modifying table structures (adding/removing columns), verify that all downstream code using those positions is correct. Distinguish between:

- **Absolute-position code** (writes to specific column numbers): needs manual verification after structural changes
- **Offset-based code** (uses `start_column + N`): may auto-adjust but still needs verification

**Pattern:** After removing/adding columns, grep for all code that writes to specific column indices and verify correctness. For the output table, the region pass writes to absolute positions (col 1 and col 10) and was unaffected by removing the "Reference" column because it uses direct column indices rather than offsets from `start_column`.

**Verification step:** Add a verification task to the plan when structural changes affect column positions. Run the relevant tests to confirm no regression.

**Example:** After removing the "Reference" column from the aggregated-output table, verify that the region pass (lines 196-197 of the output-table module) still writes to the correct columns: column 1 (Region) and column 10 (Zone).

## Quality Assurance Commands

```bash
uv run ruff check . --select=E501     # Line length
uv run ruff check . --select=F401     # Unused imports
uv run ruff check . --select=PL       # Pylint rules

grep -r "Path(__file__)" tests/ || echo "No fragile test paths"
grep -r "= True" src/ --include="*.py" | grep -v "def " | head -10

uv run pytest -m unit          # Fast feedback during development
uv run pytest -m integration   # Before committing


## 36. Validation-First Investigation Pattern

**Principle:** Family H (Verify the real thing, not the abstraction)


When a plan investigates "is X handled correctly?" or "does the system correctly handle Y?", structure the plan with verification tasks before implementation tasks:

1. **Start with verification:** Code inspection, test execution, and documentation review
2. **Then decide on implementation:** Skip implementation tasks if verification shows correctness
3. **Document findings:** Create investigation artifacts under `docs/tmp/` (or promote to canonical docs if reusable)

This pattern prevents unnecessary work when the current implementation is already correct. It applies to any "is this handled correctly?" question, regardless of domain.

**Example:** The plan file for the section-specific loss-treatment investigation used Tasks 1, 3, 5, 7, 8 for verification (code inspection, source archiving, docs review, upstream-data-source investigation, test execution) and skipped Tasks 2, 4, 6 (region-specific config, tests, guidance) because verification confirmed the existing implementation was correct. See the investigation record (local) and the plan file for the full plan.

**See also:** plan_quality_guidelines.md for plan structure guidance on verification-before-implementation task ordering.

**See also (principle cluster H):** tax-reporting "Probe the Canonical URL Before Assuming an Official Source Is Unavailable", tax-reporting "Decision-Point Doc Prose Enumerations Must Match Implemented Code Branches" (same family, distinct angle: investigation pattern / data-trace / characterization-test.).


## 37. Data Trace Verification Requirement

**Principle:** Family H (Verify the real thing, not the abstraction)


When a plan investigates "is X handled correctly?" or "does the system correctly handle Y?", code inspection alone is INSUFFICIENT. The investigation must include ACTUAL data trace verification:

1. **Trace the user's specific case:** For the exact reported scenario, verify data flows from source CSV through to final output. Do not rely on code inspection alone.
2. **Verify output matches source classification:** If the source report shows "Loss" and the output shows "Gain", the investigation is incomplete regardless of whether code CAN handle negatives.
3. **Command pattern:** `grep "specific_value" source.csv` → compare with actual Excel output cell value
4. **Failure consequence:** An investigation that concludes "no code changes needed" without performing data trace verification is INCOMPLETE and must be redone.

**Example:** The category-specific loss-treatment investigation concluded "no code changes needed" based on code inspection alone. However, data trace verification revealed that the upstream data source's report classified entries as "Loss" while the generated output showed them as "Gain", a clear discrepancy that code inspection missed.

**See also (principle cluster H):** #54, tax-reporting "Decision-Point Doc Prose Enumerations Must Match Implemented Code Branches" (same family, distinct angle: investigation pattern / data-trace / characterization-test.).


## 38. Independent Validation Fields vs Entry-Level Review Flags

**Principle:** Family C (Representation: sentinel vs None vs exception)


When adding validation-related fields to a dataclass that already has `review_required`/`review_reason` fields, distinguish between:
- **Entry-level review flags**: domain-specific validations that apply to the entry itself
- **Independent validation results**: cross-report or cross-system validations that have their own review criteria

**Pattern:**
- Add validation results as optional nested dataclass fields (e.g., `secondary_validation: SecondaryValidationResult | None = None`)
- Do NOT integrate validation-result `review_required` into entry-level `__post_init__` validation
- Keep the two review mechanisms independent; validation result carries its own `review_required`/`review_reason`
- Tests that verify "YES:"/"NO" rendering must set the nested field explicitly, not delegate to origin fields

**Why:** Entry-level validation enforces that `review_reason` is set when `review_required=True`. Independent validations have their own lifecycle and should not trigger entry-level validation. Tests must verify independence explicitly.

**Example:** In Task 1 of the validation design, a secondary-validation field was added to the entry dataclass as an optional field. The `__post_init__` validation only checks entry-level `review_reason`, not the secondary-validation `review_reason`. A dedicated test verifies this independence.

**See also:** Lesson #32 (Two-Level Review Flags), the domain rule on cross-record validation signals in the domain rules doc


## 39. Field Aggregation Strategy Depends on Semantics

**Principle:** Family D (Single source of truth)


When aggregating grouped entries (e.g., a matching pipeline grouping source rows into aggregated output events), field aggregation strategy depends on field semantics, not all fields should be summed.

**Pattern:** For each field in the aggregated result, choose the strategy based on what the field represents:
- **Lookup value fields**: Take from first entry (all entries in group share the same lookup key, so the value is identical across entries). Example: the authoritative lookup value keyed by `(date, sku, account)`
- **Per-row contribution fields**: Sum across all entries. Example: the computed result where each row contributes to the total
- **Boolean flags**: Use OR logic (True if ANY entry has True). Example: `direction_conflict`, `review_required`
- **Severity indicator fields**: Use maximum value. Example: `magnitude_diff_percent` to show worst deviation
- **Narrative text fields**: Join unique values with delimiter and deduplicate. Example: `review_reason` joined with "; "

**Implementation:** the validation-aggregation helper in Task 3 of the validation design demonstrates all five patterns.

**Why:** Assuming "sum" for all numeric fields is incorrect; some numeric fields represent a shared lookup value that must NOT be summed, while others represent independent contributions that must be summed. Mixing these semantics produces incorrect results (e.g., summing the authoritative lookup value would multiply the lookup value by the number of rows in the group, which is wrong).

**Example:** In the grouped-entry aggregation, the authoritative lookup value comes from the first entry because all rows in the matching queue for the same aggregated event share the same authoritative lookup value. But the per-row contribution is summed because each row contributes its own result to the total.

**See also:** tax-reporting lesson "Trace Each Affected OGR Row to Its Originating TH Type Before Designing a Type-Filtered Scanner" (authoritative-source overrides timing)

**See also (principle cluster D):** #104 (same family, distinct angle: field-semantics determine strategy (tax-reporting "Reuse the Parsed Value Inside the Existing Try Block When Extracting a Second Derived Value") vs field-identity (#104)).


## 40. Excel Conditional Formatting Priority Matters

**Principle:** Family E (Temporal / ordering invariants)


When applying multiple conditional fill conditions to Excel rows, implement explicit priority ordering. Highest-priority conditions should be checked first and return early, preventing lower-priority conditions from masking important issues.

**Pattern:**
1. Create a dedicated conditional formatting function (e.g., `_apply_conditional_formatting`) that documents the priority order in its docstring
2. Check conditions in priority order and return early after applying the highest-priority fill
3. Use early returns to prevent fallthrough to lower-priority conditions

**Priority example (highest to lowest):**
1. RED fill for critical issues (e.g., an authoritative-source conflict indicating sign disagreement between the authoritative source and the calculated value)
2. YELLOW fill for warnings (e.g., magnitude differences exceeding threshold)
3. RED fill for entry-level review requirements (e.g., rows above a review threshold)
4. BLUE fill for informational highlights (e.g., multi-source rows)
5. No fill (default)

**Why:** Without explicit priority, the last condition checked wins regardless of severity. A critical issue could be masked by a less severe condition that happens to apply first.

**Example:** In Task 4 of the validation design, the conditional-formatting helper checks authoritative-source conditions before entry-level review conditions. An authoritative override (critical) gets RED fill even if the entry also has `review_required=True` (less severe). If the order were reversed, the entry-level RED fill would be applied first and the critical authoritative-source conflict would be masked.

**Implementation notes:**
- Fill colors should be defined as module-level constants for consistency and to avoid repeating color codes
- Add helper functions for fill assertions (e.g., `_is_yellow_fill()`) to keep tests consistent

**See also:** Lesson #7 (Excel Output Security), Lesson #14 (Excel Column Width), Lesson #52 (Excel Output Visual Structure Tests), Lesson #61 (Adding Excel Columns Requires Constant Updates)


## 41. Adding Excel Columns Requires Constant Updates

**Principle:** Family D (Single source of truth)


When adding new columns to an Excel sheet output, update all related constants and ranges in the same commit. A single new column typically requires updates in multiple places.

**Required updates when adding columns:**
1. Column count constant (e.g., `_REPORT_NUM_COLS`)
2. Headers list (add new header string)
3. Data row rendering (write new cell value or blank/None)
4. Conditional formatting range (loop bound must match new column count)
5. Test constants (e.g., `_NUM_REPORT_COLUMNS`)
6. Auto-width tests (loop bound for column iteration)

**Verification:** Run tests after adding columns. Common failures:
- `IndexError` from loops using old column count
- Misaligned headers vs data columns
- Conditional formatting not covering new columns

**Why:** These constants are coupled; they all represent "how many columns exist." Missing one causes bugs that only appear at runtime or in specific test scenarios.

**Example:** In Task 4 of the validation design, three new authoritative-source validation columns were added (18, 19, 20). The implementation updated:
- `_REPORT_NUM_COLS` from 17 to 20
- `report_headers` list with three new header strings
- `_render_report_row()` to write authoritative-source values (or None when absent)
- `_apply_conditional_formatting()` to loop through all 20 columns
- Test `_NUM_REPORT_COLUMNS` from 17 to 20
- Auto-width test to check 21 columns (headers + 1 blank)

**Pattern:** When adding multiple columns at once, consider using a local constant or calculated offset to avoid off-by-one errors. For example, `FIRST_OVERRIDE_COL = 18` and `NUM_OVERRIDE_COLS = 3` makes the range explicit.

**See also:** Lesson #60 (Excel Conditional Formatting Priority)


## 42. Test Blank/Null Handling Explicitly for New Optional Columns

**Principle:** Family A (Equivalence-class coverage)


When adding columns that can be blank/None (e.g., when validation data is absent), add dedicated tests for that state. Do not assume "no data" works correctly based on "with data" tests.

**Pattern:**
1. Add a test specifically for the blank/None state (e.g., `test_secondary_validation_columns_blank_when_secondary_validation_none`)
2. Verify the column cells are `None` (not empty string, not zero, not default value)
3. Verify conditional formatting does NOT apply for blank state (no fill when no data)

**Why:** "With data" tests only exercise the populated path. The blank/None path has different code branches (skipped assignments, no formatting applied) and is a common source of bugs.

**Example:** In Task 4 of the validation design, a dedicated test verifies that when the optional validation field is `None`, the corresponding columns are explicitly `None` rather than containing leftover data or default values.

**See also:** Lesson #60 (Excel Conditional Formatting Priority), Lesson #61 (Adding Excel Columns Requires Constant Updates)


## 43. Backward Compatibility Testing for Flag-Controlled Features

**Principle:** Family A (Equivalence-class coverage)


When adding a new feature controlled by a boolean flag (like `enable_secondary_validation`), create dedicated backward compatibility tests that verify the "disabled" state preserves existing behavior, not just that the "enabled" state works correctly.

**Pattern:**
1. Create a dedicated test class for backward compatibility (e.g., `TestFeatureDisabledBackwardCompatibility`)
2. Test that the disabled state yields the same results as before the feature existed
3. Verify that flag-specific fields are None/blank when disabled
4. Verify that core values (result, proceeds, cost) remain unchanged from original input

**Why:** Tests for the "enabled" state only verify the new behavior works. Without explicit tests for the "disabled" state, you may silently break existing users who have the flag disabled.

**Example:** In Task 6 of the validation design, a dedicated test verifies that when `enable_secondary_validation=False`, all entries have the optional validation field set to `None` and the computed result values match the original calculated values exactly.

**Implementation trade-off note:** When a plan specifies a cosmetic constraint (e.g., "Excel has no authoritative-source columns when disabled"), but the implementation uses a fixed column structure with blank cells, prefer verifying behavioral correctness over cosmetic compliance. A consistent column structure is often a reasonable engineering trade-off.


## 44. Recalculate Validation Metrics from Aggregated Values

**Principle:** Family D (Single source of truth)


When validating aggregated data against an external source (the authoritative override source, statements, etc.), compute validation metrics from the **aggregated totals**, not from individual pre-aggregation rows.

**Problem:** Comparing individual rows to aggregated totals produces misleading percentages:
- Single row: `<ROW_AMOUNT>` vs authoritative-source total: 137.73 → "differs by 5474%" ❌ (noise)
- Aggregated: ~137 vs authoritative source: 137.73 → "differs by ~0.5%" ✅ (signal)

**Pattern:**
1. Apply corrections (e.g., direction override) to individual rows before aggregation if needed for correct totals
2. During/after aggregation, recalculate all validation metrics from aggregated values:
   - `direction_conflict` = sign(aggregated_override) ≠ sign(aggregated_calculation)
   - `magnitude_diff_percent` = |(aggregated_override - aggregated_calculation) / aggregated_calculation| × 100
   - `review_required` = based on aggregated thresholds
   - `review_reason` = built from aggregated state
3. Don't inherit/OR individual row flags; they reflect pre-aggregation noise

**Why:** Pre-aggregation rows are accounting artifacts, not the reportable event. The report covers the aggregated event, so only aggregated-level validation is meaningful to the reviewer.

**Example:** In the aggregation helper, the function recalculates `direction_conflict`, `magnitude_diff_percent`, and `review_required` from the summed per-row contribution and the shared authoritative lookup value, rather than taking max/OR from individual rows.

**See also:** the tax-rule code for the report-validation rule, tax-reporting lesson "OGR Directional Authority vs Wholesale Replacement" (authoritative-source directional authority)

**See also (principle cluster D):** tax-reporting "Trace Each Affected OGR Row to Its Originating TH Type Before Designing a Type-Filtered Scanner" (same family, distinct angle: authoritative-source authority -- override ordering (tax-reporting "Trace Each Affected OGR Row to Its Originating TH Type Before Designing a Type-Filtered Scanner") vs split by aspect (this lesson) vs aggregate-then-validate (this lesson)).


## 45. Avoid Circular Dependencies During Module Extraction

**Principle:** Family F (Layering / dependency direction)


When extracting a function to a new module, check what constants and functions it references from the source module. Circular imports occur when the new module imports from the source, and the source still needs to import from the new module.

**Resolution options:**
- Move shared constants to a lower-level module that both can import
- Inline simple literals (like `Decimal('0')`) locally in the new module
- Redesign to eliminate the cross-dependency

**Example from Task 8:** Extracting `_extract_loan_activity()` from the production module to a focused submodule required handling the `ZERO` constant. Defining `ZERO = Decimal('0')` locally in the new module avoided a circular import, since the constant is only used for loan balance calculations.


## 46. Module and Class Size Limits

**Principle:** Family F (Layering / dependency direction)


Large modules and classes become difficult to understand, test, and maintain. They accumulate unrelated responsibilities over time ("god class" or "god object" anti-pattern).

**Guidelines:**
- When a module exceeds 1,000 lines or contains 50+ functions/classes, consider extraction
- When a class exceeds 500 lines, evaluate whether it has multiple responsibilities
- Aim for focused modules: 200-600 lines is a practical target for most application code
- Orchestration layers should be thin: ~500 lines max for top-level coordination

**Extraction signals:**
- Module name describes multiple unrelated concepts
- Functions can be grouped into cohesive subsystems (e.g., parsing, validation, aggregation)
- Changes to one area of the module require understanding many unrelated sections
- Testing requires extensive fixture setup due to cross-cutting dependencies

**Example from the report-builder refactor:** The original production module was over 3,000 lines with dozens of functions handling parsing, validation, classification, aggregation, the matched-group pipeline, and orchestration. After DDD-based extraction into focused submodules (entities, classification, validation, parsing, aggregation, the authoritative-source handler, loan activity, chain derivation, operator origin, the matching helpers), the orchestration layer reduced to under 800 lines (over 60% reduction), with each specialized module under 500 lines.


## 47. Single Responsibility Principle for Modules

**Principle:** Family F (Layering / dependency direction)


Each module should have one clear reason to change. When a module's name or purpose cannot be described succinctly, or when it contains multiple independent subsystems, extraction is needed.

**Module cohesion indicators:**
- All functions serve the same domain concept (e.g., "the row-classification pipeline")
- Functions can be organized around a single abstraction or entity
- Changes to business requirements affect a predictable subset of functions
- Module has a clear, narrow public API

**Module cohesion anti-patterns:**
- "Utility" modules that mix unrelated helpers (parsing, validation, transformation)
- "Manager" classes that orchestrate unrelated workflows
- Modules where functions reference different domain layers without clear hierarchy

**Extraction approach:**
1. Group functions by domain responsibility (parsing, validation, aggregation, etc.)
2. Identify shared abstractions (entities, value objects)
3. Create cohesive modules with clear names (a focused submodule like the classification module, not `utils.py`)
4. Maintain backward compatibility via package `__init__.py` re-exports
5. Use domain-driven design: entities → services → orchestration

**Example from the report-builder refactor:** Functions were grouped by responsibility into domain-aligned focused submodules:
- the entities submodule: domain entities (source metadata, the entry dataclass, etc.)
- the classification submodule: classification logic with LRU-cached helper data
- the validation submodule: date/time validation with clear ISO format rules
- the aggregation submodule: aggregated-output calculation with threshold filtering
- the authoritative-source handler submodule: report-override logic
- the matching helpers submodule: the matched-group pipeline for related items
- the parsing submodule: file discovery and parsing
- the source-metadata submodule: source-to-supplier resolution with temporal validity

Each module has a single, clear responsibility and can be understood independently.


## 48. Read Implementation Before Writing Test Expectations

**Principle:** Family H (Verify the real thing, not the abstraction)


When adding edge case tests for existing functions, read the actual implementation first to understand what patterns it supports before writing expected results.

**Anti-pattern:** Writing test expectations based on function name, documentation, or assumptions about what the function "should" do, then debugging failures when expectations don't match reality.

**Correct approach:**
1. Read the function implementation completely
2. Identify all conditional branches, special cases, and return paths
3. Write test expectations that match the actual behavior
4. Add tests for genuine edge cases, not imagined patterns

**Example from source-identification tests:** Initial tests expected "Widget-X (Type A)" → "Category A" and "SKU-1234...abcd" → "Category B", but the actual `_identify_source` implementation returns "Unknown" for both patterns. Reading the implementation first would have revealed: the function only matches sources in a predefined `_KNOWN_SOURCES` set after normalization, it doesn't guess from label suffixes or code patterns.


## 49. Edge Case Coverage for Validation Functions

**Principle:** Family A (Equivalence-class coverage)


Validation functions with conditional logic need comprehensive edge case coverage for all validation branches.

**Required coverage for date/time validation:**
- Format checks: correct vs incorrect separators, missing components, extra components
- Zero-padding: required vs missing vs over-padded (e.g., "2024-1-1", "2024-001-01")
- Numeric ranges: non-numeric characters, out-of-range values (year < 2009, > 2100, month > 12, day > 31, hour > 23, minute > 59, second > 59)
- Calendar validity: Feb 30, Apr 31, leap year Feb 29 (2024 vs 2023)
- Time components: missing seconds, zero-padding, boundary values (00:00:00, 23:59:59)
- Whitespace handling: leading/trailing whitespace, multiple spaces, empty strings
- Boundary conditions: exact match on lower/upper bounds, before/after thresholds

**Required coverage for string validation:**
- Empty strings, whitespace-only strings, single-character inputs
- Multi-byte characters, control characters
- Multi-character prefixes, padded inputs
- Case insensitivity when applicable

**Example from date validation tests:** Added 57 edge case tests for `_validate_iso_date` and `_parse_transaction_date` covering zero-padding validation (2024-1-1 rejected), calendar dates (Feb 30 rejected), leap years (Feb 29 2024 accepted, Feb 29 2023 rejected), time boundaries (00:00:00 accepted, 24:00:00 rejected), and whitespace handling.


## 50. Direct Unit Testing for Extracted Helper Functions

**Principle:** Family A (Equivalence-class coverage)


When a complex function is extracted into a helper, add direct unit tests for the helper rather than relying only on indirect testing through integration tests.

**What to test directly:**
- Early return conditions (empty inputs, no matches)
- Conditional branches (different input paths)
- Boundary conditions (exact threshold values)
- State mutation or concatenation (appending reasons, preserving carryover)
- Edge cases (multiple items requiring min/max selection)

**Example from the matching helpers:** A helper that flags surplus-matched rows was extracted but initially only tested indirectly through the matching-pipeline integration. Added direct unit tests covering: empty surplus input (early return), mismatching identity/group (no effect), events before vs after the earliest-surplus date (conditional flagging), appending the surplus reason to the existing `review_reason` (concatenation), and preserving carryover/partial keys (state preservation).

**See also (principle cluster A):** #30 (same family, distinct angle: the audit's only true-duplicate candidate, overturned to OVERLAPPING by the fresh-agent challenge. Canonical = tax-reporting "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag" (domain-neutral control-flow taxonomy), See-also #30 (incident-anchored FIFO witness). Full record in `### true-duplicate candidates` and `## Precision gate`.).


## 51. Early Returns Can Skip Mandatory Sections

**Principle:** Family E (Temporal / ordering invariants)


When a function renders multiple independent sections (e.g., Excel sheet writers with platform data + methodology documentation), an early return in an optional-data branch can skip mandatory sections that must always render.

**Pattern to avoid:**
```python
if not optional_data:
    render_no_data_message()
    return  # ❌ Skips mandatory methodology section
render_mandatory_section()
```

**Correct pattern:**
```python
if not optional_data:
    render_no_data_message()
    # Continue to mandatory section
else:
    render_optional_data()
render_mandatory_section()  # Always executes
```

**Why this matters:** Early returns are easy to miss during refactoring. When a section is mandatory (e.g., legal documentation, audit trail), control flow must guarantee it renders regardless of upstream data availability. Use if/else blocks instead of early returns, and test with empty inputs to verify the mandatory section appears.

**Example from assumptions_sheet.py:** The methodology section (legal documentation) must render even when the source data is empty. Original code had `if not summaries: return` which skipped methodology entirely. Fixed by restructuring to if/else so methodology renders in both branches.

---


## 52. Verification Tests for Canonical Source Synchronization

**Principle:** Family D (Single source of truth)


When a system has a canonical source of truth (decision points document, feature flags config, etc.) that must be reflected in derived output (Excel methodology, UI text, API responses), add a verification test that enforces synchronization between the source and the output.

**Pattern:**
1. Define the expected set of items from the canonical source (e.g., all rule IDs from `rules/2025.md`)
2. Scan the derived output for those items (e.g., regex search for `RULE-XXX` patterns in Excel methodology descriptions)
3. Assert two conditions: (a) no expected items are missing, (b) no unexpected items are present

**Implementation example:**
```python
def test_all_rules_documented(self):
    """All rules from canonical doc are documented in output."""
    expected = {"RULE-001", "RULE-002", ..., "RULE-011"}  # From rules/2025.md
    found = set()
    for description in output_descriptions:
        found.update(re.findall(r"RULE-\d{3}", description))
    missing = expected - found
    assert not missing, f"Missing: {sorted(missing)}"
    extra = found - expected
    assert not extra, f"Unexpected: {sorted(extra)}"
```

**Why this matters:** Without verification tests, documentation drifts silently. A rule added to the canonical document may never be added to the Excel output, or a removed rule may remain as dead text. The test enforces consistency and catches drift immediately.

**Example from Task 4:** The `test_all_rules_documented` test verifies that all 11 rules (`RULE-001` through `RULE-011`) from the canonical `rules/2025.md` are present in the Excel methodology section. If a rule is added to the TOML but not to the methodology text, the test fails.

**See also:** `docs/maintenance/rules/2025.md` (canonical source), `tests/unit/application/persisting/test_assumptions_sheet.py::TestMethodologyAssumptionsSection::test_all_rules_documented`

---

**See also (principle cluster D):** #21, #41, #51 (same family, distinct angle: multi-authority synchronization; #67 is the test-enforced variant of #21's manual grep.).


## 53. Structural Identification for Excel Output Tests

**Principle:** Family H (Verify the real thing, not the abstraction)


When testing Excel output, identify data items by their structural properties (column population, font attributes) rather than hardcoded value exclusions. Tests using hardcoded values from test fixtures break when fixture defaults change.

**Pattern to avoid:**
```python
exclusion_set = {
    "Section Header 1",
    "Section Header 2",
    "Acme Exchange",  # ❌ From test fixture default
    "NO",             # ❌ From test fixture default
}
if cell_value not in exclusion_set:
    items.append(cell_value)
```

**Correct pattern, identify by structure:**
```python
for row_idx in range(1, 200):
    label = ws.cell(row_idx, 1).value
    description = ws.cell(row_idx, 2).value
    column_3 = ws.cell(row_idx, 3).value

    # Methodology items: label + description present, column 3 empty
    if label and description and not column_3:
        items.append((label, description))
```

**Why this matters:** Hardcoded exclusions couple tests to implementation details of test fixtures (`_make_entry(platform="Acme Exchange")`). When fixture defaults change, tests fail despite the Excel structure being correct. Structural identification decouples tests from data values and verifies the actual output format.

**Verification approach:** Before writing the test, inspect the actual Excel rendering to understand structural properties:
- Which columns are populated for each row type?
- Are labels bold or regular?
- What distinguishes section headers from data rows?

**Example from test_assumptions_sheet.py:** The original `test_methodology_items_have_legal_citations` excluded a fixture-default platform name and `"NO"` (values from `_make_entry` defaults). Fixed by checking that methodology items have column 1 (label) + column 2 (description) populated, with column 3 empty (data rows have multiple columns).


## 54. Characterization Tests Can Reveal Plan-Assumption Errors Between Related Quantities

**Principle:** Family H (Verify the real thing, not the abstraction)


When a characterization (golden-value) test captures the actual current behavior and the captured value disagrees with the plan's stated expected value, the disagreement is itself a finding. Investigate the root cause before any implementation task proceeds, because downstream tasks often depend on the incorrect assumed value.

**Why this happens:** Plan authors writing expected values for characterization tests may conflate two related but distinct quantities when one is a downstream authoritative total and the other is the post-transformation output. The override/transformation in question may apply directional authority (sign) while preserving the other quantity's magnitude, so the expected value the author wrote (the authoritative total) is NOT the value the pipeline actually emits.

**Required response when characterization disagrees with the plan:**
1. Capture the REAL current output as the golden value (never the plan's assumed value); the whole point of a characterization test is to lock in actual behavior.
2. Trace WHY they differ using raw source inspection (read source CSVs directly, sum the matched items, identify which quantity the plan's number actually represents).
3. Reconcile the plan narrative so downstream tasks and the user see the corrected value with rationale.
4. Flag the discrepancy to the orchestrator/user so dependent tasks are aware.

**Do NOT** weaken the characterization assertion to match the plan's incorrect value; that defeats the test's purpose and hides a real bug or real behavior.

**Example:** A characterization test captured a Case 2 expected aggregated output that disagreed with the plan's stated expected value (`<-AUTH_NET_EUR>` vs the actual `-<CALC_ITEMS_EUR>`). The authoritative-override function uses the override source for DIRECTION only and preserves the calculated MAGNITUDE: the 109 matched rows sum to `+<CALC_ITEMS_EUR>` pre-override, and flipping the sign of each yields `-<CALC_ITEMS_EUR>` post-override. The `<-AUTH_NET_EUR>` is the authoritative-source row total, a different quantity from the post-override aggregated output. The characterization test captured `-<CALC_ITEMS_EUR>` and the plan narrative was reconciled. See tax-reporting lesson "OGR Directional Authority vs Wholesale Replacement" (authoritative-source directional authority runtime semantics).

**See also:** Lesson #54 (validation-first investigation), tax-reporting lesson "Probe the Canonical URL Before Assuming an Official Source Is Unavailable" (data trace verification), tax-reporting lesson "OGR Directional Authority vs Wholesale Replacement" (authoritative-source directional authority runtime semantics), `docs/maintenance/plan_quality_guidelines.md`.

---


## 55. Trace the Fixture When Plan Pseudocode Compares Same-Unit Fields by Name

**Principle:** Family H (Verify the real thing, not the abstraction)


When plan pseudocode compares two fields by name and those fields share a unit (currency, count, timestamp) but live on different domain objects or different fields of the same dataclass, do not translate the pseudocode literally. Trace the fixture first to confirm the two fields represent the same quantity. Field names like `result_amount` suggest "the magnitude" but the field's actual semantic may be a derived quantity (computed result = component A − component B) that is structurally different from another currency-denominated field (gross proceeds) even though both live on the same dataclass.

**Why this happens:** Plan authors writing pseudocode for a comparison operation may pick the field whose name sounds closest to the intent ("`result_amount`" sounds like the magnitude), without checking whether the field's actual semantic matches the quantity the comparison requires. When multiple same-unit fields coexist on the same dataclass with distinct meanings (proceeds, cost, computed result, fee), the field-name conflation is invisible until the comparison runs against real numbers.

**Required behavior:**
1. When the pseudocode references a field by name on a domain object, especially for a magnitude or equality comparison, identify which other same-unit fields exist on that dataclass.
2. For each candidate field, trace the fixture to confirm what quantity the field actually carries (read the dataclass docstring; verify against a real source row).
3. Construct the RED-phase test fixture so that the candidate fields are set to DIFFERENT but realistic values, not the same value; this forces the test to discriminate between them. If the fixture sets `proceeds=<FEE_PROCEEDS>` and `result_amount=<FEE_RESULT>`, a pseudocode comparison against `result_amount` will fail visibly (|<FEE_PROCEEDS> − <FEE_RESULT>| = <TOLERANCE_DELTA> > tolerance), exposing the field-name error before production code ships.
4. If the fixture trace shows the pseudocode field is wrong, correct the pseudocode field reference in the plan, document the correction as a DESIGN CORRECTION note, and update the constant's comment to prevent a future maintainer from reintroducing the bug.

**Distinguishing from tax-reporting "Decision-Point Doc Prose Enumerations Must Match Implemented Code Branches":** tax-reporting lesson "Decision-Point Doc Prose Enumerations Must Match Implemented Code Branches" covers characterization tests that capture a value disagreeing with the plan's stated expected value (magnitude vs direction conflation in captured output). This lesson covers plan pseudocode referencing the wrong field by name; the comparison never runs against production data until RED-phase fixture construction exposes the field-name error. Both are verification rules but they have distinct triggers (golden-value disagreement vs fixture-driven field selection) and distinct fixes (reconcile narrative vs rewrite pseudocode field reference).

**Anti-pattern:** Reading pseudocode that says `abs(matches[0].result_amount - abs(auth_row.value)) <= TOLERANCE` and implementing it verbatim, without checking whether `result_amount` (computed result) and `auth_row.value` (gross proceeds) describe the same quantity. The comparison would silently classify correct cases as `Ambiguous` and break the entire downstream pipeline.

**Example:** A plan's pseudocode compared the authoritative source `Value` (gross proceeds for a class of rows) against the calculated `result_amount` (computed result, cost-subtracted). These are different quantities: the authoritative `Value` is gross proceeds and the correct calculated counterpart is `proceeds`. The Case 1 fixture sets `proceeds=<FEE_PROCEEDS>, result_amount=<FEE_RESULT>` against the authoritative source=`<FEE_PROCEEDS>`, so the comparison only succeeds against `proceeds` (|<FEE_PROCEEDS> − <FEE_PROCEEDS>| = 0 ≤ tolerance); comparing against `result_amount` gives |<FEE_RESULT> − <FEE_PROCEEDS>| = <TOLERANCE_DELTA> > tolerance and would wrongly route the row to `Ambiguous`. The fixture-driven trace exposed the field-name error during RED phase, and the constant's comment plus the parsed-row dataclass docstring document the correct field so a future maintainer cannot reintroduce the bug.

**See also:** tax-reporting lesson "Decision-Point Doc Prose Enumerations Must Match Implemented Code Branches" (characterization tests revealing magnitude-vs-direction conflation), tax-reporting lesson "Probe the Canonical URL Before Assuming an Official Source Is Unavailable" (data trace verification), tax-reporting lesson "Reuse the Production Validator When a Test Asserts Against a Domain-Validity Predicate" (read implementation before writing edge-case tests), CLAUDE.md §4 Agent Workflow Rules (verification-first task ordering).

**See also (principle cluster H):** #72, #73 (same family, distinct angle: general plan-claim rule (#72) and its two specific witnesses.).


## 56. Verify Plan-Time Claims About Production Code Before Writing Tasks

**Principle:** Family H (Verify the real thing, not the abstraction)


When a plan task, design invariant, or gist example makes a claim about production code (field semantics, file paths, line numbers, function behavior, return shape), the plan author must verify the claim against the actual source BEFORE writing plan tasks that depend on it. A single Read call per claim eliminates an entire class of plan-review Blockers. The same duty applies when RECEIVING code review: a finding's diagnosis and its proposed remediation are themselves claims about production code (how many sites duplicate a pattern, which module a symbol lives in, what a function returns), and both must be verified against source before the finding is applied or routed. The same duty applies when IMPLEMENTING: a selftest or assertion derived from the plan's described mechanism (e.g. "resolve_plans_dir walks UP to the repo facts") must be traced against the actual implementation before being flipped GREEN, because the implementation may intentionally diverge from the plan's prose and a passing test that pins the prose instead of the contract is a false GREEN.

**Why this matters:** Plan review sub-agents will catch these defects, but every Blocker found in review is a defect the author could have caught with one Read call. Each Blocker forces a revision cycle (re-write the plan, re-launch review, re-verify), costing more rounds than the original verification would have. Plans that ship with N unverifiable claims typically absorb N+ Blockers across the first two review rounds.

**Required behavior:**
1. Before writing any plan task that references a production-code fact (field name, line number, file path, function signature, return type), open the source file and confirm the fact.
2. Field-semantics claims are the highest-risk category: a plan that says "field X carries minute-precision timestamp" must be verified by reading the parser that populates field X. If the parser strips the time component, the claim is wrong and downstream matching logic built on it will fail.
3. Line-number claims drift as the file evolves; cite line numbers only after reading the file at plan time, and prefer function-name anchors over line numbers when the surrounding code is stable. The same applies to inline code comments: name the guarding symbol or feature (e.g. "the fail-fast in the upstream loader") rather than a `file.py:NNN` line, because any edit above the anchor shifts the number.
4. When a user-facing design preference (e.g., "match by timestamp + asset + account + amount") implies a code capability (timestamp precision on a domain field), verify the capability exists before accepting the preference. If it does not, surface the trade-off explicitly in the plan's Monitor section rather than silently substituting an alternative.
5. When acting on a code-review finding, verify the finding's OWN claims before applying or routing it: count the sites a "duplication" finding names (grep for the shared pattern across the package, not just the two the finding cites), and confirm any path/function the finding's proposed fix names actually exists and carries the responsibility claimed. A finding can understate scope or propose a wrong target; applying its proposed fix verbatim can write a second wrong path or leave the real duplication in place.

**Distinguishing from #54 / tax-reporting "Probe the Canonical URL Before Assuming an Official Source Is Unavailable":** Lesson #54 covers investigation tasks ("is X handled correctly?") and mandates verification-first task ordering. tax-reporting lesson "Probe the Canonical URL Before Assuming an Official Source Is Unavailable" extends that to data trace verification. This lesson covers **plan-time claims** about code structure (what a field carries, what a function returns, what line N does) and mandates source verification during plan authoring, before any task is written. The trigger is the author writing a code-reality claim, not the author investigating an existing behavior.

**Anti-pattern:** Writing "the match key is (timestamp, asset, account, amount) with minute-precision timestamp" in a plan without checking whether the entry dataclass's `date` field actually carries minute precision. The field is day-level (the date-formatting helper in the upstream parser strips the time), so the entire matching strategy must be reworked in revision, costing a full review round.

**Example:** A dedup plan claimed minute-precision timestamp matching in its Gist, Design Invariant 6, Task 4 test names, and Task 4 implementation note. The r1 plan review caught the field-shape error as Blocker 1 across 4 plan locations. The revision dropped timestamp from the match key and adopted `(date, asset, account, amount)` with strict-equality at 6-decimal rounding, but the cost was one full review round. A single Read of the date-formatting helper in the upstream parser during plan authoring would have prevented the Blocker entirely.

**Review-reception example (branch review):** Two findings made production claims that verification corrected before they were applied. (a) Finding #6 framed a config-loading block as a TWO-way duplication with the classification module's token-loading helper; grepping the package revealed it is THREE-way (the classification, dedup, and value-resolver modules all mirror the same symlink/size guards over the same JSON), which shifted the right fix from "extract one module" to "share one secure loader." (b) Finding #20's proposed remediation named the matching domain-entities module as the matching engine; that path is the domain-entities module, not the engine (the engine is a separate package). Applying the finding's proposed path verbatim would have written a second wrong reference. In both cases a single grep/Read before acting prevented a wrong fix.

**Implementer-side example (2026-07-03 lessons-recall-hook Task 7):** A Task-7 selftest asserted that `resolve_plans_dir(cwd)` walks UP to the repo facts, because the plan described the mechanism that way. The first attempt failed GREEN-flip: `facts_paths.resolve_toml_key` reads `<start_dir>/.ai-playbook/facts.md` DIRECTLY and does NOT walk up by design; the cross-subdir GATING guarantee is delivered by a different mechanism (`classify_path`'s default-suffix fallback on the target's realpath, Arm 2). The selftest was rewritten to pin the real contract (resolve at root returns the facts value byte-for-byte; subdir returns None by design; the gate fired from a subdir still classifies a `docs/plans/foo.md` target via the Arm 2 fallback). A single Read of `resolve_toml_key` before writing the assertion would have produced the correct selftest first time.

**Citation-precedent example (TH-anchored transaction-view plan):** The plan's Gist bullet 1 and Invariant 2 justified a proposed `tx_id` precedence chain (`TxHash -> TxSrc -> TxDest -> None`) by citing the token-origin helper as the established precedent, claiming "real upstream exports store the transaction hash in `TxSrc`." Reading the cited code revealed it reads `TxSrc` ONLY (single field, no fallback) and an independent parser call site reads `TxHash` ONLY; the two call sites use DIFFERENT fields and neither implements a precedence chain. The chain was net-new behaviour misattributed to existing code. r1 review caught this as Blocker 1; the revision dropped the citation, marked the chain net-new, and added a Task 1 measurement step that halts for user confirmation before locking the precedence from real-CSV data. A single Read of the token-origin helper during plan authoring would have prevented the false-precedent Blocker.

**See also:** Lesson #54 (verification-first task ordering), tax-reporting lesson "Probe the Canonical URL Before Assuming an Official Source Is Unavailable" (data trace verification), Lesson #71 (trace fixture when comparing same-unit fields by name), CLAUDE.md §4 Agent Workflow Rules.

**See also (principle cluster H):** #73 (same family, distinct angle: general plan-claim rule (#72) and its two specific witnesses.).


## 57. Add a Count-Matched-Items-Per-Event Safety Check When Matching by Non-Unique Keys

**Principle:** Family G (Data-loss observability)


When a dedup or matching algorithm uses a key tuple that does not include a globally unique identifier (e.g., `(date, asset, account, amount)` without a transaction hash or row ID), add a count-matched-target-items-per-source-event safety check that logs a warning when one source event matches more than one target item. The warning surfaces two distinct cases for review: legitimate fan-outs (one source event split into N target rows, all expected to match) and coincidental amount collisions (two unrelated events on the same date with the same amount, an over-removal risk).

**Why this matters:** Without a unique identifier, the matcher cannot distinguish "N target items are fan-outs of one source event" from "N target items are unrelated events that happen to share the key." The first case is correct (remove all N); the second is a silent over-removal that corrupts downstream aggregates. The warning does not block removal (the fan-out case is more common in practice) but it makes the coincidental-collision case observable in logs so the user can audit.

**Required behavior:**
1. After the matching pass, group removed target items by their originating source event.
2. For each source event with `matched_count > 1`, log a warning naming the source event (date, label, amount) and the matched count.
3. Phrase the warning to surface both interpretations: "possible fan-out or coincidental amount collision."
4. Add a unit test that constructs the coincidental-collision case (two target items with the same amount as one source event but unrelated to it) and asserts the warning fires.

**Distinguishing from a strict matcher:** A strict matcher (match at most one target per source event, warn on overflow) is tempting but wrong for fan-out cases: a single source event may legitimately produce 50+ target rows, all of which should be removed. The count-based warning preserves correct behavior for the common case while making the rare over-removal case visible.

**Anti-pattern:** Matching by (date, asset, account, amount) with no post-pass check, assuming amount disambiguation is sufficient. On a fixture with 108 target rows at one timestamp (fan-outs of one source event) plus 2 unrelated source events with amounts that coincidentally match 2 of the 108 rows, the matcher silently removes those 2 unrelated rows along with the legitimate matches, corrupting the aggregate. The user sees an unexpected aggregated total with no warning to explain it.

**Example:** A source-event/target-row dedup plan added a per-event count check after a review flagged the silent-overremoval risk. The implementation builds a `dict[source_event_key, list[matched_target_rows]]`, removes all matched rows, and logs a WARNING per source event whose matched count > 1. The motivating fixture had 108 target rows at one timestamp; if any row's amount coincidentally matches an unrelated source event, the warning surfaces the collision for review.

**See also:** CLAUDE.md §3 Repository Constraints (no silent drops), CLAUDE.md §1 Instruction Rules (data-loss at warning+).


## 58. Trace ALL Branches of a Multi-Branch Conditional When Implementing a Tiered Rule

**Principle:** Family H (Verify the real thing, not the abstraction)


When a plan modifies a multi-branch conditional (e.g., an `if amount == 0: ... if total == 0: ...` block) to implement a new tiered rule, the plan author MUST trace every input combination through ALL branches before finalizing the implementation steps. A common failure mode: changing one branch's condition to suppress an input, while leaving the sibling branch unchanged, which still fires on that same input and contradicts the stated design invariant.

**Why this happens:** When reading a conditional like `if amount == 0: flag_A()` followed by `if total == 0: flag_B()`, the author focuses on the branch they intend to modify (the amount branch) and overlooks that the sibling branch (total branch) has no guard against the same input. For the input `amount=0, total=0`, both branches evaluate True and both fire. The plan's design invariant ("zero-zero never flags") is then unachievable as written.

**Required behavior:**
1. Enumerate the full input domain (all combinations of the branching variables).
2. For each combination, trace through EVERY branch in order, not just the branch being modified.
3. If any combination produces an outcome that contradicts a stated design invariant, the plan MUST modify every branch that contributes to that outcome, not just the "obvious" one.
4. Include a trace table in the plan showing input -> expected branch outcomes -> expected final result. The trace is part of the plan, not just a verification step for review.

**Example:** The 2026-06-15 review-threshold plan (r1) proposed gating only the amount branch (`if amount == 0 and total >= threshold:`) while leaving the total branch (`if total == 0:`) unchanged. The design invariant stated "zero-zero entries never flag". But for input `amount=0, total=0`: the amount branch evaluates `0 >= 10` = False (correctly suppressed); the unchanged total branch evaluates `0 == 0` = True (INCORRECTLY fires). The 779 zero-amount entries the plan intended to suppress would still flag. r1 Blocker 1 caught this; the fix required adding `and amount > 0` to the total branch so zero-zero inputs fail both conditions.

**Distinguishing from #72 (verify claims against source):** Lesson #72 verifies that file paths, line numbers, and function signatures match reality. This lesson verifies that the proposed CODE CHANGE produces the stated BEHAVIOR across the full input domain. A plan can have perfectly accurate citations and still specify a code change that contradicts its own design invariants.

**Anti-pattern:** A plan that says "modify branch X to handle case Z; leave branch Y unchanged" without tracing case Z through branch Y. The trace must be explicit: "for input Z, branch X evaluates to <result>, branch Y evaluates to <result>, combined outcome is <result>, which matches/falsifies the design invariant."

**See also:** Lesson #72 (verify plan claims against source), CLAUDE.md §4 Agent Workflow Rules (TDD approach), the r1 Blocker 1 trace in the zero-basis plan review r1 (local).

**See also (principle cluster H):** #91, #81 (same family, distinct angle: plan pseudocode vs tests vs invariants.).


## 59. Calibrate Exception Handling Strategy to the Cost of Silent Failure When Reusing a Helper Pattern

**Principle:** Family B (Error-policy propagation)


When reusing a security/validation pattern from another module (symlink rejection, size limit, JSON parsing), do NOT blindly inherit the source module's exception-handling strategy. The right behavior for malformed input depends on the cost of silent failure at the NEW call site, not at the source. A non-critical feature may gracefully degrade (return empty on malformed input); a correctness-critical feature MUST raise.

**Why this happens:** When a plan says "reuse the security patterns from the known-entry loader," the implementer reads the source function and copies both the validation guards AND the exception handling. The validation guards (symlink rejection, size cap) are universally correct. The exception handling (`except json.JSONDecodeError: return frozenset()`) is a per-feature decision based on what "empty" means downstream. Copying it without checking the new feature's failure cost produces a silent-correctness-bug class.

**Required behavior:**
1. Distinguish "validation guards" (security, format) from "exception handling strategy" (degrade vs raise) when reading the source pattern. Only the guards are universally reusable.
2. For the new call site, ask: what happens downstream if this function returns empty on malformed input?
   - If empty means "skip a non-critical enrichment" (e.g., known-entry detection, cosmetic annotation) -> graceful degradation with WARNING log is correct.
   - If empty means "skip a correctness-critical step" (e.g., deduplication, required validation, aggregation) -> raising `FileProcessingError` is mandatory. Silent empty leaves wrong data in the output.
3. Only the MISSING-file case is uniformly safe to degrade (Design Invariant 8 pattern); malformed-content (bad JSON, wrong shape, wrong types) must raise when correctness is at stake.

**Example:** The classification module's known-entry loader swallows `json.JSONDecodeError` and returns `frozenset()` because known-entry detection is a non-critical enrichment, and an empty set means "no extra annotation," which is harmless. The dedup plan's Task 2 reused the symlink rejection and size limit from that loader but intentionally DIVERGED on exception handling: the labels loader raises `FileProcessingError` on malformed JSON, missing label key, or wrong value type. Silently returning `frozenset()` would skip deduplication, leaving the aggregated total inflated by the double-counted matched rows (the exact bug the plan exists to fix). Only the missing-file branch degrades (WARNING plus empty set), per Design Invariant 8.

**Distinguishing from #44 (logging for silent handlers):** Lesson #44 says "if you DO degrade, log it." This lesson says "decide whether to degrade or raise in the first place, based on downstream cost." A correctly logged silent degradation is still wrong if the feature is correctness-critical.

**Canonical in-repo example:** The infrastructure JSON loader is the reference implementation of "inherit the guards, recalibrate exception handling." It centralizes the universally-reusable guards (symlink rejection, existence, strict size cap, `json.load`) but delegates EVERY failure to a caller-supplied `on_error(path, kind, detail)` callback and returns whatever that callback returns. The helper itself never decides degrade-vs-raise and never logs; each of the three callers (the classification known-entry loader, the labels loader, the value-resolver loader) owns its own `on_error` policy: classification and dedup raise on malformed content, value-resolver degrades to defaults.

**Anti-pattern:** A plan that says "mirror the error handling of `<source function>`" without checking whether the source function's degrade-vs-raise choice fits the new call site. The implementer copies `except JSONDecodeError: return frozenset()`, the new feature silently no-ops on malformed config, and the user sees a wrong aggregated total with no error to explain it.

**See also:** Lesson #44 (log silent exception handlers), tax-reporting lesson "Cross-Module Function Dependencies Require Complete Imports" (all-or-nothing validation for file sets), CLAUDE.md §1 Instruction Rules (data-loss at warning+, fail clearly), CLAUDE.md §3 Repository Constraints (no silent drops).

**See also (principle cluster B):** tax-reporting "Sentinel for `dict.get` Default Must Exclude All Valid Observed Data Values", #101 (same family, distinct angle: recalibrate policy on reuse (#77) vs raise-not-sentinel + ordering (tax-reporting "Sentinel for `dict.get` Default Must Exclude All Valid Observed Data Values") vs propagate through wrappers (#101)).


## 60. Use an Ordered Queue Per Non-Unique Key When Multiple Source Events May Share a Key With Multiple Target Items

**Principle:** Family E (Temporal / ordering invariants)


When a matching algorithm pairs N source events against M target items by a key tuple that is NOT globally unique (e.g., `(timestamp, asset, account, amount)` without a transaction hash or row ID), and multiple source events can share the same key with multiple target items, build a `dict[key] -> deque[target_items]` (or any matching queue) and pop exactly one item per source event. Do NOT use `dict[key] = item` assignment, which silently overwrites earlier items when two targets share a key, and do NOT use `dict[key] = item` followed by `del dict[key]`, which loses the second target if a second event arrives for the same key.

**Why this matters:** Without a queue per key, a same-key collision is no longer deterministic. With a dict-of-scalars, the second target item overwrites the first and the first source event matches nothing. With a dict-of-lists plus naive indexing, the matching order depends on iteration order, which is not the intended order. A per-key deque (a) preserves target order (the order items were appended, typically sorted by the intended match ordering), (b) ensures each source event consumes exactly one target, and (c) makes "items left over after all events consumed" observable as a separate surplus signal.

**Required behavior:**
1. Sort target items by their intended match order (typically `(key, secondary_key, row_index)`) before building the index, so the deque order is deterministic.
2. Build `dict[key] -> deque()` and append each target item to its key's deque.
3. For each source event (in source-sorted order), pop one target from the head of its key's deque. If the deque is empty, the event falls through to the next matching phase (or is recorded as unmatched).
4. After all source events are processed, any non-empty deque holds surplus target items that no source event claimed. Surface these in a single summary WARNING (not per-item) so the user can audit whether the surplus is a missed fan-out, a stale item from a prior year, or a coincidental key collision.

**Distinguishing from #74 (count-matched-items-per-event warning):** Lesson #74 addresses the one-source-event-to-many-targets case (one source event split into N matched target rows). This lesson addresses the many-source-events-to-many-targets case (multiple source events on the same timestamp with the same amount). Both can occur in the same matcher; #74's per-event count check and this lesson's per-key queue are complementary guards against different silent-loss modes.

**Distinguishing from tax-reporting "Decision Point Flags Require TaxJurisdictionConfig Field" (deduplication key identity):** tax-reporting lesson "Decision Point Flags Require TaxJurisdictionConfig Field" is about CHOOSING the right key tuple (which fields uniquely identify an item). This lesson assumes the key is already chosen and is non-unique by design (because no globally unique identifier is available in the source data), and prescribes the data structure that prevents silent loss under that constraint.

**Anti-pattern:** Building `matched = {key: target for target in targets}` and then `for event in events: matched.pop(key(event), None)`. When two targets share a key, the second assignment overwrites the first; the first source event finds the second target and removes it; the second source event finds nothing. The first target is silently retained in the output (the opposite of the intended dedup), and no warning fires because the per-key deque length was never observed.

**Example:** A source-event/target-row dedup plan implemented phase 1 (exact match) with `dict[tuple[str, str, str, Decimal], deque[_IndexedItem]]`. Each source event pops one target row from the head of its key's deque; if the deque is empty, the event falls through to phase 2 (contiguous-range fallback). After both phases, a surplus-collection helper walks the non-empty deques to report leftover rows in the summary WARNING. The motivating fixture had 108 target rows at one timestamp; if two source events on that timestamp have the same amount as two of those rows, the deque ensures each event consumes its own target rather than the second event finding an empty bucket.

**See also:** tax-reporting lesson "Decision Point Flags Require TaxJurisdictionConfig Field" (deduplication key identity), Lesson #74 (count-matched-items-per-event warning), CLAUDE.md §3 Repository Constraints (no silent drops).

**See also (principle cluster E):** #80, #82 (same family, distinct angle: the matcher temporal-invariant triple.).


## 61. Recompute Window-Relative Tolerance After Every Shrink Step in a Two-Pointer Sliding-Window Matcher

**Principle:** Family E (Temporal / ordering invariants)


When implementing a two-pointer sliding-window matcher that finds a contiguous range of items whose summed amount equals a target within tolerance, and the tolerance scales with the window size (`tolerance = scale * range_size`), recompute the tolerance after every shrink step. Use `left < right` (not `left <= right`) as the shrink-loop bound so the single-item window is preserved as a candidate match.

**Why this matters:** Two correctness traps hide in this algorithm:

1. **Stale tolerance after shrink.** If the tolerance is computed once before the shrink loop, the shrink condition `running_sum > target + tolerance` uses the tolerance for the ORIGINAL window size, not the shrunken window. After shrinking, `range_size` is smaller and the tolerance should be tighter; using the stale (larger) tolerance admits windows that should have been rejected, and the matching condition `abs(running_sum - target) <= tolerance` then accepts a sum that is outside the correct tolerance for the current window. The fix is to recompute `range_size` and `tolerance` inside the shrink loop after each `left += 1`.

2. **Single-element window collapse.** If the shrink condition uses `left <= right`, the loop shrinks past the single-element window (`left == right + 1`), leaving an empty window. The single-element window is the ONLY candidate when `range_size == 1`, and it may match the target within tolerance. Collapsing it discards that candidate. The fix is `left < right`: the loop stops when `left == right`, preserving the one-element window for the matching check.

**Required behavior (canonical two-pointer form):**
```python
left = 0
running_sum = ZERO
for right in range(n):
    running_sum += items[right].amount
    range_size = right - left + 1
    tolerance = scale * range_size
    while running_sum > target + tolerance and left < right:
        running_sum -= items[left].amount
        left += 1
        range_size = right - left + 1
        tolerance = scale * range_size   # recompute after shrink
    if abs(running_sum - target) <= tolerance:
        return items[left:right + 1]
return None
```

**Why `left < right` and not `left <= right`:** The shrink loop's purpose is to discard items from the left while the sum is too large. When `left == right`, the window is the single item at index `right`; shrinking further would empty the window. The single item may itself match the target within tolerance (the `range_size == 1` case), so it must be tested by the matching condition below the shrink loop, not discarded by the shrink loop.

**Why the tolerance must scale with window size:** When items are matched target rows whose individual amounts carry rounding error from upstream currency conversion, the cumulative rounding error grows with the number of rows summed. A fixed tolerance is too tight for large windows (rejecting valid 50-row sums) and too loose for small windows (admitting invalid 2-row sums). Scaling tolerance by `range_size` keeps the acceptance probability approximately constant across window sizes.

**Performance:** This is O(N) per event (each item enters the window once and leaves at most once). For N events against the same candidate list, pre-sort the candidates once and re-scan per event; the total is O(N * M) worst case but typically much faster because most events fail fast.

**Distinguishing from #79 (per-key deques):** Lesson #79 addresses exact one-to-one matching with non-unique keys. This lesson addresses the FALLBACK phase that runs when no exact match exists: the source event's amount must equal the SUM of a contiguous range of target items. The two phases are complementary: exact match first (cheap, deterministic), contiguous-range fallback second (handles the fan-out case where one event's amount is split across N adjacent rows).

**Anti-pattern:** Computing `tolerance = scale * n` once before the for-loop, then using that constant tolerance inside the shrink loop and the matching check. For a 500-item candidate list with `scale = 0.00001`, the constant tolerance is `0.005`. After shrinking to a 3-item window, the correct tolerance is `0.00003`; the stale `0.005` admits sums up to `target + 0.005`, a 166x loosening. A window summing to `target + 0.004` is accepted when it should be rejected, silently removing 3 rows that did not actually correspond to the source event.

**Example:** A source-event/target-row dedup plan implemented `_find_contiguous_range(candidates, target)` with `_RANGE_TOLERANCE_SCALE = Decimal("0.00001")`. The shrink loop recomputes `range_size` and `tolerance` after every `left += 1`. The shrink bound is `left < right`. The 10,000-item performance test completes in about 30 ms (well under the 2 s budget); the 500-item worst case completes in under 1 ms.

**See also:** Lesson #79 (per-key deques for exact match), Lesson #74 (count-matched-items-per-event warning), CLAUDE.md §3 Repository Constraints (no silent drops).

**See also (principle cluster E):** #82 (same family, distinct angle: the matcher temporal-invariant triple.).


## 62. Re-Read RED Test Assertions Against Revised Design Invariants Before Flipping to GREEN

**Principle:** Family H (Verify the real thing, not the abstraction)


When an implementation plan is revised between the RED phase (writing the failing test) and the GREEN phase (implementing the fix), the RED test may still assert the pre-revision contract. Flipping it GREEN without re-reading it against the current design invariants lets a stale assertion pass against the wrong implementation, or forces the implement sub-agent to patch the test silently during the GREEN flip without flagging that the contract changed.

**Failure mode:** The RED test was written when Design Invariant N specified "per-item WARNING logs". A plan revision (r1 → r2) changed the invariant to "per-item INFO plus one aggregate WARNING". The GREEN implementation follows the new invariant, but the RED test still asserts the old one. The implement sub-agent must either update the test (silently changing what was supposed to be a characterization of correctness) or leave it asserting the wrong contract and watch it fail for the wrong reason.

**Required behavior at GREEN flip:**

1. Before running the GREEN validation command, re-read every RED test that this task is supposed to flip, against the **current** design invariants in the revised plan.
2. If the RED test asserts a contract that the revision changed, update the test to assert the new contract as part of the GREEN flip. Do not leave the stale assertion in place.
3. Call out in the implement log that the RED test was updated at GREEN-flip time, citing the design invariant number and the revision that changed it. This makes the contract change auditable rather than a silent edit.

**Why this matters:** A RED test is supposed to characterize the desired behavior. When the plan is revised, the characterization must be revised too. An implement sub-agent that silently rewrites a RED test to match its GREEN implementation (without citing the revision) destroys the characterization value and hides a contract change from reviewers.

**Distinguishing from #57 (TDD RED-then-GREEN):** Lesson #57 requires creating a failing test before implementing the fix. This lesson addresses the case where the plan was revised AFTER the RED test was written, so the RED test's assertions may no longer match the revised contract. Lesson #57 is about process ordering; this lesson is about keeping the test characterization in sync with a revised spec.

**Example:** A source-event dedup plan wrote a trace test as a RED test asserting 3 per-item WARNING logs. The r2 revision introduced a Design Invariant requiring per-item INFO plus a single aggregate WARNING. Task 6's GREEN flip had to update the test's `caplog.at_level` from WARNING to INFO and change the assertion from "3 WARNINGs" to "3 INFOs + 1 WARNING mentioning `removed`". The implement log records the contract change against the new invariant.

**See also:** Lesson #57 (TDD RED-then-GREEN ordering), Lesson #72 (verify plan-time claims before writing tasks, the plan-authoring counterpart), Lesson #91 (reconcile plan pseudocode against tests and design invariants before GREEN).

**See also (principle cluster H):** #76 (same family, distinct angle: plan pseudocode vs tests vs invariants.).


## 63. Re-Run Phase-N Feasibility Scans on the Post-Phase-(N-1) State, Not the Original Input Set

**Principle:** Family E (Temporal / ordering invariants)


When a multi-phase matching (or removal) algorithm runs phase 1 (e.g., exact-match consumption) before phase 2 (e.g., contiguous-range fallback), any brute-force feasibility scan the plan author runs to predict phase-2 behavior MUST run against the POST-phase-1 input set, not the original full input set. Phase 1 consumes target items, which changes both the candidate count and the candidate sum seen by phase 2. A "no contiguous range sums to X" claim derived from the full set does not survive phase-1 consumption and will be falsified by the implementation.

**Why this matters:** Plan authors routinely run brute-force scans (in a REPL, a gist, or a throwaway script) to justify design claims like "phase 2 will only remove 2 items, not 108." Those scans are cheap and persuasive, which is exactly why they are dangerous when run against the wrong input set. The scan produces a true statement about the full set ("no subset sums to X") that is silently false about the post-phase-1 state. The plan ships with a prediction the implementation cannot match, forcing a revision cycle (re-trace, re-write test expectations, re-explain the divergence to reviewers).

**Failure mode:** Phase 1 removes N target items via exact match. The remaining M items have a sum that is within tolerance of a phase-2 target (often BECAUSE the removed items carried the excess). Phase 2's contiguous-range scan then matches the ENTIRE remaining M-item set as a single contiguous range. The plan, having scanned the full N+M set and found no match, predicted phase 2 would remove 0 or 2 items; the implementation removes all M.

**Required behavior:**
1. Before writing a plan claim that depends on phase-N behavior ("phase 2 matches k items"), identify every prior phase that consumes or filters the input set.
2. Replay the prior phases' consumption on the actual fixture (or a representative sample) to derive the post-phase-(N-1) input set.
3. Run the feasibility scan against THAT set, not the original full set.
4. If the prior phases' consumption is data-dependent (depends on which items match exactly), run the scan for each plausible consumption branch and record which branch the prediction assumes.
5. When the consumption is too complex to replay by hand, instrument the actual implementation (a debug print of the post-phase-1 candidate list) and run the scan against that output. Do not substitute a hand-wave for the replay.

**General form:** Whenever a multi-stage algorithm's stage N feasibility depends on the output of stage N-1 (consumption, filtering, transformation), predictions about stage N must be grounded in the stage-(N-1) output, not the stage-1 input. This holds for matchers, aggregators, pipeline stages, and any sequential transformation where an early stage alters the input seen by a later stage.

**Distinguishing from #72 (verify plan-time claims against source):** Lesson #72 verifies STATIC facts about production code (field semantics, line numbers, return shapes). This lesson verifies DYNAMIC algorithm state transitions: the input set a later phase sees after an earlier phase has consumed items. A plan can have perfectly accurate code citations and still produce a wrong phase-N prediction because the feasibility scan ran against the wrong input set.

**Distinguishing from #80 (sliding-window tolerance recomputation):** Lesson #80 addresses correctness of the sliding-window mechanic itself (recompute tolerance per shrink step). This lesson addresses correctness of the PLAN-TIME prediction of what the sliding window will match: the candidate list fed to the window is not the original full list when an earlier phase has consumed items.

**Anti-pattern:** A plan author runs `brute_force_sum_scan(full_target_list, target=<REALIZED_AMOUNT>)` in a REPL, observes "no contiguous range sums to <REALIZED_AMOUNT>," and writes in the plan: "phase 2 matches at most 2 items." The implementation runs phase 1 first, which removes one specific item (`<SINGLE_AUX_AMOUNT>`), leaving 107 items whose sum is `<REALIZED_AMOUNT>` within tolerance. Phase 2 matches all 107. The implementer must either patch the test to assert 109 removals (silently contradicting the plan) or flag the divergence and request a revision.

**Example:** A two-phase dedup plan updated a case-2 fixture's expectations. The plan predicted 2 items removed in phase 1 (one auxiliary type + another auxiliary type exact match) and ~106 remaining. The actual pipeline removed all 109 items: phase 1 removed the 2 exact-match items, then phase 2's contiguous-range scan ran against the remaining 107 items whose sum (full set minus one auxiliary amount = `<REALIZED_AMOUNT>`) was within tolerance of the target source event (`<REALIZED_AMOUNT>`). Phase 2 matched the entire 107-item set as a single contiguous range. The plan's brute-force scan had correctly found "no contiguous range in the FULL 108-item set sums to `<REALIZED_AMOUNT>`," but that scan did not account for phase-1 removing one auxiliary item first. The test asserts the ACTUAL output (109 removed, 0 remaining) with a docstring explaining the divergence.

**See also:** Lesson #72 (verify plan-time claims about production code), Lesson #80 (sliding-window tolerance recomputation), Lesson #81 (re-read RED tests against revised invariants), CLAUDE.md §4 Agent Workflow Rules.

**See also (principle cluster E):** #79 (same family, distinct angle: the matcher temporal-invariant triple.).


## 64. Grep Across ALL Test Files for Stale Assertions When a Task Changes Data Flow Semantics

**Principle:** Family A (Equivalence-class coverage)


When a task changes data flow semantics (adds a filter that removes items, adds a dedup step, changes a transformation output, splits one pipeline into two), assertions on the affected data may exist in multiple test files at different test tiers (unit, integration, e2e). Each task's "update affected tests" scope must include a grep across ALL test files for assertions that reference the changed data, not just the tests the task author listed as in-scope. A stale assertion in a sibling test file survives a focused update of the task's listed files and only surfaces during full regression, by which point the implement sub-agent has already moved on, forcing a cleanup commit.

**Why this happens:** A feature is initially implemented with tests in both the unit tier (testing the integration point with real fixtures) and the e2e tier (testing the final Excel output). When a follow-on plan changes the data flow, the plan author typically lists only the tests they remember writing or the tests in the file they are editing. The sibling test in a different tier that also references the same data is forgotten. The focused test run passes because it runs only the listed files; the failure only appears when the full `uv run pytest` is run at the end of the plan, often by a later validation task rather than the task that introduced the change.

**Required behavior:**
1. Before marking a task that changes data flow as complete, identify the identity tuple of the affected data (e.g., `(date, asset, platform)` for a domain entry, or `(field_name, expected_value)` for a transformation output).
2. Grep across the ENTIRE test tree (`tests/`) for assertions referencing that identity: `grep -rn "<date>.*<asset>.*<platform>" tests/`, `grep -rn "<field_name>" tests/`, or `grep -rn "<expected_value>" tests/`.
3. For each hit, re-read the assertion against the new contract. If the assertion encodes the old behavior, update it as part of THIS task; do not defer to a later validation task.
4. When a plan describes "update test expectations for the new behavior," the plan's task list should explicitly include "grep all test files for assertions on the affected identity tuple and update stale ones" as a sub-step, not just "update tests/test_X.py".

**Distinguishing from #81 (re-read RED tests against revised invariants):** Lesson #81 addresses stale assertions in the RED test that THIS task is supposed to flip; the test is in scope but its assertions were written against a superseded invariant. This lesson addresses stale assertions in tests OUTSIDE this task's listed scope; the tests are in sibling files the task author forgot to grep. The failure mode for #81 is caught at GREEN-flip time (the implement sub-agent sees the test fail and patches it); the failure mode here is caught only at full-regression time (the focused run never executed the sibling test).

**Distinguishing from tax-reporting 'Guard "Take From First Entry" Fields Against Silent Heterogeneity' (fix in-scope findings in the same branch):** tax-reporting lesson 'Guard "Take From First Entry" Fields Against Silent Heterogeneity' addresses refactoring findings in files the task touched. This lesson addresses test-staleness that crosses file boundaries: the task touched the dedup module and updated its dedicated test file, but a stale assertion in a pipeline-integration test class (a different file the task never opened) encodes the old contract.

**Anti-pattern:** A task implements a dedup step that removes a target row for a specific `(date, asset, account)` triple from the affected entries. The task updates the e2e test that asserts the row is absent from the output but does not grep `tests/` for other references. A unit test in a different file still asserts the OLD contract (`len(case1_matches) == 1` with `result == -<FEE_RESULT_AMOUNT>`). The focused test run passes; the full regression at task 9 fails. The cleanup commit then has to explain why a stale test survived three task boundaries.

**Example:** A dedup task updated Case 1 and Case 2 e2e expectations in a separation e2e test. The plan did not list the pipeline-integration unit test `test_entries_excludes_affected_rows_when_flag_on`, which had been written in an earlier task (the initial separation) and still asserted `-<FEE_RESULT_AMOUNT>` for the affected row. The dedup correctly removed that row (the source row carried the affected label), so the unit test failed at task 9's full regression. A grep for the row's identifying date/asset/account tuple or `case1_matches` across `tests/` at task 7 time would have surfaced the stale assertion and let task 7 update it in the same commit as the e2e expectations.

**See also:** tax-reporting lesson 'Guard "Take From First Entry" Fields Against Silent Heterogeneity' (fix in-scope refactoring findings in the same branch), Lesson #81 (re-read RED tests against revised invariants), CLAUDE.md §4 Agent Workflow Rules.

**See also (principle cluster A):** #84 (same family, distinct angle: cross-file stale assertions (#83) vs within-file name-vs-body scope (#84)).


## 65. Test Method Names Must Reflect Their Actual Coverage Scope

**Principle:** Family A (Equivalence-class coverage)


When a test method's name implies coverage of N pathways (e.g., `test_*_propagate_timestamp` for a function with 5 emitter sites, or `test_all_branches_handle_*` for a 4-branch conditional) but the body exercises only 1, reviewers reading the test list will assume the implied coverage exists. A later refactor that breaks an unexercised pathway will pass the existing test suite because the suite never tested that pathway; the misleading name delayed the discovery.

**Why this matters:** Test method names are a discovery surface during code review and refactor risk-assessment. A reviewer deciding whether a change is safe to merge will scan test names to estimate coverage; a name that overstates coverage produces a false-confidence green light. The test passes for the wrong reason, not because the contract holds across all pathways, but because only one pathway was ever asserted.

**Required behavior:**
1. When writing a test for a function with multiple dispatch pathways (multiple emitter sites, multiple branches, multiple subclasses, multiple strategies), either:
   - Name the test after the SPECIFIC pathway it covers (e.g., `test_order_fulfillment_emitter_propagates_timestamp`), OR
   - Parameterize the test across ALL pathways and keep the general name (e.g., `@pytest.mark.parametrize("emitter", ALL_EMITTERS)`).
2. Never use a general name like `test_emitters_propagate_timestamp` for a test that covers only one emitter, hoping to add the rest later. The hope rarely survives the next refactor.
3. When inheriting or reviewing a test with a general name and a narrow body, either rename the test to reflect its scope or expand the body (or parameterize) to cover what the name claims. Do not leave the gap.

**General form:** A test's name is a contract with future readers about what the test verifies. If the name claims a category, the body must verify the category. If the body verifies a single instance, the name must name the instance.

**Distinguishing from tax-reporting "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag" (helper functions need direct unit test coverage):** tax-reporting lesson "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag" requires direct unit tests for extracted helpers (versus only indirect integration coverage). This lesson addresses the narrower problem of a test that DOES exist but whose name overstates the scope of what it verifies. tax-reporting lesson "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag" is "the test does not exist at the right level"; this lesson is "the test exists but its name lies about what it covers."

**Distinguishing from #83 (grep all test files for stale assertions):** Lesson #83 addresses stale assertions across multiple test files when data flow changes. This lesson addresses the gap between a test's name and its body WITHIN a single test file, regardless of whether data flow changed.

**Anti-pattern:** A function `_emit_order_fulfillment` is one of 9 emitter sites that should all propagate `event_timestamp`. The implementer writes `test_emitters_propagate_timestamp` (plural noun suggesting all emitters) that constructs a single fulfillment context and asserts the timestamp is set. The other 8 emitters are never exercised. A later change to `_emit_internal_transfer` drops the timestamp assignment; the test suite stays green because that emitter was never covered. The misleading name hid the gap from the reviewer who approved the change.

**Example:** A dedup plan's Task 3 added a timestamp propagation field to 15 constructor sites across the parsing, emitters, matching, matching-helpers, and orchestration modules. The unit test `test_matching_emitters_propagate_timestamp` in the matching-emitters test file constructs one fulfillment context and asserts the timestamp is forwarded. The other 8 emitter sites (internal transfer, refund, fee, split, etc.) are not parameterized into the test. A later refactor that drops the timestamp from the fee emitter would pass the test suite. See the implementation log (local) Finding 3.

**See also:** tax-reporting lesson "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag" (helpers need direct unit tests), Lesson #83 (grep all test files for stale assertions), CLAUDE.md §4 Agent Workflow Rules.


## 66. Default-Empty Excel Cell Assertions Must Accept Both None and Empty String

**Principle:** Family C (Representation: sentinel vs None vs exception)


When a test asserts that an Excel cell is "empty by default" (e.g., an optional field like `notes` that was never set on the entry, written via `safe_cell_value(entry.notes)` where `entry.notes` resolves to `""`), the read-back value from openpyxl may be EITHER `None` OR `""`. openpyxl normalizes empty-string writes to `None` in some code paths and preserves the empty string in others, depending on whether the cell had prior content, the write went through `Worksheet.cell()` vs direct attribute assignment, and the version of openpyxl in use.

**Why this matters:** A brittle assertion like `assert cell.value == ""` or `assert cell.value is None` will pass on one openpyxl version and fail on another, or pass for one field and fail for its sibling field written the same way. The test then appears flaky and gets disabled, or the implementer papers over the failure with a hack that masks a real bug.

**Required behavior:**
1. For default-empty cell assertions, accept BOTH representations: `assert cell.value in (None, "")` (or `assert cell.value is None or cell.value == ""`).
2. Do NOT assert a single value unless the production code under test GUARANTEES that value (e.g., the field is always initialized to a non-empty sentinel).
3. When the production write uses `safe_cell_value(x)` where `x` may be `None`, the empty-state assertion must accept `None`, `""`, or both; never assert one exclusively.

**Distinguishing from lesson at section "When adding columns that can be blank/None" (around line 957):** That rule says to ADD a dedicated test for the blank/None state and verify the cells are `None` (not empty string, not zero, not default value); its concern is detecting leftover data from prior rows. This lesson #86 addresses the opposite problem: when the expected state IS empty and the write went through `safe_cell_value("")`, the read-back may normalize to `None`. The two rules compose: add a dedicated empty-state test (per the earlier rule), and in that test accept both `None` and `""` (per this lesson #86).

**General form:** Any Excel cell assertion about an empty/default value must account for openpyxl's dual representation of "empty". The set `{None, ""}` is the correct expected-empty set for cells written via `safe_cell_value()`.

**Example:** Task 4 of a category-columns plan added `test_row_writes_notes_default_empty` for the new `Notes` column (column 12) on the category output sheet. The entry was constructed without `notes`, so `entry.notes` defaulted to `""`. The production write is `worksheet.cell(row, 12, safe_cell_value(entry.notes))`. The test asserts `cell.value in (None, "")` because openpyxl may read back either value. A brittle `== ""` assertion would fail when openpyxl normalizes the empty string to `None`.

**See also:** Lesson around line 957 (add dedicated blank/None tests), `coding_guidelines.md` #4 (type-safe sentinels for absent optional fields), CLAUDE.md "Data Handling".

**See also (principle cluster C):** #85, #97 (same family, distinct angle: sentinel string leak (#85) vs `None`-value interpolation (#97) vs test-expectation `None`/`""` (#86)).


## 67. Reconcile Plan Pseudocode Against Plan Tests and Design Invariants Before GREEN

**Principle:** Family H (Verify the real thing, not the abstraction)


When a plan body contains both executable pseudocode AND RED-test expectations that purport to verify that pseudocode, the author must trace each pseudocode branch against the test inputs and the design invariants BEFORE handing the plan to the implementer. The pseudocode and the tests must agree on every input combination. If they disagree, the implementer will either (a) follow the pseudocode and fail a RED test that encodes the invariant, or (b) silently extend the logic beyond the pseudocode to satisfy the tests, producing a defensible but undocumented deviation.

**Why this matters:** Lesson #72 covers verifying plan-time CLAIMS ABOUT PRODUCTION CODE (field semantics, line numbers, return shapes) by reading the source. This lesson covers verifying the plan's INTERNAL CONSISTENCY (pseudocode vs tests vs invariants) by reading the plan itself. The two failure modes share a symptom (the implementer hits a contradiction) but have different triggers: #72 fires when the author makes a claim about reality; this lesson fires when the author's own deliverable is self-contradictory. A self-consistency trace before GREEN eliminates the "implementer added an undocumented third branch to satisfy the invariant" outcome, which is defensible but obscures the actual rule.

**Required behavior:**
1. Before declaring the plan ready for implementation, build the full decision table from the pseudocode (every branch condition -> every input combination -> expected flag/output).
2. For each RED test, look up its inputs in the decision table and confirm the pseudocode-predicted output matches the test-asserted output. Any mismatch is a plan defect; fix the pseudocode (or the test, or the invariant) before implementation.
3. Pay special attention to backward-compat invariants (e.g., "threshold=0 preserves prior flag-everything behavior"); these are easy to violate with two-branch "guard the new case" logic that inadvertently suppresses the old case.
4. If the implementer reports adding a branch not in the pseudocode to satisfy a test/invariant, treat it as a plan-authoring defect (the pseudocode was incomplete), not just an implementer deviation. Capture the missing branch in the plan's implementation note so the rule is discoverable.

**Anti-pattern:** Writing two-branch pseudocode ("if A then X; if B then Y") when a third input combination (A=false, B=false, threshold=0) must also fire per the backward-compat invariant. The implementer correctly adds a third branch (`A=false AND B=false AND threshold=0 -> fire`) to satisfy the RED test, but the branch is undocumented in the plan body, leaving the rule discoverable only by reading the implementation.

**Example:** The 2026-06-15 review-threshold plan Task 2 specified two-branch pseudocode for `_build_review_reason`:
- tier 3: `amount == 0 AND total > 0 AND total >= threshold`
- tier 4: `total == 0 AND amount > 0`

Design Invariant 4 required "when threshold=0, prior flag-everything behavior is preserved", and a RED test `test_threshold_zero_flags_all_zero_amount` asserted `amount=0, total=0, threshold=0 -> review_required=True`. Neither branch matches that input (tier 3 requires `total > 0`; tier 4 requires `amount > 0`), so the implementer added a third branch (`amount == 0 AND total == 0 AND threshold == 0 -> fire`) to satisfy the invariant. The deviation is correct; the plan pseudocode was simply incomplete. A pre-GREEN decision-table trace would have caught the gap and folded the third branch into the plan body.

**Second example (2026-06-22 synthetic-fixtures-off-local-data plan, Task 1.5 - literal instruction vs design invariant):** Task 1.5's literal bullet asserted "identical aggregated-source-entries and matched-target-entries counts per `(date, sku, supplier)` case key" between the real and synthetic fixtures, but Design Invariant #2 stated the synthetic fixture is deliberately a smaller, controlled matched-item set. The literal bullet would false-fail (real=26 matched entries vs synth=2; no shared case keys by design). The task's HEADER ("shape parity") and Invariant #2 were authoritative; the implementer read the invariant's intent (code-path/dedup-phase + case-structure parity, not numeric count-equality) and recorded the reconciliation in the implement log rather than blocking or retro-editing the fixtures. Same family as the first example, distinct trigger: a literal assertion INSTRUCTION (no pseudocode branch table) whose wording contradicts a stated invariant. The fix is the same - reconcile to the invariant's intent and document - but the detection cue is "the task's literal bullet and its own design invariant cannot both be true," not "pseudocode branches miss an input combination."

**See also:** Lesson #72 (verify plan-time claims about production code), Lesson #81 (re-read RED tests against revised invariants after plan revision), CLAUDE.md §4 Agent Workflow Rules.

**See also (principle cluster H):** #76 (same family, distinct angle: plan pseudocode vs tests vs invariants.).


## 68. Do Not Run `ruff check --fix` on Modules That Re-Export for Backward Compat

**Principle:** Family F (Layering / dependency direction)


When a module deliberately re-exports symbols (via plain `from X import Y` without `__all__` gating, or via an `__all__` that `ruff` cannot fully see) for backward-compat consumers, including tests that import from the re-export module rather than the canonical source; do not run `ruff check --fix` on the whole module. The unused-import heuristic (`F401`) frequently flags and removes re-exported names, silently breaking downstream imports. Apply targeted manual edits to the import block instead.

**Why this matters:** `ruff check --fix` is the default cleanup command in this repo, and on a normal module it is safe and expected. On a re-export module (typically `application/<feature>_reporting.py` or a package `__init__.py`), the same command silently deletes public API surface that tests rely on. The failure surfaces as `ImportError` during test collection, but only after the agent has already moved on to the next command. Recovery is straightforward (`git checkout`), but the time cost compounds when the agent re-runs the fix to "clean up" the next round.

**Required behavior:**
1. Before running `ruff check --fix` on a module, check whether it re-exports symbols consumed elsewhere. Signals: a long `from X import Y, Z, ...` block at the top of the file where some names are not referenced in the file body; an `__all__` declaration; module docstrings describing "re-exports for backward compat".
2. For re-export modules, prefer targeted manual edits to the import block (add or remove specific names explicitly). Do not run `--fix` on the whole file.
3. If you must run `--fix`, restrict the rule set to exclude `F401` (e.g., `ruff check --fix --select=E,F-minus-F401` is not directly supported; instead run `ruff check --select=<specific-rules>` without `--fix`, review the diagnostics, and apply only the safe ones manually).
4. After any ruff run on a re-export module, run the test suite for that module's consumers before declaring the cleanup complete. `ImportError` at collection is the failure signal.

**Anti-pattern:** Running `uv run ruff check --fix` on the production re-export module after adding a new import, then discovering the auto-fix removed the re-exported domain entities, summary classes, the auxiliary loader, the dedup entry point, and other names that tests import from this module. The fix is `git checkout` of the file and a targeted manual edit adding only the new name, but the cycle costs a full ruff+test iteration.

**Example:** The review-threshold plan Task 2 implementation added `DEFAULT_REVIEW_THRESHOLD` to an import block in the production module. An initial `ruff check --fix` run aggressively removed re-exported names that the module's test file imports from this module. The implementer reverted via `git checkout` and applied only the targeted one-line edit. Lesson #4 already documents that backward-compat re-exports live in such modules; this lesson extends it to "do not auto-fix the import block".

**See also:** Lesson #4 (backward-compat via `__init__.py` re-exports), CLAUDE.md "Code Quality" (Ruff primary linter/formatter).


## 69. Do Not `git stash` for Baseline Comparisons in the docs-branch State

**Principle:** Family H (Verify the real thing, not the abstraction)


This repo carries a docs/orphan-branch workflow (`docs-branch` skill) and at times a working tree with staged deletions (files marked `D` in the index but still present on disk). In that combined state, using `git stash` to get a transient clean tree for a baseline tool comparison is unsafe: the stash records the staged deletions and the subsequent `git stash pop` did not restore the on-disk content, leaving all affected tracked files missing from the working tree.

**What happened (2026-06-17):** During the review-threshold review-fix session, three `git stash` / `git stash pop` cycles were used to compare `ruff` diagnostics on the edited tree versus the committed baseline. The working tree had 10 tracked files staged as deletions (`D`) but present on disk. The stash cycles dropped all 10 files from the working tree. Recovery was via `git fsck --lost-found` to locate the dangling commit from the last dropped stash, then `git checkout <sha> -- <files>` and `git reset HEAD -- <files>` to unstage. All edits were recovered intact because the stash had captured them before being dropped.

**Required behavior:**
1. For any "compare tool output against the committed baseline" task in this repo, read the committed blob non-destructively: `git show HEAD:<path> | uv run ruff check -` per file. Do NOT stash.
2. If a fully clean checkout is genuinely required, use `git worktree add <tmp> <base>` into a temporary path and remove it afterward. Never `git stash`.
3. Before any `git stash` in this repo, audit `git status` for staged deletions (`D`) and gitignored paths overlapping tracked files; if present, do not stash.

**Related (shell recovery):** The recovery command `git checkout <sha> -- $FILES` failed under zsh because zsh does not word-split unquoted variables (the whole string was treated as one pathspec, "pathspec did not match"). Multi-path git operations must use a quoted array: `files=(...); git checkout <sha> -- "${files[@]}"`.

**General form:** See shared `agent_workflow_guidelines.md` #55 (Non-Destructive Baseline Comparisons). The repo-specific aggravator is the docs-branch orphan-branch workflow combined with staged deletions, which makes the stash/pop failure mode both more likely and more damaging here than in a plain repo.

**See also:** `docs-branch` skill, shared `agent_workflow_guidelines.md` #55, CLAUDE.md/AGENTS.md git-safety bullets.

**See also (principle cluster H):** #88, #94, #95 (same family, distinct angle: the git/docs-state verification cluster.).


## 70. In a Per-Row Matching/Correction Loop, Run the Fallible Resolution Before Mutating the Match Structure (and Make It Raise, Not Sentinel)

**Principle:** Family B (Error-policy propagation)


A per-row matching or correction loop typically does two things per row: resolve a fallible value (rate lookup, parse, derived field) and mutate a shared match structure (`deque.popleft`, index pop, counter decrement). If the mutation runs before the fallible resolution, or the resolution returns a sentinel instead of raising, a single bad row either corrupts shared state or escapes the per-row boundary, defeating the "one bad row must not abort the batch" guarantee from #6.

**What happened (2026-06-18):** In the value-correction refactor plan, `correct_values` matches each zero-value calculated row to an auxiliary source row via a per-key `deque` and infers a reference value through a caller-supplied `rate_fn`. The premortem review agent found that if `rate_fn` returned a sentinel (`None`) when a rate had no configured value, `_infer_corrected_value` would evaluate `amount * None`, raising `TypeError`, which is NOT in the orchestrator's per-row `except (ValueError, KeyError)`, so one missing rate would abort the entire correction loop and every later auxiliary row would silently keep its stale value. Separately, the quality agent verified the safe ordering requirement: the corrected value must be computed BEFORE `popleft`, so a caught exception leaves the deque entry unconsumed.

**Required behavior:**
1. A caller-supplied resolution callable (rate function, resolver, lookup) that can fail must RAISE an exception type the per-row boundary already catches. Do not return a sentinel (`None`, empty) that downstream code multiplies, concatenates, or uses unconditionally; a forgotten guard turns `value * None` or `value + None` into an uncaught `TypeError` outside the boundary.
2. In the loop body, execute the fallible resolution BEFORE any irreversible mutation of the shared match structure (`deque.popleft`, index pop, set removal). Mutate only on the success branch. A per-row `try/except` that catches the exception is necessary but not sufficient: if the mutation already happened, the shared structure loses an entry (a matched source row consumed with no correction applied), silently breaking subsequent 1:1 matches.
3. When designing or reviewing such a loop, write the per-row body in the order: look up the bucket -> resolve the fallible value (inside the try) -> on success, mutate the structure and emit the corrected row; on exception, warn with row identity and emit the row unchanged. Trace what shared state remains if the exception fires at each step.

**Why this is distinct from #6/#74/#79:** #6 says catch per row so one bad row does not discard the dataset; #74/#79 say use a `deque` + `popleft` (never `dict[key] = item`) for collision-safe matching. This lesson adds the within-iteration ordering and the raise-not-sentinel contract that make the per-row catch actually safe when the loop also mutates shared matching state.

**See also:** CLAUDE.md/AGENTS.md "Repository Constraints" (matched-item / partially-matched rules), row-level catch, deque matching, coding_guidelines.md sealed-class sentinel variants.

**See also (principle cluster B):** #77, #101 (same family, distinct angle: recalibrate policy on reuse (#77) vs raise-not-sentinel + ordering (tax-reporting "Sentinel for `dict.get` Default Must Exclude All Valid Observed Data Values") vs propagate through wrappers (#101)).


## 71. Discriminating Tests: Assert Properties That FAIL Under the Wrong Implementation

**Principle:** Family A (Equivalence-class coverage)


A RED test that passes against the intended implementation AND against a plausible wrong implementation does not discriminate; it gives a false GREEN. Two recurring shapes: (1) a behavioral property that holds regardless of WHERE a cross-cutting mechanism is attached, and (2) a single OR'd case that lets an implementer exercise one of several independent guards and skip the rest.

**What happened (2026-06-18):** During the r4 confirmation pass on the threshold-correction refactor plan, the testing agent found two non-discriminating RED tests. (a) The memoization test for `_get_threshold_config` asserted only "returns the same `(rules, tag)` on repeated calls"; that property holds whether `@lru_cache` sits on the resolver or on the reader, and the sibling `_load_known_entries` in `classification.py` actually inverts the placement the plan forbids, yet would satisfy the assertion. (b) The loader degrade test read as one OR'd case ("given malformed JSON, an oversize file, OR a symlinked path"), so an implementer could test one guard (say malformed JSON) and ship without the symlink or oversize guard, including the security-critical symlink rejection.

**Required behavior:**
1. To test WHERE a mechanism attaches (memoization decorator, registration hook, cache), assert a property that only holds at the intended site: `hasattr(target, "cache_info")` and `not hasattr(other, "cache_info")`, or mutate the input between calls and assert the cached function returns stale while the uncached one returns fresh. "Same value on repeated calls" is not discriminating.
2. When a function has N independent guards (symlink, size, format, permission), write N parametrized cases, each asserting its own return value AND its own distinct signal (a WARNING or error message naming that specific failure). A single "A OR B OR C" case lets N-1 guards be absent silently.
3. Before declaring a RED test sufficient, ask: "Could I implement this wrong and still pass?" If yes, add the assertion that fails under the wrong implementation.

**Why this extends #6/tax-reporting "Check Prior Same-Session Commits Before Reporting a Verification-Time Scope Violation"/tax-reporting "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag":** those lessons require edge-case and branch coverage; this lesson requires that each covered case actually binds the implementation to the intended design, not merely to a shape that happens to satisfy the assertion.

**See also:** CLAUDE.md/AGENTS.md "Agent Workflow Rules" and "Testing", edge cases, validation coverage, extracted-helper coverage, empirically confirm a guard-binding test discriminates by disabling the guard and observing RED.

**See also (principle cluster A):** #100 (same family, distinct angle: principle (tax-reporting "Outer Row-Level Exception Block Must Not Prevent a Trusted-Branch Operation From Completing") vs procedure (#99) vs restore/undo variant (#100). Each body distinguishes itself.).


## 72. Verification Guards That Read a Manifest File Must Fail Closed When the Manifest Is Absent

**Principle:** Family G (Data-loss observability)


A guard command (leak detector, lint check, coverage gate) that reads an external manifest/patterns file and is written as `cmd && echo BAD || echo GOOD` reports GOOD when the manifest is missing. The command exits non-zero on a missing `-f` input (grep: exit 2 "cannot read patterns"), the `&&` branch is skipped, and the `|| GOOD` branch fires: a false pass exactly when the guard cannot run. When the manifest is gitignored (absent in fresh checkouts and CI), that missing-input state is the default outside the author's working tree.

**What happened (2026-06-19):** The value-correction refactor plan's personal-data hygiene guard was `grep -rnf docs/maintenance/personal/personal_data_patterns.txt <tracked files> && echo "!!! LEAK !!!" || echo "clean"`. The patterns file is gitignored (it holds the user's real identifiers), so it is absent in any fresh checkout or CI run. Verified empirically: with a real leak planted and the patterns file absent, `grep -f <missing>` exits 2 and the guard printed "clean". A leak detector that reports success when its own input is missing is the worst failure mode, and the missing-input state is the norm outside one developer's tree.

**Required behavior:**
1. A guard whose input file may be absent MUST fail closed: assert the input exists and is non-empty before the check (`test -s "$PATTERNS" || { echo "CANNOT VERIFY: ..."; exit 1; }`), so a missing input is a loud failure, never a silent pass.
2. Prefer `if grep ...; then echo BAD; else echo GOOD; fi` over `grep ... && echo BAD || echo GOOD`, but note this alone does NOT fix the missing-input case (grep's exit 2 still routes to the else/"GOOD" branch). The `test -s` pre-check is what makes it fail-closed.
3. For any verification step that consumes a gitignored/local-only manifest, treat "the manifest is absent in CI" as the design's normal state and verify the missing-input path itself (a test that runs the guard with the manifest absent and asserts it fails, not passes).

**See also:** data-loss at warning+, never silent, internal sentinels must not leak as user-facing values, discriminating tests.

**See also (principle cluster G):** tax-reporting "Matching Event Fields Must Mirror the Normalization Applied to Domain Entry Fields" (same family, distinct angle: guard-fail-closed (tax-reporting "Use `get_args(hint)` Not `get_origin(hint)` for Precise Generic Type Dispatch in Config Loaders") vs guard-scan-coverage (tax-reporting "Matching Event Fields Must Mirror the Normalization Applied to Domain Entry Fields")).


## 73. Static Guards Must Cover Code Paths Skipped in CI (No Runtime Backstop)

**Principle:** Family G (Data-loss observability)


A test that `pytest.skip`s when its real fixture is absent (common when the fixture is gitignored personal data) is never executed in CI. A defect that would only surface by running that test, for example a hardcoded real identifier or magic value baked into the test, therefore has no runtime backstop in CI. The only thing that can catch it is a static guard (grep/scan), so the static guard's scan list MUST include those skipped test files. A guard that scans only the "obvious" doc/config files and omits the fixture-driven tests leaves the highest-risk files with no protection at all.

**What happened (2026-06-19):** The value-resolver plan's personal-data hygiene guard scanned the plan, one unit test, the JSON config, and the domain docs, but omitted the integration test, the capturing-loader test, and the new end-to-end test that the wiring task explicitly adds. Those are precisely the files where a hardcoded real source-transaction amount or an credential-bearing filename would land, and the e2e test is skipped in CI (the real upstream-data-source fixture is gitignored-absent), so running it never catches a leak there. The grep guard was the e2e test's only backstop, and the guard did not scan it.

**Required behavior:**
1. When designing a static hygiene/leak guard, enumerate the files where the protected value could realistically land, including test files that consume real fixtures, and put all of them in the scan list, not just the docs/config a reader would name first.
2. For any test that `skip`s when a fixture is absent, recognize it has zero CI runtime coverage and ensure a static guard or a dedicated assertion covers the leak class for that file.
3. Audit the scan list against the task that creates or edits files: every file a task touches that could carry the protected value should be in the guard's list.

**See also:** grep ALL test files when a data-flow identity changes, discriminating tests, fail-closed guard input.


## 74. `git mv <src> <dest>` Nests When `<dest>` Exists; the doc-hierarchy `full` Gate Does Not Catch Intra-Tree Nesting

**Principle:** Family H (Verify the real thing, not the abstraction)


`git mv <src> <dest>` renames `src` to `dest` only when `dest` does not already exist. When `dest` is already a directory, git moves `src` **into** it, producing `dest/<src-basename>/` one level deeper than intended. The doc-hierarchy `full` verify gate does not catch this: its rogue-path scan flags only `docs/<not-allowed>/` top-level trees, so anything under an allowed tree (`docs/history/`, `docs/maintenance/`) passes regardless of how its internal directories are shaped. Files dropped at `docs/history/plans/plans/` instead of `docs/history/plans/` are invisible to the gate.

**What happened (2026-06-19):** During the doc-hierarchy migration, `git mv docs/plans docs/history/plans` ran after `docs/history/plans/` already existed, so all 31 plan files moved to `docs/history/plans/plans/...` (and `completed/` to `plans/plans/completed/`), with nothing at the intended top level. The `full` gate still passed because the nested path sits under the allowed `docs/history/` tree. The defect surfaced only when `bootstrap-ai-playbook` ran next: the hand-authored `plans_completed_dir = "docs/history/plans/completed/"` pointed at a path that did not exist, and bootstrap's on-disk check (does each `facts.md` key's target exist on disk?) rejected it. (The migration-map Step 2 special cases guard this for `reviews/` but not for `plans/` or other directory moves.)

**Required behavior:**
1. Before `git mv <src> <dest>` of a directory into a target tree, check whether `dest` already exists. If it does, move the **contents** into the target (`git mv src/* dest/`) or move then flatten, never the bare directory, or you get `dest/<src-basename>/`.
2. A passing `full` gate is necessary but not sufficient: it checks allowed top-level trees and rogue-path absence, not internal directory depth. After moving directories into an allowed tree, verify contents landed at the intended depth (e.g. `find docs/<tree> -maxdepth N -type f`).
3. Treat `bootstrap-ai-playbook` on-disk path-key validation as the backstop the gate cannot provide: run bootstrap rather than hand-authoring `.ai-playbook/facts.md`, because it fails on, and forces correction of, any key whose target does not exist.

**See also:** verification-first: inspect actual git state before reporting, docs-branch / git working-tree hazards, verification guards must fail closed.

**See also (principle cluster H):** #38, #95 (same family, distinct angle: the git/docs-state verification cluster.).


## 75. Translate Stale Doc Paths in Plans Authored Before a doc-hierarchy Migration, Before execute-plan

**Principle:** Family H (Verify the real thing, not the abstraction)


A plan written before a doc-hierarchy migration keeps the pre-migration prefixes in three load-bearing places: task `Files:` lists, prose code-path literals (e.g. `_REPOSITORY_ROOT / "docs" / "tax" / ...`), and `## Validation Commands` grep targets. Executing such a plan untranslated produces two silent failure modes: sub-agents write to non-existent old locations (e.g. a pre-migration path to a known-entry set file), and the plan's own validation commands grep against nothing - a false pass with no signal that the gate did not actually run against the migrated tree.

**What happened (2026-06-19):** The refactor plan (value correction) was authored at `3f8e898`, before the three-layer doc-hierarchy migration (`5d085e5`) that moved all `docs/` content under `docs/maintenance/` (plus `docs/plans/` -> `docs/history/plans/`, `docs/reviews/` -> `docs/history/reviews/`). A pre-Phase-1 scan found 38 stale path references across five prefixes (`docs/tax/`, `docs/domain/`, `docs/plans/`, `docs/personal/`, `docs/reviews/`). The orchestrator translated them in a standalone prep commit (28 line swaps, zero logic change) before Task 1, so per-task commits stayed clean and validation targets resolved.

**Required behavior:**
1. Before Step 1.1 of `execute-plan`, when the repo has the migration-complete signal and the plan predates the migration, grep the plan body for the migration's moved prefixes (e.g. `grep -nE 'docs/(tax|domain|plans|personal|reviews)/' <plan>`) and translate every hit to its migrated location. This is `execute-plan` Step 0.4b.
2. Translate segmented code-path literals too (`"docs" / "tax"` -> `"docs" / "maintenance" / "tax"`), not just prose paths, so the literal matches the authoritative source path.
3. Run the plan's `## Validation Commands` once after translation to confirm grep/test targets resolve against the current tree (empty grep output is a false pass, not success).
4. Make the translation its own pre-Phase-1 commit so the per-task commits carry only task logic.

**See also:** verify cited paths/line numbers against current source before depending on them, verification-first git-state inspection, sibling doc-hierarchy migration hazard: `git mv` nesting. Skill home: `execute-plan` Step 0.4b.

**See also (principle cluster H):** #38, #93 (same family, distinct angle: the git/docs-state verification cluster.).


## 76. Pre-Bind Every Local Referenced After a Try Whose Except Continues Rather Than Re-Raises

**Principle:** Family B (Error-policy propagation)


When a `try ... except` block logs and CONTINUES (warn-and-continue, graceful degradation) rather than re-raising, and code after the try reads a local that is assigned only inside the `try`, the local must be PRE-BOUND to a safe default BEFORE the try opens. Otherwise the except path runs to completion without binding the local, and the post-try reference raises `NameError` on exactly the failure path that the warn-and-continue was meant to survive.

**Failure mode:** the bug is latent. The happy path binds the local inside the try, so every test that exercises the success branch passes. The `NameError` fires only when the failure branch (`except`) runs AND control reaches the downstream read - the rare path, usually untested.

**What happened (2026-06-19, the refactor plan Task 6):** `_main` in `main.py` had `region_config = None` pre-bound at the top of the function (the safe-default idiom for this warn-and-continue pattern), but the newly-added `app_config` local was NOT pre-bound. The config-load `except (FileNotFoundError, OSError)` branch logs "Config file not found; pipeline will run without region filters" and continues. A new downstream call site `rates=app_config.rates if app_config is not None else None` then `NameError`s on `app_config` on the config-missing + upstream-data-present path - the very path the except exists to keep working. The fix was a one-line pre-bind `app_config: Config | None = None` next to the existing `region_config = None`.

**Required behavior:**
1. Audit every `try ... except` whose `except` body does NOT re-raise (i.e. logs/warns and falls through). For each, list every name assigned only inside the `try` and referenced after the block.
2. Pre-bind each such name to a safe default BEFORE the try opens, mirroring the existing pre-bind idiom (e.g. `region_config = None` in the same function). A guarded downstream read (`x.foo if x is not None else None`) is NOT sufficient on its own - the `NameError` fires before the `is not None` check.
3. Cover the failure path with at least one test that triggers the continue-branch `except` and then reaches the downstream read. A structural test (assert the call does not raise `NameError`) plus a behavioral test (assert the warn fires and the safe-default path runs) together bind the invariant.

**General form:** This holds for any continue-style exception handler, not just config loading. Whenever you add a new local that a warn-and-continue `try` assigns and post-try code reads, pre-bind it. The local need not be the thing the `try` was originally written to guard - any local added later inside the same try inherits the hazard.

**Distinguishing from #78 (reuse the parsed value inside the try):** Lesson #78 prevents an UNCAUGHT exception by re-invoking a fallible operation outside the try. This lesson prevents a `NameError` by ensuring a local assigned inside a continue-style try is bound on the except path too. Both are error-scope guards but address different failure modes: #78 keeps fallible ops inside the catch scope; this one keeps locals readable on the degradation path.

**Distinguishing from #44 (log silent exception handlers):** Lesson #44 says the degradation must be OBSERVABLE (log it). This lesson says the degradation must be SOUND (every downstream read resolves). A correctly logged warn-and-continue that then `NameError`s is still broken.

**See also:** log silent exception handlers, reuse parsed value inside the try block, reusing a pattern: inherit the guards, recalibrate exception handling. `main.py` config-load block (the canonical pre-bind idiom: `region_config = None`, `app_config: Config | None = None`).


## 77. F-Strings Interpolating a `str | None` Into User-Facing Output Must Degrade Explicitly for `None` (Especially When `None` Is Reached via a Warn-Only Config-Drift Path)

**Principle:** Family C (Representation: sentinel vs None vs exception)


When an f-string interpolates a value typed `str | None` (or `Optional[str]`) into a user-facing string (review reason, Excel cell, log line addressed to the operator), and `None` is REACHABLE through a config-drift path the loader only warns about (does not refuse) - for example, an item listed in `tracked_items` but absent from `item_references`, so the lookup returns `None` and execution continues to the reason builder - the f-string `f"...{reference}..."` emits the literal Python repr `"None"` into the output (`"no None->reference value in config"`), which is nonsensical, unactionable, and indistinguishable from a real value to a non-technical reviewer.

**Why this matters:** The bug is silent and ships correct-looking output. Happy-path tests (reference present) all pass; the `None` branch fires only under config drift, which the loader treats as non-fatal. No exception is raised, so per-row error handling does not catch it. The user sees a reason containing the word `None` and has no idea what to do.

**Required behavior:**
1. Audit every f-string that interpolates a `str | None` into user-facing text. If `None` is reachable (not provably impossible), the f-string MUST degrade explicitly: build a phrase conditional on `None` (e.g. `rate_phrase = f"no {reference}->reference value in config" if reference else "no conversion rate configured"`), mirroring any sibling phrase that already degrades for the same `None` (in this case `reference_phrase`).
2. When the `None` reachability comes from a warn-only config-drift path (loader logs a WARNING but does not raise), treat the drift case as a first-class code path, not an impossible state. Add a discriminating test that constructs the drift config (e.g. `tracked_items={"X"}, item_references={}`) and asserts the literal substring `"None"` does NOT appear in the emitted reason (this assertion FAILS under the unguarded f-string; see tax-reporting "Outer Row-Level Exception Block Must Not Prevent a Trusted-Branch Operation From Completing").
3. Mirror existing degradation patterns within the same function. If a sibling phrase already handles `None` (`reference_phrase = f"{reference}-referenced item" if reference else "item"`), the new phrase built from the same value must degrade the same way; diverging patterns silently emit `None` in the diverging phrase.

**General form:** Any f-string interpolating an `Optional[str]` into output a human reads must not rely on the value being non-`None` unless the type system or an upstream guard proves it. When the value's `None` case is reachable through degradation (warn-only loader, partial config, best-effort lookup), the f-string must branch on `None` with an explicit human-readable phrase, and a test must assert `None` does not leak as a literal.

**Distinguishing from #85 (internal placeholder sentinels must not leak):** Lesson #85 addresses a sentinel STRING returned by a resolver (`UNKNOWN_OPERATOR_REVIEW_REQUIRED`) leaking into display; the value is a `str`, never `None`. This lesson addresses the Python `None` VALUE itself being interpolated via f-string into a string, producing the literal text `"None"`. Different value, different root cause (resolver design vs f-string + reachable `None`), same symptom class (nonsensical text in user output).

**Distinguishing from #96 (pre-bind locals for continue-style try):** Lesson #96 prevents a `NameError` on the degradation path by pre-binding locals. This lesson prevents a silent bad-value emission on the degradation path by branching the f-string. Both are "the degradation path must be SOUND" guards, but #96 is about name resolution and this one is about value rendering.

**What happened (2026-06-19, a refactor plan review r1):** The missing-reference reason helper in the value-correction module built the tier-4 review reason with `reference_phrase` that correctly degraded for `reference is None` (`"item"`), but the rate portion used a raw f-string `f"AND no {reference}->reference value in config"`. Under config drift (item in `tracked_items`, absent from `item_references` - the loader warns but continues), `reference` is `None` and the reason shipped as `"... AND no None->reference value in config - supply the conversion value."`. The Medium review finding (r1) added `rate_phrase = f"no {reference}->reference value in config" if reference else "no conversion rate configured"` mirroring `reference_phrase`, plus the discriminating test `test_drift_item_missing_reference_does_not_emit_none_literal`. See the review-r1-address log (local).

**See also:** internal sentinels must not leak, discriminating tests, pre-bind locals on degradation paths, inherit the guards when reusing a pattern. The missing-reference reason helper in the value-correction module (the mirrored-degradation idiom: `reference_phrase` and `rate_phrase` both branch on `None`).

**See also (principle cluster C):** #86 (same family, distinct angle: sentinel string leak (#85) vs `None`-value interpolation (#97) vs test-expectation `None`/`""` (#86)).


## 78. A Literal Timezone Token in a `strptime` Format Does Not Populate `tzinfo`; Naive Datetimes from External Reports Are LOCAL Time, Not UTC

**Principle:** Family H (Verify the real thing, not the abstraction)


`datetime.strptime(value, fmt)` sets `tzinfo` only when the format uses `%z`. A literal token in the format string, such as the text `UTC` in `%Y-%m-%d %H:%M:%S UTC`, is matched against the input but does NOT populate `tzinfo`; the result is `tzinfo=None` (naive) for that format too. Code that then unconditionally calls `.replace(tzinfo=UTC)` to "fill in the assumed zone" is correct ONLY for inputs whose format actually declares UTC; applying it to formats that carry a wall-clock LOCAL time stamps the wrong instant.

**Why this matters (latent and season-dependent):** The upstream data source's reports print `Date` / `Timestamp` as `DD/MM/YYYY HH:MM` with no zone. They are local source-zone time (winter offset vs summer offset, with DST transitions visible in the data), proven by the ~0h offset in winter and ~+1h in summer versus the explicit-UTC sibling rows (spring-forward and fall-back jumps both visible in the data). Stamping those dates as UTC means any summer event in the 00:00-01:00 local window maps to the PREVIOUS UTC day, drifting every calendar-day cross-report match key (the refactor plan's row match, the section dedup, the authoritative override) by a day. Latent only because no live case sits in that window yet.

**Detection methodology (the preventive rule):**
1. When parsing an external date, distinguish EXPLICIT-UTC formats (the format text carries a zone literal like `UTC`, or uses `%z`) from NAIVE formats. `strptime` leaves `tzinfo=None` for both; only the explicit-UTC one MEANS UTC. Detection helper: `_format_declares_utc(fmt)` = the literal `UTC` appears in `fmt`.
2. For naive formats, do NOT assume UTC. Localize to the source's IANA zone via `zoneinfo` (it handles DST transitions historically; never hand-code transition days), then convert to UTC for all cross-report match keys. Policy, per the user: a datetime with no explicit zone is LOCAL time even when it coincides with UTC.
3. Resolve the zone ONCE at config load into a `ZoneInfo` value object and thread it; do not re-construct `ZoneInfo` per call. An invalid IANA name fails fast at config load (`ValueError`, which `main()` converts to `ConfigurationError`), matching the surrounding `[REGION]` validation convention.
4. Leave explicit-UTC formats unchanged; they are already the correct instant. The upstream-row parse sites are therefore zone-agnostic.

**General form:** Any external report whose timestamps lack `%z` or an explicit zone must be treated as wall-clock local time, localized to the source's zone, and converted to UTC before joining by date. Never infer a timezone from a literal token in the `strptime` format; it does not populate `tzinfo`.

**What happened (2026-06-20, timezone-normalization plan):** `DATE_FORMATS` in the upstream parser includes `%Y-%m-%d %H:%M:%S UTC` (the only UTC-declaring format) among several naive formats. The datetime parser unconditionally did `parsed.replace(tzinfo=UTC)` at the stamp step, so naive event dates were mis-stamped as UTC. The fix (plan: the timezone-normalization plan file, quality-gated ready) threads a source `ZoneInfo` and branches: declared-UTC formats pass through; naive formats localize-then-convert; `zone=None` (default) preserves today's byte-for-byte behavior for backward compat. See the shelved RFC (the state-machine design doc) for the real-data DST evidence and the broader source-row-anchored design.

**See also:** reusing a pattern: inherit the guards, recalibrate exception handling, verify plan claims against source before dependent tasks. The datetime parser in the upstream parser module (the single normalization point). The upstream-data-source guidelines doc (export semantics).

**See also (principle cluster H):** #19 (same family, distinct angle: datetime representation traps.).


## 79. Confirm a Strengthened Guard-Binding Test Discriminates by Disabling the Guard and Confirming RED

**Principle:** Family A (Equivalence-class coverage)


When you STRENGTHEN (or add) a test that claims to bind a defensive guard (a non-finite check, a `None`-guard, a bounds/branch guard), the test passing against today's code is NOT proof it binds the guard. A guard's load-bearing case is often a narrow input (e.g. a tracked instrument for a tracked-instrument-only fallback guard); if the strengthened test exercises only a non-load-bearing input, removing the guard changes nothing observable and the test passes either way. The test then gives false confidence - exactly the failure mode of a guard "covered" by a case it does not protect.

**Required behavior:**
1. After strengthening or adding a guard-binding test, temporarily NEUTRALIZE the guard (comment it out, force its condition to the non-guarding value), run the test, and confirm it FAILS (RED) with a symptom pointing at the guard's responsibility. Disable, then RED, is the proof.
2. If the test stays GREEN with the guard neutralized, it does not bind the guard: it is exercising a path where the guard is not load-bearing. Switch the fixture to the load-bearing input and repeat until disable -> RED.
3. Restore the guard and confirm GREEN. The disable/RED then restore/GREEN pair is the empirical proof of discrimination; reasoning alone ("the guard is obviously needed") is insufficient because the non-load-bearing case is not obvious until you remove the guard and watch the test stay green.
4. Prefer the neutralize-and-run check over adding more assertion text: a stronger assertion that still passes with the guard removed binds nothing extra.

**Distinguishing from tax-reporting "Outer Row-Level Exception Block Must Not Prevent a Trusted-Branch Operation From Completing" (discriminating tests):** tax-reporting "Outer Row-Level Exception Block Must Not Prevent a Trusted-Branch Operation From Completing" states the principle - a discriminating test must assert a property that FAILS under a wrong implementation, and asks "could I implement this wrong and still pass?" This lesson is the operational answer for the guard-binding sub-case: empirically DISABLE the guard to answer that question, rather than reasoning about whether the assertion shape discriminates. tax-reporting "Outer Row-Level Exception Block Must Not Prevent a Trusted-Branch Operation From Completing" is about assertion SHAPE (where a memo attaches, N-guards-as-N-cases); this is a verification PROCEDURE (neutralize, run, observe RED/GREEN).

**Distinguishing from #57 (TDD RED-first):** #57 writes a NEW failing test before the fix. This lesson covers STRENGTHENING an existing test that already passes (e.g. adding a parametrized case to widen coverage), where the risk is that the new case does not actually bind the property it claims to - it greens against both the correct and the regressed code.

**What happened (2026-06-20 branch review, finding #1):** The non-finite Net Value guard (`if net_value is not None and not net_value.is_finite():` in `value_resolver.py`) was tested only with an untracked item. Removing the guard changed nothing for that fixture: `_resolve_value` tier-1 is False for infinity regardless, and an untracked item returns `None` ("untracked item") whether or not the guard runs. The guard is load-bearing ONLY for a tracked instrument, where without it a non-finite Net Value would skip tier-1 and route to the reference-value fallback, silently correcting the row to the reference value instead of leaving it flagged. After adding a tracked-instrument parametrized case, discrimination was confirmed by temporarily disabling the guard: the tracked-instrument case went RED (the value stayed `0` instead of being corrected to the reference value), while the untracked-item case stayed GREEN either way - proving only the new case binds the guard.

**See also:** TDD RED-first, discriminating tests, re-read RED tests against invariants before GREEN. CLAUDE.md §4 Agent Workflow Rules / Testing.

---

**See also (principle cluster A):** #100 (same family, distinct angle: principle (tax-reporting "Outer Row-Level Exception Block Must Not Prevent a Trusted-Branch Operation From Completing") vs procedure (#99) vs restore/undo variant (#100). Each body distinguishes itself.).


## 80. A Restore/Undo Final-State Test Cannot Distinguish "Fired Then Restored" from "Never Fired"; Assert the Intermediate Mutation

**Principle:** Family A (Equivalence-class coverage)


A test that verifies an undo/restore mechanism by asserting the FINAL state is back to its expected value gives a false GREEN when the mechanism never ran in the first place: the final state is identical whether (a) the mutation fired and was correctly restored, or (b) the mutation never fired at all. This is the restore/undo analogue of a guard-binding test that exercises a non-load-bearing input (#99): the assertion shape alone cannot tell you the mechanism is live.

**Root cause that makes it bite silently:** the mutation fires from a separate source whose malformation turns it into a no-op rather than a crash. Concretely (2026-06-20, the refactor plan re-zero tests): the override reads rows from an authoritative-source CSV the test built with a helper that wrote European-decimal values UNQUOTED (`-0,01`, `0,01`). Under `csv.DictReader` the decimal comma split each such value into two fields, shifting every subsequent column; the lookup extractor then read `Type` as garbage and returned `None`, so the override matched nothing and mutated no entry, silently inert, with no exception. The re-zero tests asserted a row's corrected value was restored; that holds whether the override ran (and was restored) or never ran, so both tests passed for the wrong reason. The CSV-quoting root cause is tax-reporting "`TaxJurisdictionConfig` Lives in `domain/jurisdiction.py`"; this lesson is the discrimination failure that root cause produced inside a restore/undo test.

**Detection (assert the intermediate mutation, not the restored final state):** to prove the override/restore mechanism is live, assert a signal that the mutation actually happened at the point of mutation, e.g. a row in the same run whose value carries the authoritative override (`value = base + the computed correction`), proving the override indexed and matched, separate from the row's restored final state. A restore test that cannot show the mutation happened is binding nothing.

**Required behavior:**
1. Any test asserting a restore/undo final state must ALSO assert that the mutation it restores actually fired on some row in the same run (an intermediate signal), so "never fired" goes RED rather than silently GREEN.
2. Confirm discrimination empirically (#99): temporarily make the source-of-mutation inert (revert the override, or feed it a malformed row) and confirm the intermediate-signal assertion FAILS.
3. For CSV test fixtures carrying European-decimal values, quote them; real upstream exports quote both amount and value (e.g. `...,"ITEM-A","143,75","140,18",...`). Verify field-to-column mapping with `csv.DictReader` before relying on the row.

**See also:** CSV fixture column alignment / quoting, disable-and-confirm-RED discrimination, discriminating-test assertion shape. CLAUDE.md §4 Agent Workflow Rules / Testing and §1 Reusable Engineering Rules (European decimal separators).


## 81. A Fail-Fast Exception Raised Inside a Degrade-to-None Wrapper Is Swallowed Unless Explicitly Propagated

**Principle:** Family B (Error-policy propagation)


A fail-fast guard that raises a specific exception (e.g. `ConfigurationError`) does NOT fail the run if the call site is wrapped by a tolerant handler that catches `Exception` (or a broad ancestor) and degrades to a safe default (logs "continuing without X", returns `None`). The degrading wrapper turns the fail-fast raise into a silent skip - the exact incorrect-by-default behavior the guard was added to prevent. The guard is only as strong as the narrowest handler between it and `main()`.

**Concrete incident (2026-06-20/21, timezone fail-fast):** to stop silently treating naive upstream dates as UTC, the report-loading boundary in `main.py` was given a STRICT guard that raises `ConfigurationError` when report data is present and the source timezone cannot be resolved (a configured source with `timezone is None`, OR no config loaded at all -> `region_config is None`). The guard sits BEFORE the helper's own `try ... except FileProcessingError ... except Exception` (which degrades data/parse errors to "Continuing without report data" -> `None`), so it is not swallowed by THAT block. But the report-loading boundary is itself called inside `_main`'s report-generation `try ... except Exception as e: raise ReportGenerationError(...) from e`, so without intervention the propagated `ConfigurationError` would be wrapped into a `ReportGenerationError` (wrong type; the contract says config problems surface as `ConfigurationError`). The fix is `except ConfigurationError: raise` clauses placed BEFORE every broader handler on the path: one in `_main`'s report-generation block (essential - stops the `ReportGenerationError` wrapping) and one defensively in the report-loading boundary (so any future loader-side `ConfigurationError` is not degraded to a silent skip). Without the `_main` clause the guard still "fired" but the application surfaced a `ReportGenerationError`, masking the config cause; the lesson is that the guard must be traced to `main()`, not just to the nearest function boundary.

**Detection (RED must trace through the wrapper, not stop at the guard):** a guard test that asserts the guard raises (`pytest.raises(ConfigurationError)` against the helper directly) is GREEN regardless of whether an outer wrapper swallows or re-wraps it - it never exercises the wrapper. You need a SECOND test at each outer wrapper boundary that asserts the WRAPPER propagates the right type: here, a `_main`-level test (`test_config_missing_warns_then_fails_fast_via_main`) asserts a `ConfigurationError` escapes `_main` (not `None`, not `ReportGenerationError`, not `NameError`). Pair it with a discriminating sibling confirming a plain data error (`ValueError`/`FileProcessingError`) IS still swallowed/`None` - otherwise a "fix" that propagates everything would pass and re-break the tolerant path.

**Mirror-image case (optional step wired too NARROW lets non-domain exceptions ESCAPE):** the symmetric failure. A non-blocking optional step whose own catch is scoped to the domain exception type (`except FileProcessingError`) lets the step's HTTP/parse stack raise siblings (`URLError`, `TimeoutError`, `json.JSONDecodeError`) that are NOT that domain type. Those propagate past the step's catch into the SAME outer `except Exception -> raise ReportGenerationError` block this lesson's first case worries about, aborting the run the step was supposed to be optional to. The fix is the mirror: the optional step's OWN catch must be BROAD (`except Exception`, mirroring the existing Koinly degrade template) so every failure mode degrades to "continuing without X" - unless the step raises a typed exception that genuinely must propagate, in which case the `except <TypedError>: raise` clause from Rule 1 goes ahead of the broad handler. The RED for the mirror case must inject a non-domain type (e.g. `URLError`) at the step boundary and assert the run does not raise plus the report still generates; a RED that injects only `FileProcessingError` is the one type the narrow catch already handles and cannot detect the gap.

**Required behavior:**
1. When adding a fail-fast raise inside an existing tolerant wrapper, audit EVERY `except` clause on the FULL path from the raise to `main()` (not just the nearest one) and confirm none of them degrades or re-wraps the new exception type. Add an explicit `except <SpecificError>: raise` ahead of each broader handler that would catch it.
2. Prefer a typed exception (a `ConfigurationError`/domain subclass) over a bare `Exception`/`ValueError` for fail-fast conditions; bare types are indistinguishable from the data errors the wrapper is meant to tolerate.
3. Test the propagation at the OUTERMOST wrapper boundary (`_main`/`main`), not only at the guard or the nearest function - and pair it with the "still degrades ordinary errors" sibling so the contract is pinned from both sides.
4. Keep the low-level loader a pure function (testable in isolation with the invalid input) and enforce the application contract at the orchestration boundary; this avoids coupling every parser test to the configuration requirement while still failing the real run.

**See also:** TDD RED-first; this guard's first RED traced only to the loader, masking the wrapper swallow, catch specific exceptions, not broad `Exception`, guards that fail closed when a dependency is absent, re-read RED tests against current invariants when the design is revised between RED and GREEN - this guard moved loader -> helper and targeted -> strict mid-stream. CLAUDE.md §3 Repository Constraints (optional source-data ingestion is non-blocking - that contract is for DATA errors, not config errors) and `docs/maintenance/project-guidelines.md` rule #6.

**See also (principle cluster B):** #77, tax-reporting "Sentinel for `dict.get` Default Must Exclude All Valid Observed Data Values" (same family, distinct angle: recalibrate policy on reuse (#77) vs raise-not-sentinel + ordering (tax-reporting "Sentinel for `dict.get` Default Must Exclude All Valid Observed Data Values") vs propagate through wrappers (#101)).


## 82. When Centralizing a Shared Helper Across Callers With Divergent Policies, Pin EACH Caller's Policy Arm for the Safety-Critical Kind (Coverage Fixes Are Symmetric)

**Principle:** Family A (Equivalence-class coverage)


When a refactor extracts a shared helper (e.g. a guarded-JSON loader: symlink reject + size cap + `json.load`) that N callers previously duplicated, and those callers have DIVERGENT policies for the same failure kind (one RAISES, another DEGRADES, a third has a mixed raise/degrade split), a characterization test that pins caller A's policy arm for a failure kind does NOT protect caller B's or C's copy of that arm. When a review (or your own audit) finds caller A lacks a characterization test for failure kind K, the same gap exists for B and C: fix it for all of them in the same pass, pinning the MOST SAFETY-CRITICAL kind first (the one whose silent wrong-policy corrupts an aggregate, e.g. a `stat_error` that DEGRADES to empty where the caller must RAISE, leaving a double-counted P&L).

**Why this matters:** centralization is the moment per-caller policies that used to live inline move behind a callback/strategy seam, and the implementer routinely copies one caller's `_on_error`/policy as the template for the next. If caller A's degrade-policy is the obvious template and caller B must raise for the same kind, an unguarded copy flips B's raise to a silent degrade, and EVERY characterization test for B still passes, because no test ever pinned B's raise arm. The bug is latent until the failure kind actually fires in production. Coverage gaps surfaced by centralization are symmetric across the sibling callers; a fix applied to only the caller a reviewer happened to spot leaves the siblings open.

**Qualification gate (when this rule applies):**
- A refactor extracts/centralizes a behavior (guard sequence, parse, validate) that 2+ callers previously duplicated.
- The callers do NOT share one policy: at least two differ on raise-vs-degrade (or raise-vs-skip, warn-vs-fail) for the SAME failure kind.
- At least one failure kind is "safety-critical" in some caller: its silent wrong-policy corrupts an aggregate or drops/double-counts records (not merely degrades a cosmetic default).

**Required behavior:**
1. Enumerate the failure kinds the shared helper can surface (e.g. `symlink`, `oversize`, `stat_error`, `invalid_json`, `bad_shape`, `missing`).
2. Build the caller x kind matrix; for EACH cell decide raise-or-degrade and add a characterization test pinning that arm, prioritizing the raise arm of the safety-critical kind in every caller that must raise.
3. When a review or audit finds a missing characterization test for one caller's kind, immediately check every SIBLING caller for the same kind before closing the finding. A coverage fix is symmetric, not local.
4. For the most safety-critical kind (silent corruption on wrong policy), prefer a test that asserts the raise happens in raise-callers, paired with a test that a degrade-caller yields its documented empty/default with no aggregate corruption, so a wrong-policy copy goes RED in the caller it would harm.

**Distinguishing from tax-reporting "Standalone Withdrawals Tagged Cost/Loan Fee Represent Taxable Disposals; Distinguish from Validator/Network Fees Using TxHash Co-occurrence" (sibling aggregators mirror byte-identical patterns):** tax-reporting "Standalone Withdrawals Tagged Cost/Loan Fee Represent Taxable Disposals; Distinguish from Validator/Network Fees Using TxHash Co-occurrence" is about sibling IMPLEMENTATIONS agreeing when they SHOULD produce the same output. This lesson is about sibling CALLERS of a centralized seam having INTENTIONALLY DIVERGENT policies, where the characterization-test plan must pin each one: here the callers must NOT be byte-identical, so mirroring the wrong one is precisely the bug.

**Distinguishing from #89 (branch on discriminator for a multi-cause flag):** #89 is multiple CAUSES within one function setting one flag. This is multiple CALLERS of one helper, each with its own raise/degrade policy for the same failure kind.

**General form:** Whenever a refactor moves a per-caller policy behind a shared seam, build the caller x failure-kind matrix and pin the raise/degrade arm for each cell, prioritizing the cell whose wrong policy silently corrupts output. A test gap is not a property of one caller: it is a property of the matrix, and the fix must cover the matrix.

**Example (2026-06-21 shared-loader refactor plan, the refactor plan #6):** the plan centralizes a guarded-JSON loader used by three `application/<domain>/` modules that previously each reimplemented the symlink/size/JSON guards, with DIVERGENT policies over the same failure kinds: `data_loader` DEGRADES on every kind (warn + defaults); `dedup` RAISES on every kind except `missing` (a silent empty on `stat_error` would leave the aggregated output double-counted - the exact hazard the raise exists to prevent); `classification` has a mixed split (raises on symlink/oversize/invalid_json/bad_shape, degrades on `missing` and `stat_error`). Review r1 found `classification` lacked a `stat_error` characterization test and the plan was amended to add `test_stat_error_degrades_to_empty`, pinning classification's DEGRADE arm. But the SYMMETRIC gap on `dedup` - whose `stat_error` arm is the MOST safety-critical (RAISE, nearest the double-counting hazard) - was missed until review r3 (Medium #1): no test pinned the dedup caller's `stat_error` raise, so an implementer copying classification's degrade-on-stat_error policy into the dedup `_on_error` would flip the raise to a silent empty and every Task-6 test would stay green. The fix adds a `TestLabelsConfig#test_stat_error_raises` alongside classification's degrade test, pinning the arm of the most safety-critical kind in each caller. See the shared-loader refactor plan review r3 (local) Medium #1 and r1 Medium #2.

**See also:** extracted helpers need direct unit tests, not just indirect, sibling aggregators mirror byte-identical patterns, branch on discriminator for a multi-cause flag, grep ALL test files when data-flow semantics change. `docs/maintenance/plan_quality_guidelines.md` Testing Requirements.


## 83. When Renumbering a Colliding Numeric ID in a Doc Corpus, Disambiguate Each Cross-Ref by Context, Not by the Number Alone

**Principle:** Family H (Verify the real thing, not the abstraction)


When a numeric heading (`## N.`) or ID is not unique (a collision: the same number appears on two headings), renumbering ONE of the occurrences is not the end of the work. Every cross-reference that names that number elsewhere (`See ... #N`, `development_lessons.md #N`, `Lesson #N (...)`) must be re-audited, and the audit must decide PER REF whether it intended the FIRST or the SECOND occurrence. The number alone is ambiguous under a collision; the deciding signal is the surrounding text (keywords in the referring sentence, a parenthetical that names a title verbatim, or field/term context).

**Why this matters:** after renumbering, a cross-ref left pointing at the old number is not necessarily DANGLING (the number still exists, on the FIRST occurrence), so a "no dangling refs" check passes clean. But the ref may now point at the WRONG lesson: the one whose keywords the referring text does NOT match. The ref silently re-targets to a lesson it never meant, and no automated check catches it, because the number is still valid. A reader who follows the ref lands on a topically-unrelated lesson and trusts it.

**Required behavior:**
1. Before renumbering, find the collisions: `grep -oE '^## [0-9]+\.' <file> | sort | uniq -d`.
2. For each colliding number N, grep the WHOLE corpus (all `docs/` + `AGENTS.md` + instruction files) for refs to `#N` (in multiple ref forms: `Lesson #N`, `see also #N`, `development_lessons.md #N`, `Merged into #N`, `Distinguishing from #N`, bare `#N` in prose).
3. For EACH ref, classify FIRST vs SECOND by inspecting the referring context: does the surrounding text name the SECOND-occurrence title, its keywords, or its domain terms? A parenthetical naming a title verbatim pins one occurrence. Keywords absent/present is the disambiguator.
4. Re-point only the refs classified as SECOND-occurrence; leave FIRST-occurrence refs untouched. Record the re-pointed COUNT per number.
5. After renumbering, run BOTH a no-duplicate check (`uniq -d` is empty) AND a no-dangling check (every referenced `#N` resolves to a heading). Neither check alone is sufficient: `uniq -d` empty proves uniqueness; no-dangling proves every number exists; NEITHER proves each ref points at the lesson its text intends. The per-ref disambiguation in step 3 is what makes the corpus semantically correct.

**Shape trigger (when to suspect this family):** a maintenance task says "renumber duplicate/relocating headings", "resolve ID collisions", or "deduplicate numbered anchors"; OR a grep for `uniq -d` on `## N.` headings is non-empty; OR a refactor splits/merges numbered guidance and cross-refs exist by number across files.

**General form:** Whenever a numbered or named anchor is not unique and you renumber/relocate one copy, the set of refs to that anchor is not a single homogeneous target. Each ref must be disambiguated against the surviving copies by the CONTEXT of the referring site, then re-pointed only where the context matches the moved copy. Uniqueness and no-dangling are necessary but not sufficient; semantic re-targeting is the actual fix.

**Example (2026-06-21 principle-generalization-system plan, Task 4):** `development_lessons.md` had `## 15.`, `## 16.`, `## 17.` each appearing TWICE (139 headings, 136 unique numbers). The SECOND occurrences were renumbered to #102/#103/#104. Two cross-refs to the colliding numbers existed: `AGENTS.md:109` ("See development_lessons #16", paraphrased) whose surrounding text cited `valid_from` audit-only and `service_start_date` matching (the SECOND-occurrence title's keywords) - re-pointed to #104; and `development_lessons.md:922 "Lesson #14 (Excel Column Width)"` whose parenthetical names the FIRST-occurrence title verbatim - left as #14. A no-dangling check passed either way; only the per-ref keyword audit (1 re-pointed, 1 left) made the refs semantically correct. No #15 refs existed. See the principle-generalization-system plan Task 4 implement log.

**See also:** compare against committed blob, not a stashed transient tree, grep ALL test files when data-flow semantics change - the doc analog: grep ALL docs when a doc ID moves.


## 84. A Mechanical `str.replace`/`sed` Pass Whose Search String Is a Substring of a Larger Token Silently Corrupts at the Wrong Offset; Verify With a Byte-Level Diff, Not a Match Count

**Principle:** Family H (Verify the real thing, not the abstraction)


When you run a mechanical text-replacement pass (`str.replace`, `sed s/.../.../`, a regex `sub`) over many lines, and the SEARCH string is a SUBSTRING of a larger token that also appears in the text, the engine matches at the FIRST (wrong) occurrence inside the larger token, not at the boundary you intended. The replacement "succeeds" (the count of matches is nonzero, the target substring is gone from the line), but it produced a different string than you meant, silently corrupting data. A pass that counts matches changed, or asserts the search string no longer appears, reports success on a corrupt result.

**Why this matters:** the natural verification for a bulk text edit is "did the search string disappear / did the replacement appear N times". Both pass when the engine matched at the wrong offset, because the substring you searched for WAS consumed - just from the wrong position, leaving the real target intact and the surrounding token mangled. The corruption is invisible to any check that operates on substring presence rather than the exact resulting bytes. The only reliable verification is a byte-level (or line-level exact) diff of the changed lines against the intended result.

**Qualification gate (when this rule applies):**
- You are running a bulk text replacement (string method, sed, regex sub) over multiple sites.
- The search string is a substring of a LARGER token that also appears at the edit sites (e.g. the search is `).)` and the line contains `(#NN).).` where the inner `)` of `(#NN)` precedes the search).
- There is no word-boundary or suffix anchor forcing the match at the intended offset.

**Required behavior:**
1. Before trusting the result, anchor the search to a boundary that forces the intended offset: a line-end anchor (`s/pattern$/replacement/`, or match a SUFFIX of the line rather than an interior substring), a word boundary (`\b`), or a longer search string that is UNIQUE to the intended offset (match `).).$` as a suffix, not `).)` as a substring).
2. After the pass, do NOT verify by "search string count is zero" or "replacement string count is N". Verify with a byte-level / exact-line diff: for each changed line, confirm the resulting bytes equal the intended output (e.g. `od -c` of a representative line tail, or diff the line against a hand-computed expected form).
3. When the replacement is mass-applied and a wrong-offset corruption would compound across sites, sample-verify MORE than one site (the corruption is uniform, so one sample catches it, but confirm the sample is representative of the edit class, not the single site you happened to author the search for).
4. If the first attempt corrupts, revert (`git checkout`) before retrying - do not layer a "corrective" replacement on top of corrupted bytes, which itself can substring-alias.

**Shape trigger (when to suspect this family):** a bulk text edit is described as "normalize N trailing-punctuation sites", "strip a suffix from M lines", "collapse doubled characters"; the search string is short (1-4 chars) and a common punctuation/bracket run; the verification plan is a grep/count rather than a byte diff; the edit sites contain the search string embedded inside a larger token (parenthesized numbers, quoted strings, bracketed refs).

**General form:** Whenever a bulk replacement's search string is a substring of a larger recurring token, the match lands at the wrong offset and every presence/count-based check passes on the corrupt result. Anchor the search to a boundary (suffix, word-boundary, unique longer match) and verify the EXACT resulting bytes, not substring presence.

**Example (2026-06-21 principle-generalization-system plan, review r1 Step 3.3, Finding 5):** normalizing 23 `**See also**` lines that ended with doubled trailing punctuation `).).` (close-inner-paren, stray inner period, close-outer-paren, final period). The first attempt used `str.replace(").)", ")).")`. That search string `).)` matches starting at the inner `)` of the `(#NN)` citation, not at the trailing `).)` suffix, so each line became `(#NN))..` (citation closed early, then two trailing periods) rather than the intended `(#NN)).`. The "replacement happened on all 23 lines" check passed. The corruption was caught only by a byte-level `od -c` of a changed line tail showing `(#42))..` instead of `(#42)).`. Reverted via `git checkout`; the correct fix anchored to the SUFFIX `).).$ -> )).` (unique to the intended offset). See the principle-generalization-system plan review r1 receiving-code-review log, Finding 5.

**See also:** compare against the committed blob via `git show`/worktree, not a transient stashed tree - the byte-diff analog: a stash-based presence check misleads the same way a match-count check does, plan pseudocode must be reconciled against plan tests, not the abstraction, a guard that reads a manifest must fail closed when absent - presence-based checks mislead in a different failure mode, same Family-H theme: verify the real thing, baseline log the structure - Family G data-loss observability, the observability counterpart to this verification rule.


## 85. A Validation Command That Scans a Shared Parent Directory to Enforce a NEW Convention Will False-Fail on Pre-Existing Legacy Entries; Scope the Assertion to New Work or Explicitly Accept the Legacy Pattern

**Principle:** Family H (Verify the real thing, not the abstraction)


When a plan introduces or tightens a convention (a filename-token suffix, a header shape, a naming pattern) and expresses its validation as a `find`/`grep` over a SHARED parent directory that already contains entries written under the OLD convention, the validator reports failures caused by the legacy entries, not by any defect in the new work. The validator's exit code does not distinguish "the new files violate the convention" from "old files that predate the convention still exist in the same tree." A broad-scope command that PASSES today becomes a FALSE failure the moment the convention is extended and old entries are deliberately left in place (out of scope for this plan).

**Why this matters:** the implementer of the new-convention task runs the plan's validation command, sees `BAD FILENAME TOKEN` (or the equivalent), and faces a false failure whose cause is pre-existing data outside the task's scope. Two wrong responses follow: (1) treat it as a real failure and block the task; (2) "fix" it by retro-editing the legacy entries to satisfy the new convention, silently expanding scope into files the plan declared out of scope. The correct response is to scope the assertion to the NEW entries (or to add an explicit accept-list for the legacy token), so the validator measures only what the task is responsible for.

**Required behavior:**
1. When authoring a plan task that introduces/tightens a convention over a shared directory, audit whether that directory already contains entries written under the prior convention (e.g. `ls` the parent, or `git log --oneline -- <parent>` to see which entries predate this plan).
2. If legacy entries exist and are explicitly out of scope, scope the validation command to the NEW entries: target the new subdirectory/path (e.g. `find resources/source/example/export2025* -name '*.csv'`) rather than the shared parent (`find resources/source/example/ -name '*.csv'`); OR extend the accept-pattern to include the legacy token (e.g. `grep -v -E '(_synth\.csv|_example\.csv|<legacy_token>\.csv)$'`).
3. State the scoping decision in the plan body so the implementer runs the NARROW command, not the broad one. A validation command is only authoritative for the task whose scope it matches.
4. If the broad command must remain (e.g. as a repo-wide guard), separate it from the per-task gate: the per-task task PASSES on the narrow scope; the broad command is a known-pre-existing-condition item tracked separately, not a blocker for the new-work task.

**Shape trigger (when to suspect this family):** a plan task says "add new fixtures/files under `<shared-dir>/` following convention X", "assert all `<shared-dir>/*.csv` match pattern Y", "run a hygiene check that files in `<shared-dir>` are synthetic"; AND `<shared-dir>` already contains sibling entries from earlier plans/years/exports that were authored before convention X existed. The trigger is the combination of a NEW convention + a SHARED directory + LEGACY siblings.

**General form:** Whenever a validator scans a container that mixes new-convention entries with legacy entries written under a prior convention, a blanket scan conflates the two populations. The validator must be scoped to the population it is meant to judge (the new entries), or must explicitly enumerate the legacy accept-set; an unscoped scan over the mixed container reports legacy as failure.

**Example (2026-06-22 tests-off-local-fixtures plan, Task 1 implement, finding flagged for Task 2):** Task 1 authors 10 new synthetic export 2025 fixtures under the example fixtures tree with a `_synth.csv` filename-token suffix (Design Invariant #1: synthesis not sanitization). The plan's filename-token hygiene command runs `find` across the whole example directory for `*.csv` files not matching `(_synth\.csv|_example\.csv)$`. This reports `BAD FILENAME TOKEN` because the pre-existing 2024 example fixtures use a legacy 10-char token (`xY9kLm2pQr`, `aB3cDn5oEf`) - the exact pattern the new invariant forbids. The 2024 fixtures are out of scope (an established pattern this plan extends), so all 10 NEW 2025 files pass the narrow `_synth.csv` check while the broad command false-fails on the legacy 2024 siblings. Task 2 must scope its hygiene assertion to the new dirs OR accept the 2024 legacy token. See the tests-off-local-fixtures plan Task 1 implement log, Findings to flag for downstream tasks #1.

**See also:** grep ALL test files when data-flow semantics change - the inverse scoping hazard: there you must WIDEN scope to catch stale siblings; here you must NARROW scope to avoid false-failing on legacy siblings; both are Family-H "verify the real thing, at the right population", verify plan claims against actual source before dependent tasks - the plan-time analog: the plan AUTHOR should catch the mixed-directory hazard before the implementer runs the broad command.


## 86. When Migrating a Test Off a Real Fixture to Synthetic Data, Narrow Assertions to the Behavior Under Test, Not Orthogonal Flags the Fixture's Synthetic Identifiers Incidentally Flip

**Principle:** Family H (Verify the real thing, not the abstraction)


When a test is migrated off a personal/gitignored fixture to committed synthetic data, the synthetic fixture uses deliberately unmapped or generic identifiers (fabricated source/account names not in any resolver map, placeholder tokens). Unmapped identifiers flip orthogonal downstream signals that the real-fixture version never exercised: a source-mapping resolver returns `review_required=True` / `UNKNOWN_...` for every unmapped source, so every row under the synthetic fixture carries a review flag that the real-fixture version (with mapped sources) set to `False`. If the migrated test keeps asserting the OLD flag value verbatim, it fails for a reason unrelated to what the test is verifying; if the implementer then "fixes" it by deleting the assertion entirely, the load-bearing invariant the assertion protected is lost.

The migrated assertion must be RE-SCOPED to the property the test actually exists to verify (the classification KIND, the routing path, the dedup phase), expressed in a form that is independent of the orthogonal signal the synthetic fixture flips. Assert the classification kind ("the row is routed as Category A, so the Ambiguous-classification reason text is absent from `review_reason`") rather than the unrelated flag ("`review_required` is False"). Record why the flag flips under synthetic data and why the re-scoped assertion still proves the original invariant, so a future reader does not mistake the relaxation for a weakened check.

**Qualification gate (when this rule applies):**
- You are migrating a test that read personal/real fixture data to committed synthetic data with deliberately unmapped or generic identifiers.
- The synthetic fixture causes a downstream signal (review flag, sentinel value, resolver status, validation warning) to flip relative to the real fixture because the identifiers are unmapped/placeholder.
- The pre-existing assertion checked that orthogonal signal as a side property, not as the test's primary purpose.

**Required behavior:**
1. Before copying an old assertion verbatim into the migrated test, identify which downstream signals the synthetic fixture's unmapped identifiers will flip (run the test once under the synthetic fixture and inspect every field the assertion reads).
2. For each flipped signal, decide: is this signal what the test is VERIFYING (keep, recompute against synthetic data), or an orthogonal side property (re-scope to the primary invariant, do not assert the flag value).
3. Express the re-scoped assertion on a discriminator that the primary behavior sets independently of the orthogonal flag (e.g. assert a classification-specific reason string is absent, or a routing-path log message fires, rather than asserting the review flag is False).
4. Document the re-scoping in a test comment: name the orthogonal signal, name the synthetic-identifier cause, and state the primary invariant the narrowed assertion still proves. A silent relaxation reads as a weakened check; a documented one reads as a correct migration.

**Shape trigger (when to suspect this family):** a test migration off a real/personal fixture to synthetic data; the synthetic data uses obviously-fabricated identifiers (source names like "Demo ...", placeholder tokens); an old assertion on a `review_required` / validation / resolver-status flag starts failing after the migration; the test's NAME or docstring describes a classification/routing/dedup behavior, not the flag itself.

**General form:** Whenever a fixture change causes an orthogonal downstream signal to flip and a test asserts that signal as a side property, the migrated assertion must be re-scoped to the primary behavior under test, not weakened by deletion. The discriminator the primary behavior sets (independent of the flipped signal) is the correct assertion target.

**Example (2026-06-22 tests-off-local-fixtures plan, Task 3):** A category-A trace test class and sibling classes in a pipeline e2e test asserted `review_required=False` (and absence of `"REVIEW:"`) on category-A rows, which held under the real fixture because the real source is a mapped supplier. The synthetic fixture uses `Demo Category A` / `Demo Category B` source names, deliberately unmapped, so the source-mapping resolver returns `review_required=True` (the source-mapping review signal, per the domain rule) for every row. The tests' PURPOSE is Category-A-vs-Category-B CLASSIFICATION (the authoritative-source classifier routes as clean Category A, not Ambiguous), not the source-mapping flag. The migration relaxed `assert not entry.review_required` to `assert "matches aggregated counterpart" not in entry.review_reason` (the Ambiguous-classification reason text is absent), asserting the classification KIND without conflating it with the source-mapping flag. The authoritative-source-handler log message `"routed to category A by row type; no aggregated counterpart"` (fires only on clean Category-A classification with no aggregated matches) confirms the post-dedup state. No production change was needed. See the tests-off-local-fixtures plan Task 3 implement log, Decision A.

**See also:** branch on the discriminator when a flag has multiple causes - the production-side analog: here the discriminator is used in the TEST assertion, there in production message synthesis, sentinel/`UNKNOWN_...` must not leak into display fields - the synthetic fixture flipping this signal is exactly the case #85 guards against in production; the test must not assert around it by hard-coding the flag, tests verifying "REVIEW:"/"OK" rendering must set `review_required` / `review_reason` explicitly on the fixture entry - the fixture-authoring counterpart: when you DO want to assert the flag, set it explicitly rather than relying on the fixture's incidental value, re-read each RED test against current design invariants before flipping GREEN - the re-scoping decision belongs in that re-read pass.


## 87. check-no-em-dash.sh "touched" Only Checks Unstaged/Untracked Files; Verify Committed Files by Diffing Against the Target Branch

**Principle:** Family H (Verify the real thing, not the abstraction)


When using incremental check/lint scripts (such as `check-no-em-dash.sh` or local pre-commit checks) during code review or branch validation, invoking them with a `"touched"` mode (which typically queries git for unstaged, staged, or untracked changes) only scans files currently modified in the working tree or index. If files have already been committed to the feature branch, they are no longer considered "touched" by these commands. Running the check-in-touched mode on a clean working tree will result in a false green pass, silently skipping validation for all changes introduced in the branch's commits.

**Why this matters:** When a branch review or validation is performed on a clean branch, running a touched-only check runs on zero files, exiting with success. A reviewer or automated process might assume the branch is compliant, when in fact none of the branch's changes were scanned. This leads to style or formatting violations (like U+2014 em dashes) being merged into the target branch.

**Required behavior:**
1. When validating a branch that may have committed changes (especially in review or post-commit gates), do not rely on `"touched"` or `"unstaged"` filters.
2. Query git to get the list of all files changed relative to the target branch (e.g. `git diff --name-only master...HEAD` or relative to origin/master) and filter to the appropriate extensions.
3. Pass this list of files explicitly to the checker tool (e.g. `check-no-em-dash.sh file $(git diff --name-only master...HEAD)`).
4. For automated or final check tasks in a plan, ensure the plan specifies diffing against the base branch rather than relying on current working-tree state.

**General form:** Incremental checks that filter by working tree state must be widened to diff-against-target when running on committed branch histories. A validation check must run on the actual population of files changed on the branch, not the subset of files currently in flight in the index.

**Example (2026-06-22 tests-off-local-fixtures plan, review step):** The branch review flagged low-severity em-dash findings in several committed files. Running `check-no-em-dash.sh touched` reported no issues because the changes had already been committed. Explicitly running `check-no-em-dash.sh file $(git diff --name-only master...HEAD)` correctly scanned the committed files and surfaced the em dashes, allowing them to be replaced.

**Inverse trap (2026-07-27 five-worker-review-panel plan, Task 3 hygiene scanner):** The same family fails in the opposite direction for a pre-commit check that selects files via `git diff --name-only <ref>...HEAD` (three-dot, commit-vs-commit). Three-dot diffs compare commits, not the working tree, so uncommitted-but-tracked edits and brand-new untracked files are invisible: the scan reports zero changed files and exits 0 a false PASS exactly when the gate is supposed to run (before the commit). The hygiene scanner's `--changed-from <ref>` mode had to use `git diff --name-only <ref>` (two-dot, working-tree-vs-ref) unioned with `git ls-files --others --exclude-standard` to see the actual pre-commit population. A TDD RED cycle caught it: the first implementation used `<ref>...HEAD` and every "expected fail" selftest reported PASS (zero changed files) instead of the expected hits.

**General form (both directions):** A gate that selects its file population from git must match the population the gate is supposed to inspect at the moment it runs. Post-commit / branch-final gates need commit-range diff (`<ref>...HEAD` or `<base>..HEAD`); pre-commit / pre-push gates need working-tree diff (`<ref>`, two-dot) plus untracked files. Selecting the wrong range yields a silent false green: zero files scanned, exit 0. Encode the selection in a selftest that proves the expected population is non-empty, because the "zero files" failure mode is otherwise invisible.

**See also:** grep ALL test files when data flow changes, compare against committed blob, not stashed tree, scope assertions to new work, TDD RED cycle catches invisible false-green gates (a selftest that asserts the expected hit surfaces a zero-population selection bug). CLAUDE.md §4 Agent Workflow Rules / No em dash scan.


## 88. A Boundary/Limit Characterization Test Must Hold the Non-Tested Dimension Valid: Use a Fixture That Satisfies Every Orthogonal Invariant at the Exact Boundary Value

**Principle:** Family H (Verify the real thing, not the abstraction)


A boundary or limit characterization test exercises one dimension at its edge (a size cap of exactly `N` bytes that must PASS; a count of exactly `M` items that must be accepted; a string of exactly `L` characters at the length limit). The fixture's *value along the boundary dimension* is the point of the test, but the fixture must ALSO satisfy every OTHER invariant the production path enforces on the same input (parseability, schema validity, encoding, non-emptiness). When the RED-test author reaches for a degenerate filler to hit the exact boundary (`b"x" * N`, an empty/placeholder object repeated `M` times, a string of `L` spaces), that filler violates an orthogonal invariant, so the "passes at the boundary" assertion is unsatisfiable by ANY correct implementation: the boundary dimension says ACCEPT, but the orthogonal invariant says REJECT, and the implementation correctly rejects. The test fails at GREEN for the wrong reason and an implementer who does not recognize the contradiction will either weaken the assertion (destroying the characterization) or contort the implementation to accept invalid input (introducing a real bug).

The fixture content for a boundary test must be chosen so that it would PASS through every non-boundary invariant at that exact size/count/length. For a size boundary on a JSON loader, that means VALID JSON of exactly `N` bytes (e.g. `b"1234567890"` for a 10-byte limit, not `b"x" * 10`). For a count boundary on a list validator, that means `M` valid items, not `M` nulls. The boundary dimension and the orthogonal invariants must be decoupled: vary only the boundary dimension across the boundary-pair tests (at-limit vs over-limit), keeping the orthogonal-invariant satisfaction constant.

**Qualification gate (when this rule applies):**
- You are writing a boundary/limit characterization test: an input set to the EXACT boundary value (size == limit, count == limit, length == limit) where the expected behavior is ACCEPT/PASS.
- The production path enforces at least one OTHER invariant on the same input (must parse, must validate against a schema, must decode, must be non-empty).
- The RED-test fixture reaches for a mechanical filler to hit the exact boundary value (a repeated byte/char, a repeated placeholder object, whitespace padding) rather than content that satisfies the orthogonal invariant.

**Required behavior:**
1. Before writing the boundary-pass fixture, enumerate every invariant the production path enforces on the input (parse format, schema, encoding, non-emptiness, sign, range) in addition to the boundary dimension under test.
2. Choose fixture CONTENT that satisfies ALL of those orthogonal invariants at the exact boundary VALUE. For a JSON size boundary, write the smallest valid JSON of exactly `N` bytes (a bare integer literal, a short valid object) - never a repeated sentinel byte.
3. Keep the orthogonal-invariant satisfaction IDENTICAL across the boundary pair (the at-limit test and the over-limit test differ ONLY in the boundary dimension, not in whether the content is valid). This isolates pass/fail to the boundary check.
4. When a boundary-pass test fails at GREEN despite a correct implementation, FIRST suspect the fixture: trace whether the filler violates an orthogonal invariant the implementation correctly enforces. Do not weaken the assertion until you have confirmed the fixture satisfies every non-boundary invariant.

**Shape trigger (when to suspect this family):** a RED boundary/limit/at-limit test fails during GREEN; the test's fixture is built by repeating a single byte, character, or placeholder to reach the exact limit (`b"x" * N`, `[None] * M`, `" " * L`); the production path parses/validates/decodes the input; the test name or docstring says "at limit passes" or "boundary accepted".

**General form:** A characterization test that pins behavior at a boundary must hold the non-tested dimensions at values that satisfy every orthogonal invariant, so that a pass/fail attributes solely to the boundary check. A degenerate filler that hits the exact boundary value but violates an orthogonal invariant makes the "boundary accepts" assertion unsatisfiable by any correct implementation and forces the implementer to choose between weakening the test and corrupting the implementation.

**Example (2026-06-21 value-correction-refactor plan, Task 4 GREEN):** `test_size_limit_boundary_at_limit_passes` in `tests/unit/infrastructure/test_json_loader.py` set `size_limit = 10` and wrote `path.write_bytes(b"x" * size_limit)` (10 `x` bytes), then asserted `recorder == []` and `result is not DEGRADED` (i.e. the loader parses the file and does not call `on_error`). But `b"xxxxxxxxxx"` is invalid JSON, so any correct `load_guarded_json` MUST call `on_error(path, "invalid_json", ...)` and return `DEGRADED` - the assertion is unsatisfiable. The boundary dimension (size == limit -> accept) and the orthogonal invariant (content must parse) were confounded by the filler. Resolution: change the FIXTURE ONLY to `b"1234567890"` (exactly 10 bytes, valid JSON parsing to integer 1234567890); no assertion changed. The at-limit test and the over-limit test now differ only in size, not in JSON validity. See the Task 4 implement log "Errors and retries" and lesson #77 (the loader being characterized).

**See also:** re-read each RED test against current design invariants before flipping GREEN - the re-read pass is where this contradiction is caught, reconcile plan pseudocode against plan tests and design invariants - the sibling rule for pseudocode-vs-test contradictions, this lesson for fixture-content-vs-invariant contradictions, narrow assertions to the behavior under test when a fixture flips an orthogonal signal - the migration counterpart: there the fixture is correct and the assertion over-reaches; here the fixture under-reaches and the assertion is fine, characterization golden value disagreeing with the plan's expected value, read the implementation before writing edge-case tests. CLAUDE.md §4 Agent Workflow Rules (RED-then-GREEN TDD discipline).


## 89. An `lru_cache`-Decorated Function That Reads a Module Global at Call Time Needs an Autouse Fixture That Rewires the Global AND Calls `cache_clear()` in BOTH Setup and Teardown

**Principle:** Family H (Verify the real thing, not the abstraction)


When the function under test is decorated with `@lru_cache(maxsize=1)` AND reads a module-level global (e.g. `_SOME_CONFIG_FILE` resolved at call time, not at import time), a per-test `monkeypatch.setattr(module, "_SOME_CONFIG_FILE", tmp_path / "f.json")` alone is INSUFFICIENT: the cache holds the RESULT of the previous call (computed against the previous global value), so a stale cached return masks the monkeypatched global entirely. The test would pass against the OLD cached value regardless of what the test wrote to `tmp_path`, producing a characterization test that does not actually characterize the input under test.

The fix is an `@pytest.fixture(autouse=True)` scoped to the test class that performs THREE actions: (1) SETUP rewire the module global to the test's `tmp_path` via `monkeypatch.setattr`, (2) SETUP call `func.cache_clear()` so the call observes the new global, and (3) TEARDOWN (after `yield`) call `func.cache_clear()` AGAIN so a LATER test class or function (outside the autouse scope) can never read a cached value whose underlying global pointed at a `tmp_path` that pytest has already deleted. Without teardown `cache_clear()`, the cache survives the test session pointing at a now-deleted path; the next uncached caller hits `FileNotFoundError` or, worse, a sibling test that forgot its own isolation reads a stale value and silently passes.

**Qualification gate (when this rule applies):**
- The function under test is `@lru_cache`-decorated (any `maxsize`) OR memoized via an equivalent mechanism (`functools.cache`, a module-level dict cache).
- The function reads a module-level global (path, env var, config object) at CALL time, so the cached key does NOT capture the global's value (caching is keyed on the function's arguments, not on the global it transitively reads).
- You are writing tests that change the global's value (or the file it points at) per case to drive different code paths.

**Required behavior:**
1. Add `@pytest.fixture(autouse=True)` on the test class (or module). Use a leading-underscore name (e.g. `_isolate_config`) so Ruff PT019 does not require it as a parameter; do NOT yield a value from the fixture, or Ruff flags an unused injected parameter.
2. In SETUP: `monkeypatch.setattr(module, "_GLOBAL", tmp_path / "f.json")` THEN `module._cached_func.cache_clear()`. Order matters: clear AFTER rewiring is unnecessary (the call re-reads the global), but clearing in setup guarantees no prior cached value survives into the test.
3. In TEARDOWN (after `yield`): restore the original global (monkeypatch's automatic teardown handles this, but explicit restore documents intent) AND call `module._cached_func.cache_clear()` again. The teardown clear is the load-bearing guard against cross-test-class leakage.
4. Each test reconstructs `tmp_path / "f.json"` locally (the path is deterministic given `tmp_path`); do not rely on a yielded value from the autouse fixture.

**Shape trigger (when to suspect this family):** a test monkeypatches a module global and writes a file under `tmp_path`, but the assertion passes (or fails) against a value that does not match what the test wrote; the function is `lru_cache`-decorated; sibling test classes in the same file share the module and the cache.

**General form:** A cached function that reads a module global captures the global's value ONLY transitively (via the cache key, which is the function's arguments). Per-test mutation of the global therefore requires an explicit cache invalidation in BOTH setup and teardown; a single setup clear leaves the cache populated with a stale value for whatever runs next in the session.

**Example (2026-06-21 threshold-correction-refactor plan, Task 7):** `_load_known_entries` in `application/classification.py` is `@lru_cache(maxsize=1)` and reads the module global `_KNOWN_ENTRIES_FILE` at call time. `TestClassificationLoader` added a `@pytest.fixture(autouse=True) _isolate_entries_file` that, for every test in the class: SETUP monkeypatches `classification._KNOWN_ENTRIES_FILE` to `tmp_path / "entries.json"` and calls `_load_known_entries.cache_clear()`; TEARDOWN restores the original global and calls `cache_clear()` again. Without this, `test_missing_degrades_to_empty` (no file written) could have returned a stale `frozenset({...})` cached by `TestKnownEntries.test_entries_cached` running earlier in the session, and the degrade branch would never have been exercised. See the Task 7 implement log "Key decisions / Autouse fixture mechanics".

**See also:** discriminating tests - mutate the input between calls to confirm WHERE a memo attaches; this lesson is the isolation complement for CHARACTERIZATION tests that must defeat the cache entirely, confirm a strengthened guard-binding test discriminates by disabling the guard, read the implementation before writing edge-case tests - the `lru_cache` decorator and module-global read are visible in the function signature/source and must be read before authoring the fixture. CLAUDE.md §4 Agent Workflow Rules.


## 90. execute-plan `done` docs-branch step: use ONLY the canonical script; `git add -A` / `git checkout docs -- .` on the feature branch stages gitignored docs onto the feature commit

**Principle:** Family H (Verify the real thing, not the abstraction)


The `done` skill's docs-branch step backs up gitignored docs (`docs/tmp/`, `.ai-playbook/`, `docs/history/reviews/`) to the `docs` orphan branch. Those paths are gitignored on the FEATURE branch but tracked on the docs branch, so the two lines of history are intentionally disjoint. A `done` sub-agent that improvises the backup with `git add -A` or `git checkout docs -- .` on the feature branch crosses that boundary and corrupts the feature branch: `git add -A` stages every gitignored doc into the next feature commit (171 files in the incident below), and `git checkout docs -- .` overlays the orphan-branch tree onto the feature working tree. Both are silent until `git status` is read; a sub-agent that reports "nothing to commit" or "no gitignored content lost" without checking `git status` AND the on-disk `docs/tmp/` is not to be trusted.

**What happened (2026-06-22, the value-correction-refactor execute-plan run):** The Task 8 `done` sub-agent ran a non-canonical sequence (`git checkout docs -- .` + `git add -A` + `git commit`) that committed 171 gitignored files onto the FEATURE branch (commit `7790ff3`). It detected the anomaly, hard-reset the feature branch to its clean Task 7 base (`80e5d66`), re-applied the two intended Task 8 files, and re-ran the canonical docs-branch script; the Task 8 commit itself was byte-correct. BUT the `git reset --hard 80e5d66` PURGED `docs/tmp/execute-plan/<PLAN_SLUG>/` from the working tree: the session logs had become tracked via the bad commit's index, and `80e5d66` does not track them, so the reset removed them from disk. The sub-agent reported "manifest does not exist / nothing to update" and "no gitignored content lost" - both wrong. The orchestrator recovered the session logs from git objects (`c73464c`, `b9cfe42`) via `git restore --source=<obj> --worktree -- <path>` (NOT `--staged`). The docs orphan branch tip was also truncated by the mishap (lost 47 files vs `c73464c`); it was repaired in an ISOLATED `git worktree add` on the docs branch so the feature working tree was never touched.

**Required behavior:**
1. An execute-plan `done` sub-agent (Step 1.4 / Step 3.4) must run the docs-branch step using ONLY the canonical script from the `done` / `docs-branch` skill, as a SINGLE shell invocation. Never `git add -A`, `git add .`, or `git checkout docs -- .` on the feature branch.
2. If gitignored docs are accidentally staged or committed onto the feature branch, recover in two stages: (a) hard-reset the feature branch to its pre-mishap base (this restores tracked files but PURGES any gitignored file the bad commit had tracked in its index), then (b) recover the working-tree gitignored files with `git restore --source=<obj> --worktree -- <path>` - NEVER `--staged`. `--staged` re-adds the gitignored files to the index, which is the exact hazard. Identify recovery objects via `git reflog` and the docs-branch history.
3. To repair the docs orphan branch itself (e.g. a truncated tip), use a SEPARATE `git worktree add <tmp> docs` and operate there; the feature working tree and index are never touched by orphan-branch repair. Remove the worktree afterward.
4. After any `done` docs-branch step, the orchestrator must verify (a) `git status` shows ONLY the intended task files on the feature branch (no `docs/tmp/`, no `.ai-playbook/`), (b) `docs/tmp/execute-plan/<PLAN_SLUG>/` still exists on disk with its session logs, and (c) the docs branch tip advanced. A sub-agent's "nothing to commit / nothing lost" claim does not satisfy this gate without the `git status` + on-disk check.

**Shape trigger (when to suspect this family):** an execute-plan `done` sub-agent reports a docs-branch result and the feature-branch `git status` shows gitignored paths (`docs/tmp/`, `.ai-playbook/`) as staged/modified, OR `docs/tmp/execute-plan/<PLAN_SLUG>/` is missing from disk after a `done` step that involved a reset.

**General form:** The docs orphan branch is a SEPARATE line of history whose tree is intentionally disjoint from the feature branch (gitignored on feature, tracked on docs). Any git operation that crosses the two - staging feature-gitignored paths onto the feature commit, or overlaying the docs tree onto the feature working tree - corrupts the feature branch. The canonical docs-branch script exists precisely to keep the two disjoint; improvising the crossing is the hazard.

**See also:** docs-branch `git stash` hazard - same family, distinct angle: stash vs add-A/checkout, `git mv` nesting in the doc tree, stale plan paths after doc-hierarchy migration, verify actual git state before reporting - the "nothing lost" false report is a #88 failure. `docs-branch` skill, `done` skill, `execute-plan` anti-pattern table. CLAUDE.md "Gitignored docs safety".


## 91. Never Proceed to Plan Execution or Make Code Changes Without Explicit User Approval in Planning Mode

**Principle:** Family H (Verify the real thing, not the abstraction)


In Planning Mode, once an implementation plan has been written and reviewed (even if it has zero blocker or medium findings and is marked "Ready for execution"), the agent MUST stop and wait for the user's explicit approval before making any code modifications or running execution commands.

**Why this matters:** Planning Mode is designed to align the agent and the user on the technical design and scope before any changes are committed or codebases modified. Assuming execution is authorized just because a plan is complete or marked ready (the abstraction) bypasses the user's control. Only the user's explicit command to proceed (the real instruction) authorizes execution. Bypassing the approval gate violates user intent and creates unwanted code churn or incorrect implementations that must be reverted.

**Required behavior:**
1. Once a plan has been written and its reviews complete with zero Blocker and Medium findings, present the execution handoff to the user.
2. Stop tool execution and wait for the user to explicitly say "proceed", "execute the plan", or similar.
3. Do not run any implementation tasks, write any product code, or modify production files until that explicit approval is received.
4. If code changes were made prematurely, immediately stash or revert them to return the repository to a clean state matching the approved design base.

**Shape trigger (when to suspect this family):** planning a task under Planning Mode; the plan file is written and reviewed; the next step in the workflow is execution; the user has not yet explicitly authorized execution.

**General form:** The completion of a planning phase (a green review, a ready status) is an abstraction representing preparedness, not an authorization to execute. Authorization requires verifying the real human intent (an explicit command to proceed). Executing code modifications based on the ready state alone violates the gating protocol and introduces code churn.

**Example (2026-06-23 filter-feature plan):** The agent was tasked with planning a feature-filtering pass under the local config rules. After the plan reviews finished with zero blockers/medium findings, the agent immediately proceeded to execute the tasks (updating config, creating config tests, implementing filtering) without waiting for user approval. The user corrected the agent, requesting that all premature changes be reverted or stashed and that no code changes be made until authorized. The agent stashed/reverted the changes to return HEAD to `5847e2a docs: update plan to reference r2 review` and halted for approval.

**See also:** verify actual git state before reporting, verify plan-time claims before writing tasks, `AGENTS.md` "Agent Workflow Rules".


## 92. Multi-Type Configuration Loading in Single-File Schema Requires Explicit Type-Dispatching and Scoped Default Fallbacks

**Principle:** Family D (Single source of truth)


When expanding a configuration loader (such as parsing a flat country-specific TOML config) to support non-boolean fields (e.g. subtable dictionaries `dict[str, Decimal]`), utilize explicit type-dispatching via `get_type_hints` and `get_origin` rather than assuming all values under a section share a single primitive type. Ensure default-value loops are strictly scoped to the matching type hint (e.g. only defaulting boolean fields to `False`) to avoid clobbering or type-checking crashes on missing optional fields.

**Why this is required:** If a config parser loop assumes all config values are booleans, adding a complex type (like a subtable dictionary) will cause the validation step to crash with a `ValueError` or `TypeError`. Furthermore, if the loader's fallback loop unconditionally defaults all absent keys to `False`, it will overwrite the class-level default factory (`default_factory=dict`) of the new dictionary field with `False`, breaking the configuration for any other entry that does not explicitly declare the new subtable.

**Required behavior:**
1. Retrieve type hints for the target config class using `get_type_hints(ConfigClass)` and determine type groups (e.g., bool-typed fields vs generic dict fields via `get_origin(hint) is dict`).
2. Rewrite the validation loop to branch explicitly on type groups, performing the correct validation and conversion for each group (e.g., converting dict floats/ints to `Decimal` using `Decimal(str(v))`).
3. Limit any default fallback logic (e.g., setting unset flags to `False`) strictly to the matching type group (e.g., only iterating over boolean-typed fields), allowing other complex fields to default via their standard dataclass defaults or factories.
4. Add config unit tests validating both the presence of the new type and its correct fallback to defaults when absent.

**Shape trigger (when to suspect this family):** introducing a non-boolean config flag to an existing flat configuration class that historically assumed all fields are boolean; the parser validation loop or defaults fallback crashes or incorrectly resolves the new field.

**Example (2026-06-23 filter-transaction-fees plan, Task 1):** The TOML config loader in `config.py` was generalized to accept `dict[str, Decimal]` for `exclude_fee_max_per_item`. Sibling fields were bools, and the existing validation loop crashed on the dict subtable. Additionally, the default-value loop originally set all missing keys to `False` by default, which collapsed the new dict field to `False` when missing in non-PT region configs. Dispatched bool-specific defaulting strictly to bool-typed fields, allowing dict fields to fall back to `default_factory=dict`.

**See also:** tax-reporting lesson "Decision Point Flags Require TaxJurisdictionConfig Field", Verify imports on cross-module calls.


## 93. Use Type Parameterization (TypeVar) in Shared Generic Primitives to Preserve Subclass Field Visibility Under Static Analysis

**Principle:** Family B (Type-safe domain logic)


When extracting a shared utility or matcher that operates on polymorphic event models, parameterize input sequences and return structures with generic type variables (`TypeVar("E", bound=ParentProtocol)`) rather than generic parent types. This preserves concrete attribute visibility (like custom fields used only by specific callers) at caller sites under strict static analysis (basedpyright) without needing explicit type-casting or runtime checks.

**Why this is required:** If the shared matcher is typed to accept and return generic parent models (like the parent `SourceEvent`), the caller receives the generic type. If the caller then attempts to read subclass-specific fields on the returned results (like `event.label` in the calling module), the static type checker will raise diagnostic errors because `label` is not part of the generic parent. Using `TypeVar("E", bound=SourceEvent)` forces the type checker to bind the return type to the concrete type passed by the caller.

**Required behavior:**
1. Define a generic type variable bound to the parent protocol/class (e.g., `E = TypeVar("E", bound=SourceEvent)`).
2. Parameterize both the input events sequence (`events: Sequence[E]`) and the generic matcher result structure (`MatcherResult[E]`) with that type variable.
3. Expose matching functions using this generic parameterization so that basedpyright propagates type inference cleanly back to the caller.
4. Do not reference subclass-specific attributes (like `event.label`) inside the generic matcher; keep internal algorithms strictly scoped to the parent protocol.

**Shape trigger (when to suspect this family):** extracting a shared algorithm/matcher that processes different subclassed events; caller code reads custom attributes from the matched events; static analysis reports attribute-missing errors at the caller site after extraction.

**Example (2026-06-23 filter-transaction-fees plan, Task 2):** Two matcher modules share the exact same two-phase matching algorithm. When extracting the shared matcher, the result structure `MatcherResult` was parameterized with `TypeVar("E", bound=SourceEvent)`. This allowed the calling module to access `event.label` (which is specific to a subclass and absent from the base `SourceEvent` protocol) on the returned matched metadata without raising basedpyright diagnostic errors.

**See also:** Specific type annotations for generic collections, circular imports during helper extraction, shared matcher extraction constraint.


## 94. Type Heterogeneous Validated Kwargs Dicts as `dict[str, Any]` to Feed `**`-Unpack Into a Dataclass Constructor Under basedpyright

**Principle:** Family B (Type-safe domain logic)


When a loader builds a kwargs dict whose values are heterogeneous (e.g., some `bool`, some `dict[str, Decimal]`) and then unpacks it into a dataclass constructor (`Config(**flag_kwargs)`), type the kwargs dict as `dict[str, Any]`, NOT as a union like `dict[str, bool | dict[str, Decimal]]`. Per-key type safety is guaranteed by the loader's type-dispatching validation, but basedpyright cannot propagate per-key narrowing through a `**`-splat; a union-typed kwargs dict produces one `reportArgumentType` error per constructor parameter (a value typed `bool | dict[...]` is not assignable to a param typed `bool`), while `dict[str, Any]` admits the splat cleanly.

**Why `Any` is honest here:** the values are validated at load time by the dispatching loader before being placed in the dict. The static element type of a `**`-unpacked mapping is genuinely opaque to the checker; `Any` reflects that opacity rather than hiding a real type hole. Prefer the small set of `reportAny` warnings (on the splat) over a cascade of `reportArgumentType` errors that mis-describe the situation.

**Required pattern:**
```python
from typing import Any

def _load_flags(...) -> dict[str, Any]:
    flag_kwargs: dict[str, Any] = {}
    for name, value in raw.items():
        # type-dispatching validation guarantees the per-key type here
        flag_kwargs[name] = _validate_and_convert_flag(name, value)
    return flag_kwargs

config = RuleConfig(**flag_kwargs)  # basedpyright: no ArgumentType errors
```

**When NOT to apply:** if the dict is consumed positionally (e.g. `config = RuleConfig(flags)` where the param itself is typed `dict[str, bool | dict[str, Decimal]]`), keep the precise union type; the splat is the only construct that defeats per-key narrowing.

**Shape trigger (when to suspect this family):** a loader validates heterogeneous values into a kwargs dict and splats them into a constructor; basedpyright emits one `reportArgumentType` per dataclass field; rewriting the dict annotation to a union does not silence them.

**Example (2026-06-23 filter-transaction-fees plan, Task 1):** `_load_rule_flags` returns validated bools and `dict[str, Decimal]` maps; the result is splatted into `RuleConfig(**flag_kwargs)`. Typing the dict as `dict[str, bool | dict[str, Decimal]]` produced 10 `reportArgumentType` errors; retyping to `dict[str, Any]` left only acceptable `reportAny` warnings on the splat while the per-key validation is unchanged.

**See also:** specific type annotations for generic collections, multi-type config loading requires explicit type-dispatching.


## 95. A Refactor Plan Clause That Instructs a Net-New Behavior Addition Conflicts With the Same Plan's Byte-Identical Non-Regression Criterion; Verify Against Actual Pre-Refactor Behavior Before Implementing

**Principle:** Family H (Verify the real thing, not the abstraction)


When a plan frames its task as a refactor with an explicit "behavior must be byte-identical to the current implementation" non-regression criterion, ANY clause that instructs the implementer to ADD a net-new side effect (a new log line, a new warning, a new validation, a new field) that the current code does NOT emit is internally contradictory. Implementing the addition breaks characterization/non-regression tests; implementing the byte-identical behavior contradicts the clause. The resolution is mechanical: before implementing any clause that prescribes new observable behavior in a refactor task, grep/trace the pre-refactor source to confirm the behavior already exists. If it does not, the clause is in error: the new behavior belongs in a LATER task (a feature add, not this refactor) or the non-regression criterion must be explicitly relaxed for that one side effect. Do not silently add the behavior; do not silently drop the clause; document the discrepancy and route the behavior to its owning task.

**Why this happens:** Plan authors reasoning about an extraction often think "since the matcher's old home warned for X, the new caller must warn for X too" without confirming the old home actually warned. The shared-helper extraction makes the absence visible (the matcher no longer emits the warning), so the plan tries to restore it everywhere, but the original caller may have intentionally omitted it, or never had it. The extraction did not change behavior; the plan clause would.

**Shape trigger (when to suspect this family):** a refactor/extraction plan task states "behavior byte-identical" AND contains a clause instructing the new caller or new helper to emit a warning/log/validation/field that reads like a restoration ("since X was moved out of the shared matcher, the caller now owns X"). Trace the pre-refactor source for X before writing the loop that emits it.

**Required response when a refactor clause prescribes new observable behavior:**
1. Trace the pre-refactor source for the prescribed behavior (grep for the log message, the warning call, the validation).
2. If absent: the clause conflicts with the byte-identical criterion. Do NOT implement the addition in the refactor task.
3. Route the behavior to its owning task (usually the feature task that follows the refactor), or relax the non-regression criterion for that one side effect with an explicit doc note.
4. Document the discrepancy in the implementation log so reviewers see the deviation is intentional and not a missed clause.

**Example (a filter-events plan, Task 2):** Clause 8 instructed the category-specific caller of the newly-extracted `remove_matched_items` matcher to warn for each event in `unmatched_events`, "since this warning was moved out of the shared matcher." The pre-refactor `category_dedup` emitted NO unmatched-event warning; a category event with no corresponding matched item is the expected authoritative-source-only outcome. Adding the warning loop broke 3 tests (2 unit + 1 e2e logger-name/count assertions) and violated the byte-identical non-regression criterion. Resolution: the warning loop was removed; the docstring documents that an unmatched category event is expected. The unmatched-event handling that clause 8 gestured at is owned by Task 3 (the fee filter), which has its own unmatched semantics.

**Distinguishing from tax-reporting "Decision-Point Doc Prose Enumerations Must Match Implemented Code Branches":** tax-reporting lesson "Decision-Point Doc Prose Enumerations Must Match Implemented Code Branches" covers a characterization test whose captured golden value disagrees with the plan's STATED EXPECTED VALUE (a magnitude/direction conflation in captured output). This lesson covers a refactor clause that INSTRUCTS A NET-NEW BEHAVIOR ADDITION the same plan's non-regression criterion forbids. tax-reporting "Decision-Point Doc Prose Enumerations Must Match Implemented Code Branches" is about a value mismatch in a test; #121 is about a behavior-addition instruction contradicting a non-regression constraint. Both are Family H verification rules but have distinct triggers (golden-value disagreement vs clause-vs-criterion contradiction) and distinct fixes (reconcile narrative vs route the behavior to its owning task).

**See also:** characterization tests revealing magnitude-vs-direction conflation, data trace verification, re-read RED tests against current design invariants when a plan is revised between RED and GREEN, CLAUDE.md §4 Agent Workflow Rules (verification-first task ordering).


## 96. `git checkout -- <file>` Cannot Revert a RED-Phase Break on an Untracked (New) File; Edit It Directly

**Principle:** Family H (Verify the real thing, not the abstraction)


When a RED sanity check deliberately introduces a break in a NEW, untracked source file (e.g. appending `and False` to a guard so the test suite fails and proves the tests are discriminating), the revert cannot use `git checkout -- <file>` or `git restore <file>`. Those commands restore the working-tree copy from a tracked blob in the index or a commit; an untracked file has NO tracked blob in ANY commit yet, so the restore is a silent no-op (or "pathspec did not match" / "no such ref") and the deliberate break remains on disk. The agent then re-runs the test suite believing the revert succeeded, ships a still-broken file, or layers a "corrective" edit on top of the break.

**Required behavior:**
1. Before reverting a RED-phase break on a file, check `git status --short` for that path. If it shows as `??` (untracked), do NOT use `git checkout`/`git restore`; the file has no committed baseline.
2. Revert the break by editing the file directly: re-open it, locate the injected change (the appended `and False`, the swapped operator, the commented guard), and remove it with an Edit. If the entire file is the experiment, delete the file rather than `git checkout`-ing it.
3. After reverting, re-run the test suite and assert it returns to GREEN as the proof of a clean revert; do not trust the absence of an error from `git checkout`.

**Shape trigger (when to suspect this family):** an agent reports "I broke the tagged path with `and False`, ran `git checkout -- fee_filter.py` to revert, and re-ran the suite" but the suite still fails on the same path; OR `git checkout -- <file>` returns silently with no working-tree change on a file the agent knows it modified. In both cases the file is untracked and the checkout was a no-op.

**Example (2026-06-23 filter-transaction-fees plan, Task 3):** After writing the new fee-filter module and its test suite, the implementer confirmed the suite was discriminating by temporarily breaking the tagged-fee guard with `and False` (12 tests failed as expected). The attempted revert was `git checkout -- fee_filter.py`; because the file was new and untracked, the checkout could not restore it and the `and False` break remained. The break was removed via a direct Edit, and the suite returned to 42 passing. Existing lessons #92/#93/#110 cover `git checkout` recovery for TRACKED files (re-export modules, stash-pop failures, orphan-branch corruption); this lesson covers the distinct failure mode where there is no tracked blob to restore from at all.

**See also:** ruff `--fix` recovery via `git checkout` on tracked re-export modules, `git stash` baseline-comparison hazard, docs-branch canonical-script-only rule, CLAUDE.md §4 Agent Workflow Rules (RED-before-GREEN TDD), shared `agent_workflow_guidelines.md` #6 (formatting-only commit diff inspection).


## 97. Do Not Explicitly Omit Plan-Prescribed Behavior Without Amending the Plan First

**Principle:** Family C (Plan adherence)


When a plan explicitly prescribes a behavior in its Gist or task steps (such as emitting an aggregate warning or summary after a loop), the implementer must not intentionally omit that behavior based on a local judgment call. If the implementer believes the behavior is redundant, harmful, or incorrect, they must halt and ask the user to amend the plan before proceeding. Explicitly skipping the step creates a contradiction between the plan's authorized design and the implementation, which will be caught in review as a plan-adherence failure.

**Why this matters:** The plan is the authoritative design contract. The reviewer verifies the implementation against that contract. An unauthorized omission forces the reviewer to flag it as a Blocker/High finding because the delivered code is structurally missing a required side effect. The time saved by skipping the step is lost to the subsequent review-and-fix cycle.

**Required behavior:**
1. Trace every prescribed side effect (logs, warnings, summaries, state mutations) from the plan's Gist and task body into the implementation.
2. If you intend to omit a prescribed step because you judge it incorrect, do not proceed silently. Surface the disagreement to the user and request a plan amendment.
3. If the plan remains unchanged, implement the step exactly as prescribed.

**Shape trigger (when to suspect this family):** A plan task instructs "emit an aggregate summary warning when the list is non-empty", but the implementation finishes the method without emitting it; the implementer leaves a comment or just skips it because "it seemed noisy".

**Example (2026-06-23 filter-transaction-fees plan):** The plan's Gist Step 7 required an aggregate summary warning after suspect fee events were surfaced. The implementer explicitly omitted it. The r1 code review caught the omission because it contradicted the plan, recording a High finding. The fix required adding the missing `logger.warning` loop at the end of `_surface_suspects`.

**See also:** `plan_quality_guidelines.md` (adherence to the plan).

---


## 98. Trace All Investigation Examples, Not Just the First One

**Principle:** Family A (Equivalence-class coverage)


When a user provides multiple examples to investigate (e.g., a list of missed transactions or false positives), trace and document **all** of them in the resulting analysis artifact. Do not stop after analyzing the first example.

**Why this matters:** A single example only represents one cell of an equivalence class. If the user provided multiple examples, they often belong to *different* equivalence classes with different root causes. Stopping at the first example assumes the others fail for the exact same reason, leaving the subsequent gaps undiscovered and unfixed until a future iteration.

**Required behavior:**
1. Read the user's prompt carefully to count how many examples were provided.
2. In the investigation document or feature note, create a section for each example.
3. Trace each example through the source data and identify its specific failure mode.
4. Ensure the proposed fix addresses all identified failure modes, not just the one from the first example.

**Shape trigger (when to suspect this family):** A user asks "why are these 3 transactions doing X?", the agent explains the mechanism for the first transaction, concludes the investigation, and the user responds "but what about the other two?"

**Example (2026-06-24 missing-items investigation):** The user provided three examples of records not being processed (Alpha, Beta, Gamma). The initial investigation traced only the Alpha example (an embedded record in an aggregated row) and concluded the analysis. The user had to point out that Beta and Gamma were missing. A full trace revealed Beta failed due to a co-occurrence guard (`event_count >= 2`), and Gamma failed due to a missing configuration key. All three were distinct gaps requiring different fixes.

**See also:** tax-reporting "Probe the Canonical URL Before Assuming an Official Source Is Unavailable" (data trace verification).

---


## 99. Verify Aggregation Before Concluding Data is Missing

**Principle:** Family H (Verify the real thing, not the abstraction)


When verifying a user's claim that a specific numerical amount from an output report cannot be found in the source data, verify whether the output report row is an aggregation (e.g., a daily sum) before concluding the data is missing.

**Why this matters:** Searching the unaggregated source data for an exact aggregated sum will always fail. If the agent agrees with the user that the data is missing without checking for aggregation, the investigation chases a phantom bug instead of explaining the correct behavior of the report.

**Required behavior:**
1. When asked to locate an output amount in the source, first check the reporting pipeline to see if the output level aggregates multiple events (e.g., daily totals, grouped by asset/platform).
2. If the output is aggregated, do not grep the source for the exact sum.
3. Instead, find the component rows in the source that share the aggregation keys (date, sku, etc.) and demonstrate how their sum matches the output.

**Shape trigger (when to suspect this family):** A user points to a report output row with an amount (e.g., 1.10) and says "I don't see a single transaction matching this amount in the source data".

**Example (2026-06-24 totals investigation):** The user pointed out a row with 1.1 and said "I don't see a single transaction matching this amount". The agent simply grepped the source for 1.1 and failed. In reality, the 1.1 was a daily aggregate of two 0.55 transactions. Breaking down the aggregate would have correctly explained the provenance of the number rather than falsely agreeing it was untraceable.

**See also:** #73 (trace affected authoritative-source row back to its upstream source row).



## 100. Test Fixtures Must Reflect Domain Defaults to Avoid Masking Bugs

**Principle:** Family H (Verify the real thing, not the abstraction)


When logic depends on falling back to a default value for generic cases (e.g. `default_ceiling` for generic L1 chains), test fixtures must not provide explicit overrides for the items under test. Doing so bypasses the fallback logic in the test, masking bugs where the production code fails to apply the default correctly.

Test fixtures representing domain configuration should mirror the structural intent of the real configuration: if the real config defines explicit exceptions and relies on the default for everything else, the test fixture should do the same. Tests verifying the default behavior should use an implicit item, not a mock that explicitly overrides it.


## 101. Distinguish Intentional vs Suspicious Ignored Items in Logging

**Principle:** Family G (Data-loss observability)


When a processing pipeline ignores or drops items, distinguish between *intentional/whitelisted* exclusions (e.g., explicitly tagged embedded fees) and *suspicious/unexpected* exclusions.
Log the intentional exclusions at `logger.info` and reserve `logger.warning` for items that fall outside known safe patterns.
Logging known, safe exclusions as warnings creates noise and misleads the user into thinking there is a data quality issue or missing data, whereas using `INFO` properly documents the expected behavior.


## 102. Unlisted Exclusion Candidates Must Fall Back to Suspect Surfacing

**Principle:** Family G (Data-loss observability)


When extracting items to exclude them from main processing (e.g., fee filtering), items that fail the exclusion whitelist must not be silently dropped. If they are not processed as normal items and do not qualify for exclusion, they must be yielded as suspect items so the user can review them manually.


## 103. Avoid Brittle Type Hint Zipping in Dataclass Iteration

**Principle:** Family D (Typing and invariants)


Using `zip(..., strict=True)` to pair `dataclasses.fields()` with `typing.get_type_hints().values()` is brittle. `get_type_hints()` includes non-field annotations (like `@property` or other class-level descriptors), which breaks the 1:1 length and ordering assumptions of `zip`. Always use dictionary lookups (`hints.get(field.name)`) when mapping type hints to dataclass fields.


## 104. A Locally-Archived Official Source Outranks a Conflicting External Secondary Source

**Principle:** Family H (verify the real thing, not the abstraction)


When an external or secondary web source appears to CONFLICT with a value the repo already derives from a locally-mirrored official source (an archived specification, contract, schema, or standard PDF under `docs/maintenance/.../official/`), the archived official source is authoritative. Do not escalate the discrepancy as a competing "repo conflict" or treat the unarchived secondary claim as a peer; resolve in favour of the official archive, and if the secondary claim was recorded anywhere in the repo, downgrade or remove it. The deeper error is granting a non-archived secondary source equal standing to an archived primary source.

**Example (2026-06-24 specification review):** During research, an external web claim asserted that one variant of a feature is reported under a specific category. This contradicted the repo's own routing hint. Rather than weighting the external claim equally, verifying against the repo's archived official specification PDF confirmed the repo was correct: the variant the repo routes to category A, and only a different variant routes to category B. The "conflict" was a phantom created by trusting a secondary source over the local official archive.

**Distinguishing from #72 and the AGENTS.md source-preference rule:** Lesson #72 mandates verifying a plan-time claim (path, line, field, function shape) against actual source BEFORE depending on it. The AGENTS.md hard rule ("prefer authoritative PDFs over raw HTML; reuse local mirrors") governs what to FETCH and consult. This lesson covers the narrower conflict-resolution decision: what to do once a secondary source already DISAGREES with an archived official source. The fix is a source-authority judgment (official archive wins outright), not a verification step or a fetch preference.

**How to apply:** Before writing "the repo conflicts with source X" or "this is unresolved," check whether the repo already archives an official source for the claim. If it does, the official archive settles it; cite the archived file and form field, and do not record the secondary claim as a competing position.

---


## 105. "The code emits value X" only proves X is correct for the modeled subcase; a binding source can introduce a discriminator the code does not model.

**Principle:** Family H (verify the real thing, not the abstraction)


When verifying that a classification or routing the code produces is "correct," confirming the code path emits a given section/code/value is NOT sufficient. The verifying authority (a binding spec, regulation, contract) may condition the correct answer on a discriminator the code does not branch on at all. In that case the emitted value is correct only for the modeled subcase (or a default), and is wrong for every other value of the unmodeled dimension. The deeper error is equating "the pipeline emits X consistently" with "X is the correct output value."

**What happened (2026-06-24 routing review):** A doc-review round "confirmed" a domain routing against the source code: the entry emits a fixed routing hint and operation code, and the live workbook header reads them back, so the round declared the repo correct. But the binding authority the routing rests on splits the destination on a discriminator the code never reads: the customer/peer's region (region X routes to one category; region Y routes to another). The actual records are region Y, so the workbook's emitted hint is wrong for the actual case; the code emits it unconditionally because it does not model region at all. Verifying "the code emits that value" proved only that the region X subcase is wired, not that the value is the correct one.

**General rule:** When a review or verification cites a binding authority (spec, regulation, contract) as the basis for a value the code produces, check whether that authority conditions the answer on a dimension the code does NOT branch on (a property of the peer, the item, the date range, the locale, the subtype). If the authority adds a discriminator the code ignores, the emitted value is conditional, not authoritative, and must be reported as "correct only for the modeled subcase" until the code models the dimension. Do not let a green "the code emits X" check close a correctness question that the authority answers conditionally.

**Distinguishing from tax-reporting "Probe the Canonical URL Before Assuming an Official Source Is Unavailable" and #72:** tax-reporting "Probe the Canonical URL Before Assuming an Official Source Is Unavailable" requires tracing the user's specific case end-to-end through the pipeline (data-flow verification). #72 requires verifying a plan-time claim against actual source before depending on it. This lesson is the upstream failure: the verification correctly traced the code path AND read the authority, but stopped at "code emits X" without asking whether the authority makes X depend on something the code does not compute. The fix is a discriminator-coverage check against the cited authority, not a deeper data trace.

**How to apply:** Whenever a correctness verdict rests on "the code emits value V" plus "authority A says V is right," enumerate the conditions/branches A attaches to V (read the ruling/statute's full conditional, not its conclusion). For each condition, confirm the code actually computes and branches on that dimension. Any condition the code does not model downgrades the verdict to "V is correct only when <condition> = <modeled value>"; flag the unmodeled discriminator as a separate implementation decision (see #137 for propagating the corrected text across surfaces).

---


## 106. A corrected domain rule is often echoed in multiple rendered surfaces; grep the stale string across the corpus and fix every surface in one pass.

**Principle:** Family D (single source of truth)


A single domain rule (a scope limit, a routing decision, a threshold-based exclusion) is frequently rendered in more than one place: the emitted output assumptions text, the decision-point doc, the rules doc, and sometimes a constant in code. When a review finding flags the rule as stale in ONE location, the same stale wording typically survives in the sibling surfaces. Fixing only the named file leaves the corpus internally contradictory: the code/docs the user actually relies on still state the old rule.

**What happened (a category-specific exclusion rule):** A review finding flagged the stale "long-term (>=365 days) excluded" wording for the category-specific item in the assumptions text (the assumptions module). The same stale claim also lived in the decision-points doc (the "guidelines" block, two lines) and in the domain rules doc (a domain-rule code that applied the base-item 365-day exclusion to the category-specific item). Correcting only the assumptions text would have left two authoritative docs still telling the user to exclude long-term category-specific entries. The fix had to touch all three surfaces plus their tests, with the same corrected rule (no 365-day exemption for the category-specific item; the exclusion rule is scoped to the base item only).

**General rule:** When you correct or invalidate a domain rule in response to a finding, treat the stale string as a token to grep for across the whole corpus (source code, emitted-text constants, decision-point docs, rules docs, tests) and correct every surface in the same pass. A review finding names the site the reviewer happened to read; the rule almost certainly propagates beyond it. Do not close the finding until a corpus-wide grep for the stale wording returns nothing.

**Distinguishing from #83 and #1540:** #83 greps ALL test files for stale assertions after a data-flow semantics change (test-scope). #1540 greps the package to count the true scope of a code-review duplication finding before acting (review-reception scope). This lesson is the doc/surface-propagation analog: the trigger is correcting a RULE (not changing data flow or triaging a duplication), and the target is every rendered/doc surface that echoes the rule text, not just tests or code sites. The preventive action (corpus-wide grep for the stale token before closing) is the shared shape.

**How to apply:** After correcting a domain rule, run `grep -rn "<stale wording>" src/ docs/ tests/` (and any emitted-text constants). For each hit, either apply the same correction or confirm the hit legitimately still applies the old rule. Only close the finding when the grep is clean. Pair with #136: if the correction came from a binding authority, also confirm the corrected rule is not conditional on an unmodeled discriminator before propagating it.

**Witness (vocabulary migration in shared docs, gold-source consumer surface):** The same shape applies when a shared-doc gold source is renamed and consumer files echo the old token in EXAMPLE tables. After the review-skill gold source (`agents/skills/review-staging/SKILL.md`) renamed its example-table columns `Agent`/`Agent severity` to `Worker`/`Worker severity`, three consumer skills (`review-plan`, `review-confluence-doc`, `rf-design`) still carried the old column labels in their `### Discarded findings` / `### Severity calibration` example tables. The drift survived a per-file diff inspection because the stale headers sat in pre-existing UNCHANGED context lines (a `git diff` does not surface them); only a full-file grep for `| Agent |` / `Agent severity` against the new vocabulary caught it. The prescribed fix in "How to apply" (grep the stale token across the corpus) is the same; the example-table case adds the watch-out that a diff-based review is blind to stale lines the migration did not touch, so the grep must run over file CONTENTS, not over a diff. See the 2026-07-27 five-worker-review-panel plan Task 3 inspection log.

---


## 107. When a Validator Rejects Input That Is Valid Under Your Assumed Model, Verify the Validator's Actual Key Before Hypothesizing Hidden Data

**Principle:** Family H (verify the real thing, not the abstraction) - model revision over evidence invention.


**Trigger:** An external system's validator/constraint (portal form, DB unique index, API dedup, build rule) rejects input that is valid under the model you have assumed for how that validator decides. The output looks correct to you, yet it is refused.

**Rule:**
- When observation contradicts your prediction, the bug is more often in your MODEL of the system than in an unseen extra record. Do not reconcile the contradiction by inventing hidden data ("there must be an 8th row I cannot see").
- First verify the validator's ACTUAL key/constraints: which fields the form exposes, its documented dedup/unique semantics, or the real index columns. Confirm the key composition from the system itself (field list, schema, docs) before reasoning about why rows collide.
- Prefer revising the model (the key is narrower than assumed) over revising the data (positing invisible duplicates). Only after the key is confirmed should you search for genuine duplicates that collide on the confirmed key.

**What happened (2026-06-26 form-section validation):** An external portal rejected a section entry with a "duplicate line" error. I assumed the dedup key was a broad four-field tuple (code + region + gross + tax), noted none of the visible rows collided on those four fields, and therefore told the user there must be a hidden duplicate row, asking them to locate it. The real cause (found by the user): that section exposes NO per-source field, so the actual dedup key is the narrower (code + region); the five same-code/same-region rows collide by design and must be aggregated (see #142). I should have questioned my assumed key the moment the visible rows did not collide on it, rather than positing invisible data.

**General rule:** "My model predicts no collision, but the validator reports one" is evidence that the model of the validator is wrong, not that extra records exist. Verify the validator's real key/constraints from the system before hypothesizing unseen inputs.

**Distinguishing from #136 and #72:** #136 is about the CODE's model missing a discriminator that a binding authority introduces. #72 is about verifying a plan-time claim against source before depending on it. This lesson is about the AGENT's model of an EXTERNAL validator being wrong, and the specific anti-pattern of inventing hidden evidence to preserve a mistaken model instead of confirming the validator's actual semantics and revising the model.

---


## 108. When a Plan Changes a Function Signature, Enumerate Callers Across ALL Test Tiers, Not Just the Dedicated Test File

**Principle:** Family A (Equivalence-class coverage) - the caller-side analog of #83.


**Trigger:** A plan task adds a REQUIRED parameter to an existing function (or removes/renames one), especially when flipping an optional parameter to required to make a forgotten call site fail loudly. The task's test-impact inventory lists the callers to update.

**Rule:** A function's dedicated test file (e.g. `test_section_sheet.py` for `write_section_sheet`) is NOT an exhaustive caller list. Functions with a dedicated unit-test file are frequently also called from e2e/integration tests that exercise the full workbook/report path. When a plan makes a parameter required, enumerate every caller across the ENTIRE test tree (`grep -rn "<func_name>(" tests/`), including `tests/unit/`, `tests/integration/`, and `tests/end_to_end/`. Each unlisted caller breaks with `TypeError` at execution and only surfaces in a tier the plan did not run.

**What happened (2026-06-26 routing-correctness plan, review round r5):** The plan made `region` a REQUIRED param on `write_section_sheet`. Its P0 test-impact inventory counted "~24 callers" - all in `test_section_sheet.py` - and missed 2 production-shaped callers in `tests/end_to_end/test_section_separation.py` (lines 1007, 1049). Those e2e callers were in a file the plan's A4 GREEN step explicitly runs, so they would have broken the GREEN run. The review caught it; the fix was to add the 2 e2e callers to P0's disposition (passing the existing `build_region()` fixture the e2e file already imports).

**Why this happens:** The plan author grepped or recalled callers from the function's own test module, which holds the bulk of calls, and stopped there. The e2e tier calls the same function through the real output-building path but is mentally filed under "category separation," not "category sheet signature." A focused test run on the dedicated file passes; the missed caller only fails when the broader tier runs.

**Required behavior:**
1. When a plan task changes any existing function signature (new required param, removed/renamed param, optional-flipped-to-required), the test-impact step MUST include `grep -rn "<func_name>(" tests/` and group hits by tier.
2. Record the per-tier caller count in the inventory (e.g. "~24 unit + 2 e2e"), not a single total attributed to one file.
3. For e2e/integration callers, reuse the region/fixture helper that tier already imports (e.g. `build_region()`); verify the helper exists in that file before prescribing it.

**Distinguishing from #83:** #83 is the assertion-side grep (a data-flow change breaks assertions referencing a data identity tuple; grep all test files for those assertions). This lesson is the caller-side grep (a signature change breaks call sites; grep all test files for callers of the changed function). Same hazard shape - a sibling test in another tier is forgotten - different object (callers vs assertions) and different grep target (function name vs data identity).


## 109. A Pure-Helper Unit Test Going GREEN Does Not Prove the Production Caller Invokes It

**Principle:** Family H (Verify the real thing, not the abstraction) - the wiring-coverage analog of tax-reporting "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag".


**Trigger:** A plan extracts a computation into a pure helper (e.g. `_route_for(country, peer_country) -> (category_hint, routing_code)`) and a production call site must be wired to invoke it, replacing a stale hardcoded default at that site. The plan's RED task writes helper-direct tests AND a separate construction-path test that drives the real producer; the GREEN task adds the helper and wires the site.

**Rule:** Direct unit tests for a pure helper prove only that the helper returns the right value. They do NOT prove the production caller invokes the helper. The caller can continue emitting a stale default (an unconditional `category_hint="CATEGORY_A"` / `routing_code="A1"` baked into the entity, or a constructor argument the caller still hardcodes) while every helper-direct test is GREEN. When the goal is "the production entry carries the resolved value," at least ONE test must drive the real production construction site (feed the caller's inputs and assert on the object the caller builds), not just call the helper. A suite with only helper-direct tests would go GREEN while construction still omits the routed fields - false GREEN.

**What happened (2026-06-26 routing-correctness plan, Task A1 RED):** The `TestRouting` RED suite deliberately split coverage: three cases called the not-yet-existing pure helper `_route_for(...)` directly (RED via `ImportError`), and one case (`test_peer_in_region_y_gets_category_b`) drove the real `_split_authoritative_index(authoritative_rows, calculated_entries, region)` construction site with a synthetic authoritative-source row whose identifier resolved to a region-Y peer. The construction-path case was the single load-bearing guard: its RED was an `AssertionError` (`'CATEGORY_A' == 'CATEGORY_B'`), proving the construction RAN but emitted the hardcoded default - i.e. the helper is not the only thing that must change; the wiring must change too. If only the helper-direct cases existed, Task A2 could have added the helper and flipped all three to GREEN while `_split_authoritative_index` still constructed `RoutedEntry` with the default, and the suite would pass for the wrong reason.

**Why this happens:** Helper-direct tests are cheaper to write (no fixture assembly, no region wiring), so a plan author defaults to them. They fully cover the helper's branches but say nothing about the caller. The caller's stale default is usually a field default on the entity dataclass plus (optionally) an explicit constructor argument the caller still passes; both survive a helper-only GREEN. The failure mode is "all helper tests pass, production still wrong" - a false GREEN that the focused test run never challenges.

**Required behavior:**
1. When a plan extracts a value-resolving helper AND the goal is that a production caller emits the resolved value, the RED suite MUST include at least one construction-path test that drives the real producer and asserts on the object it builds, not only helper-direct tests.
2. The construction-path test must be capable of failing for the wiring-specific reason (stale default still present), not only for the helper-missing reason. An `AssertionError` (value mismatch at the built object) is the right RED signature for the wiring case; an `ImportError` is acceptable for the helper-direct cases.
3. Before declaring GREEN, confirm the construction-path case flipped from its wiring-specific RED (value mismatch) to GREEN - not just that the helper-direct cases pass.

**Distinguishing from tax-reporting "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag":** tax-reporting "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag" is "an extracted helper needs DIRECT unit tests, not only indirect integration coverage" (the helper itself is under-tested). This lesson is the inverse: "the helper IS unit-tested and passing, but the production caller's wiring is unproven" (the caller is under-tested). tax-reporting "Branch on the Discriminator When Synthesising a Reason for a Multi-Cause Flag" says add helper tests; #147 says add a construction-site test alongside them. Both can apply to the same extraction; they protect opposite ends of the call.


## 110. When a Field's Aggregation Strategy Changes, Re-Scope the Guard That Observed the Old Strategy's Failure Mode

**Principle:** Family G (Data-loss observability) - the production-side analog of #107's test-side re-scoping rule, paired with #90's guard-adding rule.


**Trigger:** A plan task changes how a field is rendered/aggregated in a way that invalidates the trigger condition of an existing observability guard. Specifically: the field was previously ASSUMED constant across a group and read from `entries[0]` (or `first`), guarded by a #90-style heterogeneity check (`len(distinct) > 1`); the change moves the field to per-row rendering (each row carries its own value), so "heterogeneity across group members" is no longer a failure mode at all - it is the intended design. The old guard's trigger can never fire under the new design, so deleting it loses observability without replacing it.

**Rule:** When a refactor removes the `entries[0]` / `first` read for a field (because the field is now per-row), the #90 heterogeneity guard that protected that read is NOT simply deleted. Its observability must be re-scoped to the NEW failure mode the per-row design introduces: a row that failed to resolve the field and rendered blank (or a sentinel) under the region/tenant where the field is required. The re-scoped guard fires when (a) the sheet runs under the region that requires the field and (b) any rendered entry has a blank/unresolved value for that field. The old guard's positive/negative test pair is replaced by a new pair targeting the new condition (blank-under-required-region warns; all-resolved or a non-requiring region does not).

**What happened (2026-06-26 routing-correctness plan, Task A4 GREEN):** The specialized-section sheet previously rendered Category / Code / Subtype as a single row-2 detail line derived from `entries[0]`, guarded by a `distinct_constant_tuples` heterogeneity check (#90, from the 2026-06-16 review). A4 moved Category and Code to per-row columns (each entry carries its own route), so "the group disagrees on the constant" became meaningless - disagreement is now the point. Deleting the `distinct_constant_tuples` guard outright would have left no observability for the new failure mode: a region-X entry whose route failed to resolve and rendered an empty Category cell. A4 re-scoped the guard to warn when the sheet renders under region X and any entry has `category_hint == ""`, with a fresh positive/negative test pair (`test_blank_category_under_region_x_warns` / `test_no_blank_category_warning_when_routes_resolved`).

**Why this happens:** The #90 guard and the field's aggregation strategy are coupled - the guard observes the strategy's specific failure mode ("the assumed-constant field disagrees across members"). When the strategy changes, the guard's trigger condition describes a state that can no longer occur. A refactor focused on the rendering change treats the guard as dead code and removes it; the new failure mode (unresolved/blank under the requiring region) is only apparent if the author asks "what is the new shape of invalidity this field can take?"

**Required behavior:**
1. When a refactor removes an `entries[0]` / `first` read for a field (moving it to per-row or per-entry rendering), audit every guard whose trigger condition depended on the old strategy. A guard that checked `len(distinct_constant_tuples) > 1` (heterogeneity) cannot fire under per-row rendering and is dead.
2. Do NOT delete the dead guard without replacing its observability. Identify the new failure mode the per-row design introduces (typically: an entry that failed to resolve the field and rendered blank/sentinel under a region that requires it).
3. Re-scope the guard to the new condition: fire on (region-requires-field AND any-entry-blank), not on (group-members-disagree). Gate on the region config so a non-requiring region does not false-warn.
4. Replace the old guard's test pair with a new pair targeting the new condition: a positive test that constructs the new failure (blank-under-requiring-region) and asserts the warning, plus a negative test (all-resolved OR non-requiring-region) that asserts silence. The negative test defeats a trivial unconditional `logger.warning`.

**Distinguishing from #90 and #107:** #90 says ADD a heterogeneity guard when you take `entries[0]` for an assumed-constant field. This lesson #148 says RE-SCOPE that guard when the field stops being assumed-constant (the old trigger is dead; the observability must move to the new failure mode). #107 is the test-side analog (re-scope a TEST assertion when a fixture flips an orthogonal signal); this is the production-side analog (re-scope a PRODUCTION guard when the field's strategy changes).


## 111. Test Class Names Must Match pytest's `python_classes` Pattern, Else They Are Silently Deselected

**Principle:** Family A (Verify the real thing, not the abstraction) - the collection-configuration analog of #8's type-annotation specificity.


**Trigger:** A plan task prescribes a pytest test class by a specific name (e.g. `RoutingTest`), or an author names a new test class without checking the project's `pyproject.toml` / `pytest.ini` collection config.

**Rule:** A pytest class is only collected if its name matches the configured `python_classes` pattern. This repo configures `python_classes = ["Test*"]` (verified at `pyproject.toml`), so `RoutingTest` (suffix `Test`) is NOT collected - every case in it is silently deselected, and a RED run reports "0 failed" because the cases never executed. A class named `TestRouting` (prefix `Test`) IS collected. Before writing or naming a new pytest class, read the `python_classes` setting; when a task body fixes a class name, conform to the configured pattern (rename to `Test*`) rather than the task's literal name, and record the deviation in the implement log. Confirm collection with `uv run pytest <file> --co -q | grep <ClassName>` or `-k <token>` returning the expected count before relying on RED output.

**What happened (2026-06-26 routing-correctness plan, Task B1 RED):** The B1 task body named the new class `RoutingTest`. The repo's `pyproject.toml` restricts collection to `python_classes = ["Test*"]` (the existing sibling class `TestCategoryRouting` conforms). `RoutingTest` is deselected under that config: `uv run pytest -k Routing` returned "363 deselected" with the 17 new cases never running, which would have produced a false "RED achieved" signal (no failures) if not caught. Renaming to `TestRouting` made `-k Routing` select all 17 cases, which then RED correctly on the real contract (`TypeError: ... got an unexpected keyword argument 'country'`).

**Why this happens:** The default pytest behavior collects any `Test*` class, so an author assumes any name containing "Test" is collected. A project that narrows `python_classes` to an exact prefix list silently excludes suffix and infix variants. The failure mode is invisible: the run reports deselection, not error, and a RED check that sees "0 failed" can be mistaken for "not yet broken" rather than "not collected."

**Required behavior:**
1. Before writing a new pytest class, read `python_classes` (and `python_files`, `python_functions`) in `pyproject.toml` / `pytest.ini`. Conform the class name to the configured pattern.
2. When a task body prescribes a class name that does NOT match the configured pattern, rename to the matching pattern (preserving the logical name and every assertion) and record the collection-mechanism adaptation in the implement log; do NOT change test intent.
3. After authoring, confirm collection: `uv run pytest <file> --co -q` reports the expected item count and `grep <ClassName>` (or `-k <token>`) matches the new cases. Never interpret "0 failed" as RED without first confirming the cases were collected.

**Distinguishing from #8:** #8 is about type annotations preserving static-analysis visibility. This lesson #149 is about pytest collection config preserving runtime visibility of test cases. Both are "the tool silently skips your work because of a configuration detail," but at different layers (type checker vs test runner).


## 112. When a Plan Changes Rendered Output Text, Grep All Test Tiers for Tests That Locate the Row by the Stale Label

**Principle:** Family A (Equivalence-class coverage) - the output-identity analog of #146 (signature-change caller grep) and #137 (stale-string echo across surfaces).


**Trigger:** A plan task changes the text a rendered report cell carries (e.g. a description/label column that previously held a synthetic internal label now carries an official code description, or vice versa). The task's test-impact inventory lists the test files to update, typically the unit and e2e tiers that exercise the renderer directly.

**Rule:** A plan that changes rendered output text must grep ALL test tiers (`grep -rn "<old label string>" tests/`) for tests that LOCATE a row by matching that cell's text, not only the renderer's dedicated unit tests. Integration tests frequently build a domain entity, render the full workbook, then find the resulting row on the report sheet by scanning for a hardcoded label string in a specific column. When the renderer starts emitting different text for that column (e.g. an official category-code description instead of a synthetic `"Service income (consulting, fees)"` label), the row-locator match silently fails and the test errors or false-fails - but only in the integration tier the inventory did not list. The dedicated unit test for the renderer was already re-scoped; the integration test using a different identification strategy (positional scan by label) was never in the inventory.

**What happened (2026-06-26 routing-correctness plan, Phase-2 validation):** Tasks B2/B3 mapped the section codes to official category codes, which changed the description cell rendered by `_write_other_income_subsection` from a synthetic `"Service income"` / `"Other income (fees)"` label to the official category-text (or blank for source types that do not resolve to a code). B3's test-impact inventory re-scoped the unit analog (`tests/unit/application/persisting/test_report_sheet.py`) and the e2e analog. It MISSED three integration tests in `tests/integration/test_excel_generation_integration.py` that located the row by `row[0] == "Service income"` or `row[0].startswith("Service")`. Those locators never matched the new official-text cell, so the integration tier failed in Phase-2 full-suite validation, after the plan tasks were already committed.

**Why this happens:** The integration tests use a different row-identification strategy than the unit tests. The unit test calls the renderer and asserts on the returned cell value directly; the integration test builds the entity, renders the whole workbook, then SCAN-locates the row by a hardcoded label string in a column. A plan author who re-scoped the unit tier (asserting the new cell value) does not automatically notice that a sibling integration test identifies the row by the OLD cell value. The grep target is the stale label string, not a function name, so a #146-style caller grep would not find it.

**Required behavior:**
1. When a plan task changes the text a rendered report cell carries, the test-impact step MUST include `grep -rn "<old label string>" tests/` across ALL tiers (unit, integration, e2e), in addition to any signature-based caller grep.
2. For each hit, distinguish a row-locator match (the test finds the row BY this string) from an incidental assertion (the test asserts the cell EQUALS this string). Both must be updated, but the row-locator case is the silent-failure hazard: the test does not assert the label, it USES it to find the row, so a mismatch produces a "row not found" error rather than a value-mismatch failure.
3. When re-scoping a row-locator, prefer STRUCTURAL identification (position relative to a subsection header, or a populated region cell) over a new label-string match, so the test no longer couples to a specific rendered string. If a string match is retained (e.g. to also cover description rendering), match a STABLE FRAGMENT of the official text (e.g. a distinctive word from the official category description) with a module-load drift guard (`assert fragment in get_section_description(code)`), not the full verbatim string.
4. Record the per-tier re-scope in the implement log: which tier used direct cell-value assertions (unit), which used structural row-location (integration after fix), and which used label-string row-location before the fix.

**Distinguishing from #146 and #137:** #146 greps for callers of a changed FUNCTION (grep target: function name); this lesson greps for tests that locate a row by a changed LABEL (grep target: the stale string). #137 is "a corrected domain rule is echoed in multiple rendered SURFACES; grep the stale string across the corpus" (production surfaces + tests together); this lesson is the test-only specialization where the stale string is a row-locator, not an asserted value - so the failure is "row not found" rather than "wrong value asserted." Same hazard family (a sibling in another tier/file is forgotten), different grep target and different failure signature.


## 113. Verify Classification-Determined Reachability Claims Against Source Data; a Plan Hedge Is a Verify Prompt

**Principle:** Family H (Verify the real thing, not the abstraction) - the data-side sibling of #72 (code-reality claims) and #136 (data-trace verification).


**Trigger:** A plan, design note, or review finding justifies a narrow mapping or an "X never reaches code path Y" claim by appealing to a CLASSIFIER that routes by a data attribute (asset category, type field, tag). The justification often hedges ("likely", "probably", "should only reach", "in practice only").

**Rule:** When a reachability claim depends on a classifier that keys off a data attribute, trace that attribute across real source rows before trusting the claim. A single row whose attribute differs from the assumed norm (e.g. a `type="REWARD"` row that is category A, not category B) reaches the supposedly-unreachable path and invalidates the assumption. Treat a hedge word in the justification as an explicit verify prompt, not a confidence statement: the author was unsure, so confirm it against source data.

**What happened (2026-06-28 review, finding 1):** The code-correctness plan narrowed a code resolver so only one type family maps to a specific code under the local configuration, leaving every other upstream type blank. Its B0 research justified this with: "the resolver is called only inside the active-bucket aggregator, which filters to the active bucket (category-A entries); category-B rows are in the deferred-bucket state and never reach the resolver, so **likely** only one family -> the code is reachable." The hedge hid an unverified assumption: the active-bucket classifier keys off the asset CATEGORY (a domain rule), independent of the upstream `type`. A row of category A with a non-mapped `type` is in the active bucket AND not in the mapped family, so it reaches the resolver and resolves to blank. The example report had exactly ten such rows. They were invisible until a review finding proposed failing-closed on the blank code and the full suite hit them. Grepping the source data for a category-A non-mapped-type row at plan time (or at B0) would have surfaced the gap and forced an explicit decision about how those rows resolve before the mapping shipped.

**Why this happens:** Classification routing reads as a solid boundary ("category-B types are deferred, so they never reach the active-bucket resolver") because it IS solid for category-B assets. The hole is the cross-product the author did not enumerate: a type that is USUALLY category-B but CAN be category-A. The hedge word is the tell - it marks the spot the author stopped enumerating cases.

**Required behavior:**
1. When a mapping/resolver is narrowed with a "type X never reaches here" justification, identify the classifier that gates reachability and the data attribute it keys on.
2. Trace that attribute across committed source/example data (`resources/source/`, fixture CSVs) for rows of the excluded type. If any row's attribute would route it INTO the supposedly-excluded path, the narrowing is unsound until that row's resolution is decided explicitly.
3. Read hedge words ("likely", "probably", "should only", "in practice") as verify prompts: restate the claim without the hedge and check it against source data.
4. When the verified mapping is deliberately narrow pending a legal-judgment call (here: the official wording of the mapped code plausibly covers a broader class, but extending it was deferred), record the EXACT official wording of the mapped code at the mapping site so a future maintainer can reason about coverage without re-deriving it from the PDF - otherwise a "never guess" narrow mapping reads as "the rule only covers the mapped type" when it is really "the rule is broad but only one type is verified so far."

**Distinguishing from #72 / #136 / #83:** #72 verifies plan claims about CODE structure; this lesson verifies claims whose truth depends on a classifier AND source DATA category. #136 is full data-trace verification across reports; this is the narrower trigger of a hedge-marked reachability assumption. #83 greps test files for stale assertions after a semantics change; the fixture-data grep in step 2 above is the input-side complement (the source data itself can encode the case that breaks the assumption).


## 114. Flipping an Error Contract Orphans the Superseded Strategy's Surface Across All Tiers - Remove It, Do Not Leave a Dual Mechanism

**Principle:** Family D (consistency / no drift) + the surgical-edits orphan rule. When a branching behavior changes from strategy A to strategy B, every tier that strategy A touched becomes dead the moment the flip lands. The "remove orphans your changes created" hard rule covers orphans inside the file you just edited; this lesson covers the WIDER grep: the superseded strategy's surface typically spans tiers the flip task did not open (a dataclass field defined elsewhere, a renderer `if`-branch in another module, a dedicated test), and leaving it produces a dual mechanism where only one branch is reachable.


**Trigger:** You change how a field/condition is handled - most commonly flipping an error contract from flag-and-continue (emit a review-flagged row) to fail-closed (raise), or the reverse. Also triggers on any behavior flip that replaces one strategy wholesale with another (e.g. "compute X inline" -> "compute X via helper"; "render field on a detail line" -> "render field per row").

**Rule:** After the flip, grep ALL tiers for the superseded strategy's surface and remove it: (1) the dataclass/entity fields that only the old strategy populated; (2) the renderer or conditional branches that only the old strategy reached (`if entry.<flag>:` blocks whose producer no longer sets the flag); (3) the dedicated tests that exercise the now-unreachable path. A codebase that carries the fields, renderer, AND test for strategy A while only strategy B is live is a drift trap - a future maintainer reads the entity/renderer contract and expects the old behavior, and the test green-lights dead code. Verify the orphaned surface is not shared with another live consumer before removing (grep readers of each field/branch across src/).

**What happened (2026-06-28 routing review round 4, finding 1):** Round 3 flipped the blank-code case from flag-and-continue to fail-closed (raise `FileProcessingError`), the user-approved decision (#156). The flip landed in `aggregate_active_bucket_entries`, but three tiers of the OLD flag-and-continue strategy were left in place: `AggregatedEntry.review_required`/`review_reason` fields (entities.py), two `if entry.review_required:` renderer blocks in `report_sheet._write_other_income_subsection` (type-specific "REVIEW:" override + red fill), and `test_other_income_renders_yes_reason_when_review_required`. Because the only producer that could set the flag now raised before constructing the entry, every produced entry carried `review_required=False` and the renderer blocks were unreachable - dead dual mechanism. Round 4 caught it; the fix removed all three tiers (fields, renderer blocks, test) plus two stale assertions in the aggregator's own tests. Crucially the OTHER `review_required` readers (the aggregated-totals sheet, the specialized-section sheet, the supplementary sheet) bind to different entities where the flag stays live, so the removal was scoped to the one entity only.

**Why this happens:** The flip task edits the producer (the aggregator) and verifies the new contract with a new test, so it goes green. The superseded strategy's surface lives in files the task never opened (the entity dataclass, a sibling renderer, a sibling test), so it is not in the task's diff and survives the commit. It then takes a later review round - or a maintainer confused by the dead contract - to notice.

**Required behavior:**
1. When you flip an error contract or replace a strategy wholesale, enumerate the tiers the OLD strategy touched: producer assignment, entity/dataclass fields, renderer/conditional branches, and tests.
2. Grep readers of each orphaned field/branch across src/ (`grep -rn "\.<field>" src/`) before removing, to confirm no OTHER live consumer still depends on it; remove only what is now unreachable.
3. Remove the dedicated test for the superseded behavior together with the behavior (a passing test for dead code green-lights the dead surface and is itself debt).
4. In code review, treat "the producer raises/never sets X, but a renderer/test still branches on X" as a finding to raise.

**Distinguishing from the hard "remove orphans your changes created" rule and #156:** The hard rule is about orphans INSIDE the file your edit touched (same diff). This lesson is about the WIDER, cross-tier orphan a behavior flip creates in sibling files the flip task did not open - it requires an explicit cross-file grep, not just cleaning up the file you edited. #156 is the DECISION of which error contract to use; this lesson is the CLEANUP of the superseded contract's surface once the decision flips it. #121 (byte-identical non-regression refactors must not add net-new side effects) is about not introducing NEW behavior in a refactor; this is about removing OLD behavior left behind by a contract change.


## 115. A Predicate That Compares to the Same Hardcoded Literal That Gates Entry to Its Branch Is Structurally Untestable for the Case That Would Expose Its Error

**Principle:** Family H (Verify the real thing, not the abstraction) - the testability-hazard analog of #147 (a passing helper test does not prove the caller invokes it). The hazard is structural unreachability disguised as coverage.


**Trigger:** A branch is guarded by a comparison to a hardcoded literal (e.g. `if field == LITERAL:`) and, INSIDE that branch, a second predicate compares a DIFFERENT field to the SAME literal (e.g. `if other_field == LITERAL:`). The code reads as if it handles both the matching and non-matching cases of the second field, but the outer gate makes the non-matching case unreachable for any input where the literal is wrong.

**Rule:** When two predicates share the same hardcoded literal - one as a branch-entry gate and one as a discriminator inside the branch - the inner predicate is structurally untestable under the input that would expose a bug in it. Concretely, if the inner predicate SHOULD compare the field to a runtime value (the reporting country, the configured tenant, the request origin) but instead compares it to the same literal used as the outer gate, the bug is unreachable: every input that enters the branch already satisfied `field == LITERAL`, so `other_field == LITERAL` is the only path ever exercised, and the `!= LITERAL` arm of the inner predicate is dead. The test suite can be fully green while the inner predicate is wrong, because no test can reach the arm where it would fail. Two corrections are required together: (1) the inner predicate must compare to the runtime value, not the literal; (2) the outer gate must be changed to something that admits the discriminating input (typically a decision-point flag or a runtime config field), otherwise the corrected inner predicate remains untestable. A test that exercises the corrected inner predicate under the formerly-unreachable input is mandatory to prove the bug existed and is fixed.

**Why this matters:** The code looks covered (both arms of the inner predicate are visible) but one arm is dead by construction. A reader who notices the inner predicate is wrong cannot write a failing test without first removing the outer literal gate; a reader who does not notice ships the latent bug. The coupling between the gate and the predicate is the root cause: as long as they share the literal, the branch is a coverage trap.

**Shape trigger (when to suspect this family):** You see a branch of the form `if x == K: ... if y == K: ...` where `K` is a literal (a region code, a tenant id, a magic string, a numeric constant), and `y` SEMANTICALLY should be compared to a runtime value of the same kind as `x` but drawn from a different source (the configured region vs the peer, the request tenant vs the resource owner). The two `== K` comparisons look parallel but encode different questions; the shared literal is the smell.

**General form:** When a guard literal doubles as a discriminator literal inside the guarded branch, the discriminator's "not equal" arm is unreachable and any bug in it is invisible. Decouple the discriminator to compare against the runtime peer value, AND change the guard to admit the discriminating input (flag/config), then add the test that was previously impossible to write.

**Example (2026-06-27 flag-based-dispatch plan, Task 2):** The locale router in `handler._route_for` was guarded by `if country.upper() != HOME_REGION_CODE: return "", ""`, and INSIDE the home branch the locale test was `if peer_country.upper() == HOME_REGION_CODE: # local`. The predicate SHOULD have compared `peer_country` to the record's own `country` (the local case is "peer is in the SAME region as the record"), but it compared it to the literal `"HOME"`. Under the literal gate, every input reaching the inner predicate already had `country == "HOME"`, so the inner predicate's `peer_country == "HOME"` vs `!= "HOME"` arms were the only paths exercised and the bug (`== "HOME"` vs `== country`) could never fire for a non-HOME record. Task 2 corrected the predicate to `peer_country == country` AND replaced the outer literal gate with `if not route_via_peer_region: return "", ""` (a decision-point flag), making the non-local-peer and non-HOME-local cases reachable for the first time. The targeted GREEN tests then exercised `('HOME','HOME',True)`, `('HOME','XX',True)`, AND `('YY','YY',True)` (a non-HOME record with a local peer), the last of which was structurally impossible to test under the old literal-gated form. See the Task 2 implement log, Invariant 2 and Command 2.

**See also:** #145 (region-specific output must be gated, not unconditional - the architectural principle; this lesson is the testability hazard a literal gate creates when a sibling predicate reuses the same literal), #147 (a passing helper test does not prove the caller is wired to it - same family, different failure mode), #51/#113 (the flag/config mechanism that decouples the gate from the literal).


## 116. A Test Deferred in Task N as Out-of-Scope Becomes Stale in Task N+1 When N+1 Changes the Contract the Test's Premise Rests On

**Principle:** Family A (Equivalence-class coverage) - the cross-task-boundary analog of #107 (re-scope a test when a fixture flips an orthogonal signal) and #150 (grep all tiers for a changed rendered label). The hazard is a test that is correctly OUT of Task N's scope but correctly IN Task N+1's scope, with no inventory line that bridges the two.


**Trigger:** A multi-task plan splits work such that Task N defers a test fix because the test lives outside Task N's file scope ("out of scope, defer"). Task N+1 changes the dispatch CONTRACT (the discriminating condition that gates a behavior - e.g. "non-HOME region blanks the field" becomes "flag-off blanks the field"). A test deferred in Task N whose premise rests on Task N's OLD contract silently goes stale under Task N+1's new contract, but the test was never in Task N+1's inventory because it was filed under Task N's scope.

**Rule:** When a task changes a dispatch CONTRACT (the condition that gates a behavior - region literal, flag value, enum discriminator, presence of a field), enumerate tests whose PREMISE rests on the old contract, regardless of which prior task originally owned them. A test deferred in an earlier task as "out of scope" does not stay out of scope once a later task changes the contract the test's premise assumes. The bridging step is mandatory: before declaring the later task GREEN, grep ALL tiers for tests that assert the OLD discriminating condition (e.g. `grep -rn "non.home\|non_home\|country.*YY\|country.*ZZ" tests/` when the gate moves from region-literal to flag), and for each hit ask "does this test's premise still hold under the NEW contract?" If the premise is now stale (the test still drives the old discriminating input but the old input no longer gates the behavior), re-scope the test to drive the NEW discriminating input (e.g. flip the flag off instead of setting a non-HOME region) and update its docstring to name the new gate. Record the cross-task re-scope in the later task's implement log.

**Why this happens:** The plan author files each test under the task that owns its primary file. When Task N defers a test as out-of-scope, that deferral is correct for Task N. But the deferral is recorded in Task N's log, not carried forward into Task N+1's inventory. Task N+1 then changes the contract, and the deferred test - which now lives in Task N+1's logical scope by virtue of the contract change - is never re-examined. Its premise ("a non-HOME region blanks the field") becomes stale ("the flag being off blanks the field"), and because the test still passes for the wrong reason (the flag defaults to on in the shared builder, so `country=YY` no longer blanks anything unless the flag is also flipped), the staleness is silent. The focused GREEN run on Task N+1's targeted classes passes; the stale test only fails when the shared builder's defaults change or when a full-suite run exercises the construction path.

**Required behavior:**
1. When a task changes a dispatch CONTRACT (not just a signature or a label - the discriminating condition itself), grep ALL tiers for tests whose premise names the OLD contract (`grep -rn "<old discriminator>" tests/`), including tests a prior task deferred as out-of-scope.
2. For each hit, decide: does this test still assert a LIVE property under the new contract, or does its premise need re-scoping? A deferred test is NOT exempt from this audit - deferral in a prior task does not survive a contract change in a later task.
3. When re-scoping, drive the NEW discriminating input (flip the flag, change the enum, remove the field) rather than the old one, and update the docstring to name the new gate so the next reader does not re-introduce the old premise.
4. Record each cross-task re-scope in the later task's implement log: which prior task deferred it, why the contract change re-scoped it, and what the new premise asserts.

**Distinguishing from #107, #146, #150, #157:** #107 re-scopes a test WITHIN a task when a fixture flips an orthogonal signal; this lesson re-scopes a test ACROSS task boundaries when a later task's contract change invalidates a premise the earlier task left in place. #146 greps callers of a changed FUNCTION; #150 greps for a changed rendered LABEL; both are same-task signature/text changes. #157 removes the orphaned surface a strategy flip leaves behind; this lesson re-scopes a SURVIVING test whose premise a contract change (not a strategy flip) silently invalidated. The shared hazard family is "a sibling in another tier/file is forgotten"; the distinct angle here is the cross-task dimension: the test was correctly out of scope for Task N and correctly in scope for Task N+1, with no inventory line bridging the two.

**Example (2026-06-27 flag-based-dispatch plan, Task 2):** Task 1 (RED) deferred two section-sheet tests - one in the section-sheet test file and one in the pipeline-integration test file - because they lived outside Task 1's allowed file list, and Task 1 only wrote RED tests (no contract change yet). Task 2 changed the dispatch CONTRACT from region-literal (`country == "HOME"`) to flag-based (`route_by_peer_region`). Both deferred tests had premises resting on the OLD contract: "a non-HOME region (`country="YY"`) blanks the category hint / routing code." Under the new flag-based contract, `country="YY"` no longer blanks anything - the shared region builder now defaults the flag `True`, so a `country="YY"` region with the flag on is a local-peer case that emits the local hint/code. Task 2 had to re-scope both tests: keep `country="YY"` but explicitly set `route_by_peer_region=False`, and update the docstrings to name the flag as the gate instead of the region. Without the cross-task grep, the staleness would have surfaced only as a full-suite failure attributed to a later task's config rather than recognized as Task 2's own re-scope obligation. See the Task 2 implement log, "## Changes" entries for the two test files.


## 117. A Wording-Pass Review Must Grep Method IDENTIFIERS, Not Only Docstrings and Rendered Messages

**Principle:** Family A (Equivalence-class coverage) - the review-pass analog of #159 (cross-task contract change) and #150 (changed rendered label). A wording/staleness review is itself a grep over the corpus; underscoping that grep's TARGET (messages + docstrings, but not identifiers) leaves the very staleness the review was supposed to catch.


**Trigger:** A plan's Task 4 (or equivalent "stale wording cleanup" gate) re-scopes tests for a renamed concept (e.g. region-literal dispatch becomes flag-based dispatch) and instructs the review to verify "no stale `non_home` / old-concept wording remains in docstrings or rendered messages." The review pass greps for the old concept string in docstrings and cell text, finds none, and clears the gate. The same tests' METHOD NAMES still encode the old concept because the grep TARGET excluded the identifier position.

**Rule:** A wording-pass review whose purpose is to catch residual references to a renamed concept must grep the old concept token across ALL positions where it can survive a rename: rendered cell text, exception messages, docstrings, comments, AND test/function/method IDENTIFIERS (the `def test_..._under_<old_concept>` names). Identifiers are a discovery surface for future readers and reviewers; a method name that names a concept the codebase no longer has is the same staleness the wording pass exists to remove, just at a position the grep target omitted. When the wording pass renames docstrings/messages, treat the method identifiers in the same files as in-scope by necessity: the grep is `grep -rn "<old concept token>" tests/ src/` with NO positional filter, then triage hits by position. A "clean docstrings and messages" result is not sufficient if identifiers were excluded from the search.

**Why this happens:** The review (and the plan task that prescribes it) scopes the grep to "user-facing and reader-facing prose" - docstrings, exception messages, rendered cell text - because those are the positions where stale wording misleads most visibly. Method identifiers are treated as structural scaffolding rather than wording, so they fall outside the grep's mental target. But identifiers that name a concept (e.g. `test_production_path_blanks_code_under_non_home`) are reader-facing too: a future reviewer scanning test names to estimate coverage reads "non_home" as a live category long after the gate became a flag, producing the false-confidence coverage signal #84 describes. The wording pass clears because the positions it scanned are clean; the staleness survives at the one position the scan never reached.

**Required behavior:**
1. A wording-pass review for a renamed concept must grep the old token with NO positional filter: `grep -rn "<old concept token>" tests/ src/` (covering messages, docstrings, comments, AND identifiers). Do not pre-filter to "docstrings and messages."
2. For each hit in an identifier position (function/method/class/variable name), treat it as in-scope for the wording pass: rename the identifier to reflect the new concept, OR confirm the identifier still names a live category and document why it survives. A bare "identifier is not wording" dismissal is not acceptable.
3. When the rename touches an identifier that is cross-referenced by exact name elsewhere (a docstring citing `def test_X` in another file, a test-selector command, a comment that names the method), grep for the old identifier as a string across the whole tree and update every cross-reference in the same wording pass; leaving one produces a stale name citation (#146 caller-grep family, identifier specialization).
4. Record in the review's worker log: the old token grepped, the positions found (messages / docstrings / identifiers / cross-references), and the renames applied. A wording pass that does not enumerate positions cannot prove identifiers were covered.

**Distinguishing from #84, #146, #150, #159:** #84 is a name-vs-body coverage gap WITHIN one test (name overclaims what the body asserts); this lesson is a name-vs-concept gap where the name survives a concept rename the body already absorbed. #146 greps callers of a changed FUNCTION signature; #150 greps for a changed rendered LABEL string; both are signature/text changes at production surfaces. #159 re-scopes a test's BODY and DOCSTRING across task boundaries when a later task changes the contract; this lesson catches the METHOD NAME that #159's body/docstring re-scope left behind, surfaced by the REVIEW pass rather than the implement pass. The shared hazard family is "a sibling position/file is forgotten"; the distinct angle here is positional (identifier omitted from a wording grep) rather than cross-file or cross-task.

**Example (2026-06-27 flag-based-dispatch plan, review round 1):** Task 4's stale-wording gate re-scoped test docstrings and messages for the region-to-flag dispatch rename and verified no `non_home` wording remained in docstrings or rendered text. The round-1 review re-grepped `non_home` across `tests/` and `src/` with no positional filter and found three METHOD IDENTIFIERS still carrying the old concept: `test_non_home_region_blanks_through_full_construction` and `test_production_path_blanks_code_under_non_home` in the pipeline-integration test file, and `test_no_blank_category_warning_under_non_home` in the section-sheet test file. Their bodies and docstrings had already been re-scoped by the flag-based-dispatch plan's Task 2 to drive the flag-off condition, but the method names were never renamed. The review's fix renamed all three to reflect the flag-based gate (e.g. `test_flag_off_blanks_through_full_construction`) and updated a fourth file where a docstring cross-referenced one of the old identifiers by exact name. The wording pass had cleared earlier because its grep target was implicitly limited to docstrings/messages. See the round-1 code-review staging doc (local) Findings summary, finding 2, and the address-review worker log.


## 118. A Wrong Constant That Fails Loudly Does Not Need a Pre-emptive Drift Detector Against Its Authority

**Principle:** Family D (Single source of truth) - a scoping refinement of #61/#67: the two-authorities-for-one-fact hazard is real only when the divergence is SILENT. A constant whose wrongness produces a visible, loud failure is categorically safe and does not warrant a pre-emptive consistency check.


**Trigger:** You have a named constant (a valid-value set, an enum mirror, a magic-number ceiling) whose authority is a separate canonical document (a family catalog, a spec, a config schema). You are about to add a pre-emptive automated check that parses the canonical document and asserts the constant matches it, to "prevent drift."

**Rule:** Before adding a pre-emptive drift detector, ask what failure mode a wrong constant produces. If a wrong constant causes a LOUD failure - the system rejects the offending input and names it (a validator rejects an unknown family letter with `invalid-family` naming the `#N`; a parser throws on an out-of-range code) - the detector is not load-bearing for safety: the wrongness surfaces the first time it matters, at a single visible point, and is fixed there. A documented constant plus a code comment naming the canonical authority is sufficient; route any pre-emptive check to Monitor. The detector IS load-bearing only when a wrong constant produces a SILENT wrong answer - the canonical document and the constant disagree, but the system happily emits a plausible-but-wrong result with no rejection (the hand-maintained derived index that drifts while the source stays correct; #61/#67). Distinguish the two: loud-failure duplication accepts a constant; silent-drift duplication demands a single source of truth or a detector.

**Why this matters:** A pre-emptive consistency check is itself a coupling between the constant and the authority's representation (a bullet-list parse, a heading shape, a filesystem path). That coupling has its own failure modes - the authority's prose gets reworded; the resolver's path needs `~`-expansion; the parse target changes shape - each of which becomes a new review finding and a new silent-degrade risk (the check silently no-ops when it cannot parse). Adding the detector to prevent drift can introduce MORE drift surface than it prevents, when the original failure mode was already loud. The single-source-of-truth principle (#61/#67) targets SILENT divergence; applying it to a loud-failure constant over-engineers the guard.

**Shape trigger (when to suspect this family):** You are writing `VALID_X = frozenset("AB...H")` with a comment "authority is spec #16-#22" and reaching for a `--selftest` that opens the spec file and asserts equality. Stop and ask: if `VALID_X` were wrong, would the next consumer fail loudly (reject + name) or silently (wrong output)? If loudly, the comment is enough; do not build the detector.

**General form:** Drift protection is warranted in proportion to the SILENCE of the wrong result. A loud failure is its own detector; do not build a second one whose own coupling costs more than the risk it covers.

**Example (2026-06-29 lessons-corpus-derived-index plan, r6):** The read-only lessons gate defines `VALID_FAMILIES = frozenset("ABCDEFGH")` whose authority is `coding_guidelines.md` #17-#25. Rounds r2 (Blocker #3) through r5 demanded an automated catalog-vs-`VALID_FAMILIES` `--selftest` check, and implementing it spawned five rounds of new Medium findings (a `~/`-expansion resolver gap, a bullet-list parse with no termination predicate, missing fixtures) - the detector's own coupling. r6 cut the check entirely: a wrong `VALID_FAMILIES` rejects the first tag of a new family letter with `invalid-family` naming the `#N` (a loud failure), so the detector was not load-bearing. The residual silent case (family REMOVAL) is negligible since the taxonomy only grows. See the r5/r6 review artifacts and the plan Design Invariant "Closed taxonomy."

**See also:** #61 (single source of truth - the silent-drift case this refines), #67, #13 (Simplify Unnecessary Complexity), #162 (the over-engineering signal that surfaced this cut).


## 119. A Review Loop Whose Finding Count Is Non-Monotonic Signals an Over-Engineered Mechanism - Cut It, Do Not Patch Its Edge Cases

**Principle:** Family A (Equivalence-class coverage) - the review-loop analog of "a passing test pins one cell; fix the class, not the cell." When each round's fix spawns NEW findings on the SAME mechanism, the mechanism is the wrong class; patching its edge cases keeps pinning cells.


**Trigger:** An adversarial plan or code review loop (the plans-skill "repeat until zero Blockers AND zero Medium" loop, or a `doing-code-review` pass) is not converging: each round confirms the prior round's findings resolved but surfaces new Medium/Blocker findings, and the new findings cluster on a mechanism that a PRIOR round ADDED as a fix or safety guard.

**Rule:** When review findings are non-monotonic - the count does not fall round over round, and new findings concentrate on a mechanism introduced in a recent round (a `.bak` + lock safety stack, a pre-emptive consistency check, a fallback resolver, a layered guard) - treat it as a signal that the mechanism is OVER-ENGINEERED for the problem, not that its edge cases need patching. Each safety layer you add carries its own edge cases (a lock needs correct acquire/release wiring; a `.bak` makes a false recovery claim; a resolver needs path expansion; a layered parse needs a termination predicate), which is exactly what generates the next round's findings. The proportionate response is to CUT or SIMPLIFY the mechanism (drop the lock and rely on a git-clean precondition; drop the pre-emptive check and rely on a loud failure per #161; collapse the fallback chain to a single documented constant) rather than patch the next layer of edge cases. Patching edge cases of a complexity layer produces its own edge cases; the loop does not converge.

**Why this matters:** The plans-skill review loop ("repeat until zero Blockers AND zero Medium") is correct as a TERMINATION criterion but says nothing about HOW to converge. Taken literally, it rewards patching - each Medium gets a targeted fix, the round clears, and the loop continues. When the findings are non-monotonic, that patching behavior is the trap: the fixes themselves are the source of the next round's findings, so the loop can run indefinitely (observed: r3=3 Medium, r4=4, r5=5, all clustered on two mechanisms r4 added). The non-monotonic trend is the diagnostic that distinguishes "the plan has N independent defects to fix" (monotonic decrease - keep patching) from "the plan has 1-2 over-engineered mechanisms generating N edge-case findings each" (non-monotonic - cut the mechanism).

**Shape trigger (when to suspect this family):** Across 2+ review rounds, the Medium/Blocker count is flat or rising AND the new findings name a mechanism introduced 1-2 rounds ago as a safety guard or fix. You find yourself adding a guard to fix a finding, then a guard for THAT guard's edge case next round. The fixes are getting more meta (lock-release wiring for a lock you added to prevent a race in a check you added to prevent drift).

**General form:** A review loop's finding-count trend is a signal, not just a score. Monotonic decrease = independent defects, keep patching. Non-monotonic with findings clustering on recently-added mechanisms = over-engineering; simplify or remove the mechanism rather than elaborate its edge cases.

**Example (2026-06-29 lessons-corpus-derived-index plan, rounds r3-r6):** The plan review loop ran r1, r2 (2 Blockers resolved), then r3=3 Medium, r4=4 Medium, r5=5 Medium - non-monotonic, with every new Medium clustering on two mechanisms r4 had added: an automated catalog-consistency `--selftest` check (whose resolver needed `~`-expansion, whose bullet-list parse needed a termination predicate, which needed fixtures) and an adopter `.bak` + done-lock safety stack (whose `.bak` made a false recovery claim, whose lock needed non-functional Python acquire/release wiring, whose `.tmp` write followed symlinks). r6 cut both mechanisms - the catalog check (a wrong constant fails loudly, #161) and the `.bak`+lock (a manual one-time tool needs only a git-clean precondition + atomic rename) - and the loop converged immediately (r6: Blocker=0, Medium=0, ready=yes). Six rounds of patching could not reach what one round of cutting achieved. See the r5 and r6 review artifacts.

**See also:** #13 (Simplify Unnecessary Complexity), #161 (the loud-failure constant cut, one of the two mechanisms), the `plans` skill review loop ("repeat until zero Blockers AND zero Medium" - the termination criterion this lesson refines with a convergence diagnostic).


## 120. A Plan/Doc Claim That a Mechanism Is "Inherited/Validated/Already Tested" Creates a Review Blind Spot for Exactly That Mechanism - Re-measure It, Do Not Trust the Label

**Principle:** Family H (Verify the real thing, not the abstraction) - the review analog of "do not trust names, summaries, or mocks; trace the actual data." A claim of validity is an abstraction standing in for the measurement; treating the claim as evidence skips the verification.


**Trigger:** A plan, design doc, or CR guard carries language asserting a mechanism is already proven without restating the test: "gate-core inherited," "validated by prior rounds," "fence-aware counting is specified and tested," "unchanged from the prior phase," "previously reviewed and clean." An adversarial review panel then declares the plan ready (Blocker=0, Medium=0) without re-exercising that mechanism.

**Rule:** When reviewing a plan or doc, treat every "inherited/validated/tested/unchanged" claim as a flag to RE-VERIFY the mechanism by exercising it against the REAL artifact it operates on, not as a reason to skip it. The areas a doc declares settled are the most likely place for a latent defect to hide, because the declaration itself suppresses re-measurement: each subsequent review panel reads the claim, treats it as proof, and points its attention elsewhere. "Skip findings the plan already addresses" applies to specific prior findings that were mitigated; it does NOT apply to mechanisms the plan merely asserts are proven. When a plan operates on a real file/schema/API, run at least one structural measurement of that artifact that the code's correctness depends on (fence-marker parity, key uniqueness, encoding, delimiter/count parity) - reading the source is necessary but is not the same as measuring the property the code relies on. A claim of validity is never a substitute for the measurement.

**Why this matters:** This defect evaded ~13 consecutive review rounds on the same plan and was caught only when one panel measured the real artifact. The plan under review asserted its gate's fence-aware tag parser was "inherited" and "specified and tested," and an early round had recorded "the fence-aware tag counting is specified and tested." Every later round read that and moved on. The real project file had an ODD fence-marker count (57; an unclosed code fence) - a naive toggle parser inverts its in/out-of-fence state and silently drops real tags, corrupting the gate, the adopter, and the migration classifier's strongest signal. No round caught it until one agent ran `grep -c` on the real file and asked "is this even?" The plan text was identical between the ready=yes round and the ready=no round that found it - the only difference was whether the panel measured the artifact or trusted the label.

**Shape trigger (when to suspect this family):** You are reviewing a plan/doc that builds on "prior validated work" (phased plans, RFC continuations, refactors, "inherit the gate core") and the doc asserts a mechanism is proven rather than showing the test. Or: a review loop returned ready=yes but the panel's findings describe only NEW change types and never re-probe the carried-over mechanisms. Or: you find yourself about to skip a section because the plan says it is "already handled."

**General form:** "Tested/validated/inherited" is a label, not evidence. A doc that asserts a mechanism is proven creates a review blind spot for exactly that mechanism, because the assertion instructs reviewers to skip the verification most likely to find a latent defect. The fix is asymmetric: re-measure the settled mechanisms (cheap - one grep, one measurement) and measure the real artifact's load-bearing structural properties, rather than re-asserting the doc's claims about them.

**Example (2026-06-29 lessons-corpus-derived-index plan, r1 vs r2):** r1 returned ready=yes (0 Blocker). r2, on the SAME plan text, found a Blocker: the gate's fence parser was specified as "track ``` toggling" and exercised only against a balanced-fence self-test, while the real `docs/maintenance/development_lessons.md` has 57 fence markers (odd - an unclosed `bash` fence at line 860), so a naive toggle drops a large fraction of the 157 real tags. Every prior round trusted the plan's "inherited/specified and tested" framing and never measured fence parity. r2's quality agent measured it. See the r2 review artifact; the fix (reset `in_fence` at each heading + an odd-fence self-test) is in the plan, and the `review-plan` and `plans` skills were updated to re-verify inherited claims and measure real artifacts.

**See also:** coding_guidelines.md #25 (Family H, the parent principle), the `review-plan` skill ("Inherited/validated claims are claims, not proof" + "Measure the real artifact"), the `plans` skill ("Do not make bare inherited/validated/tested claims"), #162 (a different review-loop failure mode: non-monotonic findings signal over-engineering).


## 121. A Transformation Engine's Output-Consistency Self-Check Cannot Detect Its Own Input Mis-Classification

**Principle:** Family H (Verify the real thing, not the abstraction) - the classification-correctness analog of #158 (a passing check proves reachability, not correctness) and #163 (a validity label is not a measurement). The hazard is a self-referential reconciliation that validates decision-APPLICATION, not decision-CORRECTNESS.


**Trigger:** You build (or review a plan for) a transformation engine - a token rewriter, a classifier, a matcher - that (a) decides a per-input action (rewrite / keep / remove) via a discriminator that EXCLUDES some inputs through a denylist or allowlist, and (b) self-checks by reconciling its OUTPUT against its OWN decision log (asserting every decided token was acted on consistently).

**Rule:** A self-reconciliation that compares the output stream to the engine's own decision log can only prove the engine APPLIED its decisions consistently; it CANNOT prove the decisions were CORRECT. When the discriminator mis-classifies an input (a denylist gap routes a non-target token as a target, or an allowlist gap drops a real target), the engine records that token under its WRONG decision and then "correctly" confirms it acted on the wrong decision - the check passes green over corrupted output. Mis-classification requires two INDEPENDENT-OF-THE-ENGINE fixes, not a stronger self-check: (1) build the exclusion set EMPIRICALLY from the real input corpus - case-insensitive where the data varies in case, enumerated by scanning the actual input, never recalled from memory - because a hand-constructed set misses real forms; and (2) make the mis-classification detector independent of the engine's own decisions: emit the distinct classification-CONTEXT vocabulary (the lead-in/keyword preceding each token the engine TREATED as a target, grouped by context) for a one-time human confirmation that no non-target context appears in the "treated as target" group. A decision log entry saying "renumbered-to-new" is the engine's assertion, not evidence the token was a target.

**Why this matters:** The reconciliation reads as a strong gate ("authoritative, exact, closes the blind spot") while proving nothing about classification correctness. An operator signs off on silent corruption because every check is green. The denylist-miss class is especially dangerous because it is invisible to BOTH the engine and its self-check - only an independent view of WHAT-WAS-CLASSIFIED-AS-A-TARGET surfaces it. The same logic dooms idempotency assertions ("a re-run produces no changes") on an engine whose first run already corrupted the input: a stable corrupted state is still corrupted.

**Shape trigger (when to suspect this family):** You are writing or reviewing a plan/spec for a transformation engine whose discriminator uses an exclusion set (a denylist of non-target lead-ins, an allowlist of target forms, a keyword negative-context) AND the design claims a self-check (reconciliation, audit, idempotency) "catches any miss" or "is authoritative." The smell is self-reference: the same engine that classifies the input also authors the list the check reconciles against.

**General form:** If entity E classifies inputs and then validates its output by reconciling against its OWN classification log, the validation proves consistency-of-application, not correctness-of-classification. Mis-classification corruption needs an INDEPENDENT detector: either an externally-grounded reference (the real input's distinct context vocabulary, confirmed by a human or a second source) or a positive specification of the target class the engine cannot itself have authored.

**Example (2026-06-29 lessons-corpus-derived-index plan, review round r6):** The migration engine rewrites in-corpus `#N` lesson citations and leaves NON-lesson process identifiers (`Rule #4`, `Finding #1`, `Design Invariant #2`) untouched via a process-prefix denylist. The r5 design claimed the "authoritative remap-driven reconciliation" (record every touched token old->action; assert none left at its old value unless action was removed/left-non-lesson) would "catch any future miss." r6 found this false on two axes: the denylist was case-SENSITIVE while the real corpus has lowercase `rule #6` and `finding #1`, and it omitted `Invariant`, so the load-bearing `Design Invariant #2` (line 2092) was mis-classified as a lesson and silently renumbered/removed; AND the reconciliation did not catch it, because the engine recorded `Design Invariant #2` as `renumbered-to-new` (a lesson) and then correctly confirmed it had renumbered that "lesson." The fix was case-insensitive matching + `Invariant` in the denylist + an INDEPENDENT backstop: the engine emits every distinct `<lead-in> #N` it discriminated as a lesson, grouped by lead-in, for a one-time operator confirmation that no process-id lead-in appears in the "treated as a lesson" group. See the plan Task 4 discriminator guard (v) and the r6 review Medium 1.

**See also:** coding_guidelines.md #25 (Family H, the parent principle), #163 (a validity label is not a measurement - the doc-claim facet of the same family), #158 (a passing check proves reachability, not correctness - the testability facet), tax-reporting "Use `get_args(hint)` Not `get_origin(hint)` for Precise Generic Type Dispatch in Config Loaders" and #93 (independent-detector siblings: a guard that fail-closes on a missing manifest, and a presence check that misleads when grounded on a transient/derived tree - both contrast a self-referential check with an externally-grounded one), tax-reporting "Standalone Withdrawals Tagged Cost/Loan Fee Represent Taxable Disposals; Distinguish from Validator/Network Fees Using TxHash Co-occurrence" (match by the real identifier, not a derived one - the matching facet of "verify the real thing").


## 122. A RED Test That Is Itself the Deliverable (Committed RED, Later-Task GREEN) Must Fail as a Clean Assertion Naming Its Resolution, Never as an Error

**Principle:** Family A (Discriminating tests) cross with the TDD-process family of #57/#81. The RED phase has two distinct roles: in #57 it is a transient PROCESS step (write RED, then GREEN in the same task); in this lesson the RED test is itself the SHIPPED ARTIFACT of one plan task, and a SEPARATE later task flips it GREEN. Those two roles put different demands on how the test must FAIL.


**Trigger:** A multi-task plan where a RED test is committed as the deliverable of Task N (the assertion encodes a contract a later migration/rewrite will satisfy) and Task N+k (k>=1) is the GREEN flip - typically a migration, refactor, or seeding step that lands in a different commit. The plan and its orchestrator docs explicitly mark the failure "intentionally RED" / "designed RED."

**Rule:** When the committed test IS the deliverable, the RED failure MUST be a clean assertion failure routed through `pytest.fail(<message>)` (or an `assert` with a message), never an unhandled exception, collection error, or runtime error inside the test body. The message MUST name the resolving task/phase and the specific condition that flips it GREEN (e.g. "...missing #126/#127 - Task 5 migration rewrites this file with contiguous #N"), so reviewers, CI, and the per-task `done` sub-agent can distinguish a DESIGNED-RED from an accidental regression by reading the failure text alone. State the designed-RED status AND the resolution-naming requirement in the implement log so the `done` sub-agent does not treat the failure as a regression to "fix" before committing. Do NOT let the test error out (a collection error or runtime exception looks identical to a real bug to automation that classifies by outcome type).

**Why this matters:** A committed RED test that fails by exception is indistinguishable from a broken test to the `done` workflow and to CI: both surface as "1 failed" with an error traceback, and a sub-agent or reviewer reading only the outcome cannot tell whether to commit, block, or "fix" it. A clean `pytest.fail` with a resolution-naming message is self-describing: the failure text itself says "this is designed-RED, it resolves at Task 5," which is the only signal that survives when the implement log and the CI dashboard are read independently. Without this, the `done` sub-agent blocks the commit as a regression (the orchestrator has to override), or worse, a reviewer "fixes" the RED by deleting the assertion, destroying the contract the test was meant to pin.

**Shape trigger (when to suspect this family):** You are implementing or reviewing a plan task whose deliverable is described as "the RED test" / "intentionally RED" / "fails now, passes at Task N+k," OR a `done`/CI run is about to block on a test failure and you need to decide regression vs designed-RED. The smell is a multi-task plan where one task's output is a failing test and a later task's output is the fix.

**General form:** When a test's failure is the SHIPPED ARTIFACT (not a transient process step), the failure mode itself becomes part of the contract. An exception-shaped failure erases the distinction between "designed-RED" and "broken test"; an assertion-shaped failure with a resolution-naming message preserves it. The message is the load-bearing element: it is what lets downstream automation and human reviewers act correctly without re-deriving the plan's task graph.

**Example (2026-06-29 lessons-corpus-derived-index plan, Task 3):** Task 3's deliverable is the conformance test suite, including `test_project_file_independence`, which pins the post-migration contract that `docs/maintenance/development_lessons.md` has contiguous `#N` headings (1..N, no gaps) and no `lessons_index`/`UL#` coupling. The live project file is pre-migration (199 headings, gaps at #126/#127, max #164), so the contiguity check fails now; Task 5 (run the migration skill) rewrites the file and flips it GREEN. The implement log routed the failure through `pytest.fail("non-contiguous #N in project file: count=199, ... missing=[163, 164] - Task 5 migration rewrites this file with contiguous #N")` rather than letting it raise, so the `done` sub-agent could read the failure text and the implement-log "intentional RED" note and commit the test as-is without treating it as a regression. See the Task 3 implement log "CRITICAL: intended RED state" section.

**See also:** #57 (TDD RED-then-GREEN as a PROCESS step within one task - the transient case), #81 (re-read RED assertions against REVISED invariants before the GREEN flip - the stale-assertion case), tax-reporting "Outer Row-Level Exception Block Must Not Prevent a Trusted-Branch Operation From Completing"/#99 (discriminating tests must assert each independent signal separately - Family A parent). This lesson fills the third vertex of the RED triangle: #57 is process ordering, #81 is assertion freshness under revision, #165 is failure-SHAPE discipline when the RED test is the shipped deliverable.

## 123. A Bulk "Drop the #N Token" Rewrite on Prose Leaves Mangled Stub Residues for Mechanical Forms the Rewrite Pass's Anchors Do Not Consume

**Principle:** Family H (Verification discipline: a passing edit-count check proves the edit fired, not that the surrounding sentence survived) cross with the bulk-punctuation-edit family of #84/#83 (short search strings inside larger tokens). The distinct facet here is not offset-misanchoring (#84) or legacy-scope false-failure (#85); it is that removing a SUB-TOKEN (`#N`) from inside several distinct surrounding SYNTACTIC frames leaves each frame's OWN residue behind, and a rewrite pass that matches "citation-phrase + `#N`" or "lead-in + `#N`" never sees the frames whose lead-in it did not enumerate.


**Trigger:** A migration/migration-like engine or a scripted bulk edit removes a short token (a `#N` citation, a ref number, an inline cross-reference) from many docstring/comment/prose sites across a repo, where the token appears inside several MECHANICAL frames: parenthesized lists `(/, )`, slash-lists `( /  shape)`, per-token forms `lesson #N` / `repo lesson #N` with NO filename anchor, and `See <path> #N for ...` / multiline `See$\n<punct>` forms. The verification plan is a grep that the OLD token no longer appears, plus an edit-count check.

**Rule:** After any bulk sub-token-removal pass on prose, run an EXHAUSTIVE stub-residue sweep that is independent of the rewrite pass's match anchors. The sweep must target each mechanical frame the token can sit inside, not just the citation-phrase form the rewriter consumed. Specifically, after dropping `#N`, search the same file set for:
1. Empty/structural leftovers from parenthesized or slash-list citations: `()`, `(/)`, `(,)`, `( /  )`, `(  shape)`, doubled/trailing separators inside parens.
2. Orphaned per-token labels where the `#N` was removed but its governing noun was NOT a citation phrase: `lesson :`, `lesson .`, `repo lesson ,`, `URL #N` tails.
3. Multiline `See ... for ...` tails where the `#N` and the preceding path sat on one line and the trailing ` for ...` / `.` continued on the next: orphan ` for ...` / `.` lines, or a leading-punct line following a `See` whose `#N` was deleted.
For each residue, apply the user's verbatim citation policy (cite the title if decisive, else drop the whole sentence) rather than leaving a grammatically broken stub. A grep that confirms "the old `#N` string is gone" passes while every one of these stubs remains; the edit-count check is necessary, not sufficient.

**Why this matters:** The rewrite pass's anchors (citation-phrase `<filename> #N`, or `<lead-in> #N` for an enumerated lead-in set) are exactly the structures the rewriter was BUILT to consume. The mechanical frames above are the structures it was NOT built to consume, and a per-token `#N` removal that fires when no filename lead-in matches hits them silently: the `#N` goes, the surrounding paren/label/See-tail stays, and the file now contains a docstring with `(, )` or `lesson .` in it. A reader sees mangled prose; a re-run of the engine does not fix it (the engine already considers the site "processed"). Only an independent sweep by frame-shape, not by the removed token, finds them.

**Shape trigger (when to suspect this family):** You are reviewing the output of a migration engine or scripted edit that "removes citation number `#N`" / "strips ref tokens" / "drops cross-tier references" from prose; OR a post-migration verification scan reports "all old `#N` removed" and "edit count matches plan" but you have not separately swept for structural residue. The smell is a sub-token removal operating on prose where the token nests inside punctuation/label/multiline frames the rewriter's match grammar did not enumerate.

**General form:** When a mechanical edit removes a SUB-TOKEN (something smaller than a word) from many prose sites, the verification of completeness must be framed by the SURROUNDING syntactic frames the token sat in, not by the removed token itself (which is, by construction, gone everywhere). Each distinct frame class (parenthesized list, per-token label, multiline continuation) produces a distinct residue class; a frame-class sweep is the independent detector, exactly parallel to #121's "an output-consistency self-check cannot detect its own input mis-classification" - here the rewrite pass cannot detect the stubs its own per-token removal created because it has no anchor that matches an empty paren.

**Example (2026-06-29 lessons-corpus-derived-index plan, Task 5, post-implement orchestrator cleanup):** The `lessons_migrate` engine rewrites cross-tier `#N` citations to REMOVE (the lesson moved to the user corpus). Its r6 pass handled citation-phrase forms (`` `development_lessons.md` #N ``) and per-lead-in `<lead-in> #N` forms. After the real run, an orchestrator verification scan found 29 mangled stubs across 13 files in three frame classes the r6 pass did not cover: (1) paren-wrapped/slash-list citations like `(#51 / #113)` collapsed to `(/)` and `(,)` when both `#N` were removed; (2) per-token `lesson #N` / `repo lesson #N` with no filename became `lesson :` / `lesson .` after the `#N` dropped; (3) multiline `See <path> #N\n for ...` left orphan ` for ...` lines. The self-check gate (Cmd 1, validates the user corpus) passed; Cmd 9a (grep for old `#N`) passed because the `#N` strings WERE gone; neither detected the stubs because neither sweeps by surrounding frame. The orchestrator's frame-class sweep (paren residue, per-token label residue, multiline-See residue), NOT a token grep, was the detector. Cleanup applied the title-or-drop policy per site (29 sub-agent sites + 3 residual multiline-See sites the sub-agent missed). See the Task 5 implement log "Pass 2 (orchestrator post-implement citation-stub cleanup)" section.

**See also:** #121 (an engine's output self-check cannot detect its own input mis-classification - the parent principle; this lesson is its stub-residue specialization: the rewriter's anchors cannot match the empty frames its own sub-token removal created), #84 (bulk short-string edits mis-anchor inside larger tokens - the offset facet), #83 (heading-collision renumbering requires per-ref audit - the disambiguation facet), #158 (a passing check proves reachability, not correctness - the testability facet), coding_guidelines.md #25 (Family H parent).

## 124. A Faithful Identity-Remap (Renumber/Rename/Relocate) Tracks Entity Identity, Not Prose-Semantic Correctness of Pre-Existing References; the Latter Is a Separate Audit and Out of Scope

**Principle:** Family H (Verify the real thing - here, verify what KIND of pass the contract specifies, before rejecting faithful work or widening scope). The distinct facet vs the #83/#121/#123 cluster: those lessons make a MECHANICAL pass more correct (disambiguate collisions #83, fix self-check mis-classification #121, sweep stub residue #123). This lesson draws the SCOPE BOUNDARY of a mechanical pass: a faithful identity-remap is, by definition, NOT a prose-semantic audit, and a review must not conflate the two.

**Trigger:** A migration/remap task is scoped as a mechanical transformation - "renumber lessons", "rename symbols", "relocate files", "repoint references to new IDs" - and a reviewer (human or agent) then objects that a reference "points at the wrong thing" semantically: the referring sentence's keywords describe a DIFFERENT entity than the number/name it cites. The smell is a scope-conflation objection arriving against an identity-preserving transformation.

**Rule:** When a task contract is an identity-remap (old entity -> SAME entity, new identifier), the contract is FAITHFUL TRACKING, not prose-semantic correctness of every reference. The remap is correct iff each old identifier resolves to the same entity at its new identifier. A reference whose prose described a different entity than its number named - BEFORE the remap - survives the remap still mismatched, and is PRE-EXISTING debt, NOT a migration defect: (a) the number was never ambiguous (no collision, so #83 does not apply), (b) the engine classified the token correctly as a target reference (so #121 does not apply), (c) nothing was removed or mangled (so #123 does not apply). Detecting or fixing a prose/number semantic mismatch requires a SEPARATE prose-semantic audit (does the referring sentence's keywords match the TITLE of the entity its number names?), which is a fundamentally different pass and must be scoped explicitly, not smuggled into the remap. Reviewing a remap: confirm identity-tracking fidelity per old->new pair; route any prose/number mismatch findings to a separate maintenance task and ACCEPT the remap as-is unless an identity tracking error exists.

**Why this matters:** Conflating the two scopes produces two failure modes. (1) REJECTING FAITHFUL WORK: a reviewer flags a correct remap as "defective" because a citation's prose was always mismatched, blocking merge on work the migrator performed correctly. (2) SCOPE CREEP INTO UNBOUNDED VALIDATION: widening "repoint references to new numbers" to cover "audit whether each citation's prose semantically matches its number" turns a bounded mechanical task into an open-ended prose-correctness pass over every reference in the repo, with no completion criterion the original contract defined. Both failure modes are avoided by naming the scope boundary up front: identity-remap fidelity is the gate for the remap task; prose-semantic correctness is a different task with its own gate.

**Shape trigger (when to suspect this family):** You are reviewing or triaging the output of a renumber/rename/relocate/repoint-references migration and a finding says "citation `#N` / reference `<name>` now points at the wrong lesson/symbol/file, the prose describes a different one." Before accepting the finding as a migration defect, ask: did the old identifier track the SAME entity through the change (old `#X` was lesson L, new `#Y` is also lesson L)? If yes, the remap is faithful and the mismatch is pre-existing prose debt - the finding is ACCEPT-AS-IS with a route to a separate semantic-audit task, not a migration Blocker/Medium. The discriminator question is "was identity preserved", not "does the citation read correctly".

**General form:** Whenever a transformation's contract is preserving identity across a representation change (renumber, rename, relocate, re-encode), correctness is measured against identity preservation, not against the semantic correctness of references that were ALREADY inconsistent with what they named before the transformation began. Pre-existing reference/entity semantic mismatches are carried through unchanged by any faithful identity transformation; they cannot be introduced by it and cannot be fixed by it. They are a distinct concern (a reference-correctness audit) with a distinct gate, and must be scoped as a separate task. This holds for lesson-citation renumbering, API/symbol renaming, file-path relocation, ID-namespace migration, and any other identity-preserving remap.

**Example (2026-06-29 lessons-corpus-derived-index plan, review round r1, finding 1):** The `lessons_migrate` engine renumbered the project `development_lessons.md` from 195 lessons to 41 retained lessons. The `AGENTS.md` "docs/review singular" rule (current post-migration text: "Never write to `docs/review/` (singular); use `docs/history/reviews/` (plural). See `development_lessons.md` tax-reporting "Two-Level Review Flags: Separate Platform-Level from Row-Level".") But project `tax-reporting "Two-Level Review Flags: Separate Platform-Level from Row-Level"` is now "Use the resolve-vars Utility Skill for Path Discovery" - an unrelated lesson; the prose describes "Review Documents Are Temporary Artifacts" (project `#21`). The r1 reviewer flagged this as a stale citation. It is PRE-EXISTING debt: pre-migration the same line cited `#68`, and pre-migration `#68` was ALSO "Use the resolve-vars Utility Skill for Path Discovery" (verified via `git show <pre-migration>:docs/maintenance/development_lessons.md`). The migrator's remap old `#68` -> new `tax-reporting "Two-Level Review Flags: Separate Platform-Level from Row-Level"` is internally faithful: it tracked the resolve-vars lesson through the compact renumber. The prose described a different lesson than its number BOTH before and after. The migrator cannot detect that the citation's prose describes a different lesson than its number - that is a human-authored prose/number mismatch predating the migration. 12 of 13 surviving `AGENTS.md` citations ARE semantically correct; `tax-reporting "Two-Level Review Flags: Separate Platform-Level from Row-Level"` is the lone mismatch. Triage decision: ACCEPT-AS-IS, route the optional one-line cleanup (`tax-reporting "Two-Level Review Flags: Separate Platform-Level from Row-Level"` -> `#21`) to a separate doc edit; the migration verdict stayed CLEAR (0 Blocker / 0 Medium / 3 Low, 0 fixes applied). See the r1 doing-code-review and receiving-code-review logs.

**See also:** #83 (heading-collision renumbering requires per-ref disambiguation - applies only when the number is AMBIGUOUS, i.e. a collision; this lesson is the no-collision case where identity tracking alone defines fidelity), #121 (engine self-check cannot detect its own input mis-classification - applies when the engine mis-classifies a token; this lesson is the case where classification was CORRECT and the defect is pre-existing prose debt outside the engine's scope), #123 (sub-token removal leaves stub residue - applies to removal passes; this lesson's remap is a renumber, not a removal), coding_guidelines.md #25 (Family H parent - verify the real thing: here, verify the contract scope before rejecting faithful work).

## 125. Active Code Review Must Gate Authorization Findings on PR Story Scope and Author-Documented MVP Intent, Not Domain Seed Data Alone

**Principle:** Family H (Verification discipline: confirm the failure is in scope and reachable in this change before staging a High finding). Cross with review-scope discipline: a theoretically correct RBAC observation is not a merge blocker when the PR author, tests, and description bound the story differently.

**Trigger:** An active code review stages a High or Medium finding that a role, caller type, or authorization rule "blocks" behavior (for example managers cannot call `/me`, API keys fail `anyRequest()`). The evidence cites seed SQL, domain enums, or sibling design docs, but the PR adds only a subset of routes and existing PR review threads contain author replies such as "for now", "no endpoints yet", or "configure when added".

**Rule:** Before keeping authorization or RBAC findings at Medium+, read existing PR review comments (not only dedup against them). Treat author-documented MVP scope as evidence in Step 4.2 assumption checks. Distinguish: (1) path-scoped `requestMatchers` already carving out public routes, (2) intentional admin-only on the current protected set, (3) forward-looking roles in seed data not exercised by this PR's routes or tests. Drop or downgrade when head code matches stated intent; keep only when implementation contradicts the author's documented decision or the PR's own tests/description.

**Why this matters:** Staging a High finding from seed-data inference without reading author threads produces false merge blockers and erodes review trust. The orchestrator used sub-agent RBAC logic and missed reviewer-gh-handle's inline reply that PROJ-537 intentionally requires admin on all protected paths and defers API-key routes.

**Shape trigger:** Authorization finding on `SecurityFilterChain`, `hasAuthority`, or role names where PR tests use only one role fixture and PR description lists a narrow endpoint set.

**Example (2026-07-02, example-crm-platform PR #8 review):** Finding #1 claimed `.anyRequest().hasAnyAuthority(ROLE_CRM_ADMIN)` incorrectly blocked managers and API keys. Seed data includes `ROLE_CRM_MANAGER`, but PROJ-537 ships only `/me` and `/permissions` with admin integration tests, and the author replied on `CrmSecurityConfig` that all protected paths are admin-only for now with per-route matchers when new endpoints land. Finding withdrawn after user correction.

**See also:** doing-code-review SKILL.md Step 1 (gather PR comments for scope) and 4.2 (author intent, story scope vs seed data), coding_guidelines.md #25 (Family H).

## 126. Code Review "What the Contract Says" Must Cite a PR-Visible Normative Source or Be Reframed

**Principle:** Family H (Verification discipline: name the evidence source before claiming contract drift). Cross with doing-code-review §4.9.1 (posted comments cannot cite gitignored instruction files).

**Trigger:** A staged finding opens with **What the contract says** but cites a team logging policy, company guideline, or vague "security-sensitive flows should..." text that does not appear in the PR diff (`openapi.yaml`, edited README, schema, tests).

**Rule:** Before finalizing Medium+ findings, verify the normative source is PR-visible and name it (file + section or OpenAPI response). If the only rule is private or gitignored, drop the finding or reframe as **What this PR establishes** (design the PR itself introduces, such as audit table columns and tests). Fix suggestions must be code or in-diff doc edits only; do not offer "relax the logging policy in guidelines" when the policy was never a PR-visible contract.

**Why this matters:** Vague contract sections invite author pushback ("which contract?") and false contract-drift framing. A valid hygiene finding (duplicate PII in app logs vs audit table) was weakened by inventing a nonexistent written contract.

**Shape trigger:** Review Comment uses **What the contract says** without quoting a line from a file in `gh pr diff --name-only`.

**Example (2026-07-02, example-crm-platform PR #8, finding #5):** Draft cited "audit without PII in application logs" with no PR source. Rewritten to **What this PR already establishes** (`auth_audit_log.email`, `createFailure`, integration tests) vs duplicate WARN logging in `OAuthLoginService`.

**See also:** doing-code-review §4.12 contract section gate, 4.9.1, UL#162, coding_guidelines.md #25 (Family H).

## 127. A Module-Level `pytest.skip` Disables Tests That Do Not Share the Skipped Resource; Gate the Skip to the Dependent Test Only

**Principle:** Family H (Verify the real thing, not the abstraction - a green suite does not prove the invariant was evaluated). Cross with Family A (equivalence-class coverage - the resource-absent environment is an equivalence class where coverage silently drops to zero).

**Trigger:** A test module guards a shared, machine-specific resource (an external script, a playbook checkout, a live corpus file) and skips when that resource is absent, but the skip is placed at MODULE scope (`pytest.skip(..., allow_module_level=True)` at import time, or a module-level `pytestmark = pytest.skip(...)`) while the module also contains pure-file or pure-logic tests that do NOT touch the resource.

**Rule:** Scope a resource-availability skip to the test(s) that actually depend on the resource, never to the whole module. Move the guard inside each dependent test (skip when `not Path(script).is_file()` or `not resource_present`), or split the module so independent tests live outside the gated module. After placing the skip, verify on a machine LACKING the resource (`RESOURCE=/nonexistent pytest ...`) that the independent tests still RUN (passed/failed), not just that the suite exits 0. A module-level skip reports as one skipped item and hides that N independent invariants were also silently disabled.

**Why this matters:** On CI or any contributor machine without the resource, the independent invariants (contiguity checks, no-coupling asserts, plain-file shape) are silently unenforced, yet the suite reports green. A future regression caught only by those tests lands green on such machines. The docstring claim "always runs" becomes false under the gating, and nothing fails to flag the discrepancy. The green status is an abstraction standing in for "the invariant held"; the real thing - "was the invariant actually evaluated on this machine?" - was never checked.

**Shape trigger:** A test file contains `pytest.skip(..., allow_module_level=True)` (or module-wide `pytestmark` skip) AND other test functions/classes in the same file whose bodies never reference the skipped resource.

**Example (2026-07-02, tax-reporting branch `2026-06-29-lessons-corpus-derived-index`):** `tests/unit/test_lessons_corpus_conformance.py` had a module-level skip when `~/.ai-playbook/scripts/lessons_index.py` was absent, which disabled all three tests including `test_project_file_independence` (a pure-file assertion over the repo's own `docs/maintenance/development_lessons.md` that never invokes the gate). Verified: `LESSONS_INDEX_SCRIPT=/nonexistent uv run pytest ...` reported `1 skipped` and ran zero tests, so the contiguity invariant was unenforced on any machine without the playbook. Fix: moved the skip into `test_gate_passes_user_corpus` only; the pure-file test now always runs.

**See also:** UL#148/#2219/#3202 (a passing test does not prove the thing under test - same Family H testability-hazard cluster, distinct facet: here the test never ran at all), coding_guidelines.md #18/#25 (Family A / Family H).

## 128. Code Review Company-Rule Findings Use "As Per Company Guidelines" With the Public Playbook URL, Not "Contract or Docs"

**Principle:** Family H (Verification discipline: name the evidence source before claiming contract drift). Cross with UL#163 and doing-code-review §4.9.1.

**Trigger:** A staged finding cites company engineering rules (logging, layering, naming) under **What the contract or docs say** or labels them "repo security rules" without a PR-visible normative source.

**Rule:** Company guidelines are not API contracts. Use **As per company guidelines**, link the public company-playbook copy with the rule number, and **verify the rule exists at that URL before posting** (fetch the file; confirm the numbered rule or quoted text is present). Keep **What the contract or docs say** for OpenAPI, README, and other files in the PR diff only. If the rule is not publicly available or verification fails, do not cite guidelines: rephrase as a suggestion and refer to common engineering practice or widely accepted best practices.

**Why this matters:** Framing private or local guidelines as "the contract" invites author pushback and violates 4.9.1 when the link is missing. A public playbook URL gives reviewers and authors a shared, citable source only when the link resolves and the rule is present; unverified links (for example 404 on raw GitHub fetch) should fall back to best-practice suggestions.

**Shape trigger:** Review Comment opens with **What the contract or docs say** but the cited rule is PII logging, method-length limits, or other company-guidelines content not quoted from a file in `gh pr diff --name-only`.

**Example (2026-07-03, example-crm-platform PR #9, finding #9):** Draft cited "repo security rules: do not log PII" under **What the contract or docs say**. Rewritten to **As per company guidelines** with public company-guidelines.md #13 before posting.

**See also:** doing-code-review §4.9.1, §4.12 contract section gate, UL#163.

## 129. Shell Scripts Under `set -u` That Expand a Possibly-Empty Array on macOS bash 3.2 Must Use `${arr[@]+"${arr[@]}"}`, Not `"${arr[@]}"`

**Principle:** Family H (Verify the real thing, not the abstraction: the script "works on my bash 4+ machine" abstraction hides that the deployment target is bash 3.2, whose array-expansion semantics differ). Cross with the portability family of scripts that run on the macOS default `/bin/bash`.

**Trigger:** A bash script uses `set -u` (nounset) and expands an array that can legitimately be empty with the standard `"${arr[@]}"` form, and the script must run on macOS default bash 3.2 (or any bash older than 4.4).

**Rule:** Under `set -u`, the canonical `"${arr[@]}"` raises `unbound variable` on bash 3.2 when the array is empty (has no assigned elements). Use the bash-3.2-safe idiom instead:

```bash
cmd ${arr[@]+"${arr[@]}"}
```

The `${arr[@]+...}` conditional expansion yields nothing when the array is empty and the quoted `"${arr[@]}"` when it has elements, preserving correct word-splitting safety on both bash 3.2 and bash 4+. Do NOT switch to the unquoted `${arr[@]}` form to dodge the error; that reintroduces word-splitting on element values containing spaces.

**Why this matters:** macOS ships bash 3.2 as `/bin/bash` and many hook/CLI scripts have `#!/bin/bash` shebangs. A script tested only on bash 4+/5 (Linux, Homebrew bash) will pass the empty-array path there and fail on a stock macOS host the first time the array is legitimately empty (for example a hook invoked with no matching lessons). The failure is `set -u` aborting the whole script, not a silent bug, so it surfaces in production rather than CI.

**Shape trigger:** A bash script begins with `set -u` (or `set -euo pipefail`) AND expands an array that is populated conditionally (filtered results, optional args, dedup windows) AND targets `/bin/bash` or documents macOS support.

**Example (2026-07-03, ai-playbook lessons-recall adapters):** The Claude/Codex/agy hook adapters build an `args` array for `session_channel.py` and expand it as `"${args[@]}"`. The empty-CLAUDE_CODE_SESSION_ID echo-pipe test (which leaves the array empty) aborted the adapters on macOS bash 3.2. Switched all three adapters to `${args[@]+"${args[@]}"}`.

**See also:** coding_guidelines.md #25 (Family H parent: verify the real deployment target, not the dev-machine abstraction).

## 130. A Selftest That Asserts "No U+2014 in Output" Must Reference the Byte via `chr(0x2014)` or a Language Escape, Never a Literal U+2014, Because the File-Level `check-no-em-dash.sh` Scan Flags Any Source File Containing the Byte

**Principle:** Family H (Verify the real thing, not the abstraction: the file-level scanner is a `grep` for the byte U+2014 over committed source paths; the assumption "this byte is safe because it is a test fixture input" is an abstraction the scanner does not share). Cross with the agent-layer em-dash policy family (agent_workflow_guidelines.md §39) and with the self-referential-test hazard of #121 (a check that cannot inspect its own input).

**Trigger:** You write a Python (or other) selftest that asserts some output contains NO em dash, OR a test that exercises a deny path keyed on the em-dash byte (for example a `#no_em_dash` selftest, or a test that constructs a payload containing U+2014 to confirm a rejector fires), AND the repo runs `check-no-em-dash.sh` (or any file-level U+2014 grep) over committed source files.

**Rule:** In the selftest source, NEVER embed a literal U+2014 byte to stand for "the em dash we reject". Reference it indirectly so the source file itself contains zero U+2014 bytes:

- Python: `chr(0x2014)` (preferred) or a `"\\u2014"` string literal that resolves to the byte at runtime
- Shell/other: `$(printf '\xe2\x80\x94')` or the equivalent escape for the language

The selftest still asserts the byte's absence (or presence-then-rejection) at runtime; only the SOURCE representation is escaped. A literal byte in the test source makes `check-no-em-dash.sh file <selftest>` fail on the test file itself, and the failure is correct: the scanner cannot distinguish "intentional test input" from "prose that leaked an em dash".

**Why this matters:** A `no_em_dash` selftest is the canonical case where the verifier (the U+2014 scanner) and the verified (a tool that must not emit U+2014) share the SAME byte. Putting the literal byte in the test source defeats the file-level scan silently for everyone except the test author who knows "that one is intentional". The escape form keeps the source clean while the runtime assertion stays byte-exact.

**Shape trigger:** A selftest or test name contains `em_dash`, `no_em_dash`, `u2014`, or the test constructs a string it then asserts "does not contain" / "rejects" an em dash, in a repo with a file-level em-dash gate.

**Example (2026-07-01 ai-playbook lessons-recall-hook plan, Tasks 2 and 4):** Both `lessons_corpus.py --selftest#no_em_dash` (Task 2) and `skill_gate.py --selftest#no_em_dash` (Task 4) initially embedded a literal U+2014 in the assertion string to express "the byte we must not emit". `CHECK_NO_EM_DASH_ALL=1 check-no-em-dash.sh file <selftest>` flagged the test source itself. Replaced the literal with `chr(0x2014)`; the runtime assertion is byte-identical and the file scan is clean.

**See also:** agent_workflow_guidelines.md §39 (em-dash policy and the file-level scanner), coding_guidelines.md #25 (Family H parent: verify the real byte the real scanner sees, not the "it is just a test input" abstraction), #121 (a self-check cannot validate its own input classification).

## 131. A Predicate's Selftest That Authors Synthetic Fixtures Alongside the Predicate Can Pass While the Real Install Fails: Doctor/Validate Selftests Must Mirror the Real Installed Artifact (or Run Against It), Not a Hand-Crafted Sample That Matches the Predicate's Own Assumptions

**Principle:** Family H (Verify the real thing, not the abstraction: a selftest whose synthetic fixture was authored alongside the predicate verifies that the predicate matches the fixture, not that either matches the real artifact. The "GREEN selftest" abstraction hides that the fixture and the predicate share a blind spot). Cross with the self-referential-test hazard of #121 and the test-real-behavior angle of #7.

**Trigger:** You write a validator/doctor predicate (for example a `--doctor` check that audits installed config files) AND its selftest uses a hand-crafted fixture string you wrote in the same pass, AND there is a real installed artifact the predicate is meant to police. The risk peaks when the predicate's matching logic looks for a token/idiom and the fixture's representation of "correct" coincidentally matches the predicate's mental model.

**Rule:** For any selftest that exercises a predicate targeting a real installed artifact (an adapter script, a hooks.json, a config file shipped elsewhere), at least one of the following MUST hold:

1. The selftest includes a fixture that mirrors the ACTUAL real installed artifact verbatim (copy the real `claude.sh` / `hooks.json` / config into the fixture, not a paraphrase of it), OR
2. The selftest suite has a "run against the real install" mode (the predicate is invoked on the real installed path, not a temp fixture) and that mode is part of the GREEN gate, OR
3. A separate RED step proved the new fixture would have failed the OLD predicate before the predicate was changed (proving the fixture exercises the predicate's actual decision boundary, not a coincidental match).

A selftest fixture authored from the predicate's own assumptions satisfies NONE of these; it only re-asserts the predicate against itself.

**Why this matters:** A predicate and its hand-crafted fixture are often written by the same author in the same mental model, so the fixture inherits the predicate's blind spot (the predicate looks for token X; the fixture's "correct" sample contains X in the expected place; both agree; the real artifact puts X somewhere the predicate did not look). The full selftest suite reports ALL PASS against an install the predicate falsely FAILs (or falsely PASSes). Only running the predicate against the real installed artifact, or mirroring that artifact byte-for-byte in a fixture, breaks the shared assumption. This is the doctor/validator analogue of "tests that pass because they test the mock".

**Shape trigger:** A predicate audits an external file/format, its selftest fixtures are hand-written strings (not copies of a real artifact), and the predicate ships before anyone runs it against the real artifact it polices. Suspect it when a `--doctor`/`--validate`/`--check` command's selftest is GREEN but the command FAILs (or wrongly PASSes) on the real installed target.

**Example (2026-07-03 ai-playbook lessons-recall-hook plan, Task 4 corefix):** `scripts/skill_gate.py --doctor` runs two checks over installed hook adapters. check(3) flagged adapters that "read `CLAUDE_CODE_SESSION_ID` directly"; its selftest fixture put the bare token in a synthetic adapter body, and the predicate matched the bare token anywhere. Both passed. The REAL mandated Claude adapter contains the bare token ONLY inside a stderr warning string and comments (it derives the session via a helper, never reading the env var), so the predicate false-FAILed a correct install. check(5) looked for the Claude matcher `Write|Edit|MultiEdit` in `hooks.json`; the selftest fixture used that matcher; the REAL agy install uses the AGY tool vocabulary matcher, so the predicate could not find the skill-gate entry at all. The fix (RED-first: rewrite the agy-timeout fixture to the real agy matcher + real `skill-gate` command path, add a `doctor_real_install_shape` selftest mirroring the real Claude adapter, confirm both went RED, then fix the predicates) is exactly option (1) + option (3) above. The synthetic fixtures had encoded the predicate's wrong assumption instead of the real install's shape.

**See also:** coding_guidelines.md #25 (Family H parent: verify the real artifact, not the abstraction), #7 (test real behavior, not implementation details), #121 (a self-check cannot validate its own input classification).

## 132. A Follow-On Multi-Agent Hook Plan Must Freeze Non-Target Adapters, Default Shared-Core Behavior to v1, and Gate Regression With a Merge-Base Diff Plus Four-Agent Echo-Pipes

**Principle:** Family D (Single source of truth for who may change) cross Family H (verify steady-state agents did not drift: the abstraction "shared core improvement" must not silently retarget Claude/Codex/agy envelopes or session glue).

**Trigger:** You write a v2 plan that touches shared hook cores (`lessons_recall.py`, `skill_gate.py`, `session_channel.py`) while multiple per-agent adapters already ship in production (Claude, Codex, Cursor, agy). The user states that other agent types must not be affected.

**Rule:**

1. **Frozen adapter list:** Name every adapter script that MUST NOT change in Review Scope (stdin parse, envelope shape, exit codes, session-arg glue). Reject plan-related findings on frozen paths unless a regression test proves a mandatory fix.
2. **Shared-core backward compat:** New session channels or classifiers default to v1/off behavior when the new input is absent (empty env var, omitted flag). Pin selftests that prove byte-identical v1 output on the fallback path.
3. **Regression task:** Final task runs the predecessor four-agent echo-pipe matrix AND `git diff --name-only "$(git merge-base HEAD main)"...HEAD` against the frozen list.
4. **Plans skill completeness:** Creating the plan is not done until Phase 0/1, review-plan loop (minimum two rounds), and `ready=yes` with Blocker=0 Medium=0 on the latest review artifact. A draft plan file without the review chain is not READY.

**Example (2026-07-04 ai-playbook agent-hooks-workflow-v2):** User asked whether hook workflow could improve and insisted Claude/Codex/agy must not regress. v1 draft skipped full plans skill and would have changed classifier default and `claude.sh`. Revised plan freezes six adapter scripts, keeps `--classifier v1` default, adds Cursor-only bridge, and passed review r4 (0 Blocker / 0 Medium) after four rounds.

**See also:** #131 (doctor fixtures must mirror real installs), lessons-recall-hook plan Monitor (agent steady states), `plans` skill Plan Quality Gate, `review-plan` skill.

## 133. When a Hardening or Isolation Discipline Is Established at One Call Site, It Must Be Propagated to Every Sibling Call Site (and Re-Applied to Every New Sibling Added Later), Each Pinned by Its Own Discriminating Regression Test

**Principle:** Family D (Single source of truth for the discipline: the established pattern is authoritative for ALL sibling call sites of the same concern, not just the one that triggered the original fix) cross Family G (Data-loss observability: a missing guard at one sibling site silently lets the original hazard through that one aperture, with no error to explain it).

**Trigger:** A review or incident fix establishes a hardening or isolation discipline at ONE call site (symlink rejection, size cap, exception narrowing, HOME/tempdir isolation for selftests, log-pollution guard, sentinel-vs-exception policy), AND the same subsystem has other sibling call sites that touch the same concern (other read/write paths, other selftest arms, other modules that parse the same format). The risk peaks when a NEW sibling is added LATER (a new selftest arm, a new module reusing a shared helper, a new read path) after the discipline was already established at the original site.

**Rule:**

1. **Enumerate sibling sites when establishing the discipline.** When you fix one call site, grep the subsystem for EVERY sibling call site of the same concern (every `os.open`, every `--selftest` arm that touches the real HOME, every caller of the shared loader) and apply the discipline to all of them in the same pass. The fix is for the CLASS, not the tested cell (cross with tax-reporting "AT Guidance May Cite Pre-Amendment Paragraph Numbers" / Family A).
2. **Re-apply on every NEW sibling.** When a new selftest arm, new module, or new call site is added to a subsystem where the discipline was previously established, grep the established pattern and apply it to the new sibling BEFORE the new code runs against the real environment. "It was added later" is the most common re-bite vector.
3. **Pin EACH sibling with its own discriminating regression test.** A single test at the original site does not protect the siblings. Each sibling call site gets its own test that would fail if the discipline were reverted at THAT site (HOME-patch guard asserting zero real-log delta; symlink-leaf refusal asserting empty set AND preserved leaf; keying-tag assertion pinning the specific log line). A revert at one sibling that the shared test still passes is the failure mode this rule prevents.
4. **The baseline/regression guard must assert the SIDE EFFECT on the real environment, not just the return value.** For isolation disciplines, capture the real-environment state BEFORE (real hooks.log line count, real HOME contents) and assert zero delta AFTER, in addition to the function-under-test assertions.

**Why this matters:** A discipline established at one site creates a false sense that the concern is handled subsystem-wide. Reviewers reading the original fix assume the pattern was propagated; the next person adding a sibling copies the original un-hardened template (or no template at all) because the discipline lives only in the one fixed site's diff. The re-bite surfaces rounds later as a new Medium/Low in a review of a sibling that was assumed clean. Three re-bites within one subsystem (r1 establish, r2 sibling, r4 new sibling + new selftest arm) is the signature of this lesson.

**Shape trigger:** A review finding of the form "X discipline was applied to site A in round N but site B (a sibling read/write path, selftest arm, or new module) still uses the un-hardened pattern," OR a selftest pollutes/reads the real environment (real log file grew, real HOME read) because the isolation guard from a sibling selftest was not copied into it. Suspect it whenever a NEW selftest arm or NEW call site is added to a subsystem that already has an established hardening/isolation discipline.

**Example (2026-07-04 ai-playbook lessons-recall-hook plan, r4 review):** Three re-bites of the same Family-D shape across one hooks subsystem.

(a) r1-M6 established HOME-patch isolation (`tempfile.TemporaryDirectory()` + `os.environ["HOME"]` patch + a `_m13` regression guard asserting zero leak into the real `~/.ai-playbook/logs/hooks.log`) in the `lessons_recall.py` selftest. r4-1 (Medium) found the SAME discipline was never propagated to the `facts_paths.py` selftest: arms 1 and 2 of its `resolve_project_key` selftest called the resolver with the REAL `HOME` still in scope (HOME patching only began at the old arm 3), so every `python3 facts_paths.py --selftest` run appended 2 `keying=no-anchor` lines to the developer's real `~/.ai-playbook/logs/hooks.log`. Fix: moved the HOME patch to wrap arms 1 and 2, added a `_real_log`/`_iso_before` baseline capture and a `selftest_isolation` regression guard mirroring the lessons_recall `_m13` guard; empirically verified real-log delta went from +2 to 0.

(b) r1-M2 hardened the dedup state-file WRITE path with `os.O_NOFOLLOW`. r2-M7 hardened the sibling skill-gate marker READ path with `os.lstat`. r4-2 (Low) found the dedup state-file READ path (`_read_seen_set`) still used bare `os.O_RDONLY` two rounds later. Fix: `os.O_RDONLY | os.O_NOFOLLOW`; added `dedup_state_reader_refuses_symlink_leaf` mirroring the writer selftest.

(c) The skill-gate `fail_open_oserror_resolve_sibling` selftest (r2) pinned the `keying=fail-open` log line for the OSError arm. The sibling `fail_open` (PermissionError) selftest did NOT pin its own keying line until r4-5, so a regression that deleted the `keying=fail-open` log write while keeping the stderr write would have passed the sibling test.

In all three, the discipline existed at one site; the sibling was added/found later without the discipline; the re-bite was caught only when a review specifically looked for the missing propagation.

**See also:** coding_guidelines.md #18 (Family A: cover the whole partition, not just the tested cell), #19 (Family D parent), tax-reporting "Decision Points TOML Missing Must Raise `ConfigurationError`, Not Bare `FileNotFoundError`" (Family G parent), #77 (recalibrate exception policy per call site - the inverse complement of this lesson: that one is about DIVERGING policy where divergence is correct; this one is about PROPAGATING discipline where uniformity is correct), #101 (propagate exception policy through wrappers), #131 (selftest fixtures must mirror real installs).

## 134. An API Rate-Limit Error's Reset Timestamp Is in the Provider's Reporting Timezone, Not the Local Timezone; Verify With a Cheap Probe Before Treating a Far-Future Reset as a Hard Multi-Hour Block

**Principle:** Family H (Verify the real thing, not the abstraction: the error message's reset timestamp is an abstraction; the real thing is the provider's CURRENT limit state, which a single cheap probe observes directly).

**Trigger:** A sub-agent or API call aborts with a 429 / usage-limit error whose message names a reset time (for example "Your limit will reset at 2026-07-05 23:12:59"). The orchestrator, seeing a reset that looks hours away in its own local timezone, concludes sub-agents are hard-blocked for that whole window and either (a) commits to elaborate inline recovery of the aborted unit of work, (b) pauses the workflow to ask the user how to proceed, or (c) waits. The conclusion rests on the unstated assumption that the printed timestamp is in the orchestrator's local timezone.

**Rule:**

1. **Treat the printed reset timestamp as timezone-unspecified, not local.** Provider rate-limit messages report the reset instant in the provider's reporting/dashboard timezone (commonly US-Pacific for Anthropic-class APIs), which can differ from the orchestrator's local zone by many hours. A "23:12:59" reset that reads as ~6h away may in fact be minutes away or already past. Do not convert "reset at HH:MM:SS" into "blocked for N hours" without confirming the zone.
2. **Probe the real current state with ONE cheap retry before committing to a workaround.** The authoritative limit state is "does the next call succeed right now," not the printed timestamp. Re-launch one cheap sub-agent (or make one cheap call) and observe. A probe that succeeds collapses the entire multi-hour-block assumption at near-zero cost; a probe that fails with the same timestamp confirms the block is real and you have lost only one quick call.
3. **Never let an unverified future-reset timestamp drive destructive or high-effort recovery.** Inline-recovery of an aborted review round, asking the user to choose between waiting and weakening a process gate, and abandoning the normal sub-agent workflow are all costly actions justified ONLY by a verified block. A single probe is the precondition for any of them.
4. **When you MUST reason about the timestamp, name the timezone explicitly.** If a probe is genuinely impossible and the timestamp is the only signal, state the zone assumption out loud ("assuming the printed reset is in <zone>, which is <N> hours offset from local") so the user can correct it before you act.

**Why this matters:** The cost asymmetry is extreme. The probe costs one cheap call; acting on a wrong multi-hour-block assumption costs hours of inline work, a degraded review (inline recovery sacrifices sub-agent independence), or an unnecessary user interrupt. In the triggering incident, the orchestrator spent a full address-review pass inline AND raised a structured user question predicated on a ~6h block that did not exist in the local timezone at all; a single probe sub-agent would have succeeded immediately and resumed the normal workflow. The error message was not wrong about the reset instant; the orchestrator was wrong about its timezone.

**Shape trigger:** A sub-agent aborts with a 429/usage-limit/quota error carrying a future reset timestamp, and the next planned step is either inline recovery of the aborted unit OR a user-facing "blocked for N hours, how do you want to proceed" prompt. Suspect it whenever the words "reset at" or "limit will reset" appear in an abort reason and the orchestrator's plan changes shape because of the implied wait duration.

**Example (2026-07-05 tax-reporting authoritative-source event-level plan execution, Phase 3):** An address-review sub-agent aborted with "Usage limit reached for 5 hour. Your limit will reset at 2026-07-05 23:12:59" (a 429). The orchestrator read the timestamp against the current WEST (UTC+1) local time of 16:52 and concluded sub-agents were hard-blocked for ~6h20m, then performed the r1 address-review triage INLINE (sacrificing sub-agent independence) and committed the fix inline (skipping the normal per-iteration `done`), and finally raised an AskUserQuestion offering "pause ~6h" vs "inline round 2" vs "accept round 1." The user corrected that the 23:12:59 reset was in a different timezone and there was no limitation in the local timezone at all; round 2 (and rounds 3-4) then ran as normal sub-agents and completed immediately. A single probe sub-agent launched at 16:52 would have succeeded and avoided the inline detour, the skipped `done`, and the user interrupt.

**See also:** coding_guidelines.md #25 (Family H parent), #72 (verify plan claims against actual source before dependent tasks - same shape: an unverified proxy drives downstream decisions), #54/tax-reporting "Probe the Canonical URL Before Assuming an Official Source Is Unavailable"/tax-reporting "Decision-Point Doc Prose Enumerations Must Match Implemented Code Branches" (investigation/data-trace/characterization-test cluster - probe the real state rather than reasoning from a description).

## 135. A User Redirect Targets the CATEGORY Of the Rejected Solution, Not the Literal Instance; Before Proposing the Next Variant, Articulate Why It Is Categorically Different (Not Just Literally Different)

**Principle:** Family H (Verify the real thing, not the abstraction: the user's redirect targets the real constraint - a category of solution the user does not want - but the agent verifies the next variant against an abstraction, the literal mechanism, and concludes "different mechanism, so not the same rejection". The redirect silently does not propagate) cross Family D (Single source of truth: when the user has named the SSOT for some fact, every variant that introduces a competing source for that fact - whether in code, config, defaults, or seed data - violates the SSOT regardless of where the competing source lives).

**Trigger:** A user rejects a proposed solution during plan design, code review, or implementation. The rejection reason is broader than the literal instance (e.g. "we should not bake user-specific labels into generic code", "trust the registry", "don't add escape hatches"). You immediately start drafting the next variant. The risk peaks when the next variant differs in SURFACE FORM (config field instead of code constant; default value instead of explicit list; account-keyed instead of platform-keyed) but belongs to the SAME CATEGORY the user just rejected.

**Rule:** After any user redirect on a proposed solution, before proposing the next variant, run a one-sentence category check: "The user rejected X because of category Y. The new variant Z is [literally different / categorically different]. Specifically, Z [does / does not] still require the user to populate / maintain / choose the same kind of value that triggered the rejection." If you cannot articulate in one sentence why Z is categorically different (not just literally different), do not propose it. Ask the user first, or pick a variant that is categorically different.

**Why this matters:** A redirect that does not propagate to the category forces the user to reject the same theme N times before the agent internalizes it. Each rejection costs a turn and signals the agent is pattern-matching on surface form (code constant vs config field vs default; literal A vs literal B) rather than on the user's actual constraint. The user's mental model is "I gave you a principle; apply it"; the agent's mental model is "you rejected this instance; let me try a different instance". The gap is the difference between a principle and an instance. Three rejections on the same theme inside one session is the signature of this lesson.

**Shape trigger:** Any of:
- You are about to propose a variant of a just-rejected solution and the only difference is the location/mechanism (code -> config -> default -> environment variable).
- The user's redirect used a categorical phrase ("we should not", "trust the SSOT", "no escape hatches", "this is per-user data") rather than a literal one ("change Provider A to provider A").
- You find yourself thinking "but this is different because it's in config instead of code" or "but this is auto-discovered instead of hardcoded" - both are surface-form differences; the category may be the same.
- The user repeats the rejection with stronger wording on the second or third variant ("DO we really need...") - this is the categorical-vs-literal gap surfacing.

**Example (2026-07-06 tax-reporting TH-anchored Transaction view Phase A, Task 4 SourceKindResolver design):** Three rejections on one theme inside a single task. The agent was designing a centralized/decentralized source-type classifier for upstream sources.

(a) Variant 1 - hardcoded seed list in production code: a few named upstream sources -> CENTRALIZED; a few other named upstream sources -> DECENTRALIZED. The agent flagged this as a CLAUDE.md violation ("Never introduce hardcoded values without first flagging it and asking the user") and presented the seed list via AskUserQuestion. The user rejected: "explain why would we need hardcoded source-name seed list? ... Why can't they be autodiscovered for each user during processing?" The categorical rejection: source-name discovery hints are per-user, not generic-code constants.

(b) Variant 2 - same list in config.ini: agent proposed a config section listing known centralized sources, treating "config" as categorically different from "code". The user rejected: "DO we really need a centralized list in config if we'll have these in registry?" Same category (user-supplied source enumeration), different literal location. The agent had pattern-matched on surface form (code vs config) instead of on the categorical constraint (no user-specific source enumeration at all).

(c) Variant 3 - per-source-name aggregation: agent proposed auto-discovery but aggregated at source-name level (one classification per distinct source-name string). The user rejected: "The same centralized source can have dozens of different accounts... All accounts belonging to one source are the same type anyway. So why don't we aggregate it on the source level?" Different theme (aggregation key, not value location) but same parent category: the agent had picked an identity granularity that fragments the source-level SSOT.

The final design (two-tier source-level resolver: registry tier 1, row-evidence auto-discovery tier 2; classification at source level; no hardcoded names anywhere) emerged only after three rejections. A category-check after variant 1 ("the user rejected the category 'user-supplied source enumeration in generic code'; does my config-field variant still require the user to supply a source list? YES -> same category") would have skipped variant 2 entirely.

**See also:** coding_guidelines.md #25 (Family H parent), #19 (Family D parent), #133 (propagate a discipline to every sibling site - the inverse: propagate a redirect to every sibling variant), #72 (verify plan claims against actual source - same shape: an unverified proxy (literal mechanism) drives downstream decisions when the real thing (category) was already named).

## 136. Active Code Review Is Read-Only On the Reviewed Repo; Doc Fixes Belong In Staging Findings, Not Tracked Edits

**Principle:** Family H (Verify the real task boundary: the user agreed to a review suggestion, but the active skill mode is still read-only review, not implementation). Cross Family D (Single source of truth: the deliverable is the gitignored staging doc and/or posted PR comments, not working-tree edits on the reviewed branch).

**Trigger:** You are running `doing-code-review` (staged or direct post). The review surfaces doc gaps, config clarifications, or small fixes. The user affirms ("sure", "yes, add that") or asks for doc improvements "for clarity." You are about to edit tracked files (`openapi.yaml`, `README`, `application.yml`, architecture docs) on the reviewed project.

**Rule:** During active code review, never modify tracked project files on the reviewed repository. Record doc/test/config suggestions only in `{reviews_dir}` staging findings and PR inline comments. If the user wants the fixes applied, they must explicitly end review and start a separate implementation task (or use fix mode when explicitly requested). A user "sure" to a doc suggestion during review means include it in review output, not commit it. If you already edited tracked files by mistake, stash or revert before `done`; do not commit those edits as part of review.

**Why this matters:** Review edits on someone else's PR branch create noise, bypass the author's workflow, and violate the skill boundary ("read-only with no exceptions" when PR author is not the current user). Doc fixes mixed into review also confuse what the PR author should land vs what the reviewer changed locally.

**Shape trigger:** `doing-code-review` is active AND you are about to `Write`/`StrReplace` on any path that `git check-ignore` does not exclude, including documentation, OR the user asked for doc clarity "during" or immediately after a review thread without saying "implement" or "commit."

**Example (2026-07-06 example-crm-platform PR #9 review):** After triaging PUT vs PATCH and internal-auth doc confusion, the user said "sure" to doc clarity suggestions. The agent edited `application.yml`, `bff/README.md`, `auth/README.md`, `integrations.md`, and `project-decisions.md` on `feature/PROJ-562` while still in review mode. The user corrected that these were unallowed during PR review; changes were `git stash`ed. Correct action: add doc findings to staging (finding #6 PATCH/PUT, optional integrations note) and post comments only.

**See also:** doing-code-review `## Limitations`; coding_guidelines.md #25 (Family H).

## 137. Migration SQL Substring Guardrails: Remove Or Slim After Flyway IT, Do Not Expand

**Principle:** Family D (Single source of truth: the migration SQL file is canonical; a parallel `contains("CREATE TABLE …")` catalog in tests is a second authority that drifts on harmless edits and still does not prove the SQL runs).

**Trigger:** A PR or review touches schema migration resources (`V*__*.sql`) and has both (a) a fast classpath/string-matching guardrail test and (b) a Flyway or Testcontainers test that applies migrations against real PostgreSQL and asserts tables, constraints, or seed rows.

**Rule:** Do not suggest adding more substring assertions that mirror migration DDL (CHECK names, index names, regex fragments). After schema shape stabilizes, suggest removing the substring catalog or keeping at most a file-existence check. Prefer one runtime truth path: Flyway integration test plus mapper DB tests. Flag expansion as review noise; flag retention of a large substring list as temporary guardrail debt worth deleting.

**Why this matters:** String-matching tests break when SQL is reformatted or renamed without behavior change, while syntax errors and invalid FKs still pass. Maintainers must update SQL and the test catalog in lockstep. The guardrail made sense during initial schema bring-up or a large rename; long term it fights the migration file as SSOT.

**Shape trigger:** Review agent proposes `assertThat(migrationContent).contains("chk_*")` or similar; OR author asks whether a schema resource test still has value post-rename; OR `FlywayIntegrationTest` (or equivalent) already validates applied schema.

**Example (2026-07-06 example-crm-platform PR #11 PROJ-533):** `AuthSchemaResourceTest` substring-matched `V1__auth_core.sql` table and index names while `FlywayIntegrationTest` applied migrations and queried `information_schema`. Review initially suggested adding `chk_operators_id` assertions; reviewer dropped that and instead posted a follow-up suggesting removal of substring guardrails to avoid two schema catalogs.

**See also:** #61, #67 (Family D silent drift); doing-code-review §4.2 (drop expand-SQL-coverage findings when Flyway IT covers runtime); testing.md (prefer tests that exercise real behavior).


## 138. A Plan's Validation Grep That Targets an English Word Inside Docstrings/Prose Produces False-Positive BAD Results; Target the Symbol-Identifier Position or Exclude the Definition Site

**Principle:** Family A (Equivalence-class coverage) - the plan-authoring analog of #117 (a wording-pass review's grep target omitted method identifiers). A plan's `## Validation Commands` grep that asserts "no production caller wires Phase A type X" or "no inline threshold literal remains" is itself a grep over the corpus; underscoping that grep's PATTERN (matches the English word inside docstrings/prose, or matches the named constant's value at its DEFINITION site) produces false-positive BAD results that block the GREEN gate without indicating any real defect.

**Trigger:** A plan's Task N validation step is expressed as a grep over `src/` or `tests/` whose GOOD/BAD semantics depend on a string being ABSENT. The string is one of: (a) an English word that also happens to be a class/identifier name (e.g. "Transaction", "History", "Report"); (b) a numeric literal (e.g. `0.95`) that has a legitimate named-constant definition site elsewhere in the tree; (c) a token that legitimately appears in docstring prose describing the concept the grep is trying to ban. The implement sub-agent runs the grep, gets BAD, and must either prove the matches are all false positives (laborious) or block the GREEN gate on a plan amendment.

**Rule:** When authoring a plan validation grep whose semantics is "no production caller wires X" or "no inline literal Y remains outside its definition site," construct the pattern against the symbol-identifier position or the usage position, NOT against the bare token. For (a) identifier-name matches, anchor to call/import/annotation syntax: `grep -nE '\b(X|Y|Z)\(|from .* import .*\b(X|Y|Z)\b|:\s*(X|Y|Z)\b'` matches calls, imports, and type annotations, NOT prose mentions. For (b) literal-value matches, exclude the constant-DEFINITION file (the line `<NAME>: <TYPE> = <VALUE>`), not just `test|constants` paths - the definition site is the legitimate home of the literal. For (c) docstring-prose collisions, scope the grep to non-docstring lines (`grep -v '"""'` or `awk` outside triple-quoted blocks), or rewrite the invariant to a structural check (call-graph analysis, AST walk) rather than a text grep. A bare `grep -rn '\bX\b' src/` where X is an English word used in prose is a false-positive factory; do not ship it as a plan gate.

**Why this happens:** Plan authors write validation greps in the same casual style as one-off shell greps (`grep X src/`) and rely on the implementer to "triage" the matches. When the token collides with prose (the word "Transaction" appears in 18 docstring references to "Transaction History report"), every match is a false positive and the triage burden moves to the implementer, who must then write a justification note in the implement log and request a plan amendment. The grep itself was never going to surface a real defect because the token was never at the position the invariant cares about. The plan gate's exit code (BAD) does not distinguish "a real caller wired the type" from "a docstring mentioned the English word"; both produce the same non-zero exit.

**Required behavior:**
1. When authoring a plan validation grep, name the POSITION the invariant cares about (call site, import statement, type annotation, assignment RHS, constant definition) and construct the pattern to match ONLY that position. A bare word-boundary pattern is acceptable only when the token is unambiguous (a coined identifier with no English-meaning collision, e.g. `TxCorrelationKey`).
2. For threshold/literal-ban greps, exclude the named constant's definition file explicitly (e.g. `account_kind.py` for `HIGH_PROBABILITY_THRESHOLD = 0.95`), not just `test|constants` paths. The definition site is the legitimate home of the literal; banning it there is a self-contradictory gate.
3. When a docstring-prose collision is unavoidable (the token IS an English word the codebase discusses in prose), prefer a structural check (AST walk, call-graph analysis) over a text grep, or scope the grep to non-docstring regions. Record the refined pattern in the implement log and route a plan-amendment request to narrow the original pattern.
4. Before flipping the GREEN gate on a BAD grep result, the implementer must verify EACH match is at the position the invariant bans (call/import/annotation/assignment), not at a prose or definition position. A grep that prints BAD with all matches in prose/definitions is a false-positive gate, not a defect; annotate the plan clause and proceed.

**Shape trigger (when to suspect this family):** A plan's validation step is expressed as `grep ... src/ && echo BAD || echo GOOD` (or the inverse). The token is an English word used in docstrings OR a numeric literal with a named-constant definition. The implement log records the grep as BAD with a note "all N matches are false positives" or "single match is the constant definition." The plan author did not specify the position the grep targets.

**General form:** A validation grep's discriminating power lives in WHERE the token appears (call site vs. prose vs. definition), not WHETHER the token appears as a bare string. A pattern that ignores position produces false-positive BAD results that block the GREEN gate without indicating any real defect. Author the pattern against the position, or replace the text grep with a structural check.

**Example (2026-07-05 Phase A plan, Task 9 validation greps):** Two of the plan's four validation greps printed BAD on a clean tree. (a) A grep for the new type names matched the prose word "Transaction" inside 18 docstring references to "Transaction History report" / "Transaction History CSV" / "transaction/network fee." Zero matches were `import Transaction`, `Transaction(...)`, or `: Transaction` - the actual positions the "no production caller wires Phase A types" invariant cares about. (b) `grep -nE '0\.95' src/ tests/ | grep -v -E 'test|constants'` matched the single constant definition site in the account-kind module because the exclusion list covered `test|constants` paths but not the constant's actual home module. Both underlying invariants held; both greps blocked the GREEN gate on a false positive. The implement log documented the false positives and the orchestrator annotated the plan clause. Recommended refined patterns: (a) anchor to call/import/annotation syntax; (b) add the constant's home module to the exclusion list or match `0.95` only on non-definition lines. See the Task 9 implement log (local).

**Distinguishing from #117:** #117 is about a wording-pass REVIEW whose grep target omitted the method-IDENTIFIER position after a rename; the false negative was staleness surviving at an unscanned position. This lesson is about a PLAN VALIDATION grep whose pattern matched the WRONG position (prose/definition) producing a false positive BAD; the failure is a gate blocking on noise, not staleness surviving. Both share the root cause "a grep whose target is underspecified," but #117's symptom is silent staleness and this lesson's symptom is a noisy false-positive gate. The position-awareness prescription is the same family of fix.

**See also:** #117 (wording-pass review grep target omission, identifier position), #84 (name-vs-body coverage gap), #150 (changed rendered label grep), #159 (cross-task contract change grep), coding_guidelines.md #18 (Family A equivalence-class coverage).


## 139. A Plan-Prescribed Cleanup-Audit Grep Must Enumerate Every Surface Where the Removed/Renamed Token Can Survive; an Audit Path Scoped to `src/` Only Will Pass Clean While Stale References Survive in `docs/` and Law-Archive READMEs

**Principle:** Family H (Verify the real thing, at the right population) - a cleanup audit's population is the SET of surfaces where the removed/renamed token can survive, not the one surface the plan author mentally associates with "production code". Compounded by Family A (Equivalence-class coverage) - the audit grep's PATH argument defines the equivalence class under test; narrowing it to `src/` while the token also lives in `docs/` undersamples the class.

**Trigger:** A plan task removes or renames a concept (deletes an alias, drops a numbered-suffix form like `Provider A (2)`, retires a code path, sunsets a flag value). The plan prescribes a Task-N cleanup-audit grep whose job is to verify no stale references survive. The audit's PATH is scoped to the production-code tree only (e.g. `grep -rn '<token>'` in the source tree). The implement sub-agent runs the prescribed grep, gets CLEAN, logs the audit as PASS, and the task closes. A later review round re-runs the same grep with a WIDER path (e.g. across the source tree AND the maintenance docs) and finds stale references surviving in docstring examples, implementation-guideline spec blocks, plan-quality examples, or law-archive README files.

**Rule:** When authoring a plan task whose job is "verify the removed/renamed token is gone from the codebase," the audit grep's PATH must enumerate EVERY surface where the token can survive a removal: production source (`src/`), tests (`tests/`), rendered-text constants, decision-point docs (`docs/maintenance/`), rules docs, implementation-guideline spec blocks AND EXAMPLES, law-archive README files (these often restate rules in prose), and any emitted-text fixtures. The author's mental model "this is a production-code change, so audit production code" is wrong for cleanups: a removal propagates docstring, doc, and law-archive updates as a matter of course, and those surfaces carry the same stale token the audit was designed to catch. A cleanup audit scoped to `src/` only is a false-negative factory: it passes CLEAN over a corpus that still contains the stale token at the unscanned surfaces.

**Why this happens:** The plan author writes the audit in the same casual style as a one-off dev grep (`grep X src/`) and mentally files "production code" as the surface that matters. But a removal audit's invariant is "the token is GONE from the codebase", not "the token is gone from production code". Docstring examples, spec blocks in implementation guidelines, decision-point prose, and law-archive READMEs are PART of the codebase for removal-audit purposes; they survive removals because they are not in the production-code path the author audits. The audit returns CLEAN; the stale references survive; only a later review round that re-greps with a wider path surfaces them. By then the cleanup task has closed and the fix lands in a review-iteration commit, costing a round.

**Required behavior:**
1. When authoring a plan task that removes or renames a concept (alias, numbered-suffix form, flag value, code path), enumerate the surfaces where the token can survive BEFORE writing the audit grep. The minimum surface set for a removal: `src/`, `tests/`, `docs/maintenance/` (including subdirs: rules, guidelines, decision points), law-archive READMEs (`docs/maintenance/tax/.../README.md`), rendered-text constants in source, and any emitted-text fixtures. Project-specific surfaces (callers in build configs, README examples, presentation artifacts) extend this set.
2. Construct the audit grep PATH to cover the enumerated set explicitly: `grep -rn '<token>' src/ tests/ docs/maintenance/` (or wider if the project has additional doc trees). A bare `grep -rn '<token>' src/` is acceptable only when the token's removal is provably scoped to production code (e.g. an internal helper with no docstring, doc, or example footprint).
3. Pay special attention to law-archive READMEs and decision-point prose: these restate rules in human-readable form and frequently echo the very token a cleanup removes. The cleanup that motivated the audit often STARTED in production code but the rule it implements is restated in the README, so the README is a high-probability survival surface.
4. The cleanup-audit grep is distinct from a validation grep (which bans a token at a position). A cleanup audit asserts ABSENCE across the codebase; its population is EVERY surface. A validation gate asserts ABSENCE at a position; its population is one position class. Cleanup audits enumerate surfaces; validation gates enumerate positions.
5. Before logging the audit as PASS, the implementer must verify the prescribed grep PATH covers at minimum `src/`, `tests/`, and `docs/`. If the plan author scoped the audit to `src/` only, the implementer must WIDEN the path (and annotate the implement log) rather than run the narrow command and report CLEAN.

**Shape trigger (when to suspect this family):** A plan task says "remove `<token>` (alias / numbered-suffix form / flag value) and audit that no stale references survive." The audit command is `grep -rn '<token>' src/...` (production-code path only). The implement log records the audit as CLEAN/PASS. The token was ALSO referenced in docstring examples, implementation-guideline spec blocks, law-archive READMEs, or decision-point prose - surfaces the grep path omitted. The cleanup task closes; the stale references survive until a review round re-greps with a wider path.

**General form:** A removal/renaming audit's discriminating power lives in WHICH SURFACES the grep enumerates, not in whether the token appears at any one surface. A path that omits the surfaces where the removed token was ALSO restated (docs, READMEs, guideline examples, law archives) produces a false-negative CLEAN that lets stale references survive the cleanup. Author the audit path to enumerate every surface where the token can live, or accept that the cleanup is incomplete and route the surviving references to a follow-up.

**Example (2026-07-05 Phase A plan, Task 8 alias removal):** Task 8 removed the numbered-alias normalization (`Provider A (2)` -> `Provider A`) and prescribed a cleanup-audit grep for `Provider A (2)\|Provider A (3)` in the source tree to verify no stale production references survived. The implement sub-agent ran it, got CLEAN, logged PASS, and Task 8 closed. Round-1 review re-ran the same token across the source tree AND the maintenance docs and found 5 stale references the audit path omitted: (a) a docstring example in the chain-derivation module still used `Provider A (2)`; (b) the implementation-guidelines doc Pitfall 4 code example and the matching spec still referenced `Provider A (2)`; (c) the plan-quality guidelines boundary-test example still used `Provider A (2)`; (d) the law-archive README still restated the "must be normalized to the same source name" rule with the `Provider A (2) -> Provider A` chain-derivation example. The audit grep's path (the source tree only) was scoped to production code only and missed every doc/README surface where the same token lived. The fix landed in the round-1 address-review commit. See the Phase A plan Task 8 audit clause, the r1 doing-code-review log Finding 1, and the r1 receiving-code-review log.

**Distinguishing from #106 (corrected domain rule surface propagation):** #106 is the REACTIVE analog: a review finding flags a stale rule in ONE location, and the lesson is "grep the stale wording across the corpus before closing the finding." This lesson is the PLAN-TIME analog: the plan AUTHOR prescribes the cleanup audit grep, and the lesson is "author the audit PATH to cover every surface where the token can survive, not just `src/`". Both share the root cause "a stale-token grep whose scope is too narrow"; #106's trigger is a finding (post-hoc), this lesson's trigger is plan authoring (ante-hoc). The path-enumeration prescription is the same family of fix.

**Distinguishing from #138 (plan validation grep position):** #138 is about a plan validation grep whose PATTERN matches the wrong POSITION (prose vs definition vs call site), producing a false-positive BAD that blocks the GREEN gate. This lesson is about a plan cleanup-audit grep whose PATH omits the surfaces where the token lives, producing a false-negative CLEAN that lets stale references survive. Both share the root cause "a plan-prescribed grep whose author under-specified what it should examine"; #138's symptom is gate-blocking noise, this lesson's symptom is silent staleness surviving a cleanup. The fix prescriptions differ: #138 refines the PATTERN (anchor to position); this lesson widens the PATH (enumerate surfaces).

**Distinguishing from #85 (validation over shared directory with legacy entries):** #85 is about a validation grep whose path is too BROAD (false-fails on legacy siblings the new convention does not cover). This lesson is about a cleanup-audit grep whose path is too NARROW (false-passes on stale references at omitted surfaces). Both share the root cause "a plan grep whose population is mis-scoped"; #85's symptom is false failure, this lesson's symptom is false success. The fix prescriptions are inverse: #85 NARROWS the path or accepts the legacy token; this lesson WIDENS the path to cover every surface.

**See also:** #106 (corrected domain rule surface propagation, the reactive analog), #138 (plan validation grep position vs cleanup-audit path), #85 (validation over shared directory with legacy, the inverse scoping hazard), #117 (wording-pass review grep target omission), coding_guidelines.md #22 (Family H verify the real thing).

## 140. A Plan Task That Prescribes a Placeholder Value or Verify Command Must Cross-Check It Against Every Downstream Guard and Reader in the Same Plan; a Placeholder That Satisfies One Task Can Violate Another Task's Invariant

**Principle:** Family H (Verify the real thing, not the abstraction) - a placeholder VALUE prescribed by a plan task is an abstraction over "this byte sequence passes every guard and reader the SAME plan prescribes downstream"; the plan author who writes `0x + 64 zeros` and asserts it satisfies "no real identifier" has verified the abstraction (the description "synthetic-looking") and not the real thing (the regex `(0x[0-9a-fA-F]{40,})|([0-9a-fA-F]{64})` that a later task's guard runs against the fixture). The same hazard applies to a verify COMMAND prescribed in one task whose reader chain differs from the production reader chain another task's tests use: the count or shape it asserts is an abstraction over "raw `csv.DictReader` happens to behave like `read_source_rows` here", which is false whenever the format has a title line.

**Trigger:** A plan contains a task that prescribes (a) a specific placeholder/constant value (a synthetic identifier, magic string, all-zero hex, well-known sentinel) AND a LATER task in the same plan whose guard/test/validation consumes that value via a regex, equality check, or parser. OR (b) a verify one-liner using a primitive (`csv.DictReader`, raw `open()`, bare `json.load`) AND a later task whose tests or characterization uses the production reader chain. The implement sub-agent for the earlier task follows the prescription verbatim and logs PASS; the later task's guard/test then fails (or would fail) on the same value/command, and the orchestrator must amend mid-execution.

**Rule:** When authoring or revising a plan task that prescribes a placeholder value or a verify command, the plan author must enumerate EVERY other task in the same plan whose guard, test, regex, or reader touches that value or path. For each enumerated downstream site, the author verifies (by reading the actual guard/regex/reader source) that the prescribed value/command satisfies the downstream site. If it does not, the prescription must be revised BEFORE execution starts. Sub-agents implementing the task who detect the collision mid-execution must halt, surface the contradiction to the orchestrator, and request an amendment rather than silently substituting a different value.

**Why this happens:** The plan author writes the placeholder in a natural style (`0x + 64 zeros reads as "obviously synthetic" to a human`) and files it as "obviously safe". The downstream guard's regex was authored against a DIFFERENT intuition ("any 64-hex string is a real identifier"), and the two intuitions never meet because the plan never cross-checks them. For verify commands, the author reaches for the most primitive reader (`csv.DictReader`) because it is the shortest incantation, forgetting that production code has a title-line-detecting wrapper (`_detect_header_index`) precisely because the raw primitive does not handle the format. The plan-as-written is internally consistent at the prose level; the plan-as-executed collides at the value/byte level.

**Required behavior:**
1. Placeholder values: before writing `<placeholder>` into a plan task body, grep the plan for every regex, equality check, and parser signature that will consume the fixture/identifier/value downstream. For each match, confirm the placeholder satisfies the consumer. If any consumer would reject the placeholder, choose a different placeholder that satisfies ALL consumers (e.g. a non-hex sentinel like `synth-event-multirecord-001` instead of all-zero hex, when a downstream regex would match all-zero hex).
2. Verify commands: prefer the PRODUCTION reader chain (`read_source_rows`, the loader entry point, the parser under test) over raw primitives (`csv.DictReader`, bare `open()`). The expected count in the verify step must be derived from running the production reader against a known-correct fixture, not from the author's mental arithmetic on data rows. If the production reader is unavailable in a one-liner, write a small script that imports it; do not fall back to the primitive and annotate the count discrepancy post-hoc.
3. Cross-task consistency: when a later task's test/guard is the canonical consumer of an earlier task's output, the earlier task's prescription must cite the later task's invariant by name (e.g. "satisfies `test_no_real_data_in_fixtures` regex at Task 7"). The citation forces the author to read the downstream site before prescribing.
4. Implementer escalation: when a sub-agent detects mid-execution that the plan's prescription collides with a downstream guard in the same plan, the sub-agent must halt and request an amendment. Silently substituting a different value hides the contradiction from the orchestrator and from any future reader of the implement log.

**Shape trigger (when to suspect this family):** A plan task prescribes a placeholder value or a verify command, AND a later task in the same plan (or a review scope clause in the same plan) defines a guard/regex/reader that consumes that value/path. The implement log records the earlier task as PASS; the later task fails (or the orchestrator amends the placeholder between tasks). The plan's prose is internally consistent; its bytes are not.

**General form:** A plan's prescriptions are a SYSTEM, not a list. Each prescribed value or command has a downstream consumer within the same plan, and the consumer's behavior is determined by its actual implementation (regex pattern, reader chain), not by the prose intuition the author used when prescribing. Verifying the prescription against the prose of the downstream task is Family H violation; verifying against the actual regex/reader source is the cure.

**Example (2026-07-07 Phase C plan, Task 1 multi-record fixture):** Task 1 prescribed `event_id = 0x + 64 zeros` as the obviously-synthetic placeholder. Task 7's `test_no_real_data_in_fixtures` regex `(0x[0-9a-fA-F]{40,})|([0-9a-fA-F]{64})` matches all-zero hex (it is a 64-hex string). Task 1's verify one-liner `parse OK 1` expected exactly 1 row, but used raw `csv.DictReader`, which counts the `Source export 2025` title line as a row (the production reader `read_source_rows` skips it via `_detect_header_index`). The orchestrator detected both collisions mid-execution and switched the placeholder to `synth-event-multirecord-001` (non-hex), and the implement log documented the verify-count discrepancy as a property of the raw primitive, not the fixture. Both fixes were correct, but the plan should have caught them at authoring time by cross-checking the placeholder against Task 7's regex source and by deriving the verify count from the production reader.

**Distinguishing from #139 (cleanup-audit grep path scope):** #139 is about a grep whose PATH is too narrow for a removal audit. This lesson is about a placeholder VALUE or verify COMMAND whose byte-level shape collides with a downstream consumer in the same plan. Both share Family H (verify against the real thing); #139's fix is widening the PATH, this lesson's fix is cross-checking the VALUE/COMMAND against every downstream guard/reader before execution.

**Distinguishing from #138 (validation grep pattern position):** #138 is about a grep whose PATTERN matches the wrong position. This lesson is about a placeholder value colliding with a downstream regex or a verify command using the wrong reader chain. #138's symptom is gate-blocking noise; this lesson's symptom is mid-execution orchestrator amendment or a fixture that fails a later task's guard.

**See also:** #138 (plan validation grep position), #139 (plan cleanup-audit grep path scope), coding_guidelines.md #22 (Family H verify the real thing).


## 141. A Count Snapshot Captured Before a Consumption Loop Cannot Serve as the Loop's "Is There Still an Item?" Guard Once the Loop Drains the Structure the Count Described

**Principle:** Family E (Temporal / ordering invariants) - a count (`len(collection)`) captured into a local BEFORE a loop is a FROZEN snapshot of the collection's size at that instant. If the loop body then mutates the collection (`popleft`, `pop`, `del`, `append`), the frozen count diverges from the LIVE size. Using the frozen count as a "should this iteration still try to consume?" guard (e.g. `if source_count[key] == 0: skip`) produces a category error: the guard answers "were there any items before the loop started?" when the question is "are there any items RIGHT NOW, after prior iterations already consumed some?" Compounded by Family H (Verify the real thing, not the abstraction) - the variable name (`source_count`, `initial_size`, `bucket_size`) is an abstraction over the live collection; the correctness property ("the bucket is empty, fall through") is a property of the live `len(collection)`, not of the named snapshot.

**Trigger:** A matcher/aggregator/corrector builds a `dict[key] -> collection` index, captures a per-key count (`counts = {k: len(v) for k, v in index.items()}`) BEFORE the consumption loop, then iterates calling `index[key].popleft()` (or `.pop()`, `.popitem()`, `del`) inside the loop. The same loop consults `counts[key]` to decide whether to attempt a match or fall through. The data shape that surfaces the bug: ONE key with MORE target items than source events (a calculated-rows key with 3 matched items but only 1 tagged upstream row). The first iteration pops the only item; the count snapshot still says `source_count[key] == 1`; the second iteration's `if source_count[key] == 0` guard is False (the snapshot is stale), so it does NOT fall through and instead attempts a second pop on the now-empty collection (IndexError) OR, worse, silently skips a candidate it should have processed because the guard was inverted.

**Rule:** When a loop consumes items from a mutable collection indexed by key, the "is there still an item for this key?" guard MUST read the LIVE collection's length (`len(index[key]) == 0`), not a count variable captured before the loop. The pre-loop count may exist for other purposes (logging "expected matches", detecting all-empty inputs, emitting a surplus summary) but MUST NOT gate per-iteration consumption. If the pre-loop count is the only signal a downstream summary needs, compute the summary from the post-loop residual (`len(index[key])` after the loop), not from `initial - consumed` arithmetic.

**Why this happens:** The implementer builds the count to drive a preflight check ("skip keys with zero items entirely") and then reuses the same variable inside the loop because it is already in scope and reads naturally (`if source_count[key] == 0: continue`). The reuse is correct ONLY for the FIRST iteration (where live `len` equals the snapshot). From the second iteration on, the snapshot is stale. The bug is silent when every key has exactly one source event (snapshot and live size agree on every iteration) and surfaces only when a key has more targets than events - precisely the partial-match case the matcher exists to handle.

**Required behavior:**
1. Capture the pre-loop count ONLY for purposes that do not gate per-iteration consumption: preflight skip of all-empty inputs, post-loop surplus reporting, expected-vs-actual logging.
2. Inside the consumption loop, guard with the LIVE collection: `if not index[key]: continue` or `if len(index[key]) == 0: continue` (reading the collection, not the snapshot).
3. When the loop is structured as `for key in keys: if index[key]: item = index[key].popleft()`, the live-empty check is implicit in the truthiness test; do NOT additionally consult a snapshot count.
4. If a refactor moves from "one item per key" to "deque per key" (UL#81), re-audit every guard that referenced the old scalar count: those guards are now snapshots over a mutable deque and must switch to live `len(deque)`.

**Shape trigger (when to suspect this family):** A function captures `counts = {k: len(v) ...}` before a loop, the loop calls `.popleft()` / `.pop()` / `del` on `v`, and the loop body branches on `counts[k]`. The symptom is either an IndexError on the second iteration of a multi-target key, OR a partial-match case (more targets than events on one key) that silently skips processing or silently double-consumes. A single-event-per-key test passes; a multi-target-key test fails or silently drops data.

**General form:** A size snapshot is correct only at the instant it is taken. Any guard that must answer "what is the state NOW?" must read the live structure, not the snapshot. The name of the snapshot variable (`source_count`, `initial_counts`) does not carry the temporal invariant; only reading the live collection does.

**Example (2026-07-10 Phase D plan, Task 4 treatment-filter flip):** `correct_values` builds `source_count = {key: len(bucket) for key, bucket in source_rows_by_key.items()}` before the per-item consumption loop. The loop calls `bucket = source_rows_by_key.get(key); bucket.popleft()` for each matched item. The original early-bucket guard was `if bucket is None or source_count.get(key, 0) == 0: continue`, which is correct only when every key has exactly one source row (snapshot equals live size on every iteration). Under the new `via_resolver=True` path, the caller pre-filters source rows to a specific treatment type, so a matched key with 3 items can have only 1 treatment-matched source row. The first item consumes the row (`popleft`); `source_count[key]` still reads `1` (frozen); the second item's guard `source_count.get(key, 0) == 0` is False, so it does NOT fall through, and the subsequent `bucket.popleft()` on the now-empty deque raises `IndexError` (or, in a variant, silently no-ops the surplus item instead of leaving it for the fallback correction path). The fix widened the guard to `if bucket is None or source_count.get(key, 0) == 0 or len(bucket) == 0: continue`, adding the live `len(bucket) == 0` check so a drained deque is detected regardless of the stale snapshot. See the Task 4 implement log "Early bucket check widened" note.

**Distinguishing from #60 (ordered queue per non-unique key):** #60 prescribes BUILDING the deque and popping one per event. This lesson assumes the deque already exists (the matcher follows #60) and prescribes the GUARD shape once consumption drains it: the per-iteration "is the bucket still non-empty?" test must read live `len(deque)`, not a pre-loop count snapshot. #60 is the data-structure lesson; this lesson is the guard-shape lesson that becomes load-bearing once #60's deque is in place and a partial-match key surfaces.

**Distinguishing from #61 (recompute tolerance after every shrink step):** #61 is about a DERIVED value (tolerance) that depends on a mutable window size and must be recomputed after every shrink. This lesson is about a COUNT value that depends on a mutable collection size and must not be reused as a guard after every pop. Both share Family E (a derived value captured before mutation diverges from the post-mutation state); #61's fix is recompute-inside-loop, this lesson's fix is read-live-collection-inside-loop.

**See also:** #60 (ordered queue per non-unique key, the data structure this guard protects), #61 (recompute window-relative tolerance, sibling "derived value vs mutable state" hazard), #82 (matcher temporal-invariant triple), coding_guidelines.md #22 (Family E temporal / ordering invariants).


## 142. A Short SHA Verified by `git rev-parse --verify <prefix>` Can Be a Phantom Abbreviation Match Against an Unrelated Commit; Reconcile SHAs in Canonical Docs by Full Hash and Cross-Check With `--all` Oneline

**Principle:** Family H (Verify the real thing, not the abstraction) - a short SHA prefix (e.g. `45171a5`) passed to `git rev-parse --verify` is an abstraction over "some commit in this repository, on some ref, whose full 40-hex SHA begins with these 7 hex characters". The command succeeds via ABBREVIATION MATCH against ANY candidate commit sharing that prefix; it does NOT confirm the short SHA is the prefix of the SPECIFIC commit the author intended (the "Phase C landing", the "release tag", the "fix commit referenced in the postmortem"). When the intended SHA does not exist on any ref (was mis-transcribed, came from a different clone, or was the author's mnemonic rather than a real hash), `--verify` STILL exits 0 if any unrelated commit happens to share the prefix, producing false confidence that the citation is correct. Compounded by Family G (Data-loss observability) - the silent failure mode is a canonical doc (feature-notes, postmortem, changelog) citing a SHA that resolves to a completely unrelated commit, and every future reader who clicks the short link lands on the wrong revision with no warning.

**Trigger:** A canonical document (feature-notes, postmortem, CHANGELOG, README history section, plan hand-off log) records a short SHA (7-12 hex) purporting to identify a specific milestone commit. A later task "reconciles" the citation by running `git rev-parse --verify <short>` or `git rev-parse <short>^{commit}`. The command exits 0, and the reconciler records "SHA verified" without printing the FULL resolved SHA and without checking that the resolved commit's metadata (subject, author date, files changed) matches the milestone the citation claims. The abbreviation-prefix collision is silent: git does not report "matched by abbreviation" vs "matched by exact short-SHA identity", and the reconciler treats exit 0 as the verification claim.

**Rule:** When reconciling a SHA cited in a canonical doc against the live repository, the reconciler MUST:
1. Print the FULL resolved SHA (`git rev-parse <short>`) and paste the full hash (or at least the first 12+ hex) into the doc, not the short prefix.
2. Print the commit's `git show -s --format='%H %an %ad %s' <resolved>` and confirm the subject, author, and date match the milestone the citation describes. A SHA whose resolved subject is "Task 10: opt-in smoke" cannot be the "Phase C landing" no matter how cleanly `--verify` exited.
3. When the cited short SHA does not resolve at all (`git rev-parse --verify --quiet <short>` exits non-zero on a fresh `git fetch`), do NOT accept an abbreviation match as a fallback. Treat the citation as WRONG and search for the correct commit by subject/date (`git log --all --oneline --grep="<milestone phrase>"`) before re-citing.
4. In repositories with multiple long-lived branches or a busy master, prefer citing the merge-commit SHA or a tag over a short prefix; tags and merge SHAs are stable identities, abbreviation matches are not.

**Why this happens:** `git rev-parse --verify <short>` is documented as resolving "a single valid SHA-1" and exits 0 on abbreviation matches by design (this is how short-SHA CLI ergonomics work for everyday `git show abc123`). The reconciler reads "exit 0" as "the SHA is real and is the one I meant", conflating "git found A commit with this prefix" with "git found THE commit I cited". The conflation is invisible when the cited SHA is correct (the two readings coincide) and surfaces only when the cited SHA is wrong AND an unrelated commit shares the prefix - a low-probability event per citation, but a near-certainty across a corpus of dozens of cited SHAs accumulated over months.

**Required behavior:**
1. Canonical docs that cite a commit MUST cite the full 40-hex SHA (or a tag/merge SHA), never a 7-hex short prefix as the canonical identifier. Short prefixes are acceptable in prose ("see commit abc123f") but the doc's authoritative citation (the line a future `git show` is run against) is the full hash.
2. A reconciliation task that verifies a cited SHA MUST log the full resolved SHA, the subject, and the author date in the task's implement log, and MUST diff those against the milestone's expected metadata. "rev-parse exited 0" alone is not verification.
3. When a cited short SHA resolves but the resolved commit's subject/date do not match the milestone, the reconciliation MUST flag the citation as a phantom match, search for the correct commit, and update the doc with the authoritative full SHA. Do not propagate the phantom.
4. Reconciliation scripts that automate SHA verification MUST use `git rev-parse --verify --quiet <short>` AND `git log -1 --format=%H <short>` AND assert the resolved full SHA starts with the cited short prefix AS-WRITTEN; if the only match is via git's abbreviation disambiguation against a different prefix, the assertion fails.

**Shape trigger (when to suspect this family):** A doc cites a short SHA. A verification step says "rev-parse --verify passed". The reconciler did not print the resolved full SHA or compare its subject to the milestone. The cited SHA, when inspected, resolves to a commit whose subject is on a different topic, a different task, or a different phase than the citation claims. The probability of phantom collision rises with repository age and commit count (more commits = more 7-hex prefixes = more collisions).

**General form:** "git accepted the short identifier" is not "git identified the intended object". Git's short-identifier resolution is a convenience over a SEARCH over all objects, not an IDENTITY check against a specific object. Any verification that treats search-success as identity-confirmation is Family H: the exit code is an abstraction over the resolution mechanism, and the real thing (which specific commit was resolved) requires inspecting the resolved object's metadata.

**Example (2026-07-10 Phase D finalize, Task 11):** The feature-notes doc cited Phase C as commit `45171a5`. The Task 11 reconciliation ran `git rev-parse --verify 45171a5` which exited 0 and resolved via git's short-SHA search to `0449a9b` (the Task 10 HEAD on the Phase D branch), an unrelated commit whose subject ("Task 10: opt-in real-data smoke") had nothing to do with Phase C ("Phase C synthetic corpus + one-shot shadow verification"). `45171a5` is NOT the prefix of any real commit on any ref; the resolution succeeded only because git's abbreviation disambiguation accepted it as a search key. The authoritative Phase C landing on both local master and origin/master is `d158904`. The reconciliation correctly flagged the phantom, searched by subject (`git log --all --oneline | grep "Phase C"`), found `d158904`, and updated the feature-notes citation to the authoritative full SHA. The lesson is that the FIRST verification (`rev-parse --verify 45171a5`) gave a false-green that would have propagated the phantom citation if the reconciler had stopped at exit 0.

**Distinguishing from #140 (placeholder value collides with downstream guard):** #140 is about a VALUE colliding with a regex/reader. This lesson is about an IDENTIFIER colliding with an unrelated object via search disambiguation. Both share Family H; #140's fix is cross-checking the value against every downstream consumer, this lesson's fix is printing and metadata-checking the resolved object.

**Distinguishing from #32 (lock key resolution from field semantics not population counts):** #32 is about resolving a KEY from field meaning rather than prevalence. This lesson is about resolving an IDENTIFIER from object metadata rather than prefix-search success. Both share Family H; #32's hazard is collapsing two semantically distinct fields, this lesson's hazard is collapsing two distinct commits that share a hex prefix.

**See also:** #32 (lock key resolution from field semantics not population counts), #140 (plan placeholder collides with downstream guard), coding_guidelines.md #22 (Family H verify the real thing).


## 143. When Updating a Fenced Markdown Template, Prefer Exact-Match Micro-Edits Over Full-Block Replacement to Avoid Fragile Patches and Accidental Drift

**Principle:** Family H (Verify the real thing, not the abstraction) - a fenced Markdown template is a real artifact with multiple invariants (opening fence marker, closing fence marker, required headings, and exact phrasing used by downstream tooling). A full "replace the whole fenced block" edit is an abstraction over many independent invariants. It is easy to accidentally change unrelated lines, break the closing marker, or retain legacy subsections while believing the template was converted. Micro-edits force verification at the granularity of each invariant and keep unrelated text unchanged.

**Trigger:** A workflow spec or skill contains a large fenced Markdown template. The change request is structural ("switch to a universal hierarchy", "add per-finding fields") but the implementer attempts a one-shot full replacement of the fence contents. Reviewers then see unrelated diffs, or the template looks updated but still contains legacy headings further down in the same fence.

**Rule:** Update fenced templates via a sequence of exact-match micro-edits:
1. Re-read the exact on-disk fenced block content first.
2. Replace only one legacy subsection at a time using an exact-match patch (unique pre and post context).
3. Preserve the original closing fence marker exactly.
4. Verify with a targeted search that required new fields exist, and that forbidden legacy headings do not exist inside the fence.

**Why this happens:** Large blocks create brittle patches because a tiny mismatch in whitespace, an ellipsis placeholder, or a prior local edit causes the patch to fail or to replace the wrong region. Even when it applies, full-block replacement makes it hard to review what changed vs what was unintentionally reformatted.

**Required behavior:**
1. Limit each patch to one subsection inside the fence (or one finding template), then re-check the file.
2. After conversion, run focused checks for required headings and removed headings scoped to the fenced block.
3. Keep everything else in the document unchanged unless the task explicitly calls for broader refactors.

**Shape trigger (when to suspect this family):** The diff shows a large fenced block entirely rewritten, the closing fence marker moved or changed, or legacy headings still appear later in the same fenced block after an attempted conversion.

**General form:** Preserve local invariants by editing only the minimal surface needed, and verify each invariant directly after each micro-change.


## 144. Multi-Agent Review Harnesses Need Structured Staging Metadata to Improve Sub-Agents Iteratively

**Principle:** Family G (Defensive warnings must also record items in the failure-tracking structure) extended to harness observability: a review panel without recorded discard reasons, dedup groups, pattern tags, and post-triage outcomes is a chat summary, not an improvement loop.

**Trigger:** A project runs many parallel review sub-agents but cannot answer which agents are redundant, which catalog patterns produce mostly false positives, or which findings survive triage. The team debates adding or removing agents without aggregate data.

**Rule:** Every review orchestrator must write a staging doc under `{reviews_dir}/` with immutable synthesis statistics (Panel with Solo/Echo, Discarded findings with reason codes and Pattern ids, Severity calibration, Deduplication groups) plus mutable **Triage outcomes** after fix passes. Sub-agents return `pattern: <agent>#<kebab-slug>` on each finding. Gold source: `review-staging` skill in the skills repo.

**Why this happens:** Raw agent output mixes in chat or ephemeral memory. Without per-agent discard reasons and triage rollups, the only signal is "too many findings" or "clean round," which does not identify catalog gaps or over-eager agents.

**Required behavior:**
1. Record statistics during synthesis, not from memory after reporting to the user.
2. Tag each finding with **Pattern** so `review-agents/*.md` edits can target high-discard patterns.
3. Update **Triage outcomes** after `receiving-code-review` without rewriting synthesis tables.
4. Emit a required `.stats.json` sidecar for aggregation across reviews; use `wrong-owner` discard code with `lead: <agent>` when tiered ownership merges non-lead returns.

**Shape trigger (when to suspect this family):** Review workflows exist but there is no `{reviews_dir}/` artifact with `## Review Statistics`, or staging docs lack **Agents**, **Pattern**, and discard **Reason** columns.

**General form:** Treat multi-agent review like an instrumented pipeline: every rejection and every fix must be attributable to an agent and a pattern, or you cannot tune the panel.

**See also:** `agents/skills/review-staging/SKILL.md`, `agents/skills/review-agents/SKILL.md`, `agents-best-practices/references/agent-legibility-feedback-loops.md`.


## 145. Vendored Skills Must Use Upstream License and Doc-Hierarchy Paths

**Principle:** Family A (Single source of truth for canonical paths and attribution) applied to skill vendoring: copied skills inherit upstream copyright and write docs only into paths the repo schema already owns.

**Trigger:** Importing skills from an external registry (for example mattpocock/skills) into `agents/skills/`, or adapting a skill that assumes root `CONTEXT.md`, `docs/adr/`, or a parallel decisions directory.

**Rule:**
1. Copy the upstream root `LICENSE` verbatim into each vendored skill's `LICENSE.txt`; never substitute the first-party `plans/LICENSE.txt` copyright.
2. Record `metadata.upstream` in `SKILL.md` frontmatter and document re-sync in `agent-runtime-layout.md`.
3. When a vendored skill writes glossary or ADR content, map to doc-hierarchy Layer 2: `docs/maintenance/glossary.md`, `docs/maintenance/project-decisions.md` (append `## ADR-NNNN` sections), and `docs/architecture/domain-model.md`; do not introduce `maintenance/decisions/` or root `CONTEXT.md` on migration-complete repos.
4. Merge overlapping meta-skills (for example skill-design vocabulary) into `how-to-write-skills/references/` instead of keeping a duplicate skill directory.

**Shape trigger (when to suspect this family):** A new vendored skill creates doc paths not listed in `doc-hierarchy/migration-map.md`, or its `LICENSE.txt` carries the playbook author's copyright instead of the upstream author's.

**See also:** `agents/skills/how-to-write-skills/SKILL.md` (LICENSE section), `agents/skills/domain-modeling/SKILL.md`, `projects/.ai-playbook/agent-runtime-layout.md`, `projects/.ai-playbook/skill-upstream-catalog.md`.


## 146. Merge Upstream Review and Discipline Patterns Before Vendoring Duplicate Skills

**Principle:** Family A (Single source of truth) applied to external skill catalogs: when an upstream repo overlaps first-party skills or always-on instructions, absorb patterns into the existing artifact and catalog the source as reference-only instead of adding a parallel skill directory.

**Trigger:** Evaluating an external registry (for example DietrichGebert/ponytail, karpathy-guidelines, cc-thingz plugins) where some modules duplicate `doing-code-review`, `docs/AGENTS.md` coding discipline, or `execute-plan`.

**Rule:**
1. Record the source in `skill-upstream-catalog.md` with **Reference only** or **Partially vendored** status and local overlap notes.
2. Merge review output conventions (tag vocabulary, one-line finding format, scope boundaries) into `review-agents/*.md` sub-agent files consumed by existing orchestrators.
3. Merge implementation-time discipline (decision ladders, safety carve-outs) into `coding_guidelines.md` numbered rules and cross-link from `docs/AGENTS.md`; do not add a persistent session-mode skill that fights always-on instructions.
4. Vendor standalone directories only when the workflow is unique (for example `grilling`, `handoff`) and not already covered by first-party skills.
5. Add each merged upstream **file** URL to `skill-upstream-catalog.md` **Merged pattern index** (repo-level row alone is not enough for refresh).

**Shape trigger (when to suspect this family):** A proposed import adds a skill whose description says "use on ANY coding task" or "ACTIVE EVERY RESPONSE" while `docs/AGENTS.md` already encodes the same bias; or adds `*-review` that only hunts complexity while `doing-code-review` already loads `simplification.md`.

**Example (2026-07-14 ai-playbook):** ponytail's tagged complexity review merged into `review-agents/simplification.md`; its minimal-solution ladder became `coding_guidelines.md` **#28**; ponytail cataloged as reference-only. Not imported: plugin hooks, benchmark scoreboard, repo-wide audit/debt skills (optional future work).

**See also:** #145, `projects/.ai-playbook/skill-upstream-catalog.md`, `agents/skills/review-agents/simplification.md`, `coding_guidelines.md` **#28**.


## 147. Orchestrator Skills Must Treat Slash Invocation as Explicit Mode Choice and Auto-Continue Through Defined Steps

**Principle:** Family D (Single source of truth for workflow contracts) applied to skill orchestrators: when the user invokes a slash command or attaches a skill, that is the mode selection; do not re-ask with a softer gate or pause between steps the contract already defines.

**Trigger:** A user runs `/execute-plan <plan-path>`, types `execute plan docs/history/plans/foo.md` or shorthand `execute docs/history/plans/foo.md`, or attaches the execute-plan skill, but the agent still shows the execute-plan / manual / read-only gate, asks to continue on a branch that already matches the plan slug, or ends a task with "want me to proceed to Task N+1?"

**Rule:**
1. Run **invocation detection first**: `execute plan` + path, shorthand `execute`/`implement`/`run` + plan `.md` path under `.../plans/...`, `/execute-plan`, and skill attachment are equivalent execute-plan choice; the three-way gate applies only when `invoked = false` (bare path or `@mention` with no verb before the plan path).
2. On Phase 0 branch setup, **auto-continue** when `git branch --show-current` equals the plan slug (basename without `.md`) or the computed plan branch name; prompt only for plausible non-exact matches or new branch creation.
3. After each task `done`, Phase 2 pass, or review-round `done`, **start the next defined step immediately**; brief progress reports are fine, permission prompts are not.

**Why this happens:** Agents pattern-match on "plan path in message" and generic safety habits (confirm branch, confirm next step). Slash commands attach the skill without putting trigger text in the user message, so text-only trigger lists miss the invocation. Step boundaries feel like natural pause points unless the skill forbids asking.

**Shape trigger (when to suspect this family):** User explicitly invoked an orchestrator skill but the agent behaves like they only mentioned a file path, or asks yes/no between tasks on a plan they already asked to execute end-to-end.

**See also:** `agents/skills/execute-plan/SKILL.md` (Invocation detection, Continuous execution, Step 0.1a, Step 1.5), `plan-execution-routing` Cursor rule, `done` skill workflow continuity.

## 148. Tune Review Panels From Review Statistics, Not Agent Count Alone

**Principle:** Family D (Single source of truth for workflow contracts) applied to multi-agent review: panel changes must be driven by staged `## Review Statistics` (solo/raw ratio, echo dedup groups, discard reason codes), not by intuition about "too many agents."

**Trigger:** A team debates merging `quality`, `implementation`, and `architecture` because full panels discard 80%+ of raw findings, or because `premortem` often echoes other agents without solo-staged output.

**Rule:**
1. Aggregate recent reviews from `{reviews_dir}/` (and project mirrors on the `docs` branch) before changing `review-agents/*.md` or orchestrator launch lists.
2. Prefer **conditional launch** (`premortem`, `concurrency` opt-in by domain tags and diff signals in `review-panel-selection.md`) over collapsing agents that still produce solo findings (each had solo/raw >= 0.62 in a Jul 2026 sample).
3. Merge only **proven overlap pairs** (for example `documentation` + `prose-clarity`); keep tiered ownership boundaries so dedup picks a **lead agent** without discarding a different fix at the same site.
4. Record `Domains:` in staging metadata explaining why each conditional agent launched or skipped.
5. Monitor solo-staged median and discard% for two weeks after a panel change; loosen triggers if solo output drops without discard improvement.

**Why this happens:** Raw finding volume looks like noise, but solo-staged counts show which lenses still add unique signal. Merging high-solo agents to reduce launches hurts detection; skipping echo-heavy agents via opt-in preserves coverage on cross-service and transactional diffs.

**Shape trigger (when to suspect this family):** Review refactor discussion cites agent count or token cost but no `## Review Statistics` aggregation, or orchestrators duplicate skip rules inline instead of `review-panel-selection.md`.

**Example (2026-07-15 ai-playbook):** Jul 13-15 CRM/tax reviews showed premortem solo/raw 0.28 vs simplification 0.62; PROJ-601 code review 77 raw to 9 staged with 4-5 agent echo clusters. Shipped: merge `documentation`+`prose-clarity`, opt-in `premortem`/`concurrency`, tiered ownership for quality/implementation/architecture/consistency, canonical `review-panel-selection.md`.

**See also:** #144, `agents/skills/review-agents/review-panel-selection.md`, `agents/skills/review-staging/SKILL.md`.
## 149. Use wrong-owner Discards and Required stats.json to Identify Merge-into Candidates

**Principle:** Family G (Defensive warnings must also record items in the failure-tracking structure) applied to review panel tuning: echo counts alone cannot distinguish "duplicate root cause" from "wrong agent filed the finding."

**Trigger:** After tiered ownership is live, the team still cannot decide whether to fold agent A into agent B because discard rows only say `duplicate` and aggregation requires hand-reading markdown tables.

**Rule:**
1. Require a `.stats.json` sidecar beside every staging `.md` (same basename); validator hard-fails when missing unless Metadata records `Stats sidecar: skipped (<reason>)`.
2. When tiered ownership merges a root cause, discard non-lead returns with reason `wrong-owner`, not `duplicate`. Notes: `lead: <agent-id>`; sidecar: `"lead_agent": "<agent-id>"`.
3. Weekly aggregation: sum `wrong-owner` by discarded `agent`; high counts on agent X with lead Y suggest folding X into Y (after triage drop rate confirms noise).
4. Keep `duplicate` for same-agent repeats or when no tiered lead applies.

**Shape trigger (when to suspect this family):** Panel-tuning discussion needs spreadsheet exports from review markdown, or discard tables never distinguish ownership misses from generic duplicates.

**See also:** #144, #148, `agents/skills/review-staging/SKILL.md`, `~/.ai-playbook/scripts/validate_review_staging.py`.

## 150. Exclusive File Locks Must Record a Long-Lived Holder PID, Not the Acquire CLI Process

**Principle:** Family E (Temporal / ordering invariants) - a lock that treats the short-lived acquire process as the holder is abandoned the moment acquire exits.

**Trigger:** A shell lock script is invoked via `eval "$(lock.sh acquire)"` (or any subprocess that prints exports and exits). Metadata stores `holder_pid=$$`. A later acquire uses `kill -0` on that PID to decide "abandoned" and steals the lock while the original session still believes it holds exclusivity.

**Rule:** Record `PPID` (or an explicit `DONE_LOCK_HOLDER_PID` for the long-lived agent/shell), never the acquire script PID. Steal paths must compare-and-swap on token/epoch before `rm` so two waiters cannot both destroy a freshly re-created lock.

**Example (2026-07-17 ai-playbook review-loop r1–r3):** `scripts/done-lock.sh` wrote `holder_pid=$$`; status showed `abandoned: yes` at age 0s and a second acquire succeeded immediately. Fixed by using PPID and CAS steal. R2: PPID alone fails for one-shot agent Shell tools; treat matching `.ai-playbook/done-lock.session` as a live fence so dead PID is not auto-stealable. R3: do not auto-steal a fenced lock even after stale TTL (operator `stale-clean` only); CAS `mv` re-checks tomb meta; clear session only when token still matches; `selftest` covers fence/CAS/incomplete-dir.

## 151. A Filter That Re-derives One Field of a Cross-Field-Invariant Dataclass Must Re-derive ALL Coupled Fields in One Replace

**Principle:** Family D (Single source of truth) - when a frozen dataclass enforces a cross-field invariant in `__post_init__` (e.g. `if review_required and not review_reason: raise ValueError`), the coupled fields are ONE fact with two slots, not two independent facts. A post-construction filter that re-derives one slot and leaves the other at its prior value creates two authorities for the same fact: the new `review_required` says "no review" while the stale `review_reason` still describes the dropped review. The constructor rejects this drift at `replace(...)` time because the inconsistent combination trips `__post_init__`. Compounded by Family C (representation) - the flag (bool) and the reason (str | None) are two representations of the same underlying signal, so partial update leaks a stale representation.

**Trigger:** You are writing a filter / transform that runs AFTER a frozen dataclass with a cross-field `__post_init__` invariant has been constructed (an aggregation step, an override application, a normalization pass) and the filter needs to recompute ONE of the coupled fields. The filter returns or sets only one slot, then calls `entry.replace(field=new_value)`. Ask: does this dataclass have a `__post_init__` that relates two or more fields? If yes, the filter must return BOTH (all) coupled fields and the caller must apply them in a single `replace(...)`.

**Rule:**
1. A filter that re-derives any field participating in a `__post_init__` cross-field invariant MUST re-derive every coupled field and apply them together in one `replace(...)` call. Partial application leaves an inconsistent intermediate that the constructor raises on.
2. Encode the coupling as a helper that returns a tuple of all coupled fields (e.g. `_re_evaluate(entry) -> tuple[bool, str | None]`) rather than one that sets a single field. The helper is the single source of truth for ALL coupled fields; the caller spreads the tuple into one `replace(...)`.
3. Pin the contract with a regression test that asserts the constructor raises on the partial-update form (apply one field, expect `ValueError`), so a future refactor that splits the helper into two single-field setters goes RED rather than silently producing the crash at runtime.
4. When the prior value of the coupled field must be preserved on some code paths, the helper returns `(prior_required, prior_reason)` unchanged on those paths - never returns the new value for one slot and lets the caller leave the other slot stale.

**Example (2026-07-15 review-flag-aggregation-boundary plan, Task 1):** The aggregated-entry dataclass's `__post_init__` raises `ValueError("review_reason must be set when review_required=True")`. The aggregation step previously set `review_required = any(item.review_required...)` and `review_reason = "; ".join(...)` independently. Task 1 added a post-aggregation filter (the review-flag re-evaluation helper, returning `tuple[bool, str | None]`) that drops a stale review flag when the aggregated result becomes material. The first sketch returned only the new `review_required` and left `review_reason` carrying the dropped text; constructing the result raised `ValueError` because `review_required=False` paired with a non-None reason is fine, but the inverse path (`review_required=True, review_reason=None`) - reached when every survivor is stripped - trips the invariant. Fix: the helper returns BOTH fields and the wiring applies them in one `replace(review_required=..., review_reason=...)`. See plan Invariant 2 ("the helper is the single source of truth for both fields; partial application triggers `ValueError` from `__post_init__`").

**See also:** glossary `docs/maintenance/glossary.md` ("Aggregated review flag", "Zero-basis review"), the entities submodule (the aggregated-entry dataclass `__post_init__`), user-level #38 (independent validation fields must NOT be coupled into entry-level `__post_init__` - the inverse of this lesson: this one is about fields that ARE coupled), #39 (per-field aggregation strategy).

## 152. Skills Whose Canonical Script Uses `${arr[@]+"${arr[@]}"}` Must Be Invoked Under bash, Not zsh: In zsh That Guard Expands to a Single Empty Argument and Runs the Loop Body Once With an Empty Variable

**Principle:** Family H (Verify the real thing, not the abstraction: the `${arr[@]+"${arr[@]}"}` idiom is the documented bash-3.2-safe empty-array guard from #129, and the abstraction "this is the portable empty-array idiom" hides that its portability is across bash versions, NOT across shells; in zsh the same syntax expands differently and runs the loop body once with an empty variable). Cross with the skill-portability family: skills authored and tested under bash must declare and enforce their target shell when they reach for shell-specific expansion semantics.

**Trigger:** An agent invokes a skill's canonical bash script (for example the `docs-branch` Step 2 sync, or any hook script) by pasting its body into the agent's default interactive shell, AND that shell is zsh (macOS default user shell; `/bin/zsh`), AND the script contains a loop of the form `for x in "${ARR[@]+\"${ARR[@]}\"}"; do ... "${x:?}" ...; done` or the equivalent unquoted-word `${ARR[@]+"${ARR[@]}"}` form, AND the array is legitimately empty at runtime.

**Rule:** When running a skill's canonical script that uses bash-specific array-expansion idioms (`${arr[@]+"${arr[@]}"}`, `${!arr[@]}`, associative arrays, `declare -A`), invoke it under `/bin/bash` (or the project's documented bash), NOT the agent's default zsh. Concretely: write the canonical text to a temp `.sh` file with a `#!/bin/bash` (or `#!/usr/bin/env bash`) shebang and run `bash <file>`, instead of pasting the body into a zsh `Bash` tool call. Reason: in zsh, `"${ARR[@]+\"${ARR[@]}\"}"` with an empty `ARR` expands to a single empty-string word, so the `for x in ...` loop iterates ONCE with `x=""`; any subsequent `${x:?}` (or `${DOCS_WORKTREE:?}/${x:?}`) then aborts with `parameter not set` / `parameter null`, even though the script is correct bash and would skip the loop entirely under bash. The bash-3.2-safe guard from #129 protects against the `set -u` + bash 3.2 hazard; it does NOT protect against the zsh empty-word hazard, which is a different shell family.

**Why this matters:** macOS ships zsh as the default user shell, and most agent harnesses' `Bash` tool inherits that shell. A skill authored under bash (or Linux) whose empty-array path was never exercised on zsh will silently work in CI and on the author's machine, then abort mid-script in production on a stock macOS agent run. For `docs-branch` specifically the abort happens AFTER the temporary worktree is created and the shadow snapshot is staged into it but BEFORE the `git commit`, so the sync silently makes no commit; on the next run the add-only restore loop also resets the working tree (because `git reset -q -- docs/ ...` runs in the live checkout), which unstaged the orchestrator's intended tracked-file change and required manual re-staging. The failure is "script aborts, no commit, working tree partially reset" - noisy but recoverable, and easy to misattribute to the skill's logic rather than to the shell.

**Shape trigger:** A skill or hook script aborts with `<varname>: parameter not set` (zsh nounset-style message, prefixed `zsh:<line>:`) at a line that is inside a `for x in "${ARR[@]+...}"` loop body that references `${x:?}` or `${x}` after arithmetic, AND the array was empty at that point, AND the invoking shell is `/bin/zsh` (verify with `echo $0` / `$ZSH_NAME`). The line number in the zsh error points at the loop BODY (the `rm`, `git add`, or `${x:?}` reference), not at the `for` header, which is the misdirection that makes this look like a script-logic bug.

**Example (2026-07-17 tax-reporting review-flag-aggregation-boundary plan, Phase 4 archive `done`):** The `done` skill's `docs-branch` Step 2 canonical script contains `for del_path in "${DOCS_EXPLICIT_DELETES[@]+\"${DOCS_EXPLICIT_DELETES[@]}\"}"; do rm -rf -- \"${DOCS_WORKTREE:?}/${del_path:?}\" ...; done`. When `DOCS_EXPLICIT_DELETES` was empty (no explicit deletes in the latest docs commit), running the pasted script body under the agent's default zsh aborted with `zsh:215: del_path: parameter not set` at the `rm -rf ... ${del_path:?}` line - because zsh ran the loop body once with `del_path=""` and the `:?` modifier fired on the empty value. The same script body run under `/bin/bash` (written to a temp `.sh` file and invoked as `bash <file>`) skipped the loop entirely and completed the sync correctly (committed `docs: update from ...` and mirrored the plan-archive rename). The fix was invocation-shell, not script-text: the canonical script is correct bash; it must be RUN as bash. Dual placement: this user-level lesson plus a one-line note in `docs-branch/SKILL.md` that the Step 2 script is bash-targeted and must be invoked under bash when the agent's default shell is zsh.

**See also:** user-level #129 (the bash 3.2 `${arr[@]+"${arr[@]}"}` idiom under `set -u` - the SAME syntax, the OPPOSITE shell family: #129 fixes a bash-3.2 hazard; this lesson is the zsh hazard that the same idiom does NOT defend against), coding_guidelines.md #25 (Family H parent: verify the real deployment shell, not the "portable idiom" abstraction), `docs-branch` SKILL.md Step 2, `done` SKILL.md Step 2 invocation guidance, CLAUDE.md/AGENTS.md "agent default shell is zsh on macOS; run bash-targeted skill scripts via `bash <file>`".

## 153. A Review Wrapper That Invokes `doing-code-review` as a Single Sub-Agent Cannot Fan Out the Panel; It Silently Collapses to Solo and the "Solo" Statistic Label Masks the Bypass

**Principle:** Family H (Verify the real thing, not the abstraction) applied to review-orchestration: the `Solo/Echo` statistics column on a review staging doc is an *abstraction* over "the panel ran"; trusting that label (or the presence of a staging doc) as proof of coverage masks the case where the panel never launched. Compounded by Family D (Single source of truth): when a caller skill (for example `execute-plan` Phase 3) wraps `doing-code-review` as one sub-agent, the caller's Code Review template must RESTATE the panel mandate and ADD an acceptance gate that checks the Panel table's raw counts - otherwise the source of truth (`doing-code-review` Hard Gate #1, `review-panel-selection.md`) is unreachable from the caller, and the single wrapped sub-agent has no sub-agent-execution capability of its own to launch the 7 default agents with.

**Trigger:** A skill that orchestrates code review (plan execution, review-loop, CI gate) wraps `doing-code-review` as a single sub-agent launched from a parent orchestrator, AND its review-step template/instructions do not explicitly (a) mandate launching the full `review-panel-selection.md` panel and (b) define a mechanical acceptance gate on the staging doc's `## Review Statistics` -> Panel table. Suspect this family when a review that "passed clean" is later found by a standalone `doing-code-review` run to have Medium+ findings the clean pass missed.

**Rule:**
1. Any caller skill that wraps `doing-code-review` as a sub-agent MUST, in its review-step template, restate `doing-code-review` Hard Gate #1 verbatim: launch the full `review-panel-selection.md` panel (7 default agents; concurrency/premortem per signals). "Solo" is a Solo-vs-Echo *dedup label* for findings that happen to converge on one agent origin; it is NEVER a mode that skips launching agents.
2. The caller MUST add a Step-3.1-style acceptance gate that rejects any staging doc whose Panel table shows the 7 default agents as `folded into Solo`, `Raw=0` with status `skipped`, or whose only non-skipped row is `orchestrator (Solo)` - UNLESS `review-panel-selection.md` explicitly authorizes each skip (and the skip reason is recorded, not blanket).
3. The review-staging validator (`validate_review_staging.py`) MUST mechanically enforce (2): a staging doc with `staged_findings >= 0` that declares all default agents `folded into Solo` / zero-raw is INVALID under `--hard` when the review type is a full code review (not a known-Solo artifact like a quick re-check).
4. When a review step is itself a single sub-agent (no fan-out capability), the parent orchestrator - not the wrapped sub-agent - is responsible for launching the panel. If the parent cannot fan out, it must delegate to a `doing-code-review` invocation that CAN, rather than running an inline Solo pass and labeling it "folded into Solo."

**Why this happens:** `execute-plan`'s Code Review template (in `subagent-prompts.md`) said "fresh adversarial review" and "follow doing-code-review staging format" but did NOT say "launch the 7 default panel sub-agents." The review sub-agent, launched as a single agent by the orchestrator, had no sub-agent-execution capability to fan out the panel, so it collapsed to an inline Solo pass and retroactively recorded the 7 agents as `folded into Solo | Raw=0`. The staging doc's own "Note on panel shape" narrated this as intentional ("the task brief instructs a Solo fresh-adversarial pass") - a post-hoc rationalization of a structural inability. The Solo label then passed every existing gate because those gates trusted the statistics label as proof the review happened.

**Shape trigger (when to suspect this family):** A review staging doc's `## Review Statistics` -> Panel table shows `quality | folded into Solo | Raw=0`, `testing | folded into Solo | Raw=0`, etc., or its only `complete` row is `orchestrator (Solo adversarial pass)`. A subsequent standalone review of the same diff surfaces Medium+ findings the "clean" pass missed. A review-step template references `doing-code-review` but is silent on `review-panel-selection.md` and panel launch.

**General form:** When a workflow skill wraps another skill whose value is a multi-agent *process* (review panels, red-team suites, fuzz harnesses, eval batteries), the caller cannot substitute a single inline pass for the process and then record the per-component statistics as if the process ran. The enforcement must be mechanical (a gate on the artifact's component-coverage table), not a label the wrapper is free to populate after the fact.

**Example (2026-07-17 `2026-07-15-review-flag-aggregation-boundary` plan):** `execute-plan` Phase 3 ran two "clear" review rounds (r1, r2) for the plan's review-flag aggregation-boundary work. Both rounds ran as Solo: each staging doc's Panel table shows `orchestrator (Solo adversarial pass) | complete | raw=1` and `quality/testing/architecture/simplification/documentation/security | folded into Solo | Raw=0`. The r2 staging doc declared the plan ready ("0 Medium+ pending; 2 Lows"). A standalone `doing-code-review` run against the same `master...HEAD` diff then launched the actual 7-agent panel and found 3 Mediums (a classifier precision mismatch: decision uses unrounded `raw_pct` but display uses rounded `pct`; branch-(d) `detail` has no classifier-level test assertion; the four-branch classifier is inlined past the extraction threshold) plus 11 Lows that neither Solo round surfaced. The Solo rounds had mutation-tested the invariants the *plan* named (None-guard, `<=` boundary, `ROUND_HALF_UP`) and confirmed they hold - valuable, but that only proves the plan's own claims; it does not find claims the plan never made, which is the panel's job. Root cause: `execute-plan`'s Code Review template did not mandate the panel, and no gate rejected the Solo-collapse.

**See also:** #144 (review harnesses need structured staging metadata - assumes the panel ran), #148 (tune panels from statistics, not agent count - assumes the panel ran), #149 (wrong-owner discards and required stats.json - assumes the panel ran; this lesson is the PRECONDITION those three depend on), coding_guidelines.md #25 (Family H parent), `agents/skills/execute-plan/subagent-prompts.md` (Code Review template), `agents/skills/doing-code-review/SKILL.md` Hard Gate #1 and Anti-patterns, `agents/skills/review-agents/review-panel-selection.md`, `~/.ai-playbook/scripts/validate_review_staging.py`.


## 154. A Plan That Inherits or Asserts a Claim About Current Code/Runtime Behavior Must Empirically Verify the Claim Against the Actual Artifact Before Building Tasks on It

**Principle:** Family H (Verify the real thing, not the abstraction) applied to plan authoring: a "today the code does X" or "this placement achieves Y" claim in a plan's Gist, Invariants, or task rationale is an *abstraction* over the actual code or runtime behavior. Trusting the claim without running the production helper, reading the actual branch taken, or tracing the actual line ordering, builds tasks on a fiction. The plan-review panel catches these via empirical verification, but each round of catching a false premise costs a full review cycle; verifying at authoring time is far cheaper. Compounded by Family D (Single source of truth): when a feature-notes or deferred-findings doc asserts "current state X" and the plan inherits it without re-verification, the doc becomes a second source of truth that can drift from the code, and the plan propagates the drift into tasks and tests that cannot go RED.

**Trigger:** Suspect this family when a plan task, RED test, or Design Invariant describes current code/runtime behavior using phrases like "today the code does X", "currently reaches Y", "this placement achieves Z avoidance", "this guard detects W", or "the upstream classifier does V" - and that description was inherited from a feature-notes doc, a session summary, or the author's prior mental model rather than re-read from the actual source this session. The strongest signal is a plan-review round returning a Critical finding whose comment contains "verified empirically" or "verified by simulation" against the claim.

**Rule:**
1. A plan task or Design Invariant that asserts "the code currently does X" or "this placement achieves Y" MUST be verified against the actual source artifact in the same authoring session: read the cited lines, run the production helper if the claim is about runtime behavior (e.g. "is this token in the set", "does this helper raise on None"), or trace the actual branch the input takes. Cite the verification in the plan ("verified at the else-branch in the production module: it fires").
2. A plan that inherits a "current state" claim from a feature-notes, deferred-findings, or RFC doc MUST re-verify the claim against the actual code before building tasks on it. The feature-notes author may have been wrong about which branch fires, which consumer reads which variable, or which precondition holds. Surface contradictions to the user (AGENTS.md: "Before deleting or overwriting, look at the target - if what you find contradicts how it was described ... surface that instead of proceeding").
3. A plan claim of the form "this invariant detects regression X" MUST be checked for tautology: if the invariant is computed as `|P| + |¬P| == |L|` over the same list (or any identity that holds by construction for the predicate family the code actually uses), it cannot detect a change to the predicate - only non-determinism or concurrent mutation, which may not be a realistic regression. If the guard's own test must be constructed via monkeypatching/non-determinism to fire, that is the tell.
4. A plan claim of the form "this placement achieves avoidance of work W" MUST verify that W actually runs AFTER the placement, not before it in an unconditional pre-block position. "Place the short-circuit inside the `if cond:` block" does not avoid work that runs at `:729-730` unconditionally before the block is entered.
5. When a plan-review round surfaces a false-premise Critical, the fix is not only to correct the affected tasks - it is to re-verify EVERY other "current state" claim in the plan in the same pass, because false premises tend to cluster (the same unverified mental model produced them).

**Why this happens:** Plan authoring is partly a translation of prior context (feature-notes, session memory, the author's earlier investigation) into tasks. When the prior context contains a behavioral claim, the path of least resistance is to inherit it into the Gist/Invariant verbatim and build tasks on it. The cost of empirical verification at authoring time feels high (run a helper, read three code sites); the cost of a false premise surfacing at plan review is much higher (a full review round, plus the cascade of fixing downstream tasks and tests that were built on the fiction). Reviewers, by contrast, are primed to verify claims against source - that is their job - so false premises disproportionately surface in review rather than authoring.

**Shape trigger (when to suspect this family):** A plan-review round returns a Critical finding with an empirically-verified comment (production-helper execution, line-number trace, N-trial simulation) that contradicts a plan claim. The plan's Gist, before/after table, or a Design Invariant asserts current behavior using inherited language ("reach the file parser and land in `context.review_entries`", "this placement makes the lookup-avoidance real", "this is a classifier-regression detector"). A RED test in the plan asserts behavior that already holds today (a "fake test" that cannot go RED).

**General form:** A claim about an external system's behavior (source code, runtime, helper output, line ordering, predicate semantics) is a hypothesis, not a fact, until verified against the system itself in the current session. The plan's job is to encode verified hypotheses as invariants; encoding unverified hypotheses as invariants propagulates drift from whatever source (doc, memory, prior session) supplied the hypothesis. This is the plan-authoring analog of AGENTS.md's "Code inspection is INSUFFICIENT for 'is X handled correctly?'; perform full data-trace verification" - applied to authoring, not just investigation.

**Example (2026-07-18 negligible-value-partition-skip plan, three same-session instances):**
1. **Feature-notes premise was factually wrong.** The source feature-notes doc item #1 asserted that 99 all-zero auxiliary rows "reach the file parser and are appended to `context.review_entries` via the all-zero + known-item branch, producing 99 WARNING log lines, 99 review-list entries." The plan inherited this verbatim into its Gist. Plan-review r1 verified empirically: the auxiliary type is NOT in the known-item set file, the known-item predicate is False for it, and the known-item collector never adds it (all rows are all-zero). So all-zero auxiliary rows take the ELSE-branch -> the skipped-zero-value registrar -> `skipped_zero_value_items`. They do NOT reach `review_entries` and emit ZERO WARNINGs. Two Task 1 RED tests asserted the non-existent pollution behavior (could not go RED), and the entire Part 1 motivation was wrong.
2. **Invariant was tautological.** The plan's Design Invariant 5 framed `len(real_rows) + len(negligible_rows) != len(active_now_entries)` -> `FileProcessingError` as a "classifier-regression detector." Plan-review r3 ran a 100,000-trial simulation: the invariant fired 0 times across all randomized inputs. The math: the helper computes `real = [not P(e)]` and `negligible = [P(e)]` as complementary filters over the same list, so `|[P]| + |[¬P]| == |L|` holds for any deterministic predicate by construction. The guard cannot detect a discriminator change; its test could only be constructed via monkeypatching/non-determinism. The plan's Task 5 test description even admitted this ("monkeypatching the partition or constructing a report whose entries mutate during iteration") - the tell was in the plan itself, unverified.
3. **Placement did not achieve the claimed avoidance.** The plan's Design Invariant 4 claimed the auxiliary-type short-circuit was placed "before the popular-item / non-latin lookups at `:729-730` (so the lookup-avoidance is real)." Plan-review r3 verified the line ordering: `:729-730` run UNCONDITIONALLY before the `if is_all_zero:` block at `:737` where the short-circuit lives. The lookups had already executed by the time the short-circuit fired. The plan asserted a guarantee the prescribed code did not deliver; the visible behavior (the auxiliary type gone from the reconciliation table) looked correct, masking the false rationale.

**See also:** coding_guidelines.md #25 (Family H parent: verify the real thing, not the abstraction), #16-tax-reporting "Decision Points TOML Missing Must Raise `ConfigurationError`, Not Bare `FileNotFoundError`" (Family A-H root-cause catalog), `plans` skill "Investigation Quality Requirements" (verification-first task ordering; code inspection is INSUFFICIENT), `plans` skill Plan Quality Gate (the review sub-agent empirically verifies claims against source - the backstop that catches this family when authoring did not), #153 (review-orchestration Family-H analog: trust the panel-ran label as proof of coverage masks the case where it never launched), AGENTS.md "Code inspection is INSUFFICIENT" and "Before deleting or overwriting, look at the target."


## 155. A RED Test Whose Fixture Contradicts Its Own Stated Intent Is Invisible at RED and Mimics an Implementation Defect at GREEN; When a Spec-Faithful GREEN Still Fails a RED Test, Suspect Fixture/Intent Consistency Before the Implementation

**Principle:** Family H (Verify the real thing, not the abstraction) cross with the TDD-process family of #57/#81/#88. The RED phase validates only ONE property: "the behavior under test is absent." It does NOT validate that the test's fixture constructs the case the the test's docstring names. A fixture that contradicts the test's own stated intent is therefore a DORMANT defect at RED - the test fails for the right reason (behavior absent) regardless of whether the fixture matches the intent, so the standard "RED must fail" check passes the contradiction silently. The contradiction only becomes executable at GREEN, when the production code makes the assertion real, and at that point the failure mimics an implementation defect: the implementer sees "test still RED after a spec-faithful implementation" and the natural hypothesis is "the implementation is wrong," not "the fixture constructs the wrong case."


**Trigger:** A multi-task TDD plan where Task N writes a RED test (the assertion encodes a behavioral contract Task N+1 will satisfy) and Task N+1 flips it GREEN. The GREEN implementation is verified to match the plan/spec pseudocode byte-for-byte, yet the RED test still fails. The implement sub-agent's first hypothesis is an implementation defect; the orchestrator (or a re-read) must diagnose that the test's fixture constructs a DIFFERENT case than the test's docstring describes (e.g. the docstring says "every row is X" but the fixture builds a mix of X and non-X rows). Critically: this is NOT triggered by a contract change between RED and GREEN (that is #81), NOT by a placeholder value colliding with an external new semantic (that is repo-style #44 / user #107), and NOT by a degenerate filler violating an orthogonal production invariant (that is #88).

**Rule:**
1. When a GREEN implementation that matches the plan/spec pseudocode byte-for-byte still fails a RED test whose RED failure was clean (a clean assertion or `pytest.fail`, not a collection/runtime error per #122), the FIRST hypothesis to check is fixture/intent consistency, NOT an implementation defect. Re-read the RED test's fixture against its OWN docstring (without consulting the implementation) and ask: does the fixture actually construct the case the docstring names? RED did not validate this; RED only proved the behavior was absent.
2. The diagnostic for "fixture constructs the wrong case": enumerate every value the fixture sets (or leaves at its default) and trace whether that value routes the fixture into the docstring's named case or into a sibling case. Defaults are the stealth vector - a fixture that omits a classification/flag/enum override inherits the default, which may route the row into a different bucket than the docstring implies. In Task 4's case: the docstring named the "all-negligible" case (`not real_rows and negligible_rows`), but the fixture left the priced rows at their default classification, which routed them into `active_now_entries` and thence into `real_rows`, so the fixture actually constructed the MIXED case and the all-negligible branch never fired.
3. The fix is to correct the FIXTURE so it constructs the case the docstring names (in Task 4: reclassify the priced rows so they stay in `pending_entries` as discriminator evidence without entering `active_now_entries`). Do NOT contort the implementation to match a misconstructed fixture, and do NOT weaken or delete the assertion. The docstring's stated intent is authoritative; the fixture is the bug.
4. Authoring-time prevention: when writing a RED test whose deliverable is the test itself (committed RED, later-task GREEN per #122), re-read the fixture against the docstring ONE more time before committing the RED task. Ask: "if the implementation matched the spec exactly, would this fixture cause the docstring's named case to fire?" If the answer is no, the RED will pass the "must fail" check for the wrong reason (behavior absent) and the contradiction will surface only at GREEN, where it is more expensive to diagnose because the implementation now looks suspect.
5. Document the fixture correction in the GREEN task's implement log as a "plan-related extension" / RED-fixture bug, not as an implementation change. The RED task wrote the contradiction; the GREEN task inherits and resolves it. The orchestrator should classify the failure as "fixture contradicts test intent" rather than "implementation incomplete" before greenlighting a fixture edit.

**Why this happens:** At RED authoring time, the implementer's attention is on (a) making the assertion name the contract and (b) making the test fail (behavior absent). The fixture is constructed to be plausible and exercise the docstring's case, but the implementer does not re-trace every fixture value to confirm it routes into the named case - partly because the production routing code does not exist yet, so the trace is hypothetical, and partly because "RED must fail" is satisfied the moment the behavior is absent, giving a false "the fixture is fine" signal. The contradiction is only checkable once the production routing code exists (GREEN), by which point the implementer's mental model has shifted to "is my implementation correct?" and the fixture is treated as ground truth rather than as a hypothesis. The mismatch between "the fixture is fine" (RED's false signal) and "the fixture contradicts the intent" (GREEN's reality) is the latency this lesson addresses.

**Shape trigger (when to suspect this family):**
- A GREEN implementation that matches the plan/spec pseudocode line-for-line still leaves a RED test failing, and the failing assertion is about WHICH branch/case fired (not about a computed value).
- The failing test's docstring names a specific case ("every row is X", "all items classified as Y", "the empty-Z case"), but the fixture builds a mix of X-and-non-X, Y-and-non-Y, or a non-empty Z.
- The fixture omits an enum/flag/classification override on some rows, leaving them at a default that routes them out of the docstring's named case.
- The implement sub-agent's GREEN log reports the failure as a "BLOCKING CONTRADICTION" and recommends either an implementation change or a spec re-read, BEFORE anyone re-reads the fixture against its own docstring.

**General form:** A RED test's failure proves only "behavior absent," never "fixture matches intent." A fixture that constructs the wrong case passes the RED gate (because behavior is absent either way) and fails the GREEN gate in a way that looks like an implementation defect (because the implementation now runs and routes the misconstructed fixture correctly). The recovery is asymmetric: trust the docstring's stated intent as authoritative and correct the fixture to construct the named case; do not "fix" the implementation to match a misconstructed fixture, and do not weaken the assertion. The cheapest prevention is a one-question re-read at RED authoring time: "does my fixture route into the case my docstring names?"

**Distinguishing from #88 (boundary-filler violates orthogonal invariant):** #88 is a BOUNDARY/LIMIT characterization test where the fixture author reaches for a DEGENERATE MECHANICAL FILLER (`b"x" * N`, `[None] * M`) to hit an exact size/count/length boundary, and the filler violates an ORTHOGONAL PRODUCTION INVARIANT (parseability, schema validity, non-emptiness). The failure is "the implementation correctly rejects the invalid input," and the fix is content that satisfies the orthogonal invariant at the exact boundary value. This lesson (#155) is NOT a boundary test: the fixture author writes PLAUSIBLE DOMAIN ROWS (no degenerate filler), every row is individually valid, the production path runs cleanly, and the failure is "the fixture constructs a DIFFERENT CASE than the docstring names" (mixed vs all-negligible), not "the fixture is invalid for the production path." #88's contradiction is filler-content-vs-orthogonal-invariant; #155's contradiction is fixture-case-vs-docstring-intent. Both surface at GREEN after a spec-faithful implementation, but the fixture shape (degenerate filler vs plausible rows) and the contradiction axis (invariant violation vs wrong-case routing) differ.

**Distinguishing from #81 (re-read RED against revised invariants):** #81 fires when the plan/spec was REVISED between RED and GREEN, so the RED test asserts a contract the revision changed; the fix is to update the assertion to the new contract. This lesson (#155) fires when NOTHING changed between RED and GREEN - the implementation matched the spec pseudocode byte-for-byte, no invariant was revised. The defect was present at RED authoring time (the fixture never matched the intent); it was just invisible because RED does not check fixture/intent consistency.

**Distinguishing from the repo-style #44 / user #107 re-scope family:** those fire when a PRE-EXISTING test (or a deferred test) used a value as an ORTHOGONAL PLACEHOLDER, and a LATER task's behavior change (or contract change) assigns that value a new semantic that breaks the test. The fix is to re-scope the placeholder value. This lesson (#155) fires on a NEW test written in the SAME plan's RED task, where the fixture is internally inconsistent with the test's OWN intent - no external semantic change or contract change is involved, and the fix is to correct the fixture (not re-scope a placeholder).

**Example (2026-07-18 negligible-value-partition-skip plan, Task 4 GREEN):** Task 3 (RED) wrote the negligible-summary test class's `test_all_negligible_empty_label` with docstring intent "given a report where EVERY active-now row is negligible (all items have a priced row elsewhere), expects the detail table shows the all-negligible empty label and a negligible summary block renders below it." The fixture built four rows - `item_a_priced` (value=1), `item_a_zero` (value=0), `item_b_priced` (value=2), `item_b_zero` (value=0) - ALL defaulting to `CLASSIFY_NOW` (no `classification=` override on any row). The two priced rows are non-zero, so under the plan's three-state partition they are `real_rows`, NOT negligible. The fixture therefore constructed the MIXED case (2 priced detail rows + 2 negligible rows), not the all-negligible case the docstring named. At RED this was invisible: the production helpers (the partition helper and the summary-block writer) did not exist yet, so the test failed for the right reason (behavior absent) and passed the standard RED check. At GREEN (Task 4), the implementation matched the plan pseudocode byte-for-byte, but the test still failed because the all-negligible branch (`not real_rows and negligible_rows`) never fired - `real_rows` held the two priced rows. The GREEN sub-agent initially reported this as a BLOCKING CONTRADICTION and was unsure whether the implementation or the test was wrong; the orchestrator diagnosed it as a Task 3 fixture bug (the fixture contradicted the test's own stated intent) and fixed the fixture by reclassifying the two priced rows to `CLASSIFY_DEFERRED`, so they remain in `pending_entries` as priced-row discriminator evidence (proving item A/B are priced items) without entering `active_now_entries` (which would make them non-negligible real_rows). After the fixture correction, all 12 Task 3 tests went GREEN and the full module passed 46/46. See the Task 4 implement log "Blocking contradiction (Task 3 RED test fixture vs. plan intent)" and "Orchestrator resolution (Task 3 fixture bug; plan-related extension)" sections.

**See also:** coding_guidelines.md #25 (Family H parent), #57 (TDD RED-then-GREEN as a process step - the transient case), #81 (re-read RED assertions against REVISED invariants before the GREEN flip - the contract-change case), #88 (boundary-filler violates orthogonal invariant - the degenerate-filler case), #107 (re-scope when a fixture flips an orthogonal signal - the migration case), #122 (a RED test that is itself the deliverable must fail as a clean assertion - failure-shape discipline), #154 (a plan that asserts current-code behavior must verify it empirically - the plan-authoring sibling), #156 (substitute an e2e-realizable analog INPUT when middleware routes the literal input away from the code under test - the e2e analog-of-the-input case), CLAUDE.md §4 Agent Workflow Rules (RED-then-GREEN TDD discipline).


## 156. When an E2E Fixture's Literal Input Cannot Reach the Code Under Test Because Upstream Middleware Routes It Elsewhere, Substitute an E2E-Realizable Analog Input That Exercises the Same Discriminator (Justified by Discriminator-Invariance)

**Principle:** Family H (Verify the real thing, not the abstraction) cross with Family A (Equivalence-class coverage). The "real thing" a discriminator-branch test verifies is the DISCRIMINATOR's behavior on an equivalence class of inputs, not the literal spelling of the motivating input. When a unit-tier fixture names a concrete motivating input (a specific ticker, identifier, or value) but the full production pipeline's upstream middleware (a classifier, a normalizer, a router) routes that literal input into a DIFFERENT bucket before it reaches the code under test, the e2e fixture cannot use the literal input verbatim: doing so would make the code under test unreachable, and mocking the middleware to route it through defeats the "full pipeline" purpose of an e2e test. The faithful move is to substitute an e2e-realizable analog INPUT whose spelling survives the middleware and lands in the same bucket, so the code under test still receives a member of the same equivalence class. The substitution is justified when the discriminator the code under test reads is INVARIANT under the analog (the discriminator branches on a property the literal and the analog share), so the analog exercises the same branch without altering the test's semantic claim.

**Trigger:** An e2e test (or a fixture promoted from a unit fixture to e2e) is meant to pin a behavior of a downstream helper whose discriminator is input-agnostic. The motivating unit fixture used a literal input that the unit test bypassed the middleware to construct directly (e.g. `classification=ACTIVE` passed verbatim, skipping the production classifier). The e2e test must run the full pipeline (parse → classify → route → render), so the middleware runs and routes the literal input into a different bucket (e.g. a category-B identifier routed to `DEFERRED` rather than `ACTIVE`), so the downstream helper never sees it and its branch is unexercisable. The implementer notices either (a) the e2e test cannot go GREEN with the literal input no matter how correct the implementation is, or (b) the helper-under-test is silently never reached and the test passes for the wrong reason (testing nothing about the discriminator).

**Rule:**
1. When authoring an e2e fixture that exercises a downstream helper whose discriminator is input-agnostic, identify the upstream middleware that runs between parse and the helper, and confirm whether the literal motivating input survives it. Trace the literal input through the middleware by hand (or by a one-shot debug print) and check which bucket it lands in.
2. If the literal input is routed away from the helper-under-test, do NOT mock the middleware to force it through (that defeats e2e), and do NOT amend production middleware to special-case the input (that is a real production change beyond the plan's scope). Instead, find an e2e-realizable analog INPUT whose spelling the middleware accepts into the bucket you need (here: a category-A identifier, because the classifier's ACTIVE branch is defined as "asset is in the category-A set", so category-A identifiers land there by construction).
3. Justify the substitution by proving the helper's discriminator is INVARIANT under the literal-vs-analog swap: state explicitly which property the discriminator reads (`value > 0`, `item in known_items`, count of priced rows) and confirm the literal and the analog both produce the same value of that property. If the discriminator is NOT invariant, the substitution is unfaithful and a different approach is required.
4. Document the substitution in the test docstring (or the implement log): name the literal input the plan prose used, name the analog, name the middleware that blocks the literal, and name the invariant that makes the analog faithful. A silent substitution reads as a deviation from the plan; a documented one reads as a correct translation.
5. Re-scope any fixture-adjacent side constraints the substitution introduces. If the analog has a different side property than the literal (here: a zero-value row on a category-A asset may be retained-or-dropped by a different retention rule than a zero-value row on a category-B asset), audit that side property and add the minimal supporting fixture row to make the analog survive to the helper-under-test. Do NOT let the side property silently drop the analog before it reaches the discriminator.

**Why this happens:** Unit-tier fixtures are constructed by calling the helper or the dataclass constructor directly, with the discriminator-set field passed verbatim (`classification=ACTIVE`). This is correct for a unit test of the helper, but it silently depends on the assumption that the production middleware would have produced the same field value. When the same motivating input is later promoted to an e2e fixture (to pin the full pipeline), the middleware runs, and the assumption is exposed: the middleware may route the literal input elsewhere because its bucket rule is orthogonal to the helper's discriminator. The plan author wrote the e2e task's prose naming the literal input (mirroring the unit fixture) without re-tracing whether the literal input survives the middleware, because the unit fixture never ran the middleware. The mismatch surfaces only at e2e authoring time.

**Shape trigger (when to suspect this family):**
- An e2e fixture's motivating prose (or its unit-fixture predecessor) names a specific identifier/value, and the e2e test must run the full pipeline (parse → classify → route → render), not a direct helper call.
- The production pipeline has a classifier/normalizer/router between parse and the code under test whose bucket rule is ORTHOGONAL to the discriminator the code under test reads (e.g. classifier branches on "is the identifier in the category-A set" while the helper branches on "is value > 0").
- The literal motivating input is a member of a bucket the classifier routes AWAY from the code under test (e.g. a category-B identifier that the classifier routes to DEFERRED, while the helper operates only on ACTIVE entries).
- The e2e test either cannot go GREEN with the literal input, or passes for the wrong reason (the helper is unreachable).

**General form:** An e2e test's value is that it runs the real pipeline. When the real pipeline's middleware routes the literal motivating input away from the code under test, the faithful fix is to substitute an analog INPUT that the middleware accepts into the needed bucket, justified by the discriminator's invariance under the swap. This is a THIRD option distinct from mocking the middleware (defeats e2e) and amending the middleware (out-of-scope production change). The substitution is faithful iff the helper's discriminator produces the same branch on the analog as on the literal, which holds iff the discriminator reads a property both inputs share.

**Distinguishing from #18 (verify path reachability before writing a test; mock OR amend):** #18 lists two responses when a path is unreachable via real data - (a) mock/patch to inject the edge case, or (b) amend the implementation to make the path reachable. This lesson (#156) is the e2e-specific THIRD option: substitute an e2e-realizable analog INPUT so the path becomes reachable through the REAL pipeline without mocking and without amending. #18's "unreachable" is about a defensive/guard path that real data never exercises (placeholder mechanism always fires first); #156's "unreachable" is about a downstream helper that real data WOULD exercise on an equivalence class, but the literal motivating input happens not to be a member of that class under the real middleware. #18 accepts mocking as a valid response (it is about a unit-tier guard test); #156 rejects mocking (it is about an e2e test whose purpose is the real pipeline).

**Distinguishing from #86 (re-scope the assertion when synthetic identifiers flip orthogonal signals):** #86 fires when migrating a test off a real fixture to synthetic data, where the synthetic identifiers flip orthogonal DOWNSTREAM SIGNALS (review flags, sentinel values) that the OLD ASSERTION checked as side properties; the fix is to re-scope the ASSERTION to the primary behavior. #156 fires when the literal INPUT cannot reach the code under test at all; the fix is to substitute the INPUT, not the assertion. #86 is about the assertion (keep the fixture, change what you assert); #156 is about the fixture input (keep the assertion, change what you feed in). They compose but address different layers: a single migration could hit both - first substitute the input (#156) so the helper is reachable, then re-scope any assertion the analog's side properties flipped (#86).

**Example (2026-07-18 negligible-value-partition-skip plan, Task 7 e2e):** The plan's Task 7 prose named `ITEM_A` (priced) and `ITEM_B` (unpriced) as the motivating identifiers for the negligible-value-partition e2e fixture, mirroring the unit fixtures in the negligible-summary test class. The unit tests construct entry dataclass rows with `classification=ACTIVE` passed verbatim, bypassing the production classifier. The e2e fixture (a dedicated example directory) must run the full upstream-export → workbook → negligible-block pipeline, so the classifier helper runs and routes EVERY category-B identifier (ITEM_A, ITEM_B, ITEM_C) to `DEFERRED`, because its ACTIVE branch is defined as "item is in the category-A set". The negligible-value partition operates exclusively on `active_entries`, so with ITEM_A / ITEM_B the partition would see an empty list and the negligible branch would be unexercisable. The fixture substitutes the category-A identifiers `ITEM_X` (priced analog of ITEM_A) and `ITEM_Y` (unpriced analog of ITEM_B). The substitution is faithful because the partition helper's discriminator is `e.item in priced_items_in_export` where `priced_items_in_export = {e.item for e in entries if e.value > 0}` - the discriminator reads `value > 0` and `item` identity, both of which ITEM_X/ITEM_A and ITEM_Y / ITEM_B produce identically (a priced ITEM_X row makes ITEM_X priced just as a priced ITEM_A row would make ITEM_A priced; a zero ITEM_Y row with no priced ITEM_Y row is unpriced just as a zero ITEM_B row would be). The fixture also adds a priced ITEM_Y detail row to keep ITEM_Y in `known_items` (a side constraint - the zero-value ITEM_Y row would otherwise be dropped by the `is_known` retention rule in the production module before it reaches the partition; this is the "re-scope side constraints" step). The test docstring documents the ITEM_A→ITEM_X, ITEM_B→ITEM_Y substitution per #86 (the assertion-scope cousin). All three e2e test methods go GREEN exercising the real pipeline. See the Task 7 implement log "Plan-vs-fixture item substitution (ITEM_A → ITEM_X, ITEM_B → ITEM_Y)" and "Classifier constraint" sections.

**See also:** coding_guidelines.md #25 (Family H parent), #18 (path reachability - mock OR amend; #156 is the e2e third option), #86 (re-scope the assertion when synthetic identifiers flip orthogonal signals - the assertion-layer cousin; #156 is the input-layer cousin), #107 (re-scope placeholder values when a later task assigns them a new semantic), #155 (RED fixture contradicts own stated intent - a fixture-construction defect, not a fixture-input substitution), #157 (a RED test pinning a NEGATIVE contract is legitimately GREEN at RED when production already satisfies it; the negative-assertion vertex of the RED-phase cluster), CLAUDE.md §4 Agent Workflow Rules.


## 157. A RED Test Pinning a NEGATIVE Contract (Must-NOT-Render on an Empty Precondition) Is Legitimately GREEN at RED When Production Already Satisfies It; Do Not Force It RED to Hit a "All N Tests Fail" Quota

**Principle:** Family H (Verify the real thing, not the abstraction) cross with the TDD-process family of #57/#81/#122/#155/#156. The RED phase of a TDD plan has TWO distinct contract shapes: (1) a POSITIVE contract ("the GREEN task adds behavior X, which is absent today, so the RED test fails now"), and (2) a NEGATIVE contract ("the GREEN task preserves behavior Y on an empty precondition, which is ALREADY satisfied today because the block is conditionally rendered"). A RED test for a negative contract is, by construction, a REGRESSION GUARD against a future always-render regression; it cannot go RED at authoring time because the production code already satisfies the negative contract. Forcing it to fail (via `pytest.fail`, a sentinel, or a `try/except` scaffold) to hit an "all N tests fail RED" summary quota is a category error: it converts a regression guard into a transient process step, destroying its guard value and conflating it with the positive-contract behavioral tests it sits beside.

**Trigger:** A multi-task TDD plan whose summary exit criterion says "confirm all N tests fail RED," where ONE of the N tests asserts a NEGATIVE property of the form "given an empty/precondition-absent input, the rendered output does NOT contain block/section/field Z." The plan's verbatim spec for that one test describes it as a "regression guard on the conditional render" (or equivalent), distinguishing it from the behavioral RED tests in the same class. At the RED run, the N-1 behavioral tests fail naturally (the GREEN behavior is absent), but the negative-contract test PASSES (production already does not render the block on the empty precondition). The implement sub-agent then faces pressure to "make the negative-contract test fail too" to satisfy the summary quota.

**Rule:**
1. Before treating a "RED test that is passing" as a defect at RED authoring time, classify the contract shape of each test in the class. A test whose assertion is of the form "given empty/precondition-absent input, output does NOT contain X" pins a NEGATIVE contract; a test whose assertion is of the form "given present input, output CONTAINS X" pins a POSITIVE contract.
2. A NEGATIVE-contract test that PASSES at RED, where the plan spec explicitly labels it a "regression guard" on the conditional render (and the relevant Section 7 / Part 7 / e2e siblings have an analogous passing-in-RED guard as precedent), is CORRECTLY GREEN. Do NOT force it RED via `pytest.fail`, a temporary sentinel, or a scaffold that flips the production conditional. The summary "all N tests fail RED" is a heuristic exit criterion that the verbatim-per-test spec overrides; the per-test spec wording ("regression guard on the conditional render") is authoritative over the summary quota.
3. Document the asymmetry in the RED task's implement log under a "Deviations from plan" section: name the negative-contract test, quote the verbatim spec wording that marks it a regression guard, cite the sibling-class precedent (e.g. "mirrors Part 7's `test_no_rewards_empty_label_unchanged` which also passes in its RED phase for the same reason"), and state explicitly that N-1 tests fail RED via natural assertion failure while the negative-contract test passes as a regression guard. This lets the `done` sub-agent and reviewers distinguish a designed-GREEN-in-RED from a misimplemented RED that failed to fail.
4. Authoring-time discipline for the negative-contract test: write it as a clean assertion (`assert header not in rendered_output` or `assert count == 0`), NOT a `pytest.fail` scaffold. The test's GREEN-today state must be the assertion's natural result on the current production code, not a forced failure that a later task removes. A negative-contract test written with a `pytest.fail` that the GREEN task deletes is a transient process step masquerading as a regression guard; it provides no guard value after GREEN and violates #122's "the failure mode is part of the contract" discipline in the opposite direction (a guard whose only failure mode is "the scaffold was not yet deleted").
5. The negative-contract test's load-bearing case is the ALWAYS-RENDER regression the guard exists to catch. Verify at GREEN (or at a later review) that flipping the production conditional to "render unconditionally" makes the negative-contract test fail; this is the analogue of #34/#99's revert-check for a guard-binding test, applied to the negative-contract vertex. If the test stays GREEN under the always-render regression, the assertion does not actually bind the conditional and must be strengthened.

**Why this happens:** TDD plan summaries default to "all N tests fail RED" because the common case is the positive-contract behavioral test (the GREEN task adds the behavior; absent today; RED now). When a negative-contract regression guard is committed in the same RED task as positive-contract behavioral tests, the summary's "all N fail" wording reads as a hard quota, and an implementer who has not classified the contract shapes treats the passing guard as a failure to make RED. The fix is contract-shape classification at RED authoring time: positive contracts fail naturally at RED; negative contracts pass naturally at RED when production already satisfies them. The summary quota is a heuristic that the per-test spec overrides; the per-test "regression guard" wording is the signal that overrides it.

**Shape trigger (when to suspect this family):**
- A RED test's assertion is a NEGATIVE membership/count claim ("X not in output", "count of X == 0", "block Z does not render") on an input where the production code today does NOT render X/Z (because the precondition the GREEN task adds is absent).
- The plan's verbatim spec for that one test describes it as a "regression guard", "no-render guard", "conditional-render guard", or "guard against a future always-render regression" - wording that distinguishes a guard from a behavioral characterization.
- At the RED run, N-1 sibling tests fail naturally and this one test PASSES; the summary exit criterion says "all N fail"; the implementer is uncertain whether to force the passing test RED.
- A sibling class in the same plan family (Part 7 e2e, an earlier task's empty-input guard) has an analogous test that also passed in its RED phase for the same reason - a precedent the implementer can cite.

**General form:** A RED test's role is determined by the SHAPE of the contract it pins, not by the exit-criterion quota of the RED task that commits it. Positive contracts ("GREEN adds X, X absent today") fail naturally at RED; negative contracts ("GREEN preserves not-X on empty precondition, not-X already true today") pass naturally at RED when production already satisfies them. A negative-contract test committed in a RED task is a regression guard against a future regression that would re-introduce the rendered block on the empty precondition; it cannot be made RED without destroying its guard value, and the summary "all N fail" quota is overridden by the per-test spec's "regression guard" wording. The recovery is asymmetric: trust the per-test spec wording as authoritative; document the N-1-RED-plus-1-GREEN asymmetry in the implement log; do NOT force the negative-contract test RED.

**Distinguishing from #155 (RED fixture contradicts own stated intent):** #155 fires when a RED test's FIXTURE constructs the wrong case (mixed vs all-negligible), so the docstring's named case never fires and the test fails for the wrong reason at GREEN. This lesson (#157) fires when the RED test's CONTRACT is negative (must-not-render) and production already satisfies it, so the test PASSES at RED by design. #155's contradiction is fixture-vs-intent (a defect); #157's pass is contract-shape-correct (a feature). #155 bites at GREEN (the implementation runs, the wrong case fires, the test fails for the wrong reason); #157 is observable at RED (the test passes when the summary says all should fail).

**Distinguishing from #122 (committed-RED must fail as a clean assertion):** #122 prescribes the FAILURE SHAPE of a RED test whose deliverable is the committed RED (clean `pytest.fail` naming the resolving task, never an unhandled exception). This lesson (#157) prescribes the PASS-vs-FAIL CLASSIFICATION of a RED test whose contract is negative: it is legitimately GREEN at RED, and forcing it to fail (via `pytest.fail` or a scaffold) violates #122 in the opposite direction by introducing a failure mode the GREEN task must then delete. #122 is about how a DESIGNED-RED test fails; #157 is about recognizing when a test is NOT designed-RED at all because its contract is negative and already satisfied.

**Distinguishing from #34/#99 (regression test must exercise the guarded production path; disable-and-confirm-RED):** #34/#99 prescribe the GREEN-time verification that a guard-binding test actually binds the guarded path (disable the guard, confirm the test fails). This lesson (#157) prescribes the RED-time classification that recognizes a negative-contract test as a guard, not a behavioral RED. The two compose: at RED, classify the contract shape (#157); at GREEN, run the disable-and-confirm-RED check (#34/#99) to verify the negative-contract test actually binds the conditional render.

**Distinguishing from #81 (re-read RED against revised invariants):** #81 fires when the plan was REVISED between RED and GREEN, so the RED test's assertions are stale relative to the new contract. This lesson (#157) fires when NOTHING was revised: the negative-contract test pins a contract the production code already satisfies, and the test passes at RED by design. #81 is about assertion freshness under revision; #157 is about contract-shape classification at authoring time.

**Example (2026-07-19 deferred-bucket-negligible-skip plan, Task 3 RED):** Task 3's deliverable was the deferred-skip test class with 7 tests pinning the "Suppressed zero-value deferred entries" block that Task 4 will render. Six tests pin POSITIVE contracts (the block renders with the negligible-value reason, the unpriced reason, the merged single-block sorted order, the `:.8f` amount format, the per-(asset,account) sort, the `safe_cell_value` wrappers); these fail RED naturally because the block is absent today (header count `0 != 1`). The seventh test, `test_empty_skipped_list_renders_no_block`, pins a NEGATIVE contract: given an empty `skipped_zero_value_deferred_entries` list, the rendered output must NOT contain the "Suppressed zero-value deferred entries" header. The verbatim Task 3 spec described this test as a "regression guard on the conditional render." At the RED run, 6 tests failed and `test_empty_skipped_list_renders_no_block` PASSED, because production already conditionally renders (the block does not exist yet, so it is trivially absent on the empty precondition). The implement log documented the asymmetry under "Deviations from plan": cited the verbatim "regression guard on the conditional render" wording, cited the sibling precedent `test_no_entries_empty_label_unchanged` (in the same test file, which also passes in its RED phase for the same reason), and stated that the 6 behavioral tests fail RED via natural assertion failure while the negative-contract test passes as a regression guard. The test was NOT forced RED via `pytest.fail` or a scaffold; it remained a clean `assert header_count == 0` assertion whose GREEN-today state is the natural result of the current conditional render. The full module run confirmed `6 failed, 48 passed` - all 48 pre-existing tests stayed GREEN and the only failures were the 6 new positive-contract behavioral RED tests. See the Task 3 implement log "Deviations from plan" section and the deferred-bucket-negligible-skip plan file Task 3 verbatim spec.

**See also:** coding_guidelines.md #25 (Family H parent), #57 (TDD RED-then-GREEN as a process step - the positive-contract transient case), #81 (re-read RED against revised invariants - the contract-change case, not the contract-shape case), #99/#34 (regression test must exercise the guarded production path; disable-and-confirm-RED - the GREEN-time guard-binding verification that pairs with this RED-time classification), #122 (committed-RED must fail as a clean assertion - the failure-shape discipline this lesson extends to the negative-contract vertex by forbidding forced failure), #155 (RED fixture contradicts own stated intent - a fixture defect at GREEN, not a contract-shape classification at RED), #156 (e2e-realizable analog input substitution - the input-layer cousin in the same plan family), CLAUDE.md §4 Agent Workflow Rules (RED-then-GREEN TDD discipline).

## 158. When You Expand an Open PR's Scope (Files and Body), Update the Title in the Same Turn

**Principle:** Family C (Descriptive Output Labels) cross with Family D (Single source of truth for the artifact the reader sees first).

**Trigger:** You push commits and/or run `gh pr edit --body` on an open PR whose scope grew or shrank (more countries, modules, tickets, or deliverables), but you leave the existing title unchanged. The user (or a later reader) opens the PR list or the PR page and still sees the old narrow title (for example "TZ UAT config draft") even though the body and file list already describe the broader work.

**Rule:**
1. Treat the PR **title** as part of the same publish surface as the body and the commit list, not as a create-time-only field.
2. After any scope-expanding (or scope-narrowing) update to an open PR, compare the current title to the new summary in one sentence. If they disagree, run `gh pr edit <n> --title "..."` in the **same** turn as the body/files push.
3. Prefer a title that names the real deliverable set (markets, modules, ticket), not the first draft's narrower intent.

**Why this happens:** Agents often update what they just edited (property files, PR body Markdown) and skip the title because it was set at `gh pr create` and is not in the local git diff. Humans scanning the PR list only see the title, so the update looks missing even when commits and body are correct.

**Shape trigger:** User asks "why didn't you update the PR?" after you already pushed files and refreshed the body; the title still matches the first draft.

**Example (2026-07-21 `example-crm-config` PR #6):** Commits and body already listed the new markets and segment keys; the title still named only the original market draft until a follow-up `gh pr edit --title`.

**See also:** `github-pr-workflow` skill (PR Descriptions and Stats: title stays in sync with scope).

## 159. Keep Code-Structure Keys Out of Per-Workspace Config-Server Overlays

**Principle:** Family D (Single source of truth) cross with Family F (Layering / dependency direction).

**Trigger:** A review of Spring Cloud Config (or similar env overlay) files asks whether a key like `mybatis.type-handlers-package`, a Java package scan path, a fixed serializer class name, or another compile-time code-structure constant belongs in the per-workspace overlay. The overlay already duplicates JAR defaults "for safety," or a follow-up doc listed the key under config-repo coverage because local/test YAML had it.

**Rule:**
1. Classify each overlay key: **env/workspace identity** (country, datasource host, feature flags that differ by region) vs **code structure** (package scan paths, type-handler registration, fixed bean class names).
2. Put code-structure keys in packaged `application.yml` (or module auto-config), not in `{service}-{cc}-{env}.properties`. Per-country files should not restate values that never change by workspace.
3. When a human asks "do we need this here?", prefer moving the key into the JAR and deleting it from every overlay in the same change set, rather than only defending why the overlay currently works.
4. Update guardrails/docs that pointed at `application-local.yml` or config-repo as the home for that key in the same pass.

**Why this happens:** Local profiles and infra checklists often list every key needed to boot. Agents copy that list into config-server drafts. Reviewers correctly flag that package paths are not regional config.

**Example (2026-07-22 `example-crm-config` PR #6):** A reviewer asked whether `mybatis.type-handlers-package` belonged in the per-workspace UAT overlay. It was only in `application-local.yml` / test YAML, so UAT overlays had been restating it. Fix: move to packaged `application.yml` and drop from all UAT overlay files.

**See also:** #163 (verify overlay `spring.application.name` against the target JAR), project `operational-guides.md` (MyBatis type-handler scanning), CRM naming ADR for deployable vs runtime identity (related but distinct: filename vs `spring.application.name`).

## 160. Read the Wiki Page Body Before Citing It for a Control Claim

**Principle:** Family H (Verify the real thing, not the abstraction)

**Trigger:** A spreadsheet, audit, RFC note, or design answer cites a Confluence (or similar) page as proof of a control (encryption, auth, network, retention). The page title or topic sounds related (e.g. "Data Points", "Event Ingestion"), so the agent scores Yes/Partial from the title or from adjacent ADR prose without opening the page body.

**Rule:**
1. Before using a wiki/doc URL as evidence for a control column or claim, fetch or open the **page body** and quote the sentence that actually states the control.
2. If the body only lists fields, events, or goals (and never states the control), do **not** score the control as present from that citation. Ask the user or mark Partial/No with remediation aimed at the real gap.
3. Do not conflate a neighbor system's edge story (e.g. the front-door service → Platform HTTPS) with this service's own Encrypted-in-Transit / Authentication columns.

**Why this happens:** Titles and ADR summaries are easy to over-read. Agents fill "Current Protection" from design intent instead of what the cited page and this service's code actually show.

**Shape trigger:** User says the cited page does not say what you claimed; or Encrypted/Auth scores reverse after they point at Event Ingestion vs Profile privacy.

**Example (2026-07-22 API Endpoint Security Audit for `example-crm-profile`):** An internal wiki page on data points lists PII fields; it does not define encryption-at-rest. Citing it for "Encrypted Data at Rest = Yes" was wrong. Separately, the event-ingestion wiki page puts HTTPS at the Platform layer; the Profile service stays private, and internal HTTPS was only under discussion, not "gateway HTTPS per ADR #27" on Profile's transit column.

**See also:** coding_guidelines.md #25 (Family H), #6 / verify-source lessons in this corpus.


## 161. Inventory Free-Text Columns Must Not Restate Structured Fields

**Principle:** Family D (Single source of truth) cross with Family C (Descriptive output labels)

**Trigger:** Filling a multi-column security or compliance inventory (Public API?, Auth, Network, Risk, Encrypted…). Notes and Remediation repeat "not public", "Auth=No", "VPC-internal risk", or the same encryption story already implied by dropdown columns.

**Rule:**
1. **Remediation Action Needed** = only the open gap to close (one short imperative). Example: encrypt and authenticate inter-service callers.
2. **Notes** = context that is **not** already in earlier columns (e.g. PII ciphertext ownership model, undeployed). Do not restate Public API?, Authentication, Network + Infra, or Risk.
3. Prefer lean wording; if a phrase duplicates a column, delete it from Notes/Remediation.

**Why this happens:** Agents summarize the whole security story into every free-text cell. Reviewers then see duplication and have to ask for a trim pass.

**Shape trigger:** User says Remediation and Notes look duplicated, or Notes repeat "Not public" / "Auth=No" already shown in columns.

**Example (2026-07-22 API Endpoint Security Audit V2.xlsx for the EU region of `example-crm-profile`):** Trimmed Notes to the service-encrypt / app-ciphertext / messaging-decrypt model + Undeployed; Remediation kept only inter-service encryption/auth. Dropped "Not public (Platform/BFF first)", "app Auth=No", and "Risk = VPC-internal" from Notes.

**See also:** #9 (descriptive labels), #160 (do not invent controls from unopened wiki pages).


## 162. Shared Skill Symlink: Install CLIs Must Not Rewrite the Playbook Tree

**Principle:** Family D (Single source of truth)

**Trigger:** Installing an external skill "for all agents" with `npx skills add -g --copy` (or similar) while `~/.agents/skills` is a symlink into `instructions_repo/agents/skills`.

**Rule:**
1. Treat the shared registry symlink as a git checkout, not a disposable install root.
2. Vendor by hand into `agents/skills/<name>/` (drop upstream `agents/` adapters; keep `LICENSE.txt` + `metadata.upstream`).
3. Use each agent's native plugin/marketplace CLI for Claude, Codex, and Antigravity.
4. After any tools CLI that claims to install into `~/.agents/skills`, run `git status` on the playbook and remove accidental vendor folders before commit.

**Why this happens:** The skills CLI copies into the path the agent scans. A symlink makes that path the versioned playbook, so "install" becomes an unreviewed tree edit.

**Shape trigger:** After `npx skills add`, `LICENSE.txt` disappeared, an `agents/` subfolder reappeared under a skill, or `git status` shows unexpected skill-tree churn you did not stage.

**Example (2026-07-23 ai-playbook, `ayghri/i-have-adhd`):** `npx skills add ... -g -a opencode --copy` wrote through `~/.agents/skills` into the playbook, reintroduced upstream `agents/`, and dropped `LICENSE.txt` until cleaned. Fixed by manual vendor + Claude/Codex/`agy` plugins.

**See also:** `agent_workflow_guidelines.md` 58.7; `agent-runtime-layout.md` (ADHD-friendly output style); vendoring checklist in `skill-upstream-catalog.md`.

## 163. Config-Server Overlay Identity Keys Must Match the Target Service JAR

**Principle:** Family H (Verify the real thing, not the abstraction)

**Trigger:** Reviewing Spring Cloud Config (or similar) per-workspace `.properties` files. A sibling service overlay uses a prefixed `spring.application.name` (e.g. `<org>-<product>-*`), or copies a deploy-region key / other keys. A premortem or security pass treats a missing overlay key as a guaranteed boot crash. The config comment cites an ADR or "same as profile."

**Rule:**
1. For every **active** identity key in the overlay (especially `spring.application.name`), open the target service's packaged `application.yml` (or equivalent) and compare the value. Do not infer the name from the config filename, from a sibling service, or from an ADR comment alone. The "profile" variant of a product may carry a longer prefixed name while "platform"/"campaign" variants use shorter unprefixed names.
2. Before flagging a missing overlay key as required, confirm the target service has a **consumer** (binding, EnvironmentPostProcessor, or fail-fast validator). Keys that exist only on a sibling service are not contract drift on this overlay.
3. Before claiming "missing key = startup crash," check whether the JAR already supplies a non-empty default. If it does, treat a missing commented placeholder as a Low go-live checklist item, not High/Critical.
4. Filename vs `spring.application.name` can intentionally differ; that split is not the same as setting the wrong application name value.

**Why this happens:** Config PRs are reviewed against sibling overlays and ADR nicknames. Agents copy the profile pattern or escalate "fail-fast" from docs without reading the service under review.

**Shape trigger:** A Medium/High finding about overlay identity or boot crash is dropped or downgraded after someone opens the service `application.yml` and finds a different default or no consumer.

**Example (2026-07-22 `example-crm-config` PR #9):** Platform UAT files set `spring.application.name` to the prefixed platform name citing an ADR; the platform JAR and naming map use the shorter unprefixed name. Architecture flagged a missing deploy-region key (profile-only consumer). Premortem rated a missing allowed-domains key High; the JAR already ships a default.

**See also:** #159 (code-structure keys out of overlays), #158 (PR title stays in sync with ticket/branch), doing-code-review §4.2 assumption checks.


## 164. When Inserting a Test Class Into an Existing File, Grep for Module-Level Helpers First (F811 May Be Off)

**Principle:** Family D (Single source of truth)

**Trigger:** An agent (especially a sub-agent in an execute-plan implement step) appends a new test class plus its fixtures/helpers to a large existing test file. The insertion re-declares module-level helpers (`_SOME_ORIGIN = OperatorOrigin(...)`, `def _make_some_fixture(...)`) that already exist earlier in the same file. A pre-commit lint step runs clean. The defect survives review round 1.

**Rule:**
1. Before appending a new test class and its helper block to an EXISTING test file, grep the target file for every module-level helper and fixture constant the new block would declare: `grep -nE '^(def |[A-Z_]+ = )' <test_file>`. If any name already exists at module scope, REUSE the original; do not re-declare it. Python silently rebinds a module-level name on the second definition, so the duplicate is behaviorally invisible when byte-identical (the later binding wins, same object).
2. Do NOT trust "ruff is clean" as evidence there are no duplicate definitions. `F811` (redefinition of unused `name`) is the ruff rule that catches this, and it is frequently OFF in a project's `pyproject.toml` `[tool.ruff]` (this repo configures it off). When `F811` is off, a byte-identical module-level redefinition produces zero diagnostics. The only reliable detectors are the pre-insertion grep (rule 1) and a diff-hunk read that notices a `def`/assignment appearing twice at module scope.
3. When you DO detect a duplicate, remove the LATER copy (the insertion), keeping the canonical original at its earlier line. Do not remove the original and keep the new one unless the new one is intentionally divergent (in which case it is not byte-identical and rule 1 should have caught it as a true edit, not a re-declaration).
4. Consider enabling `F811` selectively (per-file or in a `# noqa: F811`-free targeted `[tool.ruff.lint] select`) if duplicate module-level definitions recur in a file; the rule is cheap and has few false positives in test modules that do not re-export.

**Why this happens:** A sub-agent tasked with "add a test class for feature X" reads only the plan's fixture recipe and writes the class plus its supporting helpers as a self-contained block, without scanning the rest of the file for pre-existing shared fixtures. The plan's implement step does not instruct the agent to grep first. Round-1 review trusts the green suite and clean ruff output, both of which hold because the duplicate is byte-identical (683 tests pass) and ruff F811 is off.

**Shape trigger (when to suspect this family):** A review or self-audit of a test-file diff shows a `def _make_...` or a `_SOME_CONST = ...` block at module scope that looks familiar; OR a grep for the same name returns two top-level definitions in one file; OR the plan's implement step says "add a test class and its fixtures" to an existing test file. The risk is highest for byte-identical duplicates (no behavior change, so no test fails to flag them).

**Example (2026-07-24 logging-review r2, Low):** The event-emitter-filter review inserted `class TestEventEmitters` into `tests/unit/application/test_event_filter.py` along with a helper block re-declaring `_TEST_OPERATOR_ORIGIN` and `_make_matched_item`. The originals already existed at lines 639 and 652; the new copies landed at lines 956 and 969, byte-identical. Python silently rebound both (all 683 affected tests passed), and `uv run ruff check` reported clean because F811 is configured off in this repo. Round 1 missed it (green + clean lint). Round 2's fresh diff-hunk read found the duplication. The fix removed the second copies (old lines 956-1004), keeping the canonical originals. Full suite 1852 green after removal.

**Distinguishing from #1:** Lesson #1 is the thin Family D seed ("always check for duplicate test methods or functions before adding new code", `grep -n "def method_name" -r`). This lesson #164 is the specific, non-obvious aggravator that makes #1 actually fire reliably: F811 is OFF here, so "ruff clean" cannot substitute for the grep, and byte-identical module-level helper duplicates are the exact shape that is invisible to both the test suite and the configured linter. #1 says "grep first"; #164 says "grep first AND do not trust ruff-clean, because F811 is off."

**Distinguishing from #68:** Lesson #68 is about `ruff check --fix` REMOVING intended re-export imports (F401 false-positive on backward-compat re-export modules). This lesson #164 is the opposite direction: ruff FAILING to flag an UNINTENDED module-level redefinition (F811 off). #68 = ruff over-deletes; #164 = ruff under-reports. Both are "ruff config gap" lessons but on different rules (F401 vs F811) with opposite failure modes.

**General form:** When inserting a self-contained block (test class + fixtures, or any function + its module-level constants) into an existing module, scan the target module for pre-existing definitions of every name the block introduces. A linter that has the redefinition rule disabled cannot rescue a missed scan, especially when the duplicate is byte-identical (no runtime divergence to surface).

**See also:** Lesson #1 (duplicate-detection Family D seed), Lesson #68 (do not `ruff --fix` on re-export modules), CLAUDE.md "Code Quality" (Ruff primary linter/formatter).

## 165. Do Not Override an Agent-Enforced Mechanical Gate by Restoring Policy-Violating Content

**Principle:** Family A (mechanical invariants over prompt advice) + Family H (verify the real thing). A repo rule enforced by an agent wins over the orchestrator's model of "what the user wanted."

**Trigger:** A sub-agent (`done`/`learn`/`review`) enforces a mechanical gate (em-dash scan, linter, size gate, secret scan) against content the orchestrator authored. The gate fires, the sub-agent complies and rewrites. The orchestrator "catches" the rewrite, calls it "silent corruption," and reverts the compliant output (e.g. `git commit --amend` to restore the violating version), framing it as "preserving user intent."

**Rule:**
1. A sub-agent enforcing a repo gate that returns a compliant result is the gate working as designed, not a malfunction.
2. Before overriding any agent-enforced gate, escalate first: "Gate X fired; the agent rewrote it. Accept the compliant version, change the policy, or do a better de-violation pass?" Never amend/restore unilaterally.
3. "User authored it" / "history artifact" / "master has violations" are NOT exemptions. A policy with no documented carve-out applies to every file the gate scans. Exempting a file class is a POLICY CHANGE (edit the rule/script scope), not a per-file veto.
4. If the compliant rewrite is semantically poor (blanket `X→Y` that mangles meaning), do a BETTER de-violation pass, not a revert to the violating original.

**Why this happens:** The parent pattern-matches the rewrite to "agents silently corrupt prose" before checking whether a gate drove it, then reverts as confident diligence. The tell: the compliant agent is "silently rewriting" and the violating original is "pristine user prose."

**Shape trigger:** Before reverting a sub-agent's edit, ask: (1) Did a repo gate or SKILL step cause it? (2) Does the pre-edit version actually violate that policy (run the gate yourself)? If yes to both, escalate; do not revert.

**Example (execute-plan Task 1 `done`):** A plan file had many U+2014 em dashes. `done` ran `check-no-em-dash.sh touched` (Step 2.76), substituted replacements, committed. The orchestrator restored the em-dash version from a docs-branch snapshot and amended the commit so HEAD held the violating plan, citing "preserving user prose." The user corrected: the `done` agent was doing its job. A follow-up re-did the de-em-dashification; until then the violation sat in history.

**Distinguishing:** (a) Out-of-scope prose edits (sub-agent making unrelated `AGENTS.md` edits with no gate driving them) ARE revertible; discriminator = gate enforcing, or agent freelancing? (b) UL#115 is a gate that FAILS to fire (false pass); here the gate fired and the parent vetoed the correct outcome.

**See also:** UL#115 (`touched` misses committed files; gate-too-weak complement), `done` SKILL Step 2.76, `agent_workflow_guidelines.md` Family A.

## 166. Enumeration-Based Leak Gates Cannot Catch Novel Identifiers; Pair Them With a Judgment Review

**Principle:** Family H (verify the real thing, not the abstraction). A deny-pattern scan verifies the *enumerated* bad-token set, not the *leak surface* (any token that fingerprints the employer, OR any token that frames content in a specific application domain it should have been generalized out of). The enumeration is always a lagging subset of an open-ended surface.

**Trigger:** A public-repo hygiene/leak scan, OR a generalization-cleanup grep with a closed token set, reports PASS on content that nonetheless carries tokens the list never named. Two leak-surface flavors: (a) employer fingerprints (bare company name, service prefix, customer country-code list, ticket prefix, person name, internal URL), and (b) domain-vocabulary framing (terms that only make sense inside a specific application domain the prose should have been generalized past).

**Rule:**
1. A deny-pattern scan is a **backstop**, never the primary leak defense; it only catches identifier classes someone already enumerated. Treat a PASS as "no enumerated token matched," not "no fingerprint present."
2. The primary defense is a **per-identifier judgment review**: re-read the drafted text and, for every proper noun, run the load-bearing test ("does replacing this with a generic role weaken the rule?"). Redact anything that survives. This catches novel identifiers the scan cannot.
3. When a leak is found post-PASS, do NOT only add the token to the deny list; that fixes one employer's symptom. Ask which layer failed: drafting (generalization didn't interrogate identifiers) or review (judgment step skipped)? Strengthen the failed layer.
4. Classes most likely to leak *because they read as legitimate context*: service/product/company names and prefixed slugs, ticket-system prefixes (the prefix alone identifies the tracker), customer/market enumerations, person names/handles, internal hostnames/wiki URLs, exact incidental counts.

**Why this happens:** Enumeration scans feel authoritative (mechanical, deterministic, exit-coded), so a PASS feels like proof of cleanliness. Reviewers anchor on it and stop interrogating the prose; novel identifiers sail through because the scan already "covered" them.

**Shape trigger:** A hygiene/secret scan exits clean on content headed for a public repo, AND the content describes a specific incident (lesson, postmortem, example) rather than abstract guidance. Incident prose is where employer fingerprints hide; abstract rules rarely carry them.

**Example:** A lessons corpus passed the repo's deny-pattern scan (which listed an employer slug and email domain) while still containing the bare company name, a country-code customer list, a ticket prefix, and an employee first name, none on any list. The scan reported PASS; the leaks shipped. Fix: added a per-identifier judgment review to drafting and demoted the scan to an explicit backstop. The judgment review catches the next employer's identifiers; the scan only catches repeats.

**Witness (domain-vocabulary flavor):** A generalization pass declared a lessons corpus clean after running a closed token-set grep (`FOO|BAR|BAZ|...`). A later review's broadened domain-vocabulary grep (the employer's internal service names, the customer country-code list, the application's domain nouns, ...) found ~40 lessons whose Rules were portable but whose Examples still narrated the very application domain the rules had been generalized out of. The closed-set grep had reported PASS because none of the broadened tokens were on the list. Fix: replace the closed-set gate with a judgment review that asks, per Example, "does this prose still require the specific application domain to be meaningful?" and redact the domain framing where it does not. Same root cause, different leak surface: identifier fingerprint vs domain framing.

**Distinguishing from UL#115 (gate too weak):** UL#115 is a gate that FAILS to fire on a real match. This lesson is a gate that fires correctly on its enumerated set but whose set is provably incomplete for the open-ended leak surface: true negatives on the list, false confidence overall. Fix UL#115 = run the gate correctly; fix this = don't treat enumeration as the primary defense.

**See also:** `learn` SKILL Step 1.2 item 1c (generalize across employer identity) and Step 1.7 (proper-noun justification review) are the canonical home for the judgment-review mechanism; UL#115 (gate-too-weak complement); `agent_workflow_guidelines.md` Family H.

## 167. Invoke the Specialized Skill; Do Not Reimplement Its Workflow With Generic Harness Primitives

**Principle:** Family D (Single source of truth for workflow contracts). A specialized skill (`plans`, `review-plan`, `done`, `execute-plan`, `rfc-design`) owns its workflow: format, branch setup, ordering, and quality gates. The harness's generic primitives (plan-mode enter/exit, hand-rolled markdown in a tool call, an inline single-pass critique) look like shortcuts but silently skip the skill's conventions, producing an artifact that fails the very gate the skill exists to enforce.

**Trigger:** A task maps to a specialized skill that is installed and listed in the session's available skills, but the agent reaches for a generic harness mode or hand-rolled output instead of invoking the skill by name. The user then corrects with a variant of "use the X skill" or "the plan/output is wrong, create a proper one with the X skill."

**Rule:**
1. Before producing any plan, review, RFC, or session-finalization artifact, check whether an installed skill owns that workflow. If yes, invoke THAT skill (via the Skill tool or its slash command) and follow its steps; do not substitute the harness's plan-mode or a hand-rolled document.
2. The skill's quality gate is not optional theater. A plan written outside the `plans` skill skips `review-plan`; a review done inline skips the panel catalog; a commit done by hand skips `learn` + `docs-branch`. Each omission is a defect the skill exists to prevent.
3. If a generic harness mode is already active (e.g. plan mode) when you realize a skill should own the workflow, exit that mode and invoke the skill; do not try to "then run the skill after": the skill IS the workflow, including its own branch/file steps the generic mode blocks.
4. Corollary of UL#148: invocation is the mode selection. But invocation requires actually invoking: pattern-matching "this looks plannable" and entering generic plan mode is NOT invoking the `plans` skill.

**Why this happens:** Generic plan mode and hand-rolled output feel faster (no Phase 0 branch, no interview, no review gate). The skill's value is invisible until the artifact hits its gate and fails, or until the user notices the skipped conventions. Agents also conflate "thinking about a plan" with "running the plans skill."

**Shape trigger:** The session has `plans`/`review-plan`/`done`/`rfc-design` available AND the agent is about to write a plan/review/RFC/commit via a generic tool call or generic plan mode rather than the Skill tool.

**Example:** Asked to create an implementation plan, the agent entered the harness's generic plan mode, drafted the plan inline, and tried to exit-plan-mode to "then run plans." The user corrected twice ("you should have used plans skill instead"; "the plan is wrong. Create a proper plan with plans skill"). Fix: invoke the `plans` skill, which ran Phase 0 branch setup, wrote the format-correct file, and ran the mandatory `review-plan` gate (3 rounds, caught 2 Blockers + 8 Mediums the hand-rolled version would have shipped with).

**Distinguishing from UL#148 (auto-continue after invocation):** UL#148 fires AFTER a skill is correctly invoked (don't re-ask yes/no between its steps). This lesson fires BEFORE invocation (don't bypass the skill with a generic mode in the first place). Fix UL#148 = stop pausing inside the workflow; fix this = enter the workflow.

**See also:** `plans` SKILL (Plan Quality Gate), `review-plan` SKILL, UL#148 (auto-continue), UL#166 (do not override an agent-enforced gate), `agent_workflow_guidelines.md` Family D.

## 168. Softened review fixes need a cross-round watchlist

**Principle:** Family H (Verification discipline) and Family D (single process SOT for review readiness).

**Trigger:** A review-loop (or multi-round branch review) marks a finding fixed, then a later commit or triage softens/reverts that fix; OR a focused clear round omits the worker that owned earlier architecture/ownership findings; OR an external/bot review later finds issues the loop declared clean.

**Rule:**
1. Maintain a soften watchlist across rounds. Soften/revert after fixed keeps the item open until a later review reaffirms (still intentional) or restages.
2. Do not exit the loop on zero blocking findings alone when open softens remain, or when the clear-candidate focused panel never re-ran design-simplicity on the tip after architecture-relevant code landed.
3. Treat typed 4xx as insufficient when the wire error code / owning module is wrong for the endpoint; treat per-key repository reads over a catalog list as N+1 even when the list is size 1 today if a bulk read already exists.
4. Encode these in the review skills (review-loop, review-staging, language overlays, quality/architecture lenses), not as one-off chat advice.

**Shape trigger:** Commit subject or triage says "soften" / "restore prior" after a review fix; or loop exit used a docs/risk-only focused panel; or external review finds exception-ownership or catalog-loop issues after a clean loop.

**Example:** A branch review fixed wrong exception ownership on a mixed transport converter, then a same-day soften restored the sibling-module exception. Later focused rounds exited blocking-clean without re-checking. An external PR bot restaged both that ownership issue and a catalog-key N+1 loop the quality lens already described but agents skipped because N was tiny.

**See also:** review-loop Soften / regression watchlist and exit criteria; receiving-code-review Soften tracking; doing-code-review java-spring / kotlin-spring Transport Exception Mapping; quality.md catalog-loop item; Family H verification and Family D single SOT.

## 169. A Canonical Spec Example Shown In Multiple Formats Must Keep All Formats Consistent

**Principle:** Family D (single source of truth) and Family H (verify the real artifact). When a spec/template presents the same logical example in more than one format (for example a Markdown table and a parallel JSON sidecar, or a YAML block and a prose description), each copy is a real artifact that downstream authors copy verbatim. If the copies disagree on a load-bearing field, consumers encode whichever copy they read first, and the disagreement is invisible until two consumers built from different copies meet.

**Trigger:** A spec or skill defines a structured example twice, in two formats, and a review (or a consumer) finds that the same row/object shows different values for a field the rest of the spec treats as semantically distinct.

**Rule:**
1. When the same example appears in two formats in one spec, the load-bearing fields (status, id, key, type, severity, lifecycle state) must match across all copies.
2. After editing one copy, grep the other copy for the shared identifier (row id, pattern, key) and update it in the same pass. Do not leave a "fix the Markdown, forget the JSON" (or vice versa) split.
3. If the formats genuinely need to differ (one shows an initial state, one a terminal state), label that explicitly in both copies; do not rely on the reader inferring the lifecycle from context.

**Why this happens:** A spec change touches one fenced block (often the human-readable one); the parallel machine-readable block sits a screen or two away and is easy to miss. The two copies feel like "the same example" but are edited independently, so they drift.

**Shape trigger:** A spec change adds or edits a structured example that exists in two formats; or a review reports the same row/object with conflicting field values across sections.

**Example:** A review-skill spec introduced a watchlist example showing the same row (`round`, `pattern`, `anchor`, `prior fix`, `soften reason`) in both a Markdown table and a JSON sidecar block. The Markdown showed the row's lifecycle `status` as `reaffirmed` (terminal); the JSON showed the identical row as `open` (carried forward). Both blocks sat in the same file, screens apart. A focused review caught it; copy-paste consumers would have encoded opposite lifecycle semantics. Fix: set both copies to the same status in one pass and grep the file for the row id to confirm no third copy existed.

**See also:** UL#144 (micro-edit fenced templates, technique), UL#145 (structured staging metadata, why parallel human/machine artifacts exist), `agent_workflow_guidelines.md` Family D (single SOT) and Family H (verify the real artifact).



## 170. Execute-Plan Must Detect When the Plan File Under Execution Was Rewritten by an Intermediate docs-branch Sync

**Principle:** Family H (verify the real artifact) and Family D (single source of truth). The plan file under active execute-plan execution is tracked on BOTH the feature branch and the orphan `docs` branch (plans are not gitignored). A `done` sub-agent's docs-branch sync is add-only for gitignored paths, but it pulls a *revised* tracked plan file back into the working tree when the orphan branch carries a newer version (for example, from concurrent plan-review rounds). The orchestrator then finds its in-flight plan has changed scope, checkboxes, and task structure between the Phase 1 read and the next task iteration.

**Trigger:** An execute-plan run where plan-review rounds ran against the plan before or during execution, a `done` docs-branch sync lands a docs-sync commit on the feature branch between two orchestrator steps, and the next read of the plan shows task structure or scope that does not match the Phase 0/1 read.

**Rule:**
1. After every `done` sub-agent returns during an execute-plan run, the orchestrator must re-read (or diff) the plan file before selecting the next task.
2. If the plan's task structure, Review Scope, Validation Commands, or unchecked-item count changed since the last read, surface the change to the user and get an explicit decision (follow the updated plan vs. finish the original scope vs. abort) before continuing. Do not silently continue against either version.
3. `git log --oneline <last-known-base>..HEAD -- <plan-path>` reveals docs-sync revisions; a `docs: update from <branch-slug>` commit that touched the plan path is the cause.
4. When the user chooses the updated plan, re-derive the task inventory and remaining-checkbox set from the current working-tree version.

**Shape trigger:** an execute-plan `done` sub-agent returns, and the next orchestrator step finds the plan's task count, titles, Review Scope, or Validation Commands do not match the earlier read; OR a docs-sync commit appears in `git log` between two task commits and touched the plan path.

**Distinguishing from #90:** #90 covers gitignored paths crossing into feature commits via *improvised* git ops. This lesson covers a *correct* canonical docs-branch sync that mutates a *tracked* plan file because the orphan branch carried a revision. #90 is about crossing the gitignored/tracked boundary illegally; this is about two legitimately-tracked copies of the same file diverging and the sync reconciling them.

**Example:** An execute-plan run on a five-worker review panel plan started against a 3-task plan. Between the Task 2 and Task 3 `done` runs, a docs-sync commit landed carrying a revised plan from r1-r4 plan-review rounds: Task 3 had grown from 7 to ~25 items and changed its title. The Task 3 `done` sub-agent flagged the discrepancy. The orchestrator confirmed the docs-sync was the cause, surfaced the fork to the user, and on the user's direction re-derived Task 3's inventory from the working-tree version and continued.

**See also:** UL#118, UL#96, `execute-plan` anti-pattern table, `done` Step 2, `docs-branch` skill, Family H and Family D.

## 171. In ripgrep, `-E` is `--encoding`, NOT POSIX ERE; a `rg -oE '<pattern>'` Validation Gate Silently Exits 2 and Matches Zero

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family D (single source of truth: the grep tool's flag semantics are NOT portable across grep implementations). The abstraction " `-E` means extended regex" is true for POSIX `grep`/`sed`/`awk` but FALSE for ripgrep (`rg`), where `-E`/`--encoding` sets the file encoding and consumes the next argument. A plan or skill that writes `rg -oE '<pattern>'` believing it is using extended regex produces a gate that exits 2 (encoding error) and matches zero lines, a silent no-op that certifies GREEN on whatever it was supposed to check.

**Trigger:** A validation command, plan gate, CI step, or script uses `rg -E` or `rg -oE` (borrowed from `grep -E` / `grep -oE` muscle memory or copied from a grep-based precedent). The command's stated purpose is to match and extract/count something (cites, identifiers, patterns); it must NOT silently pass when there is nothing to flag.

**Rule:**
1. In ripgrep, extended regex is the DEFAULT engine; you do not need `-E`. To get only the matched portion, use `rg -o '<pattern>'` (or `rg --only-matching`). Never write `rg -E` or `rg -oE` when you mean extended regex; `-E`/`--encoding` will consume your pattern as an encoding name and fail.
2. When porting a `grep -E`/`grep -oE` command to `rg`, DROP the `-E` (rg is ERE by default; `-E` changes meaning). Keep `-o` (same meaning: only-matching). `grep -oE '<pat>'` → `rg -o '<pat>'`.
3. After writing any `rg`-based validation gate, RUN IT against a known-positive input and confirm it returns non-empty output before trusting it. A gate that returns empty on input known to contain matches is broken; do not certify GREEN on empty output without a positive control.
4. The silent-no-op failure mode (exit 2, zero matches, no obvious error in a piped context) is the worst kind of gate failure: it certifies the invariant holds when it was never checked. Prefer gates that fail loud (`set -o pipefail`, explicit `test -n`, or assert non-empty output) over gates whose empty output is ambiguous.

**Shape trigger (when to suspect this family):** a `rg` command in a plan, skill, or CI config carries `-E` or `-oE`; OR a validation gate that "passed clean" is later found to have matched zero lines on input it was supposed to check; OR `rg -E '<pat>' <file>` exits 2 with `grep config error: unknown encoding: <pat>` when run directly.

**Distinguishing from #85 (validation command scanning shared parent dir false-fails on legacy):** #85 is about SCOPE (the gate scans too broadly and false-fails on pre-existing entries). This lesson is about the gate being a SILENT NO-OP (it checks nothing and certifies GREEN). #85's gate runs and over-matches; this lesson's gate does not run at all.

**Example:** A plan's instruction-cite integrity gate read `rg -oE '`development_lessons\.md` #([0-9]+)' AGENTS.md`. The author ported it from a `grep -oE` precedent, intending POSIX ERE with only-matching output. In ripgrep `-E` is `--encoding`, so `rg` treated the regex pattern as an encoding name, exited 2, and printed nothing; piped through `sed | sort | uniq` the downstream produced empty output, which the gate interpreted as "no cites to check, clean." The gate certified GREEN across two plan-review rounds while the actual AGENTS.md carried 36 real cites (any of which could have dangled). Fix: `rg -o '`development_lessons\.md` #[0-9]+' AGENTS.md` (drop `-E`; keep `-o`). The corrected command captures all 36 cites and the gate can actually detect a dangling reference.

**See also:** #85 (validation scope too broad, false-fail), #72 (discriminating tests must fail under wrong implementation, the gate-analog: a gate that cannot fail is not a gate), coding_guidelines.md #25 (Family H parent), ripgrep man page (`-E`/`--encoding`).


## 172. A Plan That Hardcodes a Count of Items in a Living Source Must Re-Verify That Count Against the Live Source at Execution Start

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family D (single source of truth). A plan written at time T may record a count of items in a source that keeps changing after T (a lessons corpus, a test directory, a manifest, a config set). The count is an abstraction over the live source; between authoring and execution the source drifts, so the plan's count, its derived totals, and the validation greps that encode the count all go stale. Two failure modes follow: (a) a gate asserting "N items" silently false-passes against N+k, and (b) downstream tasks built on the count (renumber maps, append positions, "new total = old − removed") compute the wrong result.

**Trigger:** A plan's Gist, Invariants, Validation Commands, or task rationale states a numeric count of items in a living source ("207 lessons", "76 entries", "~843 tokens", "122 CROSS"), and execution starts in a later session than authoring. Strongest signal: a validation command `grep -c '^## [0-9]' <corpus>` whose expected output is hardcoded in the plan.

**Rule:**
1. At execute-plan Step 1 (before Task 1), re-run every count assertion the plan encodes against the live source (`grep -c`, `wc -l`, `ls | wc -l`, or the plan's own validation grep). If the live count differs, record the delta in the Task 1 implement log BEFORE building anything on the count.
2. Recompute every derived total from the live count. If the plan says "new total = 207 − 36 = 171" and the live corpus is 208, the new total is 208 − 36 = 172; every downstream task referencing 171/172 must use the recomputed value.
3. When the drift is a single additive item, do NOT block: classify the new item into the plan's taxonomy (MOVE / STAY / STAY+GENERALIZE) in the implement log and continue. Drift is expected for any source that accepts contributions between authoring and execution.

**Shape trigger:** a plan's Validation Command hardcodes a count (`grep -c ... → 207`); OR the Gist states "N items" / "M tokens" about a corpus/dir/manifest not frozen between authoring and execution; OR a Task 1 implement log finds the live source has one more (or fewer) item than the plan assumed.

**Distinguishing from #154 and #75:** #154 verifies *code/runtime behavior* at *authoring* time; this lesson verifies a *numeric count* at *execution* time. #75 translates stale *path strings* a migration moved; this lesson recomputes stale *counts* a contribution drift moved. All Family H, different surface and lifecycle stage.

**Example (2026-07-27 playbook-lessons migration plan, Task 1):** The plan's Section 1 and validation greps assumed the playbook user-level corpus had 207 lessons and computed the post-migration size as 207 − 36 MOVE = 171. Execution found 208: lesson #171 (`rg -E` encoding semantics) had been added after authoring. Task 1's implement log recorded the delta, classified #171 as STAY, recomputed the post-migration size as 208 − 36 = 172, and flagged that the plan's `grep -c '^## [0-9]\+\.'` validation would return 208 (pre) and 172 (post), not 207/171. No blocker, just a count correction propagated to every downstream task referencing the total.

**See also:** #154 (verify behavior claims at authoring, Family H, authoring stage), #75 (translate stale paths at execution, Family H, path surface), #72 (a gate that cannot fail is not a gate), coding_guidelines.md #25 (Family H parent), `execute-plan` Step 1.

## 173. When Resuming a Multi-Pass Transformation, Verify the Working Tree Matches the Expected Pass Boundary Before Continuing; a Botched Prior Run Leaves a Tree That Is Neither HEAD Nor Any Clean Pass

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family D (single source of truth). A multi-pass task (delete, then renumber, then rewrite refs, then generalize) is authored so each pass builds on the prior pass's output. At resume the agent assumes the tree is HEAD or the clean result of pass N-1. A third invalid state is easy to fall into: the working tree of an INTERRUPTED prior run of the SAME plan that mixed steps from multiple passes (deletions from pass 1 alongside renumbering from pass 2) and matches NEITHER. A resume that trusts "the tree is at pass N-1" recomputes from the wrong baseline and compounds the corruption. The hazard: the natural resume checks (`git diff HEAD` non-empty, plus the per-pass validation such as contiguity) both PASS on the botched tree. The diff is non-empty, and if pass 2 already ran contiguity even reports "OK 1..N". Only a DIFF-SHAPE check catches it: a delete pass must show ONLY deletions vs HEAD; a renumber pass must touch ONLY headers.

**Trigger:** a plan task is split into sequential passes. Strongest signals: (a) the plan says "Pass N must start from a clean Pass N−1 result"; (b) an earlier pass's implement log recorded the tree was NOT at the expected baseline; (c) `git diff HEAD --stat` for a delete-only pass shows INSERTIONS, or for a header-only renumber shows non-header changes.

**Rule:**
1. Before each pass after pass 1, verify the tree matches the expected pass boundary, not merely that it differs from HEAD: (a) item count equals the count the prior pass should have produced; (b) diff SHAPE matches the prior pass's contract.
2. When the shape violates the contract (insertions on a delete pass; non-header changes on a header-only renumber), treat the tree as a botched prior run, NOT a clean boundary. Reset to the last known-good baseline (`git checkout HEAD -- <file>` for pass 1, or reconstruct the prior pass from HEAD in memory) and re-run cleanly. Record the reset and reason in the implement log so the next resume does not re-trust the same tree.
3. Do NOT trust `git diff HEAD` non-emptiness or a single per-pass validation as the boundary check. Both false-pass on a botched tree that mixed passes. The diff-shape check distinguishes "clean pass N-1" from "botched mix".

**Shape trigger:** a multi-pass task resumes mid-flight; `git diff --stat` matches NO single pass's contract; OR an earlier pass's implement log already recorded a "working tree was not at baseline" pre-flight finding for the same plan.

**Distinguishing from #172, #69, #124:** #172 re-verifies a numeric COUNT against a live source at execution start (stale-plan); this lesson verifies the DIFF SHAPE of the tree against a pass contract at resume (stale-tree). #69 forbids `git stash` for baseline comparisons; this lesson is about not trusting an in-flight tree at all. #124 draws the SCOPE boundary of one mechanical pass; this lesson is about resume-time state VALIDATION across passes.

**Example (2026-07-27 playbook-lessons migration plan, Task 3 Pass 1):** Pass 1 was scoped as pure deletion (36 MOVE blocks; no renumber, no inserts). At pass start the tree held a BOTCHED prior run: count was already 173 (post-deletion) but numbering was already renumbered to contiguous 1..173 (pass 2's work). `git diff HEAD --stat` showed `+641 / -1427`, i.e. insertions present, which a delete pass must NEVER produce. The non-empty-diff check and the contiguity check (which reported "OK 1..173" because pass 2 had run) would both have false-passed; the diff-shape violation was the signal. Reset via `git checkout HEAD -- <file>` and re-run from the 209-lesson HEAD baseline. Recorded in the Task 3 Pass 1 log under "Pre-flight finding".

**See also:** #172 (re-verify counts against the live source, stale-plan surface), #69 (do not stash for baseline comparisons, stash-hazard surface), #124 (scope boundary of a single mechanical pass, scope-conflation surface), #72 (a gate that cannot fail is not a gate), coding_guidelines.md #25 (Family H parent), `execute-plan` Step 1.

## 174. Renumbering a Doc Corpus Must Re-Verify Cross-Repo Cites Too, Not Only In-Repo Cites; the In-Repo Grep Cannot See a Cite That Lives in a Different Repo

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family D (single source of truth: a corpus's reference graph spans every repo that cites it, not just the repo that owns it). When a numeric doc corpus is renumbered, the re-verification step is typically scoped to "grep the whole repo for refs to the old numbers". That scope is correct for an intra-repo corpus but is a silent gap for a corpus that OTHER repos cite (a user-level cross-project corpus cited from project repos, a shared API doc cited from service repos, a lessons corpus cited from a sibling repo's instruction files). A cross-repo cite lives outside the renumbering repo's working tree, so the in-repo grep cannot reach it; the cite dangles until a separate cross-repo integrity pass re-verifies it.

**Trigger:** a task renumbers, compacts, or otherwise rewrites the numbered headings of a doc corpus (a lessons corpus, a decisions log, an ADR list, a numbered spec) AND that corpus is referenced by `#N` cites from at least one OTHER repo. Strongest signals: (a) the corpus is the user-level/cross-project lessons file (the canonical multi-repo-cited corpus); (b) the renumbering plan's validation gate greps only the owning repo's files; (c) a sibling repo's `AGENTS.md`/`CLAUDE.md` carries `UL #N` / `user-level #N` / `<corpus> #N` cites.

**Rule:**
1. Before renumbering a corpus, enumerate every repo that cites it by number. For a user-level corpus, that is every repo whose instruction files carry `UL #N` / `user-level #N` cites (grep each repo's `AGENTS.md`, `CLAUDE.md`, and project corpus). Record the cross-repo cite inventory in the renumbering task's manifest.
2. After renumbering, run the no-dangling check in TWO scopes: (a) the owning repo (the in-repo grep), AND (b) every citing repo's instruction files. The in-repo check alone is necessary but not sufficient when cross-repo cites exist.
3. For each cross-repo cite, apply the same per-ref audit as in-repo cites: does the cite's surrounding text still name the lesson at the NEW number, or does it name a lesson that moved? Repoint to the new number; if the cited lesson was removed, drop the cite or convert it to a title pointer.
4. Encode the cross-repo cite list as a validation gate in the plan, not as a memory item. A gate that greps the known cross-repo cite sites after renumbering is what makes the check repeatable; "remember to check the other repo" is not.

**Shape trigger (when to suspect this family):** a renumber/compact/migrate task on a shared corpus has a validation gate whose file scope is the owning repo only; OR a post-migration integrity check in a different repo finds a dangling `#N` that the owning repo's gate reported clean; OR a user-level corpus is renumbered and a project repo's `AGENTS.md` still cites the old numbers.

**Distinguishing from #83 and #124:** #83 handles a COLLISION (one number on two headings) and requires per-ref FIRST-vs-SECOND disambiguation; this lesson handles a NO-COLLISION compaction where the only failure mode is a cite left pointing at a number that no longer exists, and the gap is the cite living in a repo the renumbering grep did not scan. #124 scopes a faithful identity-remap (identity tracking suffices; semantic prose-debt is out of scope); this lesson is the case where the remap was faithful in-repo but never reached the cross-repo cite at all, so identity was not even tracked for it. All three are Family H renumbering facets; #83 is disambiguation, #124 is scope-of-fidelity, this lesson is scope-of-the-grep.

**Example (2026-07-27 playbook-lessons migration plan, Task 3 vs Task 5):** Task 3 compacted the playbook user-level corpus from 208 to 174 lessons and re-verified every in-repo `#N` cite (in `projects/.ai-playbook/development_lessons.md`, playbook `AGENTS.md`, playbook `docs/AGENTS.md`). That gate passed clean. But the tax-reporting repo's `AGENTS.md` line 85 carried `UL #113, #193`, a cross-repo cite into the playbook corpus. `#193` had been renumbered to `#86` by the Task 3 compaction; the in-repo gate could not see it because tax-reporting is a different working tree. The cite dangled across Tasks 3 and 4 until Task 5's explicit cross-repo integrity pass (`rg -o 'UL #[0-9]+' AGENTS.md` run in the tax-reporting repo, then each N checked against the playbook corpus headers) caught and repointed it to `UL #113, #86`. Fix landed in the tax-reporting repo (where the cite lives), two tasks after the renumbering that created the dangle. See the Task 5 implement log.

**See also:** #83 (renumber a colliding ID requires per-ref disambiguation, in-repo surface), #124 (faithful identity-remap scope, scope-of-fidelity surface), #171 (a `rg -oE` validation gate is a silent no-op, the gate-implementation hazard this cross-repo check must avoid), #172 (re-verify counts against the live source, stale-count surface), coding_guidelines.md #25 (Family H parent), coding_guidelines.md #17 (Family D parent).


## 175. A Corpus Renumbering Cite-Check Gate Must Enumerate Every Cite Syntax the Corpus Uses, Not Only the Most Common One

**Principle:** Family H (verify the real thing) cross with Family D (single source of truth: a corpus's cite graph is the union of every cite syntax readers actually write). A renumbering cite-check gate usually greps for the cite form the author sees most often (a backtick-quoted `` `file` #N `` in an instruction file). That single-form regex under-scopes silently: the same corpus is typically cited in several syntaxes inside its own prose (`` UL#N ``, bare `` #N `` tokens in See-also lines, `` [#N] `` links), and every one must be repointed. A gate that matches one syntax reports GREEN while the others dangle at old numbers.

**Trigger:** a renumbering, compaction, or migration plan for a numbered corpus (lessons, ADRs, decisions, numbered spec sections) ships a validation gate whose regex enumerates a single cite form. Strongest signals: (a) the gate pattern is anchored to a filename or surrounding punctuation and cannot match bare tokens inside the corpus; (b) the corpus's own prose uses a cite syntax (`` UL#N ``, `` See #N ``) different from the instruction-file form the gate scans; (c) a fresh adversarial review finds dangling intra-corpus cites the gate reported clean.

**Rule:**
1. Before trusting the gate, enumerate every cite syntax the corpus uses, in both instruction files and its own prose. Run a broad `` rg -o '#[0-9]+' `` first and inspect the distinct shapes; do not assume the most-visible form is the only form.
2. Write the gate as a union over every syntax found. Each syntax is a separate alternative; `` UL#N ``, bare `` #N ``, and `` `file` #N `` need distinct alternatives in one regex.
3. Resolve every matched cite to a current `` ## N. `` header. The gate is two pieces: extract every cite regardless of syntax, then check each target exists at the new number.
4. Encode the cite-syntax enumeration as a checklist in the plan, not as memory. A regex union that explicitly lists each syntax is a gate; "remember the other syntaxes" is not.

**Shape trigger (when to suspect this family):** a renumbering gate regex matches a single cite form; OR a post-migration check finds dangling `` UL#N `` / bare `` #N `` cites inside the corpus at old numbers; OR the corpus uses more than one cite syntax in its own prose but the gate scans only instruction files.

**Distinguishing from #174 and #171:** #174 is a SCOPE gap across repos (right syntax, wrong working tree); this lesson is a SYNTAX gap in one file (right file, one syntax of several). #171 is a TOOL-FLAG error (`` rg -E `` exits 2 and matches nothing); this lesson's gate runs and matches real output, just an incomplete subset of the cite vocabulary. All three are Family H facets of a renumbering gate that certifies GREEN without checking the whole cite surface: #171 is tool misuse, #174 is repo scope, this lesson is syntax scope.

**Example (2026-07-27 playbook-lessons migration, Task 3 vs review r1 F2):** Task 3 compacted the playbook corpus and the plan's cite-check gate matched only the instruction-file form `` `development_lessons.md` #N ``. It passed clean. But the corpus's own prose carried 7 STAY-to-STAY cites in three lessons using the `` UL#N `` syntax in See-also and corollary lines, all pointing at pre-compaction numbers that no longer existed. None appeared in the gate's regex, so it certified GREEN on cites it never read. Review r1 caught them via `` rg -n 'UL#[0-9]+' development_lessons.md `` resolved against `` ## N. `` headers, then repointed each to its new number. Fix: broaden the gate to a union over every syntax the corpus uses and resolve each match to a current header.

**See also:** #174 (cross-repo cite re-verification, repo-scope facet), #171 (`` rg -oE `` silent no-op, tool-flag facet), #166 (enumeration gates cannot catch novel items), coding_guidelines.md #25 (Family H parent), coding_guidelines.md #17 (Family D parent).

## 176. Posted Review Comments Exclude Process Metacomments

**Principle:** Family F (Layering / dependency direction: author-facing surface vs reviewer-internal scratch) cross with Family D (single source of truth for what the PR author must act on).

**Trigger:** while triaging a staged code review, the reviewer (or agent) expands a narrow user ask into adjacent soft asks, or puts process chatter into the posted Comment (follow-up ticket IDs, other finding IDs, "when ticket X lands", joint-config ownership asides).

**Rule:**
1. Keep `#### Comment` about the code, contract, or behavior under review. Put reviewer-process notes (other F-ids, follow-up tickets, triage history, ownership asides) only in `#### Analysis` or Metadata.
2. When the user narrows a staged ask (for example "only comment on PII"), edit that Comment to that scope only. Do not bundle extra Javadoc, naming, or soft asks unless the user also asked for them.
3. Before posting, re-read each Comment as if you were the PR author with no staging doc: if a sentence only helps the reviewer track process, move it to Analysis.

**Shape trigger (when to suspect this family):** a triage edit grows a Comment beyond the user's ask; OR a posted inline comment names another finding ID or an out-of-PR follow-up ticket; OR the author would need the staging Analysis to understand why a sentence is there.

**Distinguishing from #168:** #168 is cross-round soften watchlist persistence. This lesson is the Comment vs Analysis surface split and narrow-triage discipline inside one review.

**See also:** `doing-code-review` 4.12, `review-staging` Comment vs Analysis split, coding_guidelines.md #17 (Family D), coding_guidelines.md #18 (Family F).

## 177. KEEP-AND-REWRITE vs MOVE a Lesson by the Rule's Portability, Not the Example's Token Count

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family A (equivalence-class coverage). When a portability review surfaces domain framing in a lesson, the fix has two branches: KEEP-AND-REWRITE (the Rule is portable engineering; only the Example carries domain tokens; rewrite the Example to a non-domain analog) or MOVE (the Rule itself only makes sense inside the source domain; relocate the whole lesson to the domain corpus). The discriminator is the **Rule's** portability, verified by reading the Rule paragraph, NOT the **Example's** token density. A lesson can be saturated with domain identifiers in its Example yet have a fully portable Rule; that lesson stays and gets its Example rewritten. Conversely a lesson with a sparse Example can have a Rule that is irreducibly domain-specific; that lesson moves.

**Trigger:** A lessons-corpus portability review (or a leak fix pass following #166) has flagged N lessons as carrying domain framing. The reviewer must now decide, per lesson, whether to rewrite-in-place or relocate. Strongest signal: a pre-triage step grouped lessons as "likely MOVE" based on how many domain tokens they contain, before reading any Rule.

**Rule:**
1. Decide per lesson by reading the **Rule** in isolation (Example covered): "If I delete every source-domain reference from this Rule, does it still prescribe a meaningful engineering behavior in an unrelated project?" Yes -> KEEP-AND-REWRITE. If the Rule collapses to a tautology ("verify against source") or only makes sense inside the source domain -> MOVE.
2. Do NOT use the Example's token count or a "looks heavy" heuristic as the discriminator. Token density is a property of the Example; the decision is a property of the Rule. A heavy Example over a portable Rule is the common case and is exactly what KEEP-AND-REWRITE fixes.
3. KEEP-AND-REWRITE rewrites only the Example/Anti-pattern/Repo-context paragraphs (the Rule and Principle are already portable), swapping domain identifiers for non-domain analogs that preserve the mechanism. Preserve cross-corpus See-also pointers unchanged (navigation, not leaks).
4. MOVE only after confirming the portable remainder is not already covered by a sibling in the target corpus (dropping a duplicate Rule is correct; losing a unique Rule is a regression). Removal + renumbering is a separate coordinated pass.
5. Pre-triage by token density is allowed only as a read-order hint, never as the decision. Record each per-lesson decision with a one-line Rule-portability reason so the next round audits the discriminator.

**Why this happens:** Token density is cheap to measure (a grep count) and feels objective; reading the Rule is judgment. A reviewer under time pressure triages by "how many domain words" and proposes MOVE for the heavy ones. This over-MOVEs lessons with portable Rules and under-MOVEs lessons whose sparse Examples hide an irreducibly domain-specific Rule.

**Shape trigger (when to suspect this family):** A portability-fix pass groups lessons into MOVE vs KEEP before any Rule is read; OR the address log's per-lesson reason is "many domain identifiers" rather than a Rule-portability sentence; OR a later round finds a MOVE candidate whose Rule is plainly portable engineering.

**Distinguishing from #166:** #166 is the *detection* layer (a closed token-set scan cannot find a domain leak; use a judgment review). This is the *fix-decision* layer that runs once a leak is found: the branch between rewrite-in-place and relocate is governed by the Rule's portability, a different property than the leak surface.

**Example (2026-07-27 playbook-lessons migration, r3 F1 address):** Round r3 flagged ~57 lessons with domain framing; a pre-triage guessed ~12 "likely MOVE" by identifier load. On reading each Rule, only ONE was a true MOVE (its Rule was entirely source-domain mechanics, reducing to a generic "verify against source" already covered by a sibling). The other ~56 had portable Rules (output-label hygiene, test-discriminator discipline, archived-source authority, classifier-reachability checks) with domain framing only in Examples. Those were KEEP-AND-REWRITE: each Example/Anti-pattern paragraph was rewritten to a non-domain analog (function/test names, sheet/column names, region/category mechanics swapped for generic equivalents), Rule and Principle intact. Without the Rule-portability discriminator, the token-density heuristic would have wrongly relocated ~55 portable engineering lessons out of the cross-project corpus. See the r3 address log Phases A and C.

**See also:** #166 (the detection layer this fixes decisions for), coding_guidelines.md #25 (Family H parent), coding_guidelines.md #18 (Family A: the Rule's portability is the equivalence-class property, the Example's tokens are an incidental member), `learn` SKILL Step 1.2 item 4 (the three-way fork: abstract precept vs cross-project lesson vs project-specific; the MOVE vs KEEP-AND-REWRITE decision is the concrete application of fork 2 vs fork 3 to a lesson already in the corpus).

## 178. A Loaded Skill's Hard Gates Are the Skill, Not the Format Section

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family D (single source of truth). When a skill is loaded, its procedural hard gates (Phase gates, branch setup, announce-before, "do not X until Y") ARE the workflow contract; the format/template sections are reference material. Loading a skill and following only its format guidance while silently skipping its explicit hard gates is the same defect as not loading the skill at all. The failure mode is treating the skill as a style reference rather than a gated procedure.

**Trigger:** A skill was attached or loaded for a task (its content is in context), and the agent edited an artifact the skill governs (a plan, a review, a commit) without running the skill's Phase 0/announce/hard-gate steps, rationalizing that the change is "just a doc edit" or "only a format tweak."

**Rule:**
1. When a skill is loaded for a task, before editing any artifact the skill governs, run its procedural gates in order: announce steps, Phase 0 branch/setup gates, and any line labeled "Hard gate" or "Do not ... until ...". A gate that says "propose and confirm before writing" means propose and confirm; "routine update skip" exceptions apply only to the narrow case the skill names, not to any edit the agent judges minor.
2. Distinguish format guidance (section templates, wording conventions, examples) from procedural gates (numbered phases, hard gates, announce directives). Format guidance is optional context; procedural gates are mandatory and run in sequence.
3. The "this is just a small edit" rationalization is the failure signal itself: hard gates exist precisely because agents under-rate the changes they gate. A substantial multi-finding plan revision on the default branch is exactly what the branch-setup gate is for.
4. If uncertain whether a step is a hard gate, treat it as one. The cost of an unnecessary confirmation prompt is one turn; the cost of skipping a gate is a polluted trunk or a broken workflow invariant.

**Why this happens:** Skills are large; the format section is visually prominent and immediately useful, while the Phase 0/announce gates sit earlier or are phrased as background. The agent pattern-matches "I have the format, I can do the task" and never returns to the gates. The rationalization "it's just a doc edit" feels reasonable because the artifact is prose, not code, but the gate exists for branch hygiene and workflow continuity, which apply to doc edits too.

**Shape trigger (when to suspect this family):** The agent loaded a skill and produced a correct-format artifact, but never proposed a branch, never announced the skill, or skipped a numbered Phase; OR the user asks "did you use the skill?" and the honest answer is "I loaded it and followed its format, not its gates."

**Distinguishing from #147:** #147 is the inverse case from the execute-plan side: do not re-ask when already on the correct branch. This lesson is the initial-gate case: when starting work the skill gates, propose and confirm the branch (or get explicit decline) before the first artifact write, even for an edit to an existing not-ready artifact on the default branch.

**Example (2026-07-29 plan revision):** A not-ready plan (10 blocking findings) was revised heavily (cohort redesign, triage-gate asymmetry, dead-subsystem removal, 19 findings folded in) over several review rounds. The plans skill was loaded, but the agent edited the plan file directly on `main` without proposing a feature branch, skipping Phase 0's hard gate ("Do not write the plan file until branch setup is complete or explicitly declined"). The user caught it post-hoc ("did you use the plans skill? why didn't you switch the branch?"). Fix: created the feature branch, carried the working-tree changes over, then committed. Root cause was not ignorance of the gate but rationalizing "plan doc edit" as below the gate's threshold.

**See also:** #147 (auto-continue on the correct branch; the inverse initial-gate case), coding_guidelines.md #25 (Family H parent), `plans` skill Phase 0 Hard gate, `done` skill workflow continuity, `grilling`/`grill-with-docs` announce directives.

## 179. After Editing a Skill, Re-read It for Internal Contradiction Introduced by the Edit

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family D (single source of truth). A skill edit that changes a default cadence, term, or rule can leave a stale clause elsewhere in the same file that contradicts the new text. The edited section is correct in isolation; the file as a whole now contradicts itself. The review that catches this must re-read the whole skill, not just the edited section, because the contradiction lives in the unchanged prose surrounding the edit.

**Trigger:** A skill file was edited to change a default, rename a mode, or reorder a workflow, and the edit touched only part of a concept that is restated elsewhere in the file (lead sentence, integration notes, examples).

**Rule:**
1. After any edit that changes a skill's default behavior, mode names, or cadence, re-read the ENTIRE skill file (not only the changed section) for restatements of the old behavior: lead paragraphs, intro sentences, integration-point notes, examples, and trigger phrases.
2. Search the file for the renamed/old term and the new term; every restatement must match the new default. A lead sentence written for the prior default is the most common regression because it reads as authoritative framing.
3. If the edit introduces a hybrid (e.g., unclear-first sequential plus clear-tail batched), confirm the file describes THAT hybrid as the single default, not two equal switches that the reader must choose between.
4. Treat a user's "the edit made the skill less clear" as a signal to re-read for contradiction, not to revert. The fix is usually to align the stale clause to the new behavior, not to undo the improvement.

**Why this happens:** Edits are localized; the author re-reads the diff, not the file. A lead sentence or integration note that summarized the OLD default survives unchanged because it was outside the diff hunk. Readers hitting the file cold read top-down and meet the stale framing before the corrected section, so the file feels contradictory even though each section is internally correct.

**Shape trigger (when to suspect this family):** A skill was recently edited to flip a default or rename a mode, and a reader reports confusion about which behavior is default; OR the file has both an old framing sentence and a new default section describing the same concept differently.

**Distinguishing from #121:** #121 is an output-consistency self-check that cannot detect its own input mis-classification (engine level). This is an authoring-discipline lesson: after editing a doc/skill, re-read the whole artifact for restatements of the pre-edit behavior. Same Family H root, different layer (human authoring review, not engine self-check).

**Example (2026-07-29 grilling skill edit):** The grilling skill was edited to make batch mode the default. The default-cadence section was rewritten, but the opening sentence still said "resolving dependencies between decisions one-by-one," which described the OLD one-at-a-time default and now contradicted the new batch default. The edit was correct in its section; the file as a whole pulled in two directions. The user flagged it ("maybe the last fix made the skill less clear"). Fix: rewrote the lead and the cadence into a single described hybrid (unclear-first sequential, clear-tail batched) so no restatement survived. The fix was to align the stale clause, not revert the improvement.

**See also:** #121 (self-check blind spot, engine layer), #178 (treat a loaded skill's gates as the contract; same Family H root applied to gates vs format), coding_guidelines.md #25 (Family H parent), `how-to-write-skills` skill.

## 180. A Privacy Leak-Scan Deny-Set Built From Real Input Must Exclude Tokens That Are Also the Public Output's Own Vocabulary, or the Scan False-Matches Non-Private Substrings

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family A (equivalence-class coverage). A privacy deny-set (the fixed-string needles a leak scan searches the public output for) is only meaningful if each needle denotes a PRIVATE identifier. When a needle is ALSO a substring of the public output's own vocabulary (a taxonomy token, a cohort label, a generic branch/filename word like `main`, `master`, `branch`, a size bucket, a role, a verdict), the scan matches that non-private occurrence and reports a leak that is not one. The deny-set is too BROAD at exactly the tokens that look most specific (a real review of the `main` branch yields `artifact_slug: "main"`, and `main` is a substring of `domain_risk_class` on every line).

**Trigger:** You build a privacy deny-set by harvesting identifiers from real input (repo names, review filename slugs, ticket-like tokens, feature names, content digests) and scan the public output (`rg -nF -f deny-set output.json output.md`). The scan reports matches, or a selftest's substring check fails, on tokens that are NOT private but are shared between the input namespace and the output's own controlled vocabulary.

**Rule:**
1. A deny-set needle is load-bearing only if the token is PRIVATE (identifies a real entity the output must never name). Before adding any harvested identifier to the set, ask: does this token ALSO appear as the output's own controlled vocabulary (a classification value, a cohort key, a generic filename/branch word)? If yes, the bare token is a false-match source.
2. Keep FULL specific identifiers (a complete review filename slug, a full repo path, a 64-hex digest, a full ticket id) as UNCONDITIONAL needles: a long specific string never collides with the output's short vocabulary tokens. The collision is only on SHORT shared words, so split the set: full identifiers unconditional; short path/branch components and bare tokens filtered.
3. Build a public-taxonomy exclusion set from the OUTPUT's own vocabulary (every classification enum value, cohort key, role, size bucket, verdict, domain class) PLUS generic filename/branch words (`main`, `master`, `branch`, `r1`, four-digit years). Filter every harvested short component and bare token through it. Anything in the exclusion set is dropped from the deny-set (it cannot be a private leak because the output emits it as its own taxonomy).
4. Verify the leak scan with `rg -nF -f deny-set output.*` (fixed-string, no regex): a zero-match result against a deny-set that still contains every full specific identifier is the real privacy proof. A non-zero result on a short shared word is a false match, not a leak; tighten the exclusion set, do not weaken the scan.

**Why this happens:** Harvesting is recall-oriented (capture every identifier that might leak), so short shared words are swept in alongside the specific slugs. The shared-word collision is invisible until the scan runs against real output, because the output's vocabulary is not visible at harvest time. The `main`-branch case is the canonical trap: the input records `artifact_slug: "main"` (a real, specific input value) and the output uses `main` inside a `domain_risk_class` token (unrelated public vocabulary); both are the same four letters, so a fixed-string scan of `main` matches the public occurrence.

**Shape trigger (when to suspect this family):** A privacy/PII leak scan built from real-input identifiers reports matches, OR a deny-inventory selftest's substring assertion fails, on short generic words (`main`, `branch`, `reviews`, a role, a size bucket) rather than on specific slugs/digests/ticket ids. The matched token is one the public output legitimately emits as its own taxonomy.

**Distinguishing from #121 (transformation-engine denylist gap):** #121 is a denylist that is too NARROW (an exclusion set misses a real non-target form, so a transformation engine mis-classifies and silently corrupts). This lesson is a denylist that is too BROAD (a deny-set includes the output's own vocabulary, so a leak scan false-matches non-private text). Same Family H root, opposite failure direction: #121 = exclusion set under-covers (engine acts wrongly); #180 = deny-set over-covers (scan reports phantom leaks).

**Distinguishing from #84 (substring-offset replacement corruption):** #84 is a bulk text REPLACEMENT whose search string lands at the wrong offset inside a larger token. This is a SEARCH-only scan whose needle is a legitimate standalone token that coincidentally also appears as a substring of public vocabulary. #84 corrupts output and needs a byte-diff to catch; #180 reports a phantom leak and needs a vocabulary-exclusion filter to silence.

**Example (2026-07-29 review-effectiveness-telemetry validation, Task 4):** The summarizer's `--emit-deny-inventory` builds a deny-set from the real review corpus (discovered repo names, full review filename slugs, ticket-like tokens, feature names, SHA-256 content digests). The first harvest included the bare token `main` because a sidecar's `artifact_slug` was the `main` branch and `main` appeared as a path component. The `rg -nF -f deny-inventory.txt report.json report.md` scan matched `main` inside `domain_risk_class` on every report line, reporting phantom leaks. Fix: added a public-taxonomy exclusion set (review types, roles, size buckets, domain classes, verdicts, plus generic filename/branch words `branch`/`main`/`master`/`r1`/`2026`); harvested short components and bare tokens are filtered through it; full specific slugs/filenames/digests remain unconditional needles. After the filter, the scan returned zero matches against a deny-set of ~994 specific identifiers. See the Task 4 implement log "TDD RED" iteration 2 and the "Design refinement" deviation.

**See also:** coding_guidelines.md #25 (Family H parent), #121 (transformation-engine denylist too narrow; the inverse direction), #84 (substring-offset replacement corruption; a different substring-collision failure), #86 (re-scope assertions when synthetic identifiers flip orthogonal signals), CLAUDE.md §4 Agent Workflow Rules.

## 181. Pre-Existing Occurrences of a Pattern Are Not Proof It Is Sanctioned Style; Verify Against the Canonical Policy Source Before Restoring or Spreading That Pattern

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family D (single source of truth). The "real thing" is the canonical policy source; the "abstraction" is an inference drawn from how often a pattern already appears in sibling files. Pre-existing occurrences may be unchallenged debt that predates the policy, not evidence the policy permits the pattern. Propagating or restoring the pattern on that inference re-spreads a violation and produces a fix that itself fails the policy gate.

**Trigger:** A review worker (or author) proposes to keep, restore, or spread a pattern (punctuation style, naming, import convention, framework idiom) because "it is the established house style here" and cites occurrences in sibling files as the only evidence, with no quote of the canonical policy.

**Rule:**
1. Before proposing to keep, restore, or spread an existing pattern as "sanctioned style," locate and quote the canonical policy source that permits it (an instruction section, a numbered guideline, or an owning skill). Sibling-file occurrences alone are not evidence; they may be un-challenged debt.
2. If a canonical policy source contradicts the pattern, the policy wins even when most sibling files already contain the pattern. Treat the siblings as pre-existing debt (note at Low or omit per NEW-vs-EXISTING), not as a style precedent.
3. The reverse also holds: do not invent a violation where the policy is silent. If no canonical source speaks to the pattern, ask the user rather than asserting a ban or a sanction from occurrence counts.
4. When a fix for a pattern is needed, apply the procedure the canonical source prescribes (for em-dashes, `agent_workflow_guidelines.md` §39.1 lists colon, comma, semicolon, period, or rewrite), not a substitute that "looks compliant" (e.g., restoring the em-dash, or swapping a hyphen).

**Why this happens:** "Everyone does it here" feels authoritative. A reviewer greps sibling files, sees many matches, and concludes the pattern is sanctioned. The matches are usually debt that predates a later-added policy, but the reviewer never reads the policy section because the occurrence count felt like sufficient evidence. The resulting "fix" (restore the pattern) is the original violation reapplied.

**Shape trigger (when to suspect this family):** A review finding's only justification for keeping/restoring a pattern is "this is the established style in these other files," and no canonical policy section is quoted; OR a proposed fix would restore the exact pattern a policy gate (e.g., `done` Step 2.76 / `check-no-em-dash.sh`) was set up to reject.

**Distinguishing from #87 (committed-files false-green):** #87 is mechanical: `check-no-em-dash.sh touched` skips already-committed files, so a clean tree false-passes. This is judgmental: a reviewer infers sanctioned style from occurrence counts and proposes to restore a pattern the policy bans, even when the files ARE scanned. Same Family H root, different layer (#87 = tool scope; #181 = evidence standard for style claims).

**Example (2026-07-31 ai-playbook review-loop, round 1 finding F2):** A branch had replaced three em-dashes with ` , ` (comma splices). Two review workers flagged the splices but argued the fix was to RESTORE the em-dashes because `security.md` and `concurrency.md` in the same repo "use em-dashes as established house style." That inference was wrong: `agent_workflow_guidelines.md` §39.1 bans U+2014 repo-wide and `done` Step 2.76 enforces it pre-commit. The sibling em-dashes were unchallenged debt, not sanctioned style. Restoring em-dashes would have failed the `done` gate. The correct fix was the §39.1-prescribed punctuation (semicolon, colon, comma-and). Caught during the same loop's `done` step before commit, not by the reviewers.

**See also:** coding_guidelines.md #25 (Family H parent), #87 (committed-files false-green; the mechanical inverse), `agent_workflow_guidelines.md` §39 (em-dash policy) and §56 (two-part instruction anti-pattern), `doing-code-review/SKILL.md` (style-preference findings must cite a canonical doc, not personal docs), CLAUDE.md §4 Agent Workflow Rules.

## 182. A Mechanical Gate Must Cover Every Producer of a Schema-Governed Artifact, and the Schema Must Be Inlined Where It Is Consumed

**Principle:** Family A (mechanical invariants over prompt advice) cross with Family D (single source of truth). When several producer skills each emit an artifact governed by one schema, a validator gate that lives in *some* producers but not all is coverage theater: the ungated producer silently emits schema-drift artifacts that the gated producers never would. Symmetrically, a schema that lives in one gold-source file and is only *referenced by name* from its consumers is unreachable to a sub-agent at write time; the producer improvises a plausible shape and nothing checks it. The durable fix is mechanical (gate every producer; inline the schema where it is consumed), not a prompt wording change.

**Trigger:** A family of producer skills share a contract (a staging doc + machine-readable sidecar, a manifest + index, a config + schema), one gold-source skill documents the schema, and a subset of producers run a `--hard` validator before reporting complete while one or more producers do not. The defect surfaces when artifacts from the ungated producer fail the validator that the gated producers pass, or when a schema field is systematically malformed across one producer's output but correct across its siblings.

**Rule:**
1. Audit producer coverage, not just the gate: for every schema-governed artifact, list every skill that writes it and confirm each one runs the validator gate (`--hard`, before reporting complete). A gate present in N-1 of N producers is a defect in the Nth, not an acceptable gap. Grep for the artifact extension (e.g. `.stats.json`) across the skill suite and require a gate at every match.
2. A schema that producers must conform to belongs *inlined in the producer's own output step*, not only in a referenced gold-source file. "Follow `<sibling-skill>` for the schema" is a load instruction the sub-agent can skip under loop pressure; the field contract (types, required fields, enum values) must be in the producer's context at the point it writes the artifact.
3. When a defect class is found in one producer, fix the *class*: add the gate to every ungated sibling in the same pass, and update bidirectional Integration Points (provider notes the consumer obligation; consumer notes the gate). Fixing only the incident producer leaves the same defect latent in the siblings.
4. Distinguish "the gate fired and was overridden" (#165), "the skill was loaded but its gates skipped" (#178), "the producer never had a gate" (this lesson), and "the gate exists and runs but enforces a *stale* spec" (the gate-side drift in item 5). The first two are execution failures against an existing mechanism; the third is a missing mechanism; the fourth is a stale mechanism.
5. When the gold-source spec the gate enforces is itself edited (a column renamed, an enum value added, a format token changed), re-sync the *gate's* hardcoded tokens in the same pass, not only the producers and artifacts. A gate that hardcodes `| Agent |` while the gold source now mandates `| Worker |` flags compliant artifacts as invalid, the inverse failure of #184 (artifact wrong, gate right). Treat the gate's regex/literal set as a third consumer of the gold source (alongside producers and sibling consumers) and grep the stale token inside the gate whenever the gold source's example tables change.

**Why this happens:** The gate is added producer-by-producer as each skill is written or hardened, so coverage is uneven by default. The gold-source skill reads as authoritative ("the schema is documented there"), so no one notices that a referenced file is not the same as an inlined file in the consumer's context. Under loop pressure a sub-agent treats "follow `<sibling>`" as satisfied by producing *a* sidecar of the right shape from the markdown it can see, rather than loading the sibling to read the exact field contract.

**Shape trigger (when to suspect this family):** Artifacts from one producer systematically fail a validator that its siblings pass, AND the failing producer's skill file references the schema by name but neither inlines it nor runs the validator; OR a schema-drift field (string vs integer id, missing required fields) is consistent across one producer's history but absent from its siblings' output; OR a *compliant* artifact is flagged by the gate, meaning the gate itself (not the artifact, not a missing producer gate) hardcoded a token/shape from the gold source and was never re-synced when the source evolved.

**Distinguishing from #165 and #178:** #165 is a gate that fired and a parent overrode the compliant result; #178 is a skill loaded whose procedural gates the agent skipped as "just a doc edit." This lesson is the structural case: the producer had no gate to skip and no schema in context to follow. Fix #165/#178 by enforcing existing gates; fix this by *adding* the gate and inlining the schema.

**Example (2026-07-31 playbook review skills):** A plan-review loop produced sidecars with string `"F1"` finding ids, sparse finding dicts (missing consequence/reachability/blast_radius/confidence), and no `panel_mode`/`source_digest`/`descendant_launches`, while sibling rounds from the same loop passed the validator. Root cause: the plan-review producer skill was the only staging producer without a `validate_review_staging.py --hard` gate (the branch-review, code-review, loop, and commit-time skills all gated), and it only *referenced* the sidecar JSON schema by name ("Follow `review-staging`") without inlining the field contract the validator enforces (integer `id`, full consequence fields, `panel_mode`, `source_digest`, `descendant_launches`). The sub-agent improvised a plausible sidecar from the markdown it could see; nothing checked it. Fix: inline the schema into the producer's synthesis step and add the `--hard` gate before reporting the round complete, then extend the same gate to the three other ungated producers (triage-update, confluence-review, rfc-review) in one pass. The gate already existed in four producers; adding it to the rest closed the defect class.

**Witness (gate-side drift, 2026-08-01 playbook review-skills plan, Task 4):** the inverse direction, where the *gate* itself lagged the gold source. After `review-staging/SKILL.md` renamed its Discarded-findings example-table header `| Agent |` to `| Worker | Worker severity | … |`, the validator's `validate_discarded_findings` header-skip regex (line 380) still matched only `^\|\s*Agent\s*\|`. A correctly-formatted `| Worker |` header was parsed as a data row, its `Reason` cell read as the discard code, and the gate emitted a spurious `unknown discard reason code: Reason` warning on the very shape the gold source mandates (the gate flags a compliant artifact as invalid). The canonical fixture `_current_clear_markdown` uses `None.` for the Discarded section, so the header-skip path was never exercised and the bug survived. Fix: `^\|\s*(?:Agent|Worker)\s*\|`, gated by a new RED→GREEN self-test whose discriminating assertion (no `unknown discard reason code: Reason`) fails pre-fix and passes post-fix, while a negative-twin BAD row (`not-a-real-reason`) keeps warning both phases to prove the fix does not over-skip genuine data rows. This is the third leg of the rename incident: producers lagged (#182), sibling consumers lagged (#181 witness at line 2226), and the enforcement gate lagged. See `scripts/validate_review_staging.py` and #184 (the artifact-side inverse: artifact wrong, gate right).

**See also:** coding_guidelines.md #17 (Family D parent), coding_guidelines.md #18 (Family A parent), #165 (gate overridden), #178 (gates skipped), #181 (the rename's consumer-side witness, line 2226), #184 (the artifact-side inverse: artifact wrong, gate right; this lesson's gate-side witness is the opposite), #144/#148 (the staging-contract content this enforces), `agents-best-practices/references/agent-legibility-feedback-loops.md` (the harness pattern: validators belong at every producer), `review-staging/SKILL.md`, `validate_review_staging.py`.

## 183. A pytest Factory Fixture (Returns a Callable the Test Invokes) Must NOT Have a Leading Underscore; Ruff PT019 Fires per Test Parameter That Requests It

**Principle:** Family A (mechanical invariants over prompt advice) cross with Family H (verify the real thing, not the abstraction). The leading-underscore convention for "private" fixtures collides with a mechanical lint rule (Ruff PT019) the moment the fixture is not autouse-and-yieldless but is instead a *factory* that the test requests by name and then calls. The lint rule is the signal; naming the fixture by what it returns (no underscore) is the fix.

**Trigger:** You write a `@pytest.fixture` that returns a callable (a closure like `run(...)`, a builder, or any function the test later invokes), and the test requests it as a parameter: `def test_x(self, example_run): ...; example_run(...)`. The fixture name starts with `_` because it "feels private" or because another rule (#89) recommends underscore names for a different fixture class (autouse, no-value).

**Rule:**
1. Ruff PT019 (`pytest-fixture-incorrect-parentheses-style` family, more precisely the "fixture name should not start with underscore when requested as a parameter" check) fires once PER test function that requests an underscore-prefixed fixture as a parameter. A factory fixture requested by 7 tests produces 7 PT019 findings, not one.
2. Drop the underscore from any fixture that tests request as a parameter and then call or read. The underscore prefix is only safe for (a) autouse fixtures that tests never request by name, or (b) fixtures that are injected purely for side effects (the #89 case). When the fixture returns a value the test uses, name it after what it returns (`example_run`, not `_example_run`).
3. If the fixture genuinely must stay underscore-prefixed for a sibling reason, the test must NOT request it as a named parameter; use `request.getfixturevalue("_name")` or make it autouse. Do not silence PT019 with `# noqa`; rename instead (a release gate that bans new `# noqa` will block the suppression anyway).
4. Distinguish from PLR0913 (too-many-arguments) and ARG005 (unused-lambda-argument), which often co-occur in the same factory-fixture cleanup: PLR0913 fires on the returned callable's parameter list (collapse bool flags into a single `flags: dict | None = None`), ARG005 on an unused closure arg (rename `year` to `_year`). PT019 is the only one of the three driven by the fixture's NAME.

**Why this happens:** Authors transfer the "private helper" underscore habit onto fixtures, or copy the #89 underscore guidance out of its autouse scope. The factory fixture does read like a private helper (it builds a closure), so `_example_run` looks correct until the linter runs. The per-parameter multiplier (7 findings from one bad name) makes the mistake expensive to leave until the release gate.

**Shape trigger (when to suspect this family):** A Ruff/PT019 finding names a fixture parameter that starts with `_`, AND the fixture returns a callable or non-None value the test uses; OR a release gate ("ruff clean, no new `# noqa`") fails with many PT019 hits traced to one fixture.

**General form:** A lint rule keyed on a NAME pattern (leading underscore) does not care about the author's intent ("private"); it cares about USAGE (requested as a parameter). Name a pytest fixture by its usage, not by a privacy convention, whenever the test requests it by name.

**Example (2026-07-31 on-chain-fetcher plan, Task 6 wiring test cleanup):** `tests/unit/application/test_main_on_chain_wiring.py` defined `@pytest.fixture _example_run(tmp_path, monkeypatch)` returning a `run(*, fetcher, env_value, config, wallets, ...)` closure that 7 tests requested as a parameter and then called as `example_run(...)`. PT019 fired 7 times (once per requesting test). Fix: rename `_example_run` to `example_run`. The same cleanup also collapsed the closure's `patch_fetcher`/`resolve_koinly_none` bool params into `flags: dict[str, bool] | None = None` (PLR0913, was 6 > 5 params) and renamed an unused lambda arg `year` to `_year` (ARG005). See the Task 6 implement log and the orchestrator post-pass.

**See also:** #89 (the inverse PT019 case: autouse fixtures SHOULD use a leading underscore and yield no value), `~/Projects/.ai-playbook/python_guidelines.md` (pytest fixture naming), CLAUDE.md §4 Agent Workflow Rules.

## 184. A Review Staging Markdown Doc Must Match the Validator's Parsed Hierarchy

**Principle:** Family H (Verify the real thing, not the abstraction) cross with Family D (single source of truth: the validator is the spec, not the agent's mental model of "plausible Markdown").

**Trigger:** authoring a review-staging Markdown doc (`.md` next to a `.stats.json` sidecar) for the first time in a session, or after a long gap, and trusting that well-formed prose with severity/bullets per finding is enough.

**Rule:**
1. The validator parses findings by **structural cues**, not by reading your prose. The Markdown must carry, in order: `### Critical` / `### High` / `### Medium` / `### Low` group headings (even when a group is "None."), then `#### F<N>. <title>` blocks (the period is load-bearing; `#### F1` without it is not recognized).
2. Each finding block needs literal `#### Comment` and `#### Analysis` sub-headings (both, or neither with the legacy Status/Triage form). A bolded paragraph labeled `**Evidence:**` is NOT `#### Analysis`; a description paragraph is NOT `#### Comment`.
3. Every `- **Triage**:` value must be one of the enum the validator accepts (`pending`/`deferred`/`done`/`dropped`/`fixed`). A custom value like `fix`, `moot-if-F5`, or `pending-cut` fails conservation (Markdown vs sidecar disagree).
4. Sidecar `findings[]` array order must be **severity-bucketed then ascending ID** (Critical, then High, then Medium..., with IDs ascending within each bucket), matching the Markdown document order. Numeric order `[1,2,3,...]` across mixed severities fails.
5. Sidecar enum fields (`reachability`, `blast_radius`) take only the documented values, not descriptive strings (`"single-skill"`, `"test-suite"`, `"uncommon"` are all invalid). When unsure of the accept-set, grep the validator (`VALID_SOURCE_KINDS`, `RESOLVED_TRIAGE_VALUES`, the reachability/blast_radius lists) before writing.
6. Treat the first `validate_review_staging.py --hard` run on a hand-authored staging doc as the authoritative format teacher: it will fail, and each error names the exact requirement. Fix forward rather than pre-guessing the format.

**Why this happens:** the staging doc looks like ordinary Markdown, so an agent authors it from a mental model of "a review report" (severity labels, bullet metadata, prose). But the validator is a structural parser keyed on heading-level regexes and enum sets; it does not read prose. Every format error it reports is a place where plausible prose diverged from the parsed contract. The sidecar JSON schema (covered by #182) is the sibling hazard; this is the Markdown half of the same artifact.

**Shape trigger (when to suspect this family):** a hand-authored review-staging `.md` fails `validate_review_staging.py --hard` with errors like "missing #### Comment/Analysis", "finding N triage disagrees", "findings are not ordered by severity then ascending finding ID", "invalid reachability/blast_radius", or "finding conservation: sidecar finding id N has no matching Markdown #### F block".

**Example (2026-08-01 playbook post-fold-digest-gate review, r1 staging doc):** the first validator run on a 12-finding staging doc produced five error classes in sequence: (1) `reachability: "uncommon"` and `blast_radius: "single-skill"/"test-suite"` were not in the accept-sets; (2) findings used `### F1` headers without severity group headings, so conservation saw "0 findings"; (3) `- **Triage**: fix` and `moot-if-F5` were not valid triage values; (4) after adding severity groups, the `findings[]` sidecar array was in numeric order `[1..12]` not severity-bucketed order; (5) Low findings written as single paragraphs lacked the `#### Comment`/`#### Analysis` sub-headings. Each was fixed forward by reading the error, not by pre-knowing the format. The doc passed only after all five were corrected.

**See also:** #182 (the producer-side gate coverage and sidecar JSON schema inlining; the JSON half of this artifact), #176 (Comment vs Analysis content split, not structure), `review-staging/SKILL.md` (gold-source hierarchy), coding_guidelines.md #25 (Family H parent), coding_guidelines.md #17 (Family D parent).

## 185. A Sub-Agent Killed Mid-Refactor Leaves Orphaned Indented Bodies - Verify the File Collects/Compiles Before Trusting the Sub-Agent's GREEN

**Principle:** Family H (verify the real thing, not the abstraction). A sub-agent's reported test pass is an abstraction over "the working tree is in a consistent state." When the sub-agent was killed mid-edit (usage-limit, quota, timeout, crash), the kill can interrupt a refactor between its delete-old and write-new steps, leaving a partial file the sub-agent never ran its own lint/collect pass on. The collection/compile step is the real thing; the sub-agent's last reported status is not.

**Trigger:** An orchestrator resumes after a sub-agent was killed mid-task (usage-limit, 429/quota reset, timeout, process crash), and the recovery plan is to trust the sub-agent's last reported GREEN or to do inline cleanup. Strongest signal: the sub-agent's final action was a multi-step refactor (extract a helper, rename a method, split one block into two) and it was killed before it could run its own `ruff` / `pytest --co` / `python -c "import <module>"`.

**Rule:**
1. After ANY sub-agent kill mid-edit, treat the working tree as suspect. Do NOT trust the sub-agent's last reported test/lint status as proof the files parse.
2. Run a parse/collect smoke check on EVERY file the sub-agent touched BEFORE trusting GREEN or proceeding to commit: `python -c "import ast,sys; [ast.parse(open(f).read(),f) for f in sys.argv[1:]]" <files>` (or `python -m py_compile`, or `pytest <files> --co -q`). For non-Python, use the language's parse/compile entrypoint.
3. The signature of the kill-mid-refactor corruption is an orphaned indented body: a block whose leading lines were part of the old structure (e.g. the tail of the function being extracted) was not deleted when the new structure was written, so the file now has an indented statement at module/class scope with no preceding `def`/`class`/control header. The concrete error is `IndentationError: unexpected indent` at import or collection time, NOT a logic error in the new code.
4. Compare the orphan against the canonical version: in every observed case the orphan duplicated the tail of a function that exists correctly elsewhere in the same file (the refactor's "write new" step succeeded; only the "delete old" step was interrupted). Fix is to delete the orphan block, not to merge it.
5. Re-run the full linter (not just the smoke check) on the touched files after the fix; the interrupted sub-agent also skipped its own `ruff check` / unused-import sweep, so F401/I001/D-class diagnostics are likely co-resident.

**Why this happens:** A refactor is a delete-then-write (or write-then-delete) sequence. The sub-agent's internal checklist runs lint/collect only at the END, after both halves land. A kill between the halves freezes a state where the new code exists and the old code was only partially removed; nothing in that intermediate state has been validated, and the sub-agent's last reported status predates the corruption.

**Shape trigger (when to suspect this family):** resuming after a sub-agent kill, the first parse/import of a touched file raises `IndentationError: unexpected indent` (or the language equivalent: `SyntaxError`, `IndentationError`, "expected an indented block", a stray `}` / unmatched brace); OR `pytest --co` aborts at collection before any test runs; OR a ruff pass that the sub-agent "would have run" surfaces F401/I001 on files the sub-agent reported clean.

**Example (an on-chain feature plan, an autodiscovery task):** the implement sub-agent completed the substantive work (RPC client, a three-layer classifier, a snapshot schema/validator, 10 tests) but was killed by a usage-limit mid-refactor while extracting two validator helpers out of a snapshot-builder function. The kill left an orphaned indented body at the bottom of the config module: the tail of the old builder that the extraction was supposed to remove. The sub-agent never ran its own ruff pass, so the orphan survived. On resume, `pytest` aborted at collection with `IndentationError: unexpected indent` in the config module. The canonical builder (a complete, correct function earlier in the file) already held the extracted tail; the orphan was a duplicate, deleted outright. A follow-up ruff pass on the touched files then surfaced three co-resident diagnostics the interrupted sub-agent had skipped (an unused import, an unsorted import block, a missing `__init__` docstring). All 2010 tests passed after the cleanup; the lesson is that the cleanup was forced by a collection-time smoke check, not discovered by trusting the sub-agent's pre-kill status.

**Distinguishing from the ruff-on-re-export lesson and #149 (pytest class naming):** both of those produce `ImportError` at collection from a config/tool action (ruff auto-fix deleted a re-export; `python_classes` deselected a class). This lesson produces `IndentationError` from a KILLED sub-agent's interrupted delete step. Same failure signature family (collection aborts before tests run), different root cause (interrupted refactor vs tool config). The shared fix is the parse/collect smoke check; the distinct fix here is "the orphan duplicates a canonical block, delete it, do not merge."

**See also:** the ruff-on-re-export lesson (`ImportError` at collection is the failure signal, but from ruff auto-fix not a kill), #149 (test class silently deselected by `python_classes`, a config cause), coding_guidelines.md #25 (Family H parent: verify the real thing, not the abstraction), `execute-plan` skill (inline recovery after sub-agent failure is allowed; this lesson is the verification step that makes that recovery safe).

## 186. Plan Validation Commands Must Discriminate; Multi-File OR and Peer-Name OR Are False Greens

**Principle:** Family H (Verify the real thing, not the abstraction). Cross with Family A (Equivalence-class coverage).

**Trigger:** Authoring or reviewing a plan whose `## Validation Commands` prove Task Done when via `grep` over skill or doc files, especially after a review fold that added new phrases.

**Rule:**
1. One `grep PATTERN file1 file2 file3` exits 0 if **any** file matches. Require the new phrase with a **per-file** grep (or `&&` chain) when each file owns a contract.
2. Do not OR a required **new** phrase with a **pre-existing** peer name (`inclusion|review-plan|execute-plan`). Pre-existing Integration Points headings green the gate with zero inclusion-gate work. Require inclusion language **and** the peer name as separate greps.
3. Closed pause enumerations need **per-anchor** greps (or one same-line pattern each). A single hit under Hard Gates does not prove Continuous execution and Step 1.5 were updated.
4. Prefer positives that fail on the pre-change tree for the new contract (`Checklist inclusion`, `delete-without-Ship-when`, `^## 62\.`). Soft ORs that already match today are not Task Done when.

**Why this happens:** Authors pack "prove coverage" into one alternation for brevity. Under continuous-execution pressure, implementers satisfy the greps with the cheapest pre-existing match.

**Shape trigger:** Plan review finds Validation Commands green on the current tree before the task edits land; OR Task 4 can pass while a named skill still lacks the new phrase.

**Example (2026-08-03 plan-executable-task-gates review loop):** r2–r4 blocked on multi-file `why executable now` OR, Integration Points ORing peer skill names with inclusion, and a single `inclusion-check failure` hit for three pause lists. Fold: per-file greps, IP AND splits, three pause anchors plus dedicated Inclusion Hard Gate (not the ask-only list).

**See also:** #87 (touched-mode false green), #182 (gate every producer), coding_guidelines.md #25 (Family H), `plans` / `review-plan` Validation Commands guidance, `docs/plans/2026-08-03-plan-executable-task-gates.md`, #187–#191 (Validation Commands false-green family from skill-gate marker plan).

## 187. Plan Validation Greps Must Target Each Obligation, Not Context Spillover

**Principle:** Family H (verify the real thing, not the abstraction) cross with Family A (equivalence-class coverage). A plan `## Validation Commands` check that greps one structural anchor with a large context window (`-A`/`-B`) and hopes a sibling obligation appears nearby verifies the wrong thing. It proves the anchor exists, not that each required obligation is present. Missing siblings still exit 0.

**Trigger:** Authoring or reviewing a plan whose Validation Commands use a wide context window around one heading or phrase to "also cover" nearby Hard Gates, anti-pattern rows, Recovery order, or Step subsections.

**Rule:**
1. Give each critical structural obligation its own dedicated search that fails when THAT obligation is absent (unique string, ordered pair, or section-anchored pattern).
2. Do not treat a large context window around a different match as proof a sibling obligation exists. Context spillover is documentation convenience, not a gate.
3. When a review finding asks to add Validation Commands coverage for an obligation already correct in skill prose, treat gate coverage as a distinct surface. Do not drop as "already fixed in the skill."
4. After editing Validation Commands, temporarily remove one target obligation and confirm the dedicated check fails.

**Why this happens:** Authors minimize command count. One greppable heading feels like it covers the whole section. Triage that drops Validation Command asks because the skill body is already right leaves the false-green gate in place.

**Shape trigger (when to suspect this family):** Validation Commands pass green while a fresh review finds a missing Step subsection, anti-pattern row, Recovery order, or Hard Gate the plan claimed to check; OR address-review drops a Validation Commands finding because `SKILL.md` already states the rule.

**Distinguishing from #171:** #171 is a wrong ripgrep flag that exits 2 and matches nothing. This is a correct grep that answers the wrong sufficiency claim (anchor present, sibling absent).

**Example (playbook execute-plan skill-gate marker plan, review r1):** The structural validation loop grepped nearby anchors with wide context and stayed green while Step 0.4b, Recovery marker-before-done order, and dedicated anti-pattern / Hard Gate checks were missing. Pass 1 dropped similar asks because skill text was already correct. Pass 2 staging required the Validation Commands; dedicated greps were added and the false-green closed.

**Witness (same plan, review r3):** Step 0.4b stayed inside a shared `-A45` structural loop. Stripping the local "immediately before that plan-file write" clause still matched the later shared `Plan-file edits` section inside that window. Pull Step 0.4b out of the wide loop; use a tight `-A12` plus the local phrase so shared cross-refs cannot false-green.

**See also:** #171 (wrong `rg -E` flag; different false-green mechanism), #179 (skill internal contradiction after partial edit), #190 (same-line character order; different false-green), `plans` Validation Commands authoring rules, `receiving-code-review` staging triage, coding_guidelines.md #18/#25 (Family A / Family H).


## 188. Pairwise Before-Last Checks Do Not Prove Full Order

**Principle:** Family A (equivalence-class coverage) cross with Family E (temporal / ordering invariants). A gate that only asserts each of N steps precedes the final step (`a < z` and `b < z`) leaves adjacent middle orders unchecked. A swapped middle pair still exits 0.

**Trigger:** Authoring or reviewing Validation Commands that extract line numbers for a required sequence and compare each step only against the last step.

**Rule:**
1. For an ordered sequence of N actions, assert the full chain (`a < b < c`), not only each element before the last.
2. After writing the check, simulate the swapped adjacent pair that should fail and confirm the check exits non-zero.
3. Name the intended order in the check comment so reviewers can see which pairs are load-bearing.

**Why this happens:** Authors treat "everything before the final action" as enough. That is not a total order; middle swaps remain green.

**Shape trigger (when to suspect this family):** Ordered validation stays green while a review finds an adjacent swap (for example mark-before-marker) still allowed; OR a simulation that only swaps the middle pair still passes.

**Example (playbook execute-plan skill-gate marker plan, review r2):** Recovery ordered check required `marker_ln < done_ln` and `mark_ln < done_ln`. Simulation with marker after mark stayed green. Tightened to `marker_ln < mark_ln < done_ln`; the swap then failed.

**See also:** #187 (context spillover false-green; different mechanism), coding_guidelines.md #18/#22 (Family A / Family E), `plans` Validation Commands authoring rules.

## 189. Lead Multi-Action Skill Steps With the Gate Action

**Principle:** Family E (temporal / ordering invariants). Agents treat the first imperative sentence of a step as the start of execution. A later "first refresh the marker" clause loses to an opening "update the plan file".

**Trigger:** Editing a skill step that has a precondition gate (marker refresh, lock acquire, validation) plus a following mutation.

**Rule:**
1. Put the gate or precondition verb in the first imperative of the step ("apply X, then update Y"), not in a follow-up sentence after the mutation.
2. Prefer one ordered sentence over two paragraphs that reverse the order.
3. After editing, re-read the step opening: if an agent obeyed only the first sentence, would the gate still run first?

**Why this happens:** Multi-sentence steps are read as sequential scripts. Opening with the mutation trains the wrong order even when a later sentence states the gate.

**Shape trigger (when to suspect this family):** A review finds a skill step whose first sentence mutates a gated artifact and a later sentence requires the gate first; OR an agent edits the gated file before refreshing the marker while "following" the step.

**Example (execute-plan Step 1.3, review r2):** The step opened with "update the plan file" then said "Apply Plan-file edits before updating checkboxes." Collapsed to one sentence that leads with the marker refresh.

**See also:** #179 (contradiction after partial edit; wrong order vs conflicting rules), #187, #190 (same-line character order for Validation Commands), `execute-plan` Plan-file edits (skill-gate).

## 190. Same-Line Presence Does Not Prove Character Order

**Principle:** Family E (temporal / ordering invariants) cross with Family H (verify the real thing).

**Trigger:** Authoring or reviewing Validation Commands that assert phrase A must precede phrase B inside a step, using a presence grep for both tokens, or a line-number compare that treats equal lines as ordered.

**Rule:**
1. When both phrases can appear on one line, assert character order inside the matched window (for example `case "$window" in *'A'*'B'*)`), not only that both tokens exist.
2. Do not treat `a_ln <= b_ln` as proof when `a_ln == b_ln`; same-line inversion stays green.
3. After writing the check, simulate same-line reverse order and two-sentence reverse order; both must fail.

**Why this happens:** Presence and line equality prove anchors exist, not left-to-right order on the same line.

**Shape trigger (when to suspect this family):** An ordered Validation Command stays green after inverting two phrases on one line, or after swapping two adjacent sentences while both tokens remain in the window.

**Distinguishing from #188 / #189:** #188 is an incomplete multi-line chain (`a < z` and `b < z`). #189 is skill prose that leads with the mutation. This lesson is a gate that cannot see character order when both tokens share a line.

**Example (playbook execute-plan skill-gate marker plan, review r3):** Step 1.3 presence and structural greps stayed green on inverted wording. A line-number `-le` check also false-greened when both phrases shared a line. Replaced with a character-order `case` requiring `Plan-file edits` before `update the plan file` inside the Step 1.3 window.

**See also:** #187 (context spillover), #188 (pairwise-before-last), #189 (lead skill steps with the gate), #191 (fail-closed abort / polarity), `plans` Validation Commands authoring rules, coding_guidelines.md #22/#25 (Family E / Family H).


## 191. Validation Blocks Must Abort Explicitly; Token Presence Is Not Polarity

**Principle:** Family H (verify the real thing) cross with Family B (error-policy propagation). A Validation Commands block that runs required greps without an explicit abort on miss, or that asserts a policy by grepping a token that survives inverted wording, reports exit 0 while the obligation is absent or reversed. Bash `set -e` and `!` do not fix this: inverted commands and mid-`&&` failures are exempt.

**Trigger:** Authoring or reviewing a multi-check Validation Commands bash block, especially after adding dedicated greps that "should" fail on miss.

**Rule:**
1. Wrap every required positive check so miss aborts: `grep ... || { echo ...; exit 1; }` or `if ! { ... }; then exit 1; fi`. Do not rely on bare grep exit status or `test A && test B` alone to stop the block.
2. For forbidden matches, use `if grep ...; then echo ...; exit 1; fi`. Do not rely on `! grep` (or `set -e` with `!`) as the abort mechanism.
3. When asserting a policy polarity (FAIL-LOUD stop, must refresh), grep for the positive obligation verbs inside a tight window, and abort on inverted phrases (`continue editing`, `without refreshing`, `skip.*marker`). Token leftovers (`unwritable`, `WRITE RECIPE`) are not enough.
4. After writing, mutate: strip one required obligation, add a bypass phrase, invert polarity wording. Each mutation must exit non-zero before the hygiene command runs.

**Why this happens:** Authors paste greps into a script and assume non-zero stops the script. Without `set -e` (or even with it for `!` / mid-pipeline), later commands including hygiene still run and the overall exit is 0.

**Shape trigger (when to suspect this family):** Validation Commands stay green after removing a Hard Gate or anti-pattern row, after adding bypass language, or after rewriting a FAIL-LOUD stop as continue-editing; OR a review finds `! grep` / bare presence greps as the only fail path.

**Distinguishing from #187 / #190:** #187 is wrong sufficiency (context spillover). #190 is same-line character order. This lesson is abort policy and polarity of wording.

**Example (playbook execute-plan skill-gate marker plan, review r4):** The shipped Validation Commands stayed green when Hard Gate #20, the anti-pattern row, Recovery marker order, or bypass language were mutated. Polarity greps for `unwritable` stayed green when shared Plan-file edits said continue editing. Fixed with explicit `|| exit 1` / `if grep; then exit 1; fi` and polarity-positive plus inverted-polarity checks.

**See also:** #187 (context spillover), #188 (pairwise-before-last), #190 (same-line order), `plans` Validation Commands authoring rules, coding_guidelines.md #19/#25 (Family B / Family H).


## 192. Tests That Pass Green Do Not Prove They Skip Gitignored Personal Data

**Principle:** Family H (verify the real thing) cross with Family C (single resolution path). A "tests must read committed synthetic data" rule enforced by static grep + a passing run does NOT prove compliance when production code resolves a default registry/config path into the gitignored per-user directory. Tests pass by reading the user's real personal data off disk; on a fresh clone (where that path is gitignored and absent) they would fail or behave differently. Static grep misses this: the offending code constructs the path programmatically (`repo_root / ... / str(year) / ...`), so no forbidden literal appears in the test. Only a runtime file-open audit catches it.

**Trigger:** A "no personal data" / synthetic-data-only rule AND production code resolves a default path under a gitignored per-user directory (config registries, fixture files, snapshots).

**Rule:**
1. When production code resolves a per-user/gitignored data path with a default, tests exercising that code MUST inject the committed example/template path explicitly (kwarg, monkeypatched loader, or fixture override) - never rely on the production default, even when the personal file exists locally.
2. The production resolver MUST fall back to the committed template when the per-user path is absent, so a fresh clone works out of the box.
3. Add a runtime guard test: run the module under a `sys.addaudithook` file-open audit (in a subprocess, since the hook is process-global) and fail if any forbidden gitignored path is opened. Mutation-verify by reverting the injection and confirming the guard fails.
4. Static grep for the forbidden path string is insufficient as the sole guard when the path is constructed programmatically.

**Shape trigger (when to suspect this family):** A test passes green on one developer's machine but would fail on a fresh clone; production code constructs a path under a gitignored per-user directory; a "no personal data" rule is enforced only by static grep; a user asks "are we sure these tests only use synthetic data?".

**Distinguishing from the "skipped-in-CI tests need static-guard coverage" lesson:** that lesson is about tests that `pytest.skip` when their real fixture is absent, so a defect never surfaces in CI - caught by extending the static guard's scan list. This is the inverse: tests that do NOT skip (they pass) by silently reading real data that happens to exist locally. The skipped-test case never runs; this case runs and reads the wrong source. Only a runtime audit catches it, because the test never fails.

**Example (on-chain tx tagger plan):** Production hardcoded `repo_root / "resources" / "source" / str(year) / "berachain_contracts.json"` (the gitignored per-user registry). Three e2e tests passed by reading the author's real registry; on a fresh clone they would raise `FileProcessingError`. Static grep for `resources/source/2025` in tests found only docstring comments. A `sys.addaudithook` audit caught the two real registries opened at runtime. Fixed by adding `contracts_path`/`lp_snapshot_path` kwargs (tests inject the `example/` path) + a production `example/` fallback + a subprocess-audit guard test (mutation-verified).

**See also:** Family H / C (coding_guidelines.md #19/#22), AGENTS.md crypto-tests rule.

## 193. A Rename Is Incomplete Until the Source Path Is Gone From HEAD

**Principle:** Family H (verify the real thing, not the abstraction). Cross with Family D (single source of truth for the live path).

`git mv` (or add-destination + delete-source) is complete only when HEAD no longer lists the old path. Staging or committing only the destination leaves both paths tracked. Callers that follow the old path and callers that follow the new path diverge silently.

**Trigger:** Archiving, relocating, or renaming a tracked file when the agent stages with `git add <dest>` instead of a true rename, or when a partial `git mv` leaves the source still tracked.

**Rule:**
1. Prefer `git mv <src> <dest>` (or an equivalent staged rename), not "copy content to dest then add dest".
2. Before calling the move done, run `git status` / `git ls-files -- <src>` and confirm the source is deleted or shows as renamed, and that HEAD after commit no longer contains `<src>`.
3. If both paths appear in `git ls-files` after the intended archive commit, treat that as a failed archive and delete the stale source in a follow-up commit before Phase 5 cleanup.

**Shape trigger (when to suspect this family):** A completed/ or moved path exists while the old active path is still tracked; `git log --follow` and `git ls-files` disagree on which path is live; a second delete commit appears right after an archive commit.

**Distinguishing from #74 (`git mv` nesting when dest exists):** #74 is about directory nesting (`dest/<basename>/`). This lesson is about an incomplete rename that leaves the original path tracked alongside the destination.

**Example (execute-plan Phase 4 archive):** An archive commit added `docs/plans/completed/<plan>.md` without removing `docs/plans/<plan>.md`. Both paths stayed in HEAD until a follow-up delete commit. Phase 5 success checklist item 5 ("plan exists under completed/") was true while the active path still poisoned future plan discovery.

**See also:** UL#74 (git mv nesting), execute-plan Phase 4, Family H / D.

## 194. Fix a Skim Surface and Its Validation Pin in the Same Change

**Principle:** Family A (equivalence-class coverage) cross with Family H (verify the real thing). Cross with Family D (Validation Commands are part of the same contract as the prose they police).

Editing policy prose on a skim surface (anti-pattern table, Integration Points, Hard Gate, Scope note) without updating `## Validation Commands` in the same change leaves the gate green on the old obligation. The next review re-finds the gap as if the prose fix never landed.

**Trigger:** A review or address pass rewrites a skim surface, and Validation still greps only an older sibling surface, a spillover context window, or a negative pattern that the Integration Points text itself can false-match.

**Rule:**
1. When you change a load-bearing skim surface, add or retarget a Validation pin for that surface in the same edit (same task / same address commit).
2. Prefer positive pins on the new obligation (path + distinctive phrase) over broad negatives that match the plan's own IP or glossary text.
3. Re-run Validation after the prose fix; if it still passes without the new pin matching, the pin is wrong or missing.

**Shape trigger (when to suspect this family):** Multiple review rounds keep filing "Validation under-pins X" after X was just rewritten; a negative grep fails on the plan's own allow/deny or IP wording; authoring cites lessons #187/#191 but the new surface has no command.

**Distinguishing from UL#187 / UL#191:** #187 is obligation vs context spillover. #191 is missing abort / polarity-blind token presence. This lesson is the lockstep rule: prose fix and Validation pin must land together, or the next panel treats the fix as incomplete.

**Example (plan-executable-task-gates Phase 3):** Address rounds fixed Recovery, Scope, leave-fail-closed, and vacuous-why surfaces while Validation lagged. Later rounds kept blocking on under-pins and false-positive negatives until pins were added beside each surface and negatives were narrowed away from IP spillover.

**See also:** UL#186, UL#187, UL#191, plans Validation authoring, review-plan inclusion checks.

