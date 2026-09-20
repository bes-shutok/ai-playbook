# Backlog: audit review-agent catalogs for language and project agnosticism

Status: open
Priority: high
Workflow: backlog
Class: skill quality and portability
Driving force: maintainability

## Problem

The review-agent catalogs are shared library guidance consumed by multiple
orchestrators and runtimes. Recent coverage additions were written from one
stack and one repository's failure shapes, so they need a dedicated audit
before they become durable standards. A catalog can accidentally encode a
language, framework, project layout, test-class suffix, build command, product
term, or repository-specific path even when the same review concept should be
portable.

## Required distinction

- Review-agent catalogs must contain language- and project-agnostic detection
  patterns, evidence requirements, and abstract failure shapes.
- Language-specific behavior belongs in the language overlay.
- Project-specific conventions, runner names, harnesses, paths, and commands
  belong in the Guideline Pack resolved from facts and sibling repository
  evidence.
- Execution framing, tool choice, output formats, and orchestration policy
  belong in the consuming skill, not in the shared catalog.

## Suggested fix

Perform a complete audit of every file under `agents/skills/review-agents/` and
every orchestrator that consumes it. For each rule, identify language,
framework, project, employer, path, command, test-name, or product assumptions;
move the rule to the correct overlay, Guideline Pack, or orchestrator when it
is not portable. Add neutral examples and a regression check that rejects new
hardcoded project or language assumptions in shared catalogs. Verify that each
catalog is still a pattern catalog and that all consuming skills load the
appropriate overlay before applying stack-specific guidance.

## Acceptance criteria

- Every shared review-agent rule passes a language-agnostic and
  project-agnostic review, with exceptions documented by placement.
- No catalog hardcodes a repository path, product name, ticket prefix, test
  suffix, build command, framework API, or language-specific syntax unless the
  rule is explicitly abstract or lives in an overlay.
- All orchestrators have a tested boundary between shared catalogs, language
  overlays, Guideline Pack material, and execution instructions.
- A lightweight validation check runs during skill changes and reports the
  offending file and rule when portability is violated.
- Existing recent additions are re-reviewed under this standard before being
  treated as complete.

## Evidence

The preceding review-coverage update was derived from one JVM/Spring,
RocketMQ, database, and repository workflow. The rules may be useful, but the
shared catalog layer has not yet received the required portability audit.
