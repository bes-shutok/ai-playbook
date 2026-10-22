# Plan: Review Staging Schema Scaffold and Validation Reuse

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-15-review-staging-sidecar-scaffold-hand-filled-sections.md`
- `docs/history/backlog/2026-10-08-review-staging-ancestor-validation-cache.md` (disposition: defer as separate performance work)
Driving force: automation
Plan review record: `.ai-playbook/reviews/2026-10-19-plan-review-review-staging-schema-scaffold-and-validation-reuse-pded94402-r*.md`
Authoring claim: `docs/tmp/authoring-claims/2026-10-15-review-staging-sidecar-scaffold-hand-filled-sections.md` (session `01a1501c-2267-70b3-9423-7dd6ba3e4dd8`)

## Terms

- **Scaffold:** optional JSON output marked `mode: scaffold`, with a current-v1 plan-review sidecar template and explicit placeholders for caller-specific values; it carries no record-validation outcome.
- **Hand-filled sections:** sidecar fields named in the scaffold backlog origin: coverage, panel rows, triage outcomes, deduplication groups, extensions, soften watchlist, inherited coverage, and omission of empty arrays.
- **Schema descriptor:** validator-owned metadata for unconditional current-v1 field presence, types, allowed local keys, and nested shapes; `usage` is allowlisted without descriptor-owned value-shape validation and keeps its shape with the capture module. Validation and scaffold generation read the same descriptor, while date-conditioned presence stays with its procedural owner.
- **Sidecar:** the `.stats.json` JSON record accompanying each staging Markdown file; the contract the validator enforces.
- **Current-v1:** the current version-1 sidecar record class the validator dispatches on.
- **Preflight:** the lint-level validation pass a round runs before it is reported complete.
- **Material lens set:** the coverage object's list of lenses whose findings the round materially relied on.
- **Telemetry witness:** the embedded selftest evidence that a command mode appends to, or leaves untouched, the isolated invocation-telemetry metrics log.

## Why

Review authors lost multiple preflight rounds in two separate cycles to coupled fields that are hard to discover from refusal messages. A read-only scaffold generated from the validator's own schema can show those couplings before authors spend a round correcting them.

## Gist & Examples

TLDR: generate an optional sidecar scaffold from the validator's schema, reducing repeated authoring retries through automation.

For example, the scaffold shows that a clean coverage record carries its material lens set and coverage lists together, and that an inherited-coverage row has the shape required by the validator. Empty optional arrays are visibly omitted where the schema requires omission. Authors fill the caller-specific values and still run the existing preflight and hard validation modes.

## Outcome

The validator can emit an optional, read-only current-v1 sidecar scaffold marked as scaffold output, without implying that a record was validated; its hand-filled shapes agree with the schema it enforces.

- Review authors can see the required and coupled sidecar shapes before their first preflight.
- Existing validation invocations retain their exit codes, stdout, stderr, and findings.
- The skill points authors to generated guidance without maintaining another schema table.

Gate delta: no new refusal class, hard gate, sidecar field, required ceremony, or blocking review duty. Consolidate existing validator structural declarations into one descriptor and add an optional read-only CLI output mode. Suppress invocation telemetry only for that mode; preserve it for all existing validation modes. Defer predecessor caching as a separate medium-priority performance optimization with no correctness consequence.

## Assumptions

- The validator remains the source of truth for the current-v1 sidecar contract; this follows the scaffold origin's stated preference and drift concern.
- The descriptor owns unconditional structural presence, type, allowed-key, and nested-shape rules except that `usage` remains allowlisted-only: the capture module owns its value shape, the scaffold omits it, and malformed usage values remain accepted by the validator. Date-conditioned field presence, cross-field semantics, Markdown/sidecar parity, linked-record checks, and delegated extension schemas keep their current procedural/schema owners. Triage outcome shape remains presence-only because both array and object forms are accepted today.
- Scaffold generation is optional, emits a JSON envelope marked `mode: scaffold` on stdout without a record-validation `outcome`, does not write files or invocation telemetry, and does not validate records. When `--scaffold` is present it selects the scaffold path without adding a combination-specific refusal; all existing validation behavior remains unchanged when the flag is absent.
- The two origins are grouped for discovery, but caching is deferred because its origin records no correctness consequence and explicitly postpones it until extension or measured need; shared file ownership alone does not make it a smaller change.
- Sources inspected: both backlog origins, `docs/history/backlog/PLAN-PROMPTS.md`, `agents/skills/review-staging/SKILL.md`, `scripts/validate_review_staging.py`, `scripts/OUTCOME_CONTRACT.md`, and the history of commits `9d6cdc751` and `90a36850e`.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep the validator's schema descriptor as the single source of truth; scaffold output and validation consume it.
- Preserve all existing CLI modes and contracts. The new output mode is additive, optional, read-only, and non-blocking.
- Do not add a manually maintained schema inventory or duplicate operative schema prose in the skill.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: structural shapes and presence defaults agree with the shared descriptor; existing procedural and delegated semantic checks retain their current behavior.
- Compatibility: existing invocation modes preserve exit codes, output channel and outcome contracts for valid, findings-bearing, usage-error, unreadable-input, and JSON cases. Help and usage text may additionally name `--scaffold`.
- Maintainability: changing the schema descriptor changes both validation and scaffold output without editing a second field inventory.
- Usability: the scaffold covers every hand-filled section named in the origin and lets an author identify where caller values belong.

**Done when:**
- The optional scaffold command emits the current-v1 sidecar shape with `mode: scaffold` and no validation outcome; fixture snapshots and the isolated telemetry witness prove it does not touch files or change validation results.
- Embedded selftests prove the listed hand-filled sections and omission/coupling cases are represented; advisory examples do not become new validator rules.
- Embedded selftests pin return code, stdout/stderr placement, and final outcome/JSON outcome for existing validation modes, and pin the no-file/no-telemetry behavior of `--scaffold`.
- The skill references the scaffold and removes at least as many operative bytes as it adds.

**Ship when:**
- No external release or deployment condition; local repository implementation only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py`

