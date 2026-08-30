# Plan: Validator contract-enforcement gates (r6 F5 + F8 + F13)

Backlog source: `docs/history/backlog/2026-08-28-validator-contract-enforcement-gaps.md`
(findings F5, F8, F13 from the 2026-08-28 review-artifact-contracts r6 code review;
validated as real gaps, deliberately deferred 2026-08-28). Requirements buffer:
`docs/tmp/plan-requirements-validator-contract-gates.md`.

## Terms

- **Schema label**: the string returned by `classify_sidecar_schema(payload)` (for example `current-v1`, `legacy-panel-mode`, `unsupported`); it keys the mistyped-container error disposition in the shared `_require_array` / `_require_object` guards.
- **Version-1 payload validator**: `validate_version1_payload`; enforces the version-1 top-level contract for records classified `current-v1` only.
- **Current-payload validator**: `validate_current_payload`; runs for every current shape (version-1 and versionless current records); owns the per-finding gates and the order/budget checks.
- **Findings loop**: the `for finding in findings:` loop inside `validate_current_payload` that gates each sidecar finding row.
- **Order check**: `validate_finding_order`; sorts dict rows by `(severity_rank, row.get("id", 0))` and errors on disorder.
- **RED / GREEN**: a selftest fixture that fails before its gate exists (RED) and passes after (GREEN); executed via `python3 scripts/validate_review_staging.py --selftest`.
- **Skill-gate marker**: consent marker at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`; refresh per `ai-playbook/agents/hooks/skill-gate/README.md` before every plan-file write. Consumed only when this plan file itself is amended mid-execution; no implementation task touches it.
- **Session key**: `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; empty-after-strip collapses to the literal `no-session`; otherwise `sha1(value)[:16]` hex. Same mid-execution-amendment scope as the marker.

## Assumptions

- assume the F5 id gate also rejects an absent `id`; basis: the version-1 table states every findings row carries `id` (integer), and `id` is absent from `REQUIRED_CURRENT_FINDING_FIELDS` only because no gate existed, so absence silently sorts as `0` today.
- assume boolean ids are rejected (`isinstance(fid, int) and not isinstance(fid, bool)`); basis: `bool` is an `int` subclass in Python and the blocking field already uses the "real Python bool" idiom in the same loop.
- assume an explicit JSON `null` for optional `depth` / `domains` is rejected; basis: omission is the documented absent form and the r5 F1 comment pins null-as-absent compatibility to versionless records only.
- assume the date gate is shape-only (`^\d{4}-\d{2}-\d{2}$` on a string), with no calendar-validity check; basis: the documented contract is the string format and the backlog asks for "lightweight type checks".
- assume `is_current_shape` stays exported and unchanged; basis: `scripts/summarize_review_stats.py` line 2491 depends on it and its docstring pins the "one exported predicate" contract.
- assume new fixtures land in the existing selftest families rather than a new harness; basis: `_selftest_current_contract` and `_selftest_versioned_schema_and_patterns` are the established fixture homes with reusable base-payload helpers.
- assume base branch = current `main` (post fence-scanner merge `0553af9`); basis: the merge landed 2026-08-29 and every line anchor in this plan was re-verified against that state.

## Gist & Examples

Three documented contracts in the review-staging validator are not enforced, so invalid sidecars pass silently or crash with a traceback instead of producing a targeted error. This plan adds the three missing gates as one deliberate pass. No documentation changes: the contract sources already state the rules, and review-plan line 102 already claims the validator "catches string-vs-integer finding ids", which becomes true with this work.

**F5, integer finding ids.** The version-1 table (review-staging SKILL.md) and the plan-review inline schema (review-plan SKILL.md line 93) require `id` to be an integer, but nothing type-checks it. Two failure shapes today:

- homogeneous string ids (`"id": "F1"`, `"id": "F2"` at the same severity) compare fine as strings, so the order check passes silently;
- mixed ids (`"id": "F1"` plus `"id": 2` at the same severity) raise `TypeError` inside `sorted` in `validate_finding_order`, surfacing as a traceback instead of a validator error.

After: the findings loop rejects a missing id, a non-integer id, and a boolean id with one targeted error each, and the order-check call site passes only rows whose ids passed that gate, so mixed-type ids can never reach the sort.

