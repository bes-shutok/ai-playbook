---
name: unit-test-runner
description: Execute the test scope requested by the caller, analyze results, and report failures without changing code. Use proactively after implementation, refactoring, or debugging, and whenever the caller asks to run or verify tests.
context: fork
agent: skill-runner
model: haiku
---

# Unit Test Runner Skill

Run tests and analyze the results. Do not modify production code or tests.

## Instructions

### 1. Determine the requested scope

Read the repository's build files and test documentation to identify the test runner and the required runtime. Classify the caller's request:

- **Focused:** the caller names test classes or asks for a clearly bounded behavior. Run only those tests.
- **Behavior-broad:** the caller asks to verify a change, feature, refactor, or fix without naming a complete test set. Trace the changed behavior into the test inventory and select every relevant test, including integration tests where applicable. Do not assume one representative test covers the behavior.
- **Full-suite:** the caller asks to confirm that no tests fail, run all tests, or equivalent. Find and run the repository's documented full-test command; report any suites it excludes. Do not substitute selected tests.

If scope is ambiguous, use the broader interpretation that fits the request. If the repository does not document a full-suite command, report that and ask for direction rather than inventing one.

### 2. Load the matching runner instructions

Read the runner-specific reference that matches the repository's build files. Current adapters:

- Maven projects with a Java POM: [maven.md](maven.md)

If no adapter matches the repository, report that the runner is unsupported and ask for direction. Follow the adapter's command and runtime rules. Do not carry assumptions from one runner into another.

### 3. Execute and analyze

Execute only the selected scope as prescribed by the adapter. If the adapter cannot run that scope without running unrelated tests, report the conflict before executing. Do not silently broaden or narrow the requested scope.

### 4. Report

Report the exact command, scope, result, test count from the runner's reports when available, and excluded suites for broad requests. If reports provide no reliable count, say it is unavailable; do not estimate from the class list. Never describe a selected subset as the full suite.

For failures, list each failed test, its method or case, reason, and the first 5-10 useful stack-trace lines, followed by brief fix directions. For compilation failures, report the file, line, compiler message, and the relevant compile-check skill when one exists.

## Constraints

- Execute tests and analyze reports only; do not modify production code or tests.
- Do not provide complete fix code.
- Report the exact tested scope and commands; do not imply a subset was the full suite.