**Documentation:**
- `agents/skills/review-staging/SKILL.md`
- `scripts/OUTCOME_CONTRACT.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py` predecessor-walk caching; separate performance concern, explicitly deferred by its origin.
- Review-staging record validation behavior or any new blocking gate; neither is required for schema discoverability.

## Validation Commands

```bash
python3 scripts/validate_review_staging.py --selftest
python3 scripts/validate_review_staging.py --help
python3 scripts/validate_review_staging.py --scaffold
python3 scripts/test_plan_readiness.py
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh --files agents/skills/review-staging/SKILL.md scripts/validate_review_staging.py
```

### Task 1: Declare the current-v1 sidecar schema once and emit an optional scaffold

Context surface: the plan's Terms and Standing constraints; both are referenced, never restated.

Files:
- `scripts/validate_review_staging.py`

Primary class anchors:
- `validate_version1_payload` in `scripts/validate_review_staging.py`
- `validate_current_payload` in `scripts/validate_review_staging.py`
- `validate_coverage_contract` in `scripts/validate_review_staging.py`
- `_main` in `scripts/validate_review_staging.py`

- [x] Given a current-v1 canonical plan-review sidecar, expect one descriptor to own unconditional required/optional field presence, structural types, allowed local keys, and nested shapes except the allowlisted-only `usage` value, and `validate_version1_payload`, `validate_current_payload`, `validate_coverage_contract`, and scaffold generation to consume it [class: IMPLEMENTATION_REQUIRED]
- [x] Given date-conditioned field presence, other date fences, cross-field semantics, Markdown/sidecar parity, linked-record checks, delegated extension schemas, the capture-module-owned `usage` shape, or the shared container and row-shape gates in `validate_current_payload`, expect their existing procedural/schema owners to remain in place and retain their current validation behavior [class: IMPLEMENTATION_REQUIRED]
- [x] Descriptor consumers: given the versionless mistyped-container family the validator's selftests already pin, expect those pins to stay green under the descriptor consolidation. [class: REPOSITORY_TEST]
- [x] Given a `usage` key with a malformed value, expect the validator to continue accepting it as allowlisted-only, and expect the scaffold to omit the key rather than inventing a shape [class: REPOSITORY_TEST]
- [x] Given each accepted `triage_outcomes` representation, expect the existing validator to continue accepting both array and object forms while the scaffold's labeled example passes [class: REPOSITORY_TEST]
- [x] Given representative existing valid, findings-bearing, usage-error, unreadable-input, and JSON invocations, expect return codes, stdout/stderr placement, and final outcome contracts to match existing behavior; the help/usage synopsis may add the new flag [class: REPOSITORY_TEST]
- [x] Commit: `feat: declare the current-v1 sidecar descriptor` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Emit the optional read-only scaffold

Context surface: the plan's Terms and Standing constraints; both are referenced, never restated.

Files:
- `scripts/validate_review_staging.py`

Primary class anchors:
- `_main` in `scripts/validate_review_staging.py`

