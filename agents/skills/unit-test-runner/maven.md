# Java Maven Test Runner

Use these instructions for Java projects built with Maven. The shared [SKILL.md](SKILL.md) owns request-scope classification and reporting; this reference owns Maven lifecycle, selector, and JDK details.

## Determine the JDK

Resolve the required JDK from the project POM and test documentation. Check active profiles and Maven toolchain configuration when they may override root properties such as `<java.version>`, `<maven.compiler.source>`, or `<maven.compiler.target>`. Use an installed JDK matching the effective requirement. For JDK 21, set `JAVA_21_HOME` to the installed JDK 21 before using the prefix below; do not fall back to an unverified `JAVA_HOME`. For JDK 8, use system Java only after confirming it is JDK 8. For other versions, set `JAVA_HOME` to the matching installed JDK. If the effective requirement or a matching JDK cannot be established, report the environment gap instead of running with a different default.

## Select Maven tests

For scoped Maven runs include `-am` (also-make), and include `-pl <module-name>` when the relevant module is known.

**Surefire unit tests** use `-Dtest` with the selected class list. A comma-separated list is valid for behavior-broad requests.

```bash
JAVA_HOME="${JAVA_21_HOME:?Set JAVA_21_HOME to an installed JDK 21}" mvn test -Dtest=<TestClass1,TestClass2> -Dsurefire.failIfNoSpecifiedTests=false -am -pl <module-name>
```

**Failsafe integration tests** use the `verify` lifecycle and `-Dit.test` with the selected class list. Since `verify` also reaches Surefire's `test` phase, when both test types are in scope combine `-Dtest` and `-Dit.test` in the same command. For an integration-only request, inspect the POM for a project-specific way to skip Surefire while leaving Failsafe enabled. Do not assume a generic skip property behaves the same across Failsafe versions. If Surefire cannot be skipped safely, stop and report the conflict before running; do not execute unrelated unit tests or silently expand the requested scope.

```bash
JAVA_HOME="${JAVA_21_HOME:?Set JAVA_21_HOME to an installed JDK 21}" mvn verify -D<project-specific-surefire-skip-property>=true -Dit.test=<IntegrationTest1,IntegrationTest2> -am -pl <module-name>
```

For an integration-only request, replace the Surefire-skip placeholder with the project-specific property verified in the POM. When both test types are relevant, use both selectors in one `verify` command and report the selected classes by plugin. For full-suite requests, keep the documented command and selectors unchanged, and run it with the required JDK selected above.

| Parameter | Purpose | Required |
|-----------|---------|----------|
| `-Dtest=<class-list>` | Select Surefire unit test classes | Focused or behavior-broad Surefire runs |
| `-Dsurefire.failIfNoSpecifiedTests=false` | Allow selected modules with no matching tests | With `-Dtest` |
| `-Dit.test=<class-list>` | Select Failsafe integration test classes | Focused or behavior-broad Failsafe runs |
| `-am` | Also build dependent modules | Scoped Maven runs |
| `-pl <module-name>` | Limit the reactor to the relevant module and required projects | When a module is known |

For behavior-broad selection, state how changed behavior maps to the chosen classes. If relevant tests cannot be found, or none exist, report the gap instead of silently narrowing scope.

## Examples

For JDK 21, prefix each command with `JAVA_HOME="${JAVA_21_HOME:?Set JAVA_21_HOME to an installed JDK 21}"`. For JDK 8, omit the prefix only after confirming system Java is JDK 8; for other versions, use the matching `JAVA_HOME`.

```bash
# Focused or behavior-broad Surefire selection
mvn test -Dtest=<TestClass1,TestClass2> -Dsurefire.failIfNoSpecifiedTests=false -am -pl <module-name>

# Failsafe integration tests only
mvn verify -D<project-specific-surefire-skip-property>=true -Dit.test=<IntegrationTest1,IntegrationTest2> -am -pl <module-name>

# Selected Surefire and Failsafe tests together
mvn verify -Dtest=<UnitTest1,UnitTest2> -Dsurefire.failIfNoSpecifiedTests=false -Dit.test=<IntegrationTest1,IntegrationTest2> -am -pl <module-name>
```
