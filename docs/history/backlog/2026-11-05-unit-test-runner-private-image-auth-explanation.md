# Backlog: explain private test-image authentication before asking for access

Status: open
Priority: high
Class: fix-class
Origin class: skills-corpus defect (learn Step 1.8, 2026-11-05 session analysis)
Added: 2026-11-05

## Observed versus expected

During a Maven test run, pulling the configured PostgreSQL test image failed because authentication to the private image registry had expired. The session asked the user to reauthenticate before explaining why a database image needed registry access or checking the repository's test configuration for an allowed local alternative. The user asked why registry access was needed, then directed the session to find a workaround before the test run continued.

Expected: when test execution fails while pulling a private image, identify the image source from the repository's test configuration, explain the exact dependency on registry authentication, and check documented or already-authorized local alternatives before asking the user for credentials. Never override an organization-mandated image source without authorization.

## Reproduction evidence (trimmed)

- A Maven test run required a PostgreSQL container image configured to resolve through a private registry.
- The pull failed on expired registry authentication; the user asked why access was needed before offering to restore it.
- `agents/skills/unit-test-runner/SKILL.md` and `agents/skills/unit-test-runner/maven.md` describe test scope and Maven execution but do not explain the private-image authentication failure path.
- The `self-heal` skill already requires reading the refusal source and searching documented recovery paths before deciding a blocker is unavoidable.

## Suspected root area

`agents/skills/unit-test-runner/maven.md`, runtime dependency failure analysis and reporting. The test adapter lacks a concise source-backed explanation step for private container-image pulls.

## Fix shape

Add a short note to the existing Maven execution and reporting guidance: trace private test-image selection to repository configuration, explain the authentication dependency, check only documented or already-authorized alternatives, and ask for access only when those paths do not resolve the pull. Point to `self-heal` for blocker recovery; do not restate its general procedure or add a test gate.

## Ship when

The Maven adapter handles an expired private-image pull by naming the configured image source and why authentication is needed, checking for an approved local alternative, and asking for credentials only if required. A realistic example must preserve any project policy that mandates the private mirror.