- [x] Given scaffold output, expect every unconditional descriptor-required key and structural shape to appear; account for conditionally present fields and label caller placeholders as unvalidated values [class: IMPLEMENTATION_REQUIRED]
- [x] Given scaffold output, expect current-v1 shapes for coverage and its lens lists, panel rows with per-row launch data, deduplication groups, optional `extensions`, soften watchlist, and inherited-coverage rows [class: IMPLEMENTATION_REQUIRED]
- [x] Given the scaffold's `triage_outcomes` example, expect it to be labeled recommended because the validator checks presence but accepts both array and object forms [class: IMPLEMENTATION_REQUIRED]
- [x] Given no soften rows, expect `soften_watchlist: []` to remain present; given no corrections extension, expect `extensions.corrections` to be absent, never null or an empty array [class: IMPLEMENTATION_REQUIRED]
- [x] Given `--scaffold`, expect a JSON envelope marked `mode: scaffold` with no record-validation `outcome` and a current-v1 plan-review template under `scaffold`, no filesystem or invocation-telemetry writes, and early scaffold dispatch without a new combination-specific refusal [class: IMPLEMENTATION_REQUIRED]
- [x] Given `--scaffold` with a positional valid path or with `--hard` and a valid path, expect the same scaffold-mode JSON envelope without a validation outcome and exit 0 with no validation or refusal output, proving early dispatch without presenting the record as validated [class: REPOSITORY_TEST]
- [x] Given the in-process telemetry selftest, expect cwd pinned to a fixture root and `invocation_telemetry.resolve_metrics_home` temporarily patched to a fresh temporary metrics directory; a try/finally restores both plus the telemetry-suppression flag on any exception [class: REPOSITORY_TEST]
- [x] Given ordinary validation and `--scaffold` calls in the telemetry selftest, expect the positive control to append only to the isolated metrics log while scaffold leaves that log unchanged through the production telemetry path [class: REPOSITORY_TEST]
- [x] Given the scaffold selftest fixture root, expect its path and content snapshot to remain unchanged across scaffold generation [class: REPOSITORY_TEST]
- [x] Given scaffold output with caller placeholders filled, expect a deterministic valid staging pair to pass existing hard validation while preserving the absent-corrections and advisory-triage rules; the filled pair's record date derives from the validator's own fence constants plus one day, never a frozen literal [class: REPOSITORY_TEST]
- [x] Given scaffold output with no caller value filled, expect existing hard validation to fail naming each placeholder field, and expect the scaffold's `source_digest` placeholder to not be valid hex, preserving the copy-through tripwire [class: REPOSITORY_TEST] (fold: the unfilled pin names the 11 gate-consumed placeholders; review_type, artifact_slug, counts.staged_findings have no record-free value gate and ride SCAFFOLD_LABELS)
- [x] Given the scaffold template, expect it to represent a record dated after every current fence: `record_kind`, the review-run-id and started-at mint pair or its fallback marker, and the four extended fields appear as labeled date-conditioned caller placeholders [class: IMPLEMENTATION_REQUIRED] (fold: record_kind and risk_signals carry canonical plan-review defaults; all date-conditioned fields are named in SCAFFOLD_LABELS)
- [x] Given bare `--scaffold` with no path and no other flags, expect exit 0 with the scaffold envelope; scaffold dispatch precedes the path-required gate; given `--scaffold --newest-for-branch`, expect the scaffold envelope [class: REPOSITORY_TEST]
- [x] Outcome posture: given `--scaffold`, expect a metadata-mode exit with no final `OUTCOME:` line (JSON envelope only), matching the selftest precedent, with the validate_review_staging.py row in `scripts/OUTCOME_CONTRACT.md` updated to name it [class: IMPLEMENTATION_REQUIRED]
- [x] Run the validator's embedded selftests; expect all existing schema and new scaffold checks to pass [class: REPOSITORY_TEST]
- [x] Commit: `feat: emit validator-owned review sidecar scaffold` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Replace repeated schema instructions with a generated-scaffold pointer

Context surface: the plan's Terms and Standing constraints; both are referenced, never restated.

Files:
- `agents/skills/review-staging/SKILL.md`

- [x] Given the review-staging authoring recipe, expect authors to use the optional `--scaffold` mode, fill caller values, and still run current preflight/hard gates [class: IMPLEMENTATION_REQUIRED]
- [x] Given the authoring recipe, expect the generated scaffold to be the source for structural shapes only; retain or point to skill guidance for date-conditioned and semantic requirements the descriptor does not represent [class: IMPLEMENTATION_REQUIRED]
- [x] Given the schema-contract prose, expect the competing “schema of record” claim and duplicate operative structural inventory to be removed, and the replacement pointer to delete at least as many operative bytes as it adds [class: IMPLEMENTATION_REQUIRED]
- [x] Given the embedded minimal-valid pair, expect it to remain only as a non-operative selftest fixture; the authoring instructions must direct users to the generated scaffold rather than copying its sidecar shape [class: IMPLEMENTATION_REQUIRED]
- [x] Given the fixture pair and its validator selftest, expect it to remain valid under the current descriptor [class: REPOSITORY_TEST]
- [x] Given the scaffold output, expect a scripted field-presence check to find every origin-listed hand-filled section, backed by Task 1's embedded selftests and the filled-scaffold-passes-hard-validation run [class: REPOSITORY_TEST]
- [x] Commit: `docs: point review authors to generated sidecar scaffold` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

- testing#missing-gate-needle: folded
- documentation#missing-outcome-contract-update: folded
- implementation#descriptor-consumer-misanchor: folded
- testing#scaffold-lags-date-fences: folded
- security#scaffold-bare-invocation-unpinned: folded
- quality#incomplete-state-restore-witness: folded
- implementation#sibling-import-surface-unpinned: folded
- simplification#delete: folded
- documentation#prose-terms-coverage: folded
- consistency#stale-cross-reference: folded
- consistency#validation-battery-missing-em-dash-scan: folded
- security#telemetry-witness-restore-not-exception-safe: folded
