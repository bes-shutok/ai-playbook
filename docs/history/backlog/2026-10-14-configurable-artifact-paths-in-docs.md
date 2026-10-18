# Backlog: keep durable documentation independent of local artifact paths

- **Filed:** 2026-10-14, consumer feedback
- **Status:** covered (docs/history/plans/2026-10-15-configurable-artifact-paths-in-docs.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class
- **Driving force:** docs + maintainability
- **Skill/step:** `agents/skills/agents-best-practices/SKILL.md`; `agents/skills/review-agents/documentation.md`; related closeout reporting in `agents/skills/done/SKILL.md`
- **Environment:** consumer repository using facts-configured local artifact homes, 2026-10-14
- **Suspected root area:** durable documentation and closeout checks describing or assuming local artifact locations that are user-configurable
- **Severity:** medium; duplicated location policy drifted from shared skill configuration, and closeout reported historical artifact references absent from its current lookup
- **Consumer urgency:** Consumer projects that use these shared skills need location-independent documentation and accurate artifact lookup; the skills-repo personal priority profile must not park or defer the fix as formal-hardening for the skills repo alone.
- **Source:** user-directed cleanup of active project guidance that duplicated configurable artifact locations; closeout report of historical review references absent from the live lookup. Historical source documents were left unchanged.
- **Capture hygiene:** `scan-public-hygiene --files` passed.

## Problem

Project-facing documentation duplicated exact local review, certification, or metrics locations even though these locations come from per-user or per-repository configuration and the shared skills own the workflow. This made the documents brittle and inconsistent with the configured artifact home.

The same closeout reported historical review references that were absent from its current lookup. That report did not establish whether the records were lost, stored in another configured home, or available only in an archive branch. The two observations may share a path-ownership problem, but the archive lookup needs verification before treating it as data loss.

## Expected

Durable project guidance describes project policy and stable concepts, while shared skills resolve configurable artifact homes and own workflow details. Review guidance should identify active documentation that duplicates local paths or temporary configuration values. Historical records should be checked against their authoritative archive before a missing-artifact report is presented as unresolved.

## Suggested investigation

Compare a concise rule in `agents-best-practices` with a documentation-review check in `review-agents`, and determine whether the closeout lookup needs a separate correction. Preserve valid stable references, keep configuration facts out of committed project prose, verify any claimed missing artifact against the configured home and archive source, and do not rewrite historical plans or fabricate review records.

## Why not fixed now

The consumer documentation cleanup is complete. Updating shared guidance and validating its review behavior require a cross-skill change beyond that cleanup. Archive availability remains unverified.

## Dedup probe

Searches of open backlog filenames and problem text for `configurable artifact`, `review artifact location`, and `facts-configured path` found no matching item. `2026-10-14-done-dirt-gate-valid-doc-removal.md` covers the closeout gate refusing an intentional removal; it does not cover the source-of-truth policy for configurable artifact locations or verification of historical archive lookups.
