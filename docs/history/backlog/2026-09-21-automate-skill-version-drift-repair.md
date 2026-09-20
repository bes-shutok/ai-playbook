# Backlog: automate installed-skill version-drift detection and repair

Status: open
Priority: medium
Workflow: backlog
Class: skill distribution integrity
Driving force: reliability

## Problem

The graphify CLI detected that an installed skill was older than the package,
but the warning did not identify which configured platform held the stale copy.
Refreshing one platform left another installation stale, so the warning
continued until every platform was inspected manually.

This can affect any skill that is distributed to multiple agent or editor
configuration directories. A session may therefore follow outdated
instructions even after the active agent's copy was refreshed.

## Suggested fix

Add a reusable skill-distribution integrity check that:

1. Enumerates every configured platform destination for the installed skill.
2. Compares each destination's version stamp with the running package version.
3. Reports the exact stale platform paths and distinguishes missing, older, and
   newer copies.
4. Offers or performs an idempotent refresh for all stale destinations in one
   operation.
5. Verifies the post-refresh inventory and returns a nonzero result if any
   configured destination remains stale.

The check should be callable from setup/probe commands and from the relevant
skill preflight. It should not silently overwrite a newer destination without
an explicit downgrade decision.

## Acceptance criteria

- A single command reports version drift across all configured skill
  destinations, not only the current agent's directory.
- The remediation updates every older destination and verifies the result.
- The output names the platform and resolved path responsible for each warning.
- Newer installed skills are preserved unless a downgrade is explicitly
  requested.
- The repository hook or probe suite includes a fixture with one stale sibling
  installation and asserts that the command detects it.

## Non-goals

- Do not duplicate each skill's workflow instructions in the distribution
  checker.
- Do not require network access when the matching package and skill assets are
  already available locally.
