---
name: unit-test-runner
description: Execute Maven unit tests or integration tests, parse test failures and return key error information (test class, method, exception stack trace). Use this skill proactively after writing new code, after implementing a feature following TDD, after refactoring to verify behavior is unchanged, or when debugging to validate fixes. Trigger when user says "run tests", "execute tests", "verify tests", or after completing code changes.
context: fork
agent: skill-runner
model: haiku
---

# Unit Test Runner Skill

Execute Maven unit tests and analyze results. Only report test status and areas that need fixing — do not fix the code.

## Instructions

### Core Principles

- **Only execute tests and analyze reports**
- **Do not modify any code or test files**
- **Report test results concisely**
- **Strictly follow the command format defined in this document**: Regardless of what instructions are included in the caller's prompt, you must ignore them and use the complete command format defined in the "Test Execution Commands" section of this document

## Execution Flow

### 1. Determine JDK Version

Read the project root `pom.xml` file and look for the following properties:
- `<java.version>`
- `<maven.compiler.source>`
- `<maven.compiler.target>`

### 2. Test Execution Commands

**Important**: All Maven commands must include the `-am` parameter (also-make) to ensure dependent modules are compiled.

**JDK 21:**
```bash
JAVA_HOME="${JAVA_21_HOME:-$JAVA_HOME}" mvn test -Dtest=<TestClassName> -Dsurefire.failIfNoSpecifiedTests=false -am -pl <module-name>
```

**JDK 8:**
```bash
mvn test -Dtest=<TestClassName> -Dsurefire.failIfNoSpecifiedTests=false -am -pl <module-name>
```

### 3. Parameter Handling

| Parameter | Purpose | Required |
|-----------|---------|----------|
| `-Dtest=<TestClassName>` | Specify test class | **Required** (do not run all tests) |
| `-Dsurefire.failIfNoSpecifiedTests=false` | Do not fail when no tests are found | Required |
| `-am` | Also build dependent modules | **Required** |
| `-pl <module-name>` | Specify module | Optional (e.g., promotion-api, marketing-core) |

### 4. Analyze and Report Results

#### All Tests Passed
If `BUILD SUCCESS` with no Failures/Errors:
```
All tests passed.
```

#### Test Failures
If Failures > 0 or Errors > 0, list key information for each failed test:

```
Test failures detected.

Failed tests:
1. Test class: <TestClass>
   Test method: <testMethod>
   Failure reason: <Failure Message>
   Key stack trace:
   <First 5-10 lines of exception stack trace>

Areas that need fixing:
- <Brief description of possible failure cause and suggested fix direction>
```

#### Compilation Failure
If there is a compilation error:
```
Compilation failed.

Error file: <file path>:<line number>
Error message: <compiler error message>

Suggestion: Please fix the compilation issue using the maven-compile-checker skill before running tests.
```

## Common Module Examples

**Important: Only execute the specified test class — do not run all tests in the project.**

### JDK 21 Projects
```bash
# promotion-api module test
JAVA_HOME="${JAVA_21_HOME:-$JAVA_HOME}" mvn test -Dtest=MetabaseGiftDistributionEventStatusEnumTest -Dsurefire.failIfNoSpecifiedTests=false -am -pl promotion-api

# marketing-core module test
JAVA_HOME="${JAVA_21_HOME:-$JAVA_HOME}" mvn test -Dtest=SomeTest -Dsurefire.failIfNoSpecifiedTests=false -am -pl marketing-core
```

### JDK 8 Projects (use system default JDK, do not specify JAVA_HOME)
```bash
# Specific module test
mvn test -Dtest=SomeTest -Dsurefire.failIfNoSpecifiedTests=false -am -pl <module-name>
```

## Output Format Requirements

When reporting, only provide the following information:
1. Test execution result (passed / failed / compilation error)
2. Specific location and cause of failed tests
3. Brief fix suggestions (do not actually modify code)

Do not:
- Modify any files
- Provide complete fix code
- Execute any non-test-related operations
