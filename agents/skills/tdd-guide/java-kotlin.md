# Java / Kotlin TDD Specifics

## Test Execution

- Use `/unit-test-runner` skill to run tests (avoids polluting the main conversation context)
- Always pass `-DfailIfNoTests=false` when using `mvn test`
- Run specific test class: `mvn test -pl module -Dtest=ClassNameTest`
- Run specific method: `mvn test -pl module -Dtest=ClassNameTest#methodName`

## Naming Conventions

- Test class: `<ClassUnderTest>Test` (e.g., `OrderServiceTest`)
- Test method (Java): `shouldDoSomething_whenCondition` or `@DisplayName` annotation
- Test method (Kotlin): backtick names — `` `should do something when condition` ``

## Frameworks

- JUnit 5 preferred (Jupiter)
- AssertJ for fluent assertions
- Mockito for mocks (use sparingly — prefer real collaborators)
- Kotlin: consider MockK for idiomatic Kotlin mocking

## Spring-Specific

- Use `@SpringBootTest` only for integration tests
- Prefer `@WebMvcTest`, `@DataJpaTest`, `@JsonTest` for sliced unit tests
- Use `@MockBean` / `@SpyBean` only at slice boundaries
- Constructor injection makes classes naturally testable without Spring context
