# Plan: Review Artifact Contracts and Review Evidence

## Terms

- **Sidecar**: the `.stats.json` file paired with a staged review Markdown file.
- **Current schema**: the explicitly versioned sidecar format produced by shared review skills.
- **Legacy sidecar**: a historical, versionless sidecar that remains readable but is not required to meet the current schema.
- **Pattern ID**: a `lens#kebab-slug` label used to attribute a finding to a shared review lens.

## Assumptions

- Versionless sidecars are historical compatibility inputs; basis: the artifact scan found several older formats, including worker-shaped records whose aggregation metrics must remain intact.
- The first explicit current schema is integer version `1`; basis: no versioned schema exists today, so a single initial version is the smallest compatible contract.
- A future extension belongs in a namespaced `extensions` object, not arbitrary top-level fields; basis: the scan found schema drift caused by unbounded top-level keys.
- Full-panel identity is expressed by worker IDs, while lens IDs remain per-worker evidence; basis: the validator's full-panel contract uses worker IDs and aggregation must not compare that namespace to lens IDs.
- No artifact migration, deployment, external coordination, or project-specific rule is needed; basis: the change is confined to this repository's shared validator and skills.

## Gist & Examples

New review sidecars will state `schema_version: 1`, use one canonical pattern format, and use only documented top-level fields. The validator will enforce that contract only for versioned sidecars. Existing versionless sidecars remain readable as legacy data, so historical review records are neither rewritten nor made unusable nor stripped of their existing aggregation metrics.

For example, a new finding uses a canonical lens such as `testing#weak-assertion` or `consistency#stale-cross-reference`. A worker name, a slash-delimited label, or an unowned label is rejected from a versioned sidecar. The shared `consistency` lens becomes a documented catalog because panel selection already assigns it ownership for plan and RFC contradictions.

When review changes include tests, the testing worker will name the production behavior, distinct outcome, assertion, and harness layer that prove it. When they include runtime registration or configuration, the implementation worker will trace the runtime wiring chain and the testing worker will confirm the live-path proof. These are shared proof obligations, not project conventions.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: the validator accepts a valid version-1 sidecar and rejects an invalid version, missing required pattern, unknown current-lens owner, invalid delimiter, legacy-only pattern emitted by a current sidecar, malformed extensions, and undocumented top-level fields.
- Compatibility: versionless historical sidecars remain legacy for contract validation while worker-shaped records preserve worker, lens, finding, and triage metrics through a compatibility aggregation adapter.
- Aggregation: a realistic version-1 five-worker sidecar enters the growth ledger using worker identity, while lens launches are derived independently from `panel[].lenses`.
- Review quality: the testing, implementation, and consistency guidance assigns a single owner and evidence expectation for test proof, runtime wiring, and plan or RFC consistency.
- Public hygiene: every changed shared skill, example, and test stays generic and contains no project-specific identifiers, internal paths, identities, credentials, or review-artifact content.

**Done when:**

- `scripts/validate_review_staging.py --selftest` covers and passes the new schema and pattern rules.
- `scripts/summarize_review_stats.py --selftest` passes using the shared schema classifier and a versionless worker-shaped fixture with preserved telemetry.
- The reviewed skill documents, inline plan-review schema, and catalog index agree on schema versioning and canonical pattern ownership.
- The gold-source schema and plan-review inline schema publish the exact required and optional version-1 top-level fields and their value types.
- Whitespace and public-hygiene checks pass.

**Ship when:**

- A maintainer elects to refresh the locally installed validator and shared skills from this repository. No deployment is required for the repository change itself.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope.

**Production code:**

- `scripts/validate_review_staging.py`
- `scripts/summarize_review_stats.py`

**Tests:**

- `scripts/validate_review_staging.py` *(built-in self-test cases)*
- `scripts/summarize_review_stats.py` *(built-in self-test cases)*

**Documentation and shared skills:**

- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-agents/SKILL.md`
- `agents/skills/review-agents/consistency.md` *(new)*
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/implementation.md`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/simplification.md`
- `README.md`

**Plan-related extension**; a finding is in scope only when it completes the versioned-sidecar contract, removes duplication from current-versus-legacy classification, or keeps the listed review producer and consumer guidance aligned.

**Out of scope; reject unless plan-related:**

- Existing review artifacts in any project; they are compatibility inputs and must not be rewritten.
- Project guidelines, company conventions, review findings, and external integrations; this plan must remain portable and non-sensitive.
- New review workers beyond the documented `consistency` lens; the goal is alignment and evidence quality, not panel expansion.

## Design Invariants (CR Guard)

- Versioned validation is strict, but history is preserved: a sidecar without `schema_version` remains legacy instead of being rewritten or rejected solely for age. Worker-shaped legacy records retain their current aggregation dimensions through a compatibility adapter.
- `consistency` is a lens identifier, not a project-specific category. Its catalog describes abstract artifact contradictions and source-of-truth drift only.
- The validator is the one source of truth for schema classification. Aggregation must call that exported classifier and choose its compatibility adapter from the returned classification.
- Full-panel growth classification compares worker IDs only: `correctness-completeness`, `testing`, `design-simplicity`, `contract-docs`, and `risk`. Lens counts are derived separately from each panel row's `lenses` array.
- New review artifacts must use `lens#kebab-slug`; legacy `prose-clarity#...` stays readable only for legacy records.
- Version-1 accepts only documented top-level fields plus an object-valued `extensions` field. Arbitrary top-level fields are invalid.
- Review evidence describes abstract behavior and never serializes corpus paths, identifiers, or finding bodies into tracked documentation.

## Validation Commands

```bash
set -euo pipefail

python3 scripts/validate_review_staging.py --selftest
python3 scripts/summarize_review_stats.py --selftest
git diff --check
( cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: Add failing schema and pattern-contract self-tests

Files:

- `scripts/validate_review_staging.py`
- `scripts/summarize_review_stats.py`

- [x] `validate_review_staging.py::_selftest_versioned_schema_and_patterns`; given a complete version-1 sidecar with a canonical `testing#weak-assertion` finding, expects hard validation to pass.
- [x] `validate_review_staging.py::_selftest_versioned_schema_and_patterns`; given a version-1 sidecar with a missing or malformed pattern, a slash-delimited pattern, an unknown owner, or legacy `prose-clarity` owner, expects hard validation to fail with a targeted error.
- [x] `validate_review_staging.py::_selftest_versioned_schema_and_patterns`; given a version-1 finding whose Markdown Pattern is missing or differs from an otherwise valid sidecar Pattern, expects hard validation to fail; given matching canonical patterns, expects it to pass.
- [x] `validate_review_staging.py::_selftest_versioned_schema_and_patterns`; given a version-1 sidecar with a valid `extensions` object, expects hard validation to pass; given a non-object extension or an arbitrary top-level field, expects hard validation to fail.
- [x] `validate_review_staging.py::_selftest_versioned_schema_and_patterns`; given a versionless historical payload, expects legacy classification without requiring version-1 fields.
- [x] `summarize_review_stats.py::legacy-adapter self-test`; given a versionless worker-shaped payload, expects legacy contract classification while worker, lens, finding, and triage aggregation totals remain equal to its pre-version compatibility shape.
- [x] `validate_review_staging.py::_selftest_versioned_schema_and_patterns`; given canonicalized simplification findings such as `simplification#shrink`, expects hard validation to pass, while the colon-delimited body tag remains presentation text rather than the sidecar Pattern ID.
- [x] `summarize_review_stats.py::current-adapter self-test`; given a realistic version-1 five-worker panel with worker IDs and their assigned lens arrays, expects current aggregation and growth-ledger eligibility without conflating worker and lens identity.
- [x] `validate_review_staging.py::_selftest_versioned_schema_and_patterns`; given every documented required field and each optional version-1 field in its permitted type, expects hard validation to pass; given any missing required field, expects hard validation to fail.
- [x] Run → expect RED: `python3 scripts/validate_review_staging.py --selftest` and `python3 scripts/summarize_review_stats.py --selftest` fail only because the new assertions do not yet have implementation support.