**F8, scalar and optional field types.** The version-1 table documents `date` as string `YYYY-MM-DD`, `review_type` and `artifact_slug` as strings, optional `depth` as a string, and optional `domains` as a list. The validator checks presence, the r5 F1 null carve-out, and container shapes only. A numeric date or a string `domains` passes hard and the summarizer silently buckets the review into `unspecified` cohorts. After: each of those fields gets a lightweight type (and, for `date`, shape) gate in `validate_version1_payload`.

**F13, one classification per run.** One validation run classifies the same payload three times: `validate_stats_sidecar` computes `schema_class`, `is_current_shape(payload)` re-classifies inside the predicate, and `validate_current_payload` computes `schema_label` under a comment claiming the label "is computed ONCE". After: `validate_stats_sidecar` classifies once, derives `is_current` by comparing the label to `CURRENT_SHAPE_LABELS`, and threads the label into `validate_current_payload` as a keyword-only parameter (default `None` keeps the internal classification for direct callers, so the exported function stays backward compatible).

**Edge cases folded into the gates:** absent `id` (today silently sorts as `0`); `True` as an id (passes a naive `isinstance(fid, int)` check); explicit `null` for optional fields (today ignored); absent optional fields (must stay valid; r4 F14 absent-stays-absent); `round` staying dual-typed string-or-integer per the doc (must stay valid).

## Evaluation Criteria

**Quality dimensions:**

- Correctness: each new gate emits a targeted error (never a traceback) for its mistyped input; mixed-type ids can no longer reach the order-check sort; every gate error names the offending finding or field.
- Regression safety: `python3 scripts/validate_review_staging.py --selftest` exits 0 after every task; every pre-existing selftest family stays green, including the positive v1 and current-shape fixtures that prove the gates do not over-fire.
- Fail-closed posture: gates are additive; valid artifacts (the selftest corpus, including the producer-artifacts family) still validate.
- Single classification: a counting probe observes exactly one `classify_sidecar_schema` call per `validate_staging_file` run (three today).

**Done when:**

- All tasks complete; the full selftest exits 0 with the new RED-derived fixtures green.
- The backlog item is moved to `docs/history/backlog/completed/`.

**Ship when:**

