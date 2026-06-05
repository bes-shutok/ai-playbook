---
name: tdd-guide
description: >
  Kent Beck Test-Driven Development (TDD) and Tidy First methodology guide.
  Use when implementing new features, fixing bugs, refactoring code, or needing TDD workflow guidance.
  Triggers: (1) starting any new feature development, (2) fixing a defect, (3) refactoring existing code,
  (4) user asks about test strategy, (5) executing the Red → Green → Refactor cycle.
---

# TDD Guide

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. No exceptions.

## Core TDD Cycle: Red → Green → Refactor

1. **Red**: Write one minimal failing test that defines a small increment of behavior
2. **Verify Red**: Run the test — confirm it *fails* for the expected reason (missing feature, not a typo or error)
3. **Green**: Implement the minimum code to make the test pass — no more, no less
4. **Verify Green**: Run all tests — confirm everything passes
5. **Refactor**: Improve code structure without changing behavior, run tests after each change
6. **Repeat**: Next failing test for the next increment

## TDD Methodology

- Use meaningful test names that describe behavior, not implementation
- Implement only enough code to pass the current test
- Make test failures clear and informative
- Prefer testing real code over mocks; use mocks only when unavoidable (external services, time)
- **Fixing a defect**: First write a failing test that reproduces the bug → fix with minimal code → verify

## Tidy First (Separate Structure from Behavior)

Classify all changes into two types — **never mix them**:

| Type | Description | Examples |
|------|-------------|---------|
| **Structural changes** | Rearrange code without changing behavior | Rename, extract method, move code |
| **Behavioral changes** | Add or modify actual functionality | Add logic, change return values, add API |

- When both types are needed, **make structural changes first**
- Run tests before and after structural changes to confirm behavior is unchanged
- Commit structural and behavioral changes separately

## Commit Discipline

Only commit when **all** of the following are true:
1. ALL tests are passing
2. ALL compiler/linter warnings have been resolved
3. The change represents a single logical unit of work
4. Commit message clearly states whether it contains structural or behavioral changes

Use small, frequent commits rather than large, infrequent ones.

## Test Failure Handling

**Fix ALL failing tests, not just the ones related to your changes.**

- Do not ignore test failures that appear unrelated to your current changes
- Even if a failure seems to be a pre-existing issue, investigate and resolve it
- If a failure genuinely cannot be fixed within current scope, explicitly report it to the user for decision

## Code Quality Standards

- Eliminate duplication ruthlessly (DRY)
- Express intent clearly through naming and structure
- Make dependencies explicit
- Keep methods small and focused on a single responsibility (SRP)
- Minimize state and side effects
- Use the simplest solution that could possibly work

## Refactoring Guidelines

- Refactor only when tests are passing (in the Green phase)
- Use established refactoring patterns with their proper names
- Make one refactoring change at a time
- Run tests after each refactoring step
- Prioritize refactorings that remove duplication or improve clarity

## Test Execution Rules

- Automatically run tests at each TDD phase (Red → Green → Refactor) without waiting for user request
- Run ALL tests each time, except long-running integration tests
- Use the project's test runner (see language-specific files in this skill directory)

## Common Rationalizations (resist all of these)

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Need to explore first" | Fine — throw away exploration, start fresh with TDD. |
| "Test is hard to write" | Listen to the test. Hard to test = hard to use = design problem. |
| "TDD will slow me down" | TDD is faster than debugging. |
| "Keep code as reference" | You'll adapt it. That's testing after. Delete means delete. |

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test | Write the wished-for API first. Write assertion first. Ask your human partner. |
| Test too complicated | Design too complicated. Simplify the interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup huge | Extract helpers. Still complex? Simplify the design. |

## Bug Fix Workflow (Outcome-Driven)

When fixing a bug or changing behavior, follow this structured process:

1. **Restate** the issue in 1-2 sentences
2. **Audit existing tests** before writing new ones:
   - Search for tests that cover or overlap the target behavior
   - Identify candidate test files, current assertions, and which to extend
   - Create a new test file only after showing no suitable location exists
3. **Define outcomes** before writing tests:
   - Return values and thrown errors
   - Side effects (DB writes, events, metrics, external calls)
   - State changes
   - Same outcome + same side effects → parameterized/table-driven rows
   - Different outcome or side effects → separate tests
4. **Premortem the test strategy** using the `premortem` skill (Pessimist + Attacker personas):
   - "These tests have passed but the bug reappeared in production. Why?"
   - Feed findings as additional test cases or assertions
5. **Propose a plan** (test matrix, grouping, location) and **stop for approval**
6. **Execute Red → Green → Refactor** with mandatory test runs each cycle
7. **Verify completion** — run the relevant suite, show command + result summary

## Testing Anti-Patterns

- Testing mock behavior instead of real behavior
- Adding test-only methods to production classes
- Mocking without understanding what you're isolating
- Test names describing implementation instead of behavior