### Task 2: Implement the versioned sidecar and canonical-pattern contract

Files:

- `scripts/validate_review_staging.py`
- `scripts/summarize_review_stats.py`

- [x] Export one validator schema classifier that distinguishes version-1 records, versionless worker-shaped compatibility records, and other legacy records. Reject an unsupported explicit version.
- [x] Require a valid canonical Pattern ID for each version-1 finding, overflow item, and discarded finding that carries a pattern. Permit the declared shared lens owners plus `unknown`; allow `prose-clarity` only in legacy data.
- [x] Define the complete version-1 top-level allowlist, require `extensions` to be an object when present, and reject unknown top-level fields.
- [x] Extend Markdown and sidecar conservation so a version-1 finding cannot omit a Pattern or present a different canonical pattern in the human record and its sidecar.
- [x] Replace the summarizer's duplicated current-payload predicate with the exported schema classifier. Route versionless worker-shaped records through a compatibility aggregation adapter that preserves their worker, lens, finding, and triage metrics; retain the existing generic legacy normalization path for other historical records.
- [x] Define separate worker-ID and lens-ID collections. Make five-worker growth eligibility use the worker IDs from the validator's full-panel contract; derive lens telemetry only from `panel[].lenses` and add the realistic five-worker regression fixture.
- [x] Run → expect GREEN: both script self-test commands pass, including the new positive, negative, and compatibility cases.
- [x] Commit: `review: version sidecar contracts`

### Task 3: Align shared review guidance and evidence ownership

Files:

- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-agents/SKILL.md`
- `agents/skills/review-agents/consistency.md` *(new)*
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/implementation.md`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/simplification.md`
- `README.md`

- [x] Document the complete version-1 top-level contract in the gold-source staging schema and plan-review inline schema: required `schema_version`, `review_type`, `date`, `artifact_slug`, `round`, `panel_mode`, `selection_reason`, `source_kind`, `source_digest`, `escalation_reason`, `counts`, `panel`, `deduplication_groups`, `discarded`, `severity_calibration`, `triage_outcomes`, `findings`, `overflow`, and `soften_watchlist`; optional `depth`, `domains`, and object-valued `extensions`. State each field's type and nullable enum behavior, then document canonical `lens#kebab-slug` IDs, historical compatibility, and the reserved extension boundary.
- [x] Add the `consistency` catalog for abstract plan or RFC contradictions, stale cross-references, source-of-truth drift, and invalid validation claims. Keep runtime bugs, test gaps, and wiring gaps with their existing lead lenses.
- [x] Preserve simplification's short body tags for readability, but define their canonical sidecar Pattern ID mapping, such as `shrink:` to `simplification#shrink`, so active producers comply with the strict contract.
- [x] Require testing findings about test quality to state the behavior under test, distinct expected outcome, assertion that would fail if behavior disappeared, and harness layer when applicable.
- [x] Require implementation findings about runtime wiring to trace definition, registration or configuration, runtime discovery, and the test or other evidence that proves the live path. Preserve testing as the lead for weak or missing tests.
- [x] Make the code-review orchestrator reject or relaunch noncanonical worker pattern IDs before staging, and carry the structured evidence requirements into worker prompts.
- [x] Update the shared catalog index and README description without naming any project, person, organization, runtime path, or artifact-specific example.
- [x] Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest` passes after the guidance and schema examples use version 1.
- [x] Commit: `review: clarify evidence ownership`

### Task 4: Verify the integrated contract and public hygiene

Files:

- All files in this plan's explicit must-fix scope

- [x] Run `python3 scripts/validate_review_staging.py --selftest`; expects every legacy, typed-field, schema-version, pattern, panel, and conservation check to pass.
- [x] Run `python3 scripts/summarize_review_stats.py --selftest`; expects the aggregation adapter and validator classification canary to pass.
- [x] Run `git diff --check`; expects no whitespace errors.
- [x] Run `( cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )`; expects exit code 0 and no sensitive or project-specific additions.
- [x] Commit: `review: verify artifact contract updates`