- The next consumer skill run (review-plan, doing-code-review, execute-plan Phase 3, review-loop) exercises the hardened validator through its existing mechanical gate; no deploy step exists for this repo-scoped script.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/validate_review_staging.py`, partially in scope; exactly these regions:
  - `validate_current_payload` (def ~1066): signature (new keyword-only `schema_label` parameter), the findings loop, and the order-check call site (~1171 to ~1216)
  - `validate_stats_sidecar` (def ~937): the classification chain (~972 to ~990)
  - `validate_version1_payload` (def ~820): the new type-gate section next to the null gate
  - the `V1_*` constants block (~78 to ~102): one new `V1_DATE_RE` constant

**Tests:**

- `scripts/validate_review_staging.py` selftest families (same file):
  - `_selftest_current_contract` (def ~2119): F5 fixtures and the F13 counting probe
  - `_selftest_versioned_schema_and_patterns` (def ~3424): F8 fixtures

**Freeze note:** all other functions in `scripts/validate_review_staging.py` are frozen; reject any review finding that touches them. Specifically frozen because this plan depends on them unchanged: `validate_finding_order` (sort-input homogeneity is enforced at its call site, which passes only rows whose ids passed the gate; the r6 F2 dict-rows filter is the precedent for filtering errored rows out of the sort; no defensive re-hardening inside the function), `is_current_shape` (exported predicate consumed by the summarizer), the fence-scanning stack (`classify_fence_lines` and both consumers, just consolidated by the merged fence-scanner plan), and the r5 F1 null-gate comment block (the new type gates are added beside it, not rewoven into it). Out-of-scope bug findings in frozen regions follow the standard rule: document as a backlog item with file, function, and one-line description; decline in-place fixes.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. A regression surfaced in `scripts/summarize_review_stats.py` by these gates is plan-related under this clause; unrelated summarizer work is not.

**Out of scope; reject unless plan-related:**

- `agents/skills/review-staging/SKILL.md` and `agents/skills/review-plan/SKILL.md`; reason: both documents already state the enforced contract, and this plan deliberately makes the existing review-plan line-102 claim true rather than rewording docs
- `docs/history/backlog/2026-08-29-fence-scanner-followups.md` and the remaining backlog items; reason: separate scheduled work, not this contract pass

## Design Invariants (CR Guard)

- **Fence-scanner consolidation is untouched.** `classify_fence_lines`, the single fence regex, the line-event vocabulary, and the partial fallback (r6 F3) were just merged in `0553af9`; this plan must not modify fence scanning in any consumer.
- **r5 F1 null carve-out preserved.** `selection_reason` / `escalation_reason` remain the only two fields where explicit `null` is the documented not-applicable form; the new type gates must not re-weave or weaken that null gate.
- **r4 F14 absent-stays-absent preserved.** Optional fields (`depth`, `domains`, `extensions`) stay valid when omitted; only present-but-mistyped values are rejected.
- **r6 F2 non-dict row skip preserved.** `validate_finding_order` compares only dict rows; the new id gate fires in the findings loop after the `isinstance(finding, dict)` continue, so non-dict rows still produce exactly the upstream "must be an object" error and nothing else.
- **Exported-predicate contract preserved.** `is_current_shape` keeps its signature, docstring, and behavior; the summarizer's `vrs.is_current_shape(payload)` call (line 2491) is unaffected.
- **Targeted errors, never tracebacks.** Every new rejection follows the established r4 F10 / r6 F2 pattern: a `result.add_error(...)` with the offending value or field named, in the same function that owns the contract.
- **Backward-compatible public function.** `validate_current_payload` gains `schema_label` as a keyword-only parameter defaulting to `None`; `None` means classify internally, so direct callers (today: none outside `validate_stats_sidecar`) keep working.
- **Dual-typed `round` stays legal.** The doc explicitly allows `round` as string or integer; no gate may narrow it, and a fixture pins both forms as valid.

## Validation Commands

```bash
python3 scripts/validate_review_staging.py --selftest && echo "SELFTEST OK"
```

Single canonical executable artifact: the selftest registers every family, including the new fixtures, and its exit code is the verdict. It is bidirectional for this plan: RED fixtures prove the gates exist, and the pre-existing positive fixtures (complete v1 sidecar, clear current-shape review) prove the gates do not over-fire on valid artifacts.

## Tasks

### Task 1: F5 RED fixtures, finding-id gates

Files:

- `scripts/validate_review_staging.py` (selftest family `_selftest_current_contract` only)

All four fixtures follow one setup recipe: render the staging markdown from the unmutated two-finding list first, then mutate the sidecar payload, then `_write_staging(root, name, md, payload)`; this keeps fixture failures attributable to the gate under test instead of garbled-header conservation noise.

- [x] `_selftest_current_contract#finding id missing rejected`: given a payload built from `_payload_with_findings([_current_finding(id=1), _current_finding(id=2)])` whose sidecar payload has `findings[1]`'s `id` key removed, with the staging markdown rendered from the unmutated list first (`md = _current_findings_markdown([...])`, then mutate the payload, then `_write_staging(root, name, md, payload)`), expects `validate_staging_file(..., hard=True)` to report a targeted error from the new findings-loop gate containing the phrase `missing id`; the pre-existing conservation error for `id None` is expected noise and must not satisfy the assertion (the base `_current_clear_payload()` ships `"findings": []`, so fixtures must add rows through these helpers, never index into the base list)
- [x] `_selftest_current_contract#finding id string rejected`: given a homogeneous string-id payload (`findings[0]["id"] = "F1"` AND `findings[1]["id"] = "F2"`, shared default severity), expects a targeted id-must-be-an-integer error per row; homogeneous strings keep every sort key tuple same-kind, so neither phase may crash the sort (this is the Gist's silent-pass failure shape)
- [x] `_selftest_current_contract#finding id bool rejected`: given `_payload_with_findings([_current_finding(id=1), _current_finding(id=2)])` with `findings[0]["id"] = True` (sibling id pinned at 2 so sort keys are deterministic by construction, not by stable-sort tie-breaking), expects the same integer-type error (bool is not accepted as integer)
- [x] `_selftest_current_contract#finding id mixed types never crash the sort`: given a two-finding payload at one shared severity with `findings[0]["id"] = "F1"` and `findings[1]["id"] = 2`, calls `validate_staging_file(..., hard=True)` inside `try` / `except TypeError` (mirroring the Task 5 probe's restore discipline) so a RED-phase crash records a FAIL for this check instead of aborting the whole suite, and expects post-gate the id-type error to be present AND no `TypeError` to propagate
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect RED: the missing-id check fails with the pinned `missing id` phrase absent (the conservation error alone must not turn it green); the homogeneous-string and bool checks fail error-absent (both are sort-safe today because their key tuples stay same-kind); the mixed-types check records FAIL via the caught `TypeError`
- [x] Commit: `test: finding-id type-gate fixtures (RED)`

### Task 2: F5 GREEN, id gate in the findings loop

Files:

- `scripts/validate_review_staging.py` (`validate_current_payload` findings loop)

- [x] Add the id gate to the findings loop immediately after `fid = finding.get("id")`, before the severity gate: absent id, non-int id, and bool id each produce one targeted `result.add_error(...)` naming the finding; the absent-id message contains the phrase `missing id` and the mistyped-id message the phrase `must be an integer`, so the Task 1 fixtures pin those phrases and cannot be satisfied by conservation noise; the loop continues gating the remaining fields so one run reports all finding-level defects
- [x] At the order-check call site, pass only gate-passing rows so an error-only gate cannot leave mixed-type ids in the sorted list: build `valid_rows = [f for f in findings if isinstance(f, dict) and isinstance(f.get("id"), int) and not isinstance(f.get("id"), bool)]` and call `validate_finding_order(valid_rows, result)`; `validate_finding_order` itself is not edited (frozen; its own dict-rows filter already skips non-dict rows, so substituting the pre-filtered list is behavior-preserving for valid artifacts)
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN for all families, including Task 1 fixtures and the pre-existing positive current-shape fixtures
- [x] Commit: `fix: enforce integer finding ids before the order check (r6 F5)`

### Task 3: F8 RED fixtures, version-1 scalar and optional type gates

Files:

- `scripts/validate_review_staging.py` (selftest family `_selftest_versioned_schema_and_patterns` only)

- [x] `_selftest_versioned_schema_and_patterns#v1 date numeric rejected`: given a `_version1_payload()` copy with `date = 20260829`, expects a targeted date-type error pinned on `'date'` plus `must be a string`
- [x] `_selftest_versioned_schema_and_patterns#v1 date malformed string rejected`: given `date = "2026-8-9"`, expects a targeted date-format error pinned on `'date'` plus `YYYY-MM-DD`
- [x] `_selftest_versioned_schema_and_patterns#v1 review_type and artifact_slug mistyped rejected`: given `review_type = 7` in one copy and `artifact_slug = []` in another, expects a targeted string-type error for each, pinned on the field name plus `must be a string`
- [x] `_selftest_versioned_schema_and_patterns#v1 optional depth mistyped rejected`: given `depth = []`, expects a targeted string-type error pinned on `'depth'` plus `must be a string`
- [x] `_selftest_versioned_schema_and_patterns#v1 optional domains mistyped rejected`: given `domains = "api"`, expects a targeted list-type error pinned on `'domains'` plus `must be a list`
- [x] `_selftest_versioned_schema_and_patterns#v1 optional explicit null rejected`: given `depth = None`, expects a targeted error pinned on `'depth'` plus `must be a string` (explicit null is not the absent form for optional version-1 fields)
- [x] `_selftest_versioned_schema_and_patterns#v1 optional domains explicit null rejected`: given a `_version1_payload()` copy with `domains = None`, expects a targeted error pinned on `'domains'` plus `must be a list`, mirroring the depth-null case (pins the domains half of the optional null-rejection assumption with its own fixture)
- [x] `_selftest_versioned_schema_and_patterns#v1 optional absent stays valid`: given copies with `depth` and `domains` keys removed entirely, expects `validate_staging_file(..., hard=True).ok` to stay True (over-gating guard)
- [x] `_selftest_versioned_schema_and_patterns#v1 round dual typing stays valid`: given one copy with `round = 3` and another with `round = "r3"`, expects both to stay `.ok` (dual-typing guard)
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect RED: the eight negative cases across the seven checks fail error-absent; the two guards already pass and must keep passing
- [x] Commit: `test: version-1 scalar and optional type-gate fixtures (RED)`

### Task 4: F8 GREEN, type gates in validate_version1_payload

Files:

- `scripts/validate_review_staging.py` (`validate_version1_payload`, `V1_*` constants block)

- [x] Add `V1_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")` beside the existing `V1_*` constants
- [x] Add the type-gate section beside the null gate: `review_type`, `artifact_slug`, and `date` (each required; each skips `None` so the r5 F1 null gate stays the single reporter for explicit-null required fields), with `date` additionally requiring the `V1_DATE_RE` string shape; `depth` (optional, string when the key is present), `domains` (optional, list when the key is present); the optional gates fire on any present value including explicit null, and only the three required gates skip null in favor of the r5 F1 reporter; every rejection is a targeted `result.add_error(...)` naming the field with `{field_name!r}` plus the expected type phrase (`must be a string` for the string gates, `must be a list` for domains, and `YYYY-MM-DD` in the date-format message), following the family's existing `{field_name!r} must be an array` pin idiom so the Task 3 fixtures can pin gate-specific substrings
- [x] The gates must not widen the r5 F1 null carve-out and must not touch the fence scanning or any frozen function
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN for all families, including Task 3 fixtures and the family's pre-existing positive v1 fixture
- [x] Commit: `fix: enforce version-1 scalar and optional field types (r6 F8)`

### Task 5: F13 RED probe, single classification per run

Files:

- `scripts/validate_review_staging.py` (selftest family `_selftest_current_contract` only)

- [x] `_selftest_current_contract#sidecar payload classified exactly once per run`: given the family's valid staging doc plus sidecar (`_write_staging` with `_current_clear_payload()`), temporarily rebind the module attribute `classify_sidecar_schema` with a counting wrapper that delegates to the original, run `validate_staging_file(..., hard=True)` once, restore the original in a `finally` block, and expects the counted calls for that run to equal exactly 1
- [x] Feasibility note (verified against the real file): the three production call sites (`validate_stats_sidecar` ~972, `is_current_shape` ~740 reached from ~981, `validate_current_payload` ~1084) all resolve the module global at call time, so the rebinding intercepts all three; no other `classify_sidecar_schema` call exists on this path
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect RED: the probe counts 3, not 1
- [x] Commit: `test: single-classification probe for sidecar validation (RED)`

### Task 6: F13 GREEN, classify once and thread the label

Files:

- `scripts/validate_review_staging.py` (`validate_stats_sidecar` chain, `validate_current_payload` signature)

- [x] `validate_stats_sidecar`: replace `is_current = is_current_shape(payload)` with `is_current = schema_class in CURRENT_SHAPE_LABELS`, and pass `schema_label=schema_class` into the `validate_current_payload(...)` call
- [x] `validate_current_payload`: add keyword-only `schema_label: str | None = None`; when `None`, classify internally exactly as today (backward-compat default); when provided, use it instead of calling `classify_sidecar_schema`
- [x] Update the "computed ONCE" comment above the old internal classification so it states the run-level contract: the label is computed once in `validate_stats_sidecar` and threaded in; the internal path exists only for direct callers
- [x] `is_current_shape` itself is not edited (exported predicate; summarizer dependency)
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN for all families, including the Task 5 probe now counting exactly 1
- [x] Commit: `fix: classify sidecar schema once per validation run (r6 F13)`

### Task 7: Backlog bookkeeping

Files:

- `docs/history/backlog/2026-08-28-validator-contract-enforcement-gaps.md`
- `docs/history/backlog/completed/2026-08-28-validator-contract-enforcement-gaps.md` *(moved)*

- [x] `git mv docs/history/backlog/2026-08-28-validator-contract-enforcement-gaps.md docs/history/backlog/completed/` and mark the item complete in its Status line per the file's own workflow note
- [x] Commit: `docs: move validator-contract-enforcement-gaps backlog to completed`

### Task 8: Final scoped verification

Files: none (verification only)

- [x] Run the full `## Validation Commands` block → expect `SELFTEST OK` (exit 0)
- [x] `git status --short` → expect clean after Task 7's commit; no untracked residue in `scripts/`
