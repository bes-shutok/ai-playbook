# Plan: review-runner bounded timeout fallback and coverage accounting

Backlog origin: `docs/history/backlog/2026-09-14-review-runner-bounded-timeout-fallback.md` (scope of record).
Language guidelines: `projects/.ai-playbook/python_guidelines.md` (applies to both validator tasks).
Reviews: `docs/reviews/2026-09-14-plan-review-review-runner-bounded-timeout-fallback-r*.md` (prefix; sidecar `.stats.json` same basename).

## Terms

- **Attempt**: one bounded launch of one worker instance (initial launch, bounded retry, or replacement launch). A worker that is retried produces multiple attempts; `panel[]` keeps exactly one terminal row per worker, and attempt lineage lives in the coverage object.
- **Attempt outcome**: enum `complete`, `failed`, `timeout`, `cancelled`, `malformed-output` (backlog vocabulary). A distinct axis from the existing `panel[]` row status vocabulary: the strings `complete`, `failed`, and `timeout` appear in both vocabularies and are interpreted per axis (a `timeout` panel row and a `timeout` attempt record are different records), while `cancelled` and `malformed-output` are outcome-only; nothing asserts cross-axis uniqueness.
- **Failure class**: why an attempt ended abnormally: `provider-timeout`, `usage-rate-limit`, `worker-crash`, `orchestrator-wait-timeout`, `parse-failure`, `data-error`, plus the admission class values `capacity-denied`, `concurrency-limit`, `provider-unavailable`, `stale-release-suspected`, `unknown` (an admission-denied attempt that never started records outcome `failed` with the admission class as its failure class). Required for outcomes `failed` and `malformed-output`; recorded when known for `timeout`; a `cancelled` attempt carries no failure class (cancellation is recorded in the outcome alone), and `complete` carries none.
- **Admission state / admission error class**: whether a backend worker slot could start this attempt (`admitted`, `denied`, `saturated`, `unknown`); error class `capacity-denied`, `concurrency-limit`, `provider-unavailable`, `stale-release-suspected`, `unknown`.
- **Usage state**: account allowance in the current window (`available`, `exhausted`, `near-threshold`, `unknown`). Separate signal from admission; one may be available while the other is not.
- **Retry budget**: fixed, configuration-visible cap on bounded retries per worker (`retry_budget.per_worker_max`); each bounded wait consumes one unit; exhaustion is recorded with its reason.
- **Panel wall-clock ceiling**: fixed total budget for the panel's attempts; never extended silently by retries or replacements.
- **Material lens**: a lens this round owns as material, declared explicitly in `coverage.material_lens_set` (full panel: the five base workers' required lenses; focused round: the lenses named in `selection_reason` plus any carried missing lens). The validator never infers materiality from lens names.
- **Coverage object / coverage outcome**: new date-fenced required version-1 sidecar top-level field `coverage`; `coverage.outcome` is `clean`, `replacement-covered`, `degraded`, or `failed`.
- **Replacement record**: a `coverage.replacement[]` entry in the replacing round: the replaced lens, the original round's artifact and sidecar, and the original failure; the replacing round's own completion of the lens shows in `coverage.completed`.
- **Inherited coverage**: a `coverage.inherited_coverage[]` entry linking a lens completed by a prior round of the same review loop (artifact + sidecar), so the latest round's coverage can prove the whole material set.
- **Late result**: an original worker's `complete` attempt recorded after the round already moved to replacement coverage for that lens; it never flips the outcome back to `clean`.
- **Attempt ledger**: the `### Attempt ledger` subsection under `## Review Statistics` in the staging Markdown; one row per attempt, mirrored by `coverage.attempts[]`.
- **Report-only boundary**: the state where the runner stops making launch decisions and only records observations (attempt records, capacity states, lifecycle observations) for the exit report; no retries, no replacements, and no panel relaunch happen past it.
- **COVERAGE_SIDECAR_MIN_DATE**: validator constant fencing the coverage obligation; version-1 records dated on or after it must carry a valid `coverage` object when `source_kind` is `plan` (the only readiness-gated kind); earlier records and other source kinds are accepted-legacy and exempt (other producers may emit `coverage`, and it is validated when present).

## Assumptions

- assume the review runner is instruction-based: the orchestrating agent following `review-plan` and `review-loop` SKILL.md instructions, with the two validators as the mechanical gates; there is no daemon process to modify; basis: repo survey 2026-09-14 (both skills launch workers via agent instructions; neither validator models processes) and the backlog's verified implementation surfaces list.
- assume bounded-wait and retry constants are pinned as named constants in `review-plan/SKILL.md` with a measured rationale comment, following the limits-table precedent (`review-loop/SKILL.md` `max_full_panel_rounds`); no new config file; basis: the repo has no runner config surface and the limits table is the established home for run budgets.
- assume the machine-readable coverage state rides a new date-fenced required top-level `coverage` object in the version-1 sidecar contract, not the optional `extensions` bag, because the readiness gate must fail closed on its absence for post-constant records; basis: the four freshness fields precedent (the `EXTENDED_SIDECAR_MIN_DATE` fence comment block in `scripts/validate_review_staging.py`) is the established contract-evolution mechanism, and `extensions` is documented as never gated.
- assume pre-constant records stay readable and may satisfy `ready=yes` (date-fenced grandfathering); basis: the freshness-fields grandfathering comment in `validate_review_staging.py` and backlog decision 4.
- assume `COMPAT_VERSION` bumps 1 to 2 together with `EXPECTED_SIBLING_COMPAT_VERSION` in the same commit; basis: the constant's own rule ("bump it ONLY together with every consumer's expected constant", validator lines 225-228) and that fail-closed coverage rules change acceptance behavior.
- assume every sub-agent launch (initial attempt, bounded retry, replacement) counts toward the existing six-launch ceiling; basis: "A worker is one launched sub-agent" (`review-panel-selection.md` lines 21-25); this preserves the ceiling invariant instead of adding a parallel budget.
- assume attempt telemetry embeds in the sidecar `coverage` object as the one canonical owner; basis: acceptance criteria 1, 2, and 5 of the backlog name panel metadata and the sidecar; bounded volume (at most six launches times small records); single-producer precedent of the optional `usage` field.
- assume worker-facing prompt text stays tool-agnostic (no tool-specific names); basis: repository AGENTS.md tool-agnostic design rule.

Decision points requiring a grill: initial timeout, retry budget, and wall-clock values: resolved as a pinned procedure - Task 1 measures the staged corpus, Task 3 pins the constants with rationale comments and conservative fallbacks (per-attempt 15 minutes, retry budget 2 per worker, ceiling 120 minutes) as recommended options accepted per standing pre-authorization in the scheduling prompt, 2026-09-14; affects Tasks 1 and 3; attempt telemetry home: resolved as the embedded `coverage` object in the sidecar with review-staging as the single contract owner; recommended option accepted per standing pre-authorization in the scheduling prompt, 2026-09-14; affects Tasks 2 and 5; replacement mapping and minimum evidence: resolved as an independent focused replacement round with its own artifact and sidecar, linked back from `coverage.replacement[]`, with no-replacement recorded as incomplete; recommended option accepted per standing pre-authorization in the scheduling prompt, 2026-09-14; affects Task 4; legacy sidecar policy: resolved as date-fenced grandfathering where pre-constant records keep satisfying `ready=yes`; recommended option accepted per standing pre-authorization in the scheduling prompt, 2026-09-14; affects Tasks 2 and 7; degraded-versus-failed boundary: resolved as degraded meaning a completed review with at least one material lens uncovered (action: narrowed re-run or an explicit user risk acceptance recorded in triage outcomes) and failed meaning an untrustworthy result (action: repair staging or runner, then re-run); recommended option accepted per standing pre-authorization in the scheduling prompt, 2026-09-14; affects Tasks 2 and 5.

## Design Invariants (CR Guard)

- Five-worker panel composition and the six-launch ceiling are preserved; attempts, retries, and replacements each consume launch slots; nothing in this plan raises the ceiling or auto-relaunches the full panel.
- `validate_full_panel_completion` semantics are unchanged: failed, timed-out, and skipped rows count as launches but never as completed coverage. The coverage gates add obligations; they never relax an existing error.
- The verdict vocabulary keeps one owner (`VERDICT_VALUES` imported by consumers); the canonical verdict line grammar in `## Summary` is unchanged.
- Legacy and versionless sidecars stay readable: `classify_sidecar_schema` outcomes for legacy shapes are unchanged, and records dated before `COVERAGE_SIDECAR_MIN_DATE` remain exempt from the coverage gate.
- Existing artifact and sidecar safeguards are preserved: Markdown plus sidecar pair per round, source-digest binding, no hand-transcription into sidecars, stale artifacts not promotable by filename or summary, and the killed-worker audit-before-relaunch rule.
- The sibling compat handshake constants move in the same commit; no commit may leave the two validators disagreeing.
- The coverage gates have exactly one wiring home in the shared readiness path: the fence, allowlist entries, `validate_coverage_contract`, and `validate_replacement_links` live inside `validate_version1_payload` (the function `validate_stats_sidecar` calls, which is the readiness gate's only path), `validate_coverage_markdown_agreement` lives in `validate_stats_sidecar`; `validate_staging_file` consumes the same shared functions with no second wiring site.
- Attempt telemetry is sanitized: no prompts, authentication material, provider payloads, or review content that is not already part of the staged artifact.
- Skill text stays tool-agnostic; behaviors are described by intent, not by tool names.

## Gist & Examples

What changes: the review runner (the `review-plan` and `review-loop` skill instructions) gains bounded per-worker attempts with a fixed retry budget, explicit replacement-lens selection, and a machine-readable coverage outcome in every review sidecar; the readiness validator refuses `ready=yes` when material lens coverage is missing, ambiguous, or unlinked.

Why: the triggering certification run had a broader correctness and implementation auditor time out twice after bounded intervals while focused reviewers supplied replacement coverage; the final `ready=yes` rested on prose reasoning that no machine could re-verify. A subsequent attempt had every worker exceed two bounded waits, pointing at prompt breadth plus an undersized timeout budget rather than at the reviewed plan. The authoring-time census (2026-09-14) of 708 staged sidecars found 2402 `complete` rows, 2 `failed`, and zero `timed-out` rows: timeouts are invisible in panel accounting today, which is exactly the gap.

**Before (today):** `review-plan/SKILL.md` step 2 says "Launch all selected workers in parallel and wait for completion" - an unbounded wait. If a worker times out, the only record is a `panel[]` row status (or nothing at all for a stopped launch); there is no deadline, no failure class, no retry count, and no notion of how many attempts remain. A focused round with a timed-out worker carries only a prose `selection_reason`; the sidecar validator has no material-coverage model for it, so a `ready=yes` whose coverage came from replacement reviewers is indistinguishable, machine-wise, from a clean run. The operator reconstructs what happened from narrative.

**After (this plan):** every launch is a bounded attempt with a recorded deadline, outcome, failure class, usage state, admission state, and execution mode. A transient provider timeout consumes one unit of the fixed retry budget (default 2 per worker) and the attempt is retried with a fresh bounded wait; a malformed-output or parse failure is classified and not retried. Because five base launches commit a full panel's first five slots and the remaining slot is reserved for replacement, retries in practice proceed only in focused rounds; a full-panel timeout goes directly to replacement-or-missing. When a material worker stays unavailable after its budget, the runner selects an explicit replacement (a focused round with its own artifact and sidecar, linked back from `coverage.replacement[]`) or records the lens as missing. The sidecar's `coverage.outcome` distinguishes `clean`, `replacement-covered`, `degraded`, and `failed`; the readiness gate accepts `ready=yes` only when every declared material lens is covered by completion, a validly linked replacement, or validly linked inherited coverage - and the Markdown coverage line must agree with the sidecar.

Example (usage versus admission): an attempt record with `usage_state: available` and `admission_state: denied`, `admission_error_class: capacity-denied` means a capacity or lifecycle problem, not usage exhaustion. The runner records the capacity state, applies only the bounded capacity retry or pause rule, and never interprets the denial as usage exhaustion, never spends a usage reset, and never relaunches the whole panel. A stopped task that still shows a worker is recorded as `stale-release-suspected` and stops at the bounded retry or report-only boundary; the runner does not claim to release a backend worker no API can release and does not terminate unrelated user-owned tasks.

Example (degraded versus failed): a focused round where `testing` times out after its retry budget records `coverage.outcome: degraded` with `missing: ["testing"]` and verdict `no`; the user-visible action is a narrowed re-run or an explicit user risk acceptance recorded in triage outcomes. A round whose staging fails conservation checks records `failed` with verdict `no`; the action is to repair staging and re-run. Neither state can ever carry `ready=yes`.

Example (legacy): a sidecar dated before `COVERAGE_SIDECAR_MIN_DATE` without a `coverage` object still validates exactly as today; the coverage gate is date-fenced the same way the four freshness fields are, so in-flight automation has a grace window and no historical record is rewritten.

Mapping to the backlog's required task order: order items 1 through 6 map to Tasks 1 through 6 below, with order item 5's staging-validation half landing in Task 2 ahead of the Task 3 and Task 4 wiring (the validation-before-wiring ordering the backlog prescribes still holds). Order item 7 ("run a fresh five-worker review of the playbook changes, then document rollout and compatibility") is delivered by this plan's own certification review (a fresh five-worker `review-plan` panel on the final digest, exit only at zero blocking findings) plus `execute-plan`'s post-implementation review loop, and by Task 7's rollout and legacy-compatibility documentation; it is not duplicated as a checklist item, which the plans checklist inclusion gate classifies as review work owned by the execution workflow's review gate.

## Evaluation Criteria

**Quality dimensions:**
- correctness: `python3 scripts/validate_review_staging.py --selftest` and `python3 scripts/plan_readiness.py --selftest` exit 0 including the five new coverage families; the fail-closed direction is selftest-asserted in both directions (a degraded-outcome record with verdict yes must fail; a replacement-covered record with valid links must pass).
- reliability: every attempt record carries a bounded deadline and an outcome; the forbidden-text sweeps for unbounded waits stay green on the edited skills.
- observability: the panel timeline is reconstructable from the sidecar alone (attempt-ledger conservation family), without reading worker logs.
- maintainability: each contract surface has exactly one canonical owner; the inlined schema copy in `review-plan/SKILL.md` is updated in the same commit as the review-staging contract change.
- compatibility: legacy sidecars keep validating (pre-constant fixtures stay green); `COMPAT_VERSION` and `EXPECTED_SIBLING_COMPAT_VERSION` both equal 2 after Task 2.

**Done when:**
- Both validators' `--selftest` runs exit 0 with the five new families registered and green.
- The full `## Validation Commands` block exits 0 on the post-implementation tree.
- `COMPAT_VERSION = 2` in `scripts/validate_review_staging.py` equals `EXPECTED_SIBLING_COMPAT_VERSION = 2` in `scripts/plan_readiness.py`.
- The readiness gate demonstrably rejects `ready=yes` for degraded, failed, missing-coverage, and markdown/sidecar-disagreement fixtures dated on or after `COVERAGE_SIDECAR_MIN_DATE`, and accepts `clean` and validly replacement-covered fixtures.

**Ship when:**
- Scheduled review loops after this plan lands emit sidecars with a `coverage` object for records dated on or after the constant, witnessed by the Task 7 discriminating count (post-constant plan-source sidecars with versus without a coverage object); `plan_readiness.py --sweep`'s verdict-coverage line is context only.
- Downstream automation (execute-plan Phase 3 exit checks, maintenance runs) can branch on `coverage.outcome` without reading review prose. Human-owned: none.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-plan/SKILL.md` (bounded-attempt and retry sections, worker prompt narrowing, coverage production step, inlined sidecar schema block; all other sections frozen)
- `agents/skills/review-loop/SKILL.md` (timeout path, degraded/failed handling, exit report; all other sections frozen)
- `agents/skills/review-staging/SKILL.md` (coverage contract subsection, Markdown template Coverage line and Attempt ledger, legacy compatibility subsection; all other sections frozen)
- `agents/skills/review-agents/review-panel-selection.md` (replacement-lens selection section; all other sections frozen)
- `scripts/validate_review_staging.py` (new constants, `validate_coverage_contract`, `validate_replacement_links`, `validate_coverage_markdown_agreement`, coverage fence and allowlist entries in `validate_version1_payload`, coverage wiring in `validate_stats_sidecar`, `COMPAT_VERSION`, five new `--selftest` families and their registration; all other functions frozen)
- `scripts/plan_readiness.py` (`EXPECTED_SIBLING_COMPAT_VERSION`, coverage cases in `_selftest_accepted_state`; all other functions frozen)

**Tests:** none as separate files; the tests are the embedded `--selftest` families named under Production code above (families `_selftest_coverage_contract` and `_selftest_coverage_readiness_gate` in Task 2; `_selftest_replacement_and_late_results`, `_selftest_capacity_admission_lifecycle`, `_selftest_prompt_scope_accounting` in Task 6; `_selftest_accepted_state` coverage cases in Task 5).

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/quota_window_probe.py`; the existing usage-budget gate is consumed as-is, not modified.
- `scripts/review_usage_capture.py`; the token-usage capture module and its single-producer contract are unchanged.
- `README.md`; no skill is added or renamed, so the catalog is unchanged.
- `docs/plans/2026-09-13-maintenance-scheduler-skill.md`; an unrelated peer plan.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
fail() { echo "VALIDATION FAIL: $1"; exit 1; }
# Three-way-split no-match helper: rc 0 = forbidden match (fail), rc 1 = clean, rc >= 2 = tool error (fail).
expect_no_match() {
  pat="$1"; shift
  for f in "$@"; do
    rc=0; grep -qiE "$pat" "$f" || rc=$?
    if [ "$rc" -eq 0 ]; then fail "forbidden pattern '$pat' found in $f"; fi
    if [ "$rc" -ge 2 ]; then fail "grep error rc=$rc scanning $f"; fi
  done
}

# V1 (stays green): both validators' full selftests, existing families plus the five new coverage families.
python3 "$REPO/scripts/validate_review_staging.py" --selftest >/dev/null 2>&1 || fail "validate_review_staging --selftest not green"
python3 "$REPO/scripts/plan_readiness.py" --selftest >/dev/null 2>&1 || fail "plan_readiness --selftest not green"

# V2: sibling compat handshake moved atomically to 2.
grep -qF 'COMPAT_VERSION = 2' "$REPO/scripts/validate_review_staging.py" || fail "vrs COMPAT_VERSION is not 2"
grep -qF 'EXPECTED_SIBLING_COMPAT_VERSION = 2' "$REPO/scripts/plan_readiness.py" || fail "plan_readiness expected sibling compat is not 2"

# V3: coverage contract declared in review-staging with the date fence, outcome enum, attempt ledger, and coverage line.
grep -qF 'COVERAGE_SIDECAR_MIN_DATE' "$REPO/agents/skills/review-staging/SKILL.md" || fail "staging coverage min-date constant missing"
grep -qF '"clean", "replacement-covered", "degraded", "failed"' "$REPO/agents/skills/review-staging/SKILL.md" || fail "staging coverage outcome enum missing"
grep -qF '### Attempt ledger' "$REPO/agents/skills/review-staging/SKILL.md" || fail "staging attempt ledger section missing"
grep -qF 'Coverage: clean | replacement-covered | degraded | failed' "$REPO/agents/skills/review-staging/SKILL.md" || fail "staging Markdown coverage line missing"
grep -qF 'coverage obligation applies only when source_kind is' "$REPO/agents/skills/review-staging/SKILL.md" || fail "staging coverage source_kind scoping missing"
grep -qF 'must not include prompts, authentication material, provider payloads' "$REPO/agents/skills/review-staging/SKILL.md" || fail "staging telemetry sanitization rule missing"

# V4: validator implements the coverage gates (one dedicated grep per obligation).
grep -qF 'COVERAGE_SIDECAR_MIN_DATE = "2026-09-16"' "$REPO/scripts/validate_review_staging.py" || fail "validator coverage min-date constant missing"
grep -qF 'def validate_coverage_contract' "$REPO/scripts/validate_review_staging.py" || fail "validator validate_coverage_contract missing"
grep -qF 'def validate_replacement_links' "$REPO/scripts/validate_review_staging.py" || fail "validator validate_replacement_links missing"
grep -qF 'def validate_coverage_markdown_agreement' "$REPO/scripts/validate_review_staging.py" || fail "validator coverage markdown agreement missing"
grep -qF 'ATTEMPT_ALLOWED_KEYS' "$REPO/scripts/validate_review_staging.py" || fail "validator attempt key allowlist missing"
grep -qF '_selftest_coverage_contract' "$REPO/scripts/validate_review_staging.py" || fail "selftest family coverage_contract not registered"
grep -qF '_selftest_coverage_readiness_gate' "$REPO/scripts/validate_review_staging.py" || fail "selftest family coverage_readiness_gate not registered"
grep -qF '_selftest_replacement_and_late_results' "$REPO/scripts/validate_review_staging.py" || fail "selftest family replacement_and_late_results not registered"
grep -qF '_selftest_capacity_admission_lifecycle' "$REPO/scripts/validate_review_staging.py" || fail "selftest family capacity_admission_lifecycle not registered"
grep -qF '_selftest_prompt_scope_accounting' "$REPO/scripts/validate_review_staging.py" || fail "selftest family prompt_scope_accounting not registered"

# V5: review-plan wiring - bounded attempts, retry classification, usage/admission separation, coverage production.
grep -qF '### Bounded attempts and retry classification' "$REPO/agents/skills/review-plan/SKILL.md" || fail "review-plan bounded attempts section missing"
grep -qF 'DEFAULT_ATTEMPT_TIMEOUT_MINUTES' "$REPO/agents/skills/review-plan/SKILL.md" || fail "review-plan attempt timeout constant missing"
grep -qF 'DEFAULT_RETRY_BUDGET_PER_WORKER' "$REPO/agents/skills/review-plan/SKILL.md" || fail "review-plan retry budget constant missing"
grep -qF 'DEFAULT_PANEL_WALL_CLOCK_MINUTES' "$REPO/agents/skills/review-plan/SKILL.md" || fail "review-plan wall-clock constant missing"
grep -qF 'usage state and worker admission are separate signals' "$REPO/agents/skills/review-plan/SKILL.md" || fail "review-plan usage/admission separation missing"
grep -qF 'must not interpret a capacity denial as usage exhaustion' "$REPO/agents/skills/review-plan/SKILL.md" || fail "review-plan capacity-not-usage rule missing"
grep -qF 'Populate the sidecar coverage object' "$REPO/agents/skills/review-plan/SKILL.md" || fail "review-plan coverage production step missing"

# V6: review-loop wiring - no full-panel relaunch, degraded action recorded.
grep -qF 'No full-panel relaunch after a timed-out or failed worker' "$REPO/agents/skills/review-loop/SKILL.md" || fail "review-loop no-relaunch rule missing"
grep -qF 'degraded requires a narrowed re-run or an explicit user risk acceptance' "$REPO/agents/skills/review-loop/SKILL.md" || fail "review-loop degraded action missing"

# V7: panel-selection owns replacement-lens selection and launch-slot accounting.
grep -qF '### Replacement-lens selection' "$REPO/agents/skills/review-agents/review-panel-selection.md" || fail "panel-selection replacement section missing"
grep -qF 'Every attempt, retry, and replacement launch counts toward the six-launch ceiling' "$REPO/agents/skills/review-agents/review-panel-selection.md" || fail "panel-selection launch-slot accounting missing"
grep -qF 'the last remaining launch slot is reserved for replacement-lens selection' "$REPO/agents/skills/review-agents/review-panel-selection.md" || fail "panel-selection reserved-slot precedence missing"
grep -qF 'launches as a separate focused review round with its own launch accounting' "$REPO/agents/skills/review-agents/review-panel-selection.md" || fail "panel-selection separate-round replacement model missing"

# V8: plan_readiness consumes the coverage outcome end to end.
grep -qF 'degraded outcome with verdict yes must fail' "$REPO/scripts/plan_readiness.py" || fail "plan_readiness accepted-state coverage cases missing"

# V9 (forbidden-text regression guard, green today and after): no unbounded-wait wording in the two runner skills.
expect_no_match 'wait indefinitely|unbounded wait|unbounded retry|retry until it (succeeds|completes)' "$REPO/agents/skills/review-plan/SKILL.md" "$REPO/agents/skills/review-loop/SKILL.md"

echo "ALL VALIDATION GATES GREEN"
```

### Task 1: Measure staged review-runner behavior by failure class and coverage

Non-behavior investigation task; no code change and no commit. The census command was executed at authoring time on 2026-09-14 against the live corpus (708 sidecars parsed, 0 unparseable; panel statuses: complete 2402, skipped 149, failed 2, timed-out 0; panel modes: full 262, focused 407, 39 legacy rows without `panel_mode`), so the command below is known-executable and the observed distribution is the fallback basis for Task 3's constants.

Files: none (evidence is recorded in the session log and consumed by Task 3).

- [ ] Run the corpus census and record the output in the session log (`docs/tmp/execute-plan/review-runner-bounded-timeout-fallback/`): `python3 -c` with `json`, `pathlib`, `collections` iterating `docs/reviews/*.stats.json`, counting `panel[].status` values, `panel_mode` values, `verdict` values, and `escalation_reason` non-null rows; expects a parse-fail-tolerant summary with per-key counts printed
- [ ] From the census, record the fallback-basis numbers for Task 3: timeout visibility (count of `timed-out` statuses, expected 0 per the authoring-time run), retry/relaunch evidence (`relaunch: true` rows in sidecars), and the focused-versus-full mode split
- [ ] Record corpus limitations observed (elapsed times are not recorded anywhere in sidecars today; this gap is part of the motivation and is closed by the attempt records, not by retroactive measurement)

### Task 2: Coverage state model - staging contract, validator gates, handshake

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-plan/SKILL.md` (inlined sidecar schema block only; the rest of the file is untouched in this task)
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py` (`EXPECTED_SIBLING_COMPAT_VERSION` line only in this task)

- [ ] Add this task's two selftest families first, expecting RED: register `_selftest_coverage_contract` and `_selftest_coverage_readiness_gate` in `run_selftest()` (five coverage families total; the other three arrive in Task 6); each family builds fixtures in a temp tree via the existing `_version1_payload` helper and asserts via the shared two-argument `check(name, ok)` counter of this validator (the three-argument `check(name, ok, detail)` form belongs to `plan_readiness.py`, which Task 5 extends); run `python3 scripts/validate_review_staging.py --selftest` → expect exit non-zero (families fail because the gates do not exist yet)
- [ ] In `review-staging/SKILL.md`, add the subsection `### Coverage sidecar contract (COVERAGE_SIDECAR_MIN_DATE)` to the version-1 contract: the `coverage` object schema (`outcome`, `material_lens_set`, `completed`, `replacement[]` with `lens`, `original_artifact`, `original_sidecar`, `original_failure`; `inherited_coverage[]` with `lens`, `artifact`, `sidecar`; `missing`, `attempts[]`, `retry_budget` with subfields `per_attempt_timeout_minutes`, `per_worker_max`, `wall_clock_ceiling_minutes`, `exhausted`, `exhaustion_reason`), the attempt record fields (`attempt_id`, `worker`, `lenses`, `started_at`, `deadline`, `elapsed`, `outcome`, `failure_class`, `usage_state`, `admission_state`, `admission_error_class`, `execution_mode`, `attempt_number`, `retry_of`, `contributed_coverage`, and the local-equivalence evidence fields `prompt_scope`, `artifact`, `sidecar`), the outcome enum documented as the quoted JSON form `"clean", "replacement-covered", "degraded", "failed"`, and the sanitization sentence "Attempt telemetry must not include prompts, authentication material, provider payloads, or review content that is not already part of the staged artifact"
- [ ] In the same subsection, state the producer scoping sentence "the coverage obligation applies only when source_kind is `plan`; other source kinds validate `coverage` when present and never require it", and pin the cross-field rules verbatim: verdict `yes` requires `outcome` in `clean`/`replacement-covered`, empty `missing`, and every material lens present in `completed` union `replacement[].lens` union `inherited_coverage[].lens`; outcome `degraded` or `failed` requires verdict `no`; `outcome: clean` forbids `replacement[]` entries; `outcome: replacement-covered` requires a non-empty `replacement[]`; the reconciliation rules: `material_lens_set` must be non-empty when the record's own `panel[]` carries launched workers; a post-constant record whose `panel[]` rows carry a `failed` or `timed-out` status (the validator's existing `INCOMPLETE_WORKER_STATUSES`; `skipped` rows are declared out-of-scope rows and never fire this rule; the worker's lens set for this rule is the row's `lenses` when present and non-empty, otherwise its required lenses from the validator's existing `REQUIRED_PANEL_LENSES` mapping, and a worker outside `DEFAULT_PANEL_WORKERS` with empty lenses fails the rule rather than passing vacuously, since its materiality cannot be determined) for a worker whose lenses appear in neither `missing` nor `replacement[].lens` nor `completed` fails the gate; and the evidence-coupling rule: every lens in `completed` must be evidenced by a `panel[]` row with status `complete` whose lenses include it (the same row-lenses-else-`REQUIRED_PANEL_LENSES` fallback as the reconciliation rule applies when the complete row carries no lenses) or by an `attempts[]` record with outcome `complete` and `contributed_coverage: true` whose lenses include it (replacement and inherited links evidence the rest); the round's own declared panel is the evidence and the validator still never infers materiality from lens names; the scope-coupling rule: a record with `replacement[]` entries must declare in `material_lens_set` at least the lenses named in its `replacement[]` and `inherited_coverage[]` entries, and a replacing round's declared material set must include the original round's `missing` lenses (replacement never silently narrows the review scope); records dated before `COVERAGE_SIDECAR_MIN_DATE` are exempt
- [ ] Extend the staging Markdown template: add the Metadata line `- Coverage: clean | replacement-covered | degraded | failed` (date-fenced like the freshness lines) and the `### Attempt ledger` subsection under `## Review Statistics` with one row per attempt; add the Markdown-sidecross-check obligation (the Coverage line outcome and the attempt-ledger row count must agree with the sidecar)
- [ ] In `scripts/validate_review_staging.py`: add `COVERAGE_SIDECAR_MIN_DATE = "2026-09-16"` beside `EXTENDED_SIDECAR_MIN_DATE` with the same grandfathering rationale comment style (records on or after the constant require valid `coverage`; earlier records exempt; the constant is the expected day after implementation lands, so same-day records stay exempt); pin the fence-window recovery: Tasks 2 through 5 run in one session so producers land with the gate, and if execution must pause between this commit and Task 5's commit across the constant date, the recovery is a follow-up commit that bumps `COVERAGE_SIDECAR_MIN_DATE` with the same rationale-comment style and re-pins the V4 grep literal in the same commit
- [ ] Add key allowlists `COVERAGE_ALLOWED_KEYS`, `ATTEMPT_ALLOWED_KEYS`, and per-entry key allowlists for `coverage.replacement[]` and `coverage.inherited_coverage[]`, and reject unknown keys inside `coverage`, `coverage.attempts[]`, `coverage.retry_budget`, and those entry arrays (same spirit as the top-level field rejection; sanitization is thereby structurally enforced: no free-form content fields exist to carry prompts or payloads); records with non-empty `attempts[]` require a non-empty `retry_budget` carrying `per_attempt_timeout_minutes` and `per_worker_max`
- [ ] Admit `coverage` as a recognized version-1 top-level field with the date fence: required for `source_kind` `plan` records dated on or after `COVERAGE_SIDECAR_MIN_DATE`, permitted and validated otherwise (the same mechanism as the four freshness fields); without this entry every covered sidecar is rejected as an unknown top-level field
- [ ] Implement `validate_coverage_contract` (schema, enums, source_kind-scoped date fence, verdict cross-field rules, reconciliation rules - where a sidecar panel row spelled `timeout` is treated as the `timed-out` axis, so the validator's `INCOMPLETE_WORKER_STATUSES` values and the documented Markdown spelling both fire the rule - late-result rule: an attempt with outcome `complete` whose lens already has a `replacement[]` entry must carry `contributed_coverage: false` and must not coexist with `outcome: clean`; the capacity/usage contradiction rule: an attempt record with `admission_state` in `denied`/`saturated` and `admission_error_class` in the capacity set (`capacity-denied`, `concurrency-limit`, `provider-unavailable`, `stale-release-suspected`) must not record `usage_state: exhausted` (capacity blockers are recorded as capacity, never as usage exhaustion); the budget-exhaustion rule: `retry_budget.exhausted: true` requires a non-empty `exhaustion_reason` naming a retryable class; the attempt required-field rule: every attempt record carries non-empty `attempt_id`, `started_at`, `deadline`, `outcome`, and `attempt_number`, outcome `failed` or `malformed-output` requires `failure_class`, `elapsed` when present is a non-negative number not exceeding `retry_budget.per_attempt_timeout_minutes`, and `attempt_number` ranges 1 through `retry_budget.per_worker_max` + 1 (the initial attempt plus at most `per_worker_max` retries); the local-equivalence rule: an `attempts[]` record with `execution_mode: local` may set `contributed_coverage: true` only when `prompt_scope` is present and `artifact` and `sidecar` name an existing artifact and `.stats.json` sidecar pair under the reviews directory whose sidecar parses (the same evidence bar as the replacement links; the completed-evidence rule counts only attempts whose local evidence passes this check)), `validate_replacement_links` (per entry kind: a `replacement[]` entry's linked original artifact and `.stats.json` sidecar exist and parse, and for a post-constant original the linked sidecar must show the named lens as uncovered (a `failed`/`timed-out` panel row or the lens in its `missing`), while a pre-constant original is accepted on the recorded `original_failure` plus file existence; an `inherited_coverage[]` entry - which carries no `original_failure` field - has its linked artifact and sidecar exist and parse, and the linked round must show the named lens covered: for a post-constant linked round the lens appears in its `completed` (evidenced by that round's own rules) or its `replacement[].lens` with outcome `replacement-covered`, for a pre-constant linked round the linked sidecar's `panel[]` carries a `complete` row whose lenses include the named lens), and `validate_coverage_markdown_agreement` (Coverage line outcome equals sidecar outcome; attempt-ledger row count equals `len(coverage.attempts[])`; date-fenced like the coverage gate, pre-constant records exempt); wire them where both entry paths share them: the `coverage` presence fence, the allowlist entries, `validate_coverage_contract`, and `validate_replacement_links` inside `validate_version1_payload` (the function `validate_stats_sidecar` calls, which is the readiness gate's only path), and `validate_coverage_markdown_agreement` inside `validate_stats_sidecar` (which receives the Markdown `content`); `validate_staging_file` keeps calling `validate_stats_sidecar`, so the staging-time path exercises the same shared wiring with no second wiring site
- [ ] Bump `COMPAT_VERSION = 2` (keeping its comment) and in the same commit set `EXPECTED_SIBLING_COMPAT_VERSION = 2` in `scripts/plan_readiness.py`; run `python3 scripts/plan_readiness.py --selftest` → expect exit 0 (handshake agrees)
- [ ] Update the inlined sidecar schema block in `review-plan/SKILL.md` (the "Sidecar schema (inlined here" block) to list the new date-fenced `coverage` field, so the inlined copy and the review-staging contract do not drift
- [ ] Run `python3 scripts/validate_review_staging.py --selftest` → expect exit 0 (families `_selftest_coverage_contract` and `_selftest_coverage_readiness_gate` green: valid clean and valid replacement-covered fixtures pass; degraded-with-verdict-yes, missing-coverage-on-post-constant-record, unknown-attempt-key, late-result-flipping-clean, broken-replacement-link, under-declared-material-set-with-timed-out-panel-row, empty-material-set-with-launched-workers, timed-out-worker-lens-placed-in-completed, mislabeled-replacement-covered-with-empty-replacement, inherited-link-whose-linked-round-shows-the-lens-uncovered, replacement-round-narrowing-the-original-material-set, and timeout-spelled-panel-row fixtures each fail with their dedicated error; a skipped-row focused round with its full declared material set complete and a valid post-constant inherited link each pass)
- [ ] Commit: `review-runner: add coverage state model and gates`

### Task 3: Narrow worker prompts and pin bounded attempt settings

Files:
- `agents/skills/review-plan/SKILL.md`

- [ ] Replace the unbounded wait in step 2 with the new section `### Bounded attempts and retry classification`: each launch runs under a bounded wait; on timeout the attempt is recorded and the retry decision follows the classification table; pin the constants with a rationale comment citing Task 1's census: `DEFAULT_ATTEMPT_TIMEOUT_MINUTES = 15`, `DEFAULT_RETRY_BUDGET_PER_WORKER = 2`, `DEFAULT_PANEL_WALL_CLOCK_MINUTES = 120`, each stating it may be re-pinned from measured completion data and that the panel enforces a fixed attempt count and total wall-clock ceiling regardless of per-attempt size
- [ ] Pin the retry classification: retryable within budget (`provider-timeout`, `provider-unavailable`, `orchestrator-wait-timeout`, `concurrency-limit`, `capacity-denied` under the bounded capacity retry rule - a capacity-class failure consumes one retry-budget unit and retries under the same bounded wait; when the budget or the launch slots are exhausted the round records the capacity state and stops at the degraded or report-only boundary, never escalating to a full-panel relaunch; `worker-crash` as a transient infrastructure failure); never retried as worker retries (`malformed-output`, `parse-failure`, `data-error` are classified and logged), and `unknown`-class attempts are never auto-retried: the attempt is recorded and the round stops at the report-only boundary; `usage-rate-limit` never triggers a worker retry and routes to the existing usage-budget gate; `stale-release-suspected` is recorded and stops at the bounded retry or report-only boundary without claiming a worker release; retries additionally obey the launch-slot precedence rule pinned in Task 4 (a retry may proceed only while more than one launch slot remains)
- [ ] Pin the usage/admission separation with the sentence "usage state and worker admission are separate signals" and the rule the runner "must not interpret a capacity denial as usage exhaustion", spends no reset on denial, and never relaunches the whole panel for one lens; add the lifecycle rule (record task-state transition plus capacity result when observable; never terminate an unrelated user-owned task as a capacity workaround) and the local-fallback rule (a local execution mode may contribute coverage only with the same lens, prompt scope, artifact lineage, sidecar evidence, and readiness rules, recorded via `execution_mode: local`; otherwise the result stays capacity-blocked or degraded)
- [ ] Narrow the per-worker prompt template: each worker's prompt carries the artifact, its assigned lens or lens group, the changed-risk signals, and the exact evidence fields it must return; workers do not re-derive the whole plan and do not perform broad cross-lens audits; any broader audit is a separately scoped escalation or replacement, never a widening of an existing worker's prompt
- [ ] Add the coverage production step to step 3 synthesis: "Populate the sidecar coverage object per review-staging (outcome, material_lens_set, completed, replacement, inherited_coverage, missing, attempts, retry_budget) in the same pass as the `.stats.json` sidecar"; a timed-out or failed material worker without accepted replacement coverage forces verdict `no` with outcome `degraded`
- [ ] Run → expect the fail-fast block to stop at V4: `bash` the Validation Commands block from the plan root and record the first failing gate (V4's three Task 6 family greps are still missing); V1, V2, and V3 pass before it (the block would otherwise have stopped earlier), V5's greps are green by this task but sit behind V4 and are verified standalone, and the V9 forbidden-text sweep is verified standalone
- [ ] Commit: `review-runner: narrow worker prompts and pin bounded attempt settings`

### Task 4: Replacement-lens selection ownership

Files:
- `agents/skills/review-agents/review-panel-selection.md`

- [ ] Add the section `### Replacement-lens selection`: when a material worker is unavailable after its permitted attempts, select the replacement through this declared rule, not narrative judgment; the selection record names the missing lens or lens group, why the original worker was not used again, the replacing round's worker or focused mode, and the evidence artifact and sidecar that establish completion
- [ ] Pin independence and scope rules: the replacement is a fresh worker instance with a narrowed evidence scope; it must not reuse the original worker's late or partial output; the replacement prompt is no broader than the missing lens requires and must not recreate the timed-out broad audit under a different name; partial coverage is declared explicitly in the replacing round's `coverage.completed` versus its `missing`
- [ ] Pin the launch-slot sentence "Every attempt, retry, and replacement launch counts toward the six-launch ceiling"; state the replacement model: "a replacement-lens selection launches as a separate focused review round with its own launch accounting" and its own artifact and sidecar pair, never as an in-round sixth worker (the escalation-worker rules are a different mechanism this plan does not use); within a round, when no launch slot remains for further attempts the round records the lens in `missing` (outcome `degraded`, verdict `no`) and the loop proceeds to the replacement round per this section; pin the precedence rule "in a full panel the last remaining launch slot is reserved for replacement-lens selection, and worker retries may proceed only while more than one launch slot remains"; state the derived consequence: with five base workers launched, one slot remains and is reserved, so retries can only proceed when at least two slots remain, which in practice means focused rounds - a full-panel timeout proceeds directly to replacement-or-missing via the follow-up focused round
- [ ] Pin the linkage rule: the replacing round records the original round in `coverage.replacement[]` (lens, `original_artifact`, `original_sidecar`, `original_failure`); when no suitable replacement exists, the lens is recorded as missing and never silently absorbed by a nearby lens
- [ ] Run → expect the fail-fast block to still stop at V4 (V7's greps are now green but sit behind V4): `bash` the Validation Commands block and record the first failing gate; verify the four V7 greps standalone to witness their green state - a mismatch means the pinned sentence in this task's `review-panel-selection.md` text needs the exact wording, fixed in this task
- [ ] Commit: `review-runner: define replacement-lens selection rules`

### Task 5: Loop behavior and readiness consumption

Files:
- `agents/skills/review-loop/SKILL.md`
- `scripts/plan_readiness.py` (`_selftest_accepted_state` coverage cases only)

- [ ] In `review-loop/SKILL.md`, add the anti-pattern row `No full-panel relaunch after a timed-out or failed worker`: after a material worker exhausts its retry budget, the loop proceeds by replacement-lens selection (focused round per review-panel-selection) or records degraded coverage; it never relaunches the full panel and never waits unbounded
- [ ] Pin the degraded and failed user-visible actions: "degraded requires a narrowed re-run or an explicit user risk acceptance recorded in triage outcomes"; failed requires repairing staging or the runner and re-running; neither state may exit the loop as clear
- [ ] Extend the exit report duty: the exit report states the final `coverage.outcome` and any `missing` lenses alongside the existing blocking-finding accounting; the existing design-simplicity-before-exit rule is unchanged and a replacement round must still satisfy it
- [ ] In `scripts/plan_readiness.py`, extend `_selftest_accepted_state` with the end-to-end coverage cases (selftest comment line `# coverage gate: degraded outcome with verdict yes must fail`): a post-constant sidecar with verdict `yes` and outcome `degraded` fails `evaluate_readiness`; the same fixture with outcome `replacement-covered`, valid links, and complete material coverage passes; a post-constant sidecar with no `coverage` object fails; run `python3 scripts/plan_readiness.py --selftest` → expect exit 0
- [ ] Run → expect the fail-fast block to still stop at V4 (V6's and V8's greps are now green but sit behind V4): `bash` the Validation Commands block and record the first failing gate; verify the V6 and V8 greps standalone to witness their green state
- [ ] Commit: `review-runner: wire degraded coverage into loop and readiness`

### Task 6: Behavioral fixture matrix for the failure-class taxonomy

Files:
- `scripts/validate_review_staging.py` (three remaining selftest families)
- `scripts/plan_readiness.py` (only if a family needs an end-to-end assertion through `evaluate_readiness`)

- [ ] Add `_selftest_replacement_and_late_results`: exhausted timeout followed by a valid replacement round passes with outcome `replacement-covered`; timeout with no replacement records `missing` and outcome `degraded` with verdict `no`; a late original `complete` attempt recorded after the replacement entry carries `contributed_coverage: false` and cannot flip the outcome to `clean`; a replacement linked to a pre-constant original (no coverage object) is accepted on the recorded `original_failure`; a valid post-constant inherited link (linked round shows the lens covered) passes while an inherited link whose linked round shows the lens uncovered fails; a record labelled `outcome: replacement-covered` with an empty `replacement[]` fails; every backlog acceptance-criterion-8 class (complete workers, retryable timeout then completion, exhausted timeout then replacement, timeout with no replacement, `malformed-output`, deterministic `parse-failure`/`data-error`, late output, markdown/sidecar disagreement) has a dedicated fixture assertion
- [ ] Add `_selftest_capacity_admission_lifecycle`: an attempt record with `usage_state: available`, `admission_state: denied`, `admission_error_class: capacity-denied` validates while the same record claiming `usage_state: exhausted` fails the contradiction gate; a `stale-release-suspected` lifecycle record stops at the boundary without a release claim; a minimal-worker `complete` attempt after a full-panel capacity-blocked launch validates without attributing cause to usage exhaustion; and the local-execution equivalence arm (backlog acceptance criterion 14): a fully evidenced `execution_mode: local` attempt (same lens, prompt scope, artifact lineage, sidecar evidence) contributes coverage and validates, while a local attempt missing one of those equivalence evidence fields fails to contribute coverage (outcome stays capacity-blocked or degraded)
- [ ] Add `_selftest_prompt_scope_accounting`: two attempts for one worker (broad prompt timing out, narrowed prompt completing within its own deadline) validate as two independent bounded attempts with per-attempt deadlines, `attempt_number` within 1 through `retry_budget.per_worker_max` + 1, and no silent deadline extension; `retry_budget.exhausted` is true only with an exhaustion reason naming a retryable class; the negative arms of the attempt required-field rule each fail (an attempt missing `deadline`, an attempt with `attempt_number` above the range, an attempt whose `elapsed` exceeds `retry_budget.per_attempt_timeout_minutes`, a `failed` outcome without `failure_class`); backlog acceptance criterion 11's accounting half is witnessed by this fixture, and its completion half (a narrowed prompt completing within the configured bounded timeout under real provider latency) is witnessed operationally by the first post-landing certification round's attempt records (elapsed within deadline), recorded in that round's session log
- [ ] Run `python3 scripts/validate_review_staging.py --selftest` → expect exit 0 with all five coverage families green; run `python3 scripts/plan_readiness.py --selftest` → expect exit 0
- [ ] Run → expect the whole block GREEN from this task on: V4's family-registration greps complete, so the fail-fast block exits 0 with every gate green
- [ ] Commit: `review-runner: add coverage fixture matrix`

### Task 7: Rollout and legacy compatibility documentation, full validation

Files:
- `agents/skills/review-staging/SKILL.md` (legacy compatibility subsection only)

- [ ] Add the legacy compatibility subsection to the coverage contract: records dated before `COVERAGE_SIDECAR_MIN_DATE` remain valid without `coverage` and may satisfy `ready=yes` under the existing gates; consumers keying on `coverage.outcome` must treat its absence as not-yet-covered rather than degraded; no historical sidecar is rewritten; and document the producer scoping for operators: the coverage obligation is plan-source-scoped, so branch and document review producers (`doing-code-review`, `rfc-design`, `review-confluence-doc`) are unchanged post-landing and may adopt `coverage` in a follow-up (validated when present, never required for their source kinds)
- [ ] Document the rollout behavior for in-flight reviews: a review loop straddling the landing commit records coverage only for rounds staged after landing; the grace window is intentional and matches the freshness-fields precedent; a replacement linked to a pre-constant original is accepted on the recorded `original_failure` (the grandfathered-link rule), so a straddling loop with evidence present is not forced into degraded
- [ ] Run → expect GREEN, whole block: execute the full `## Validation Commands` block and record exit 0 with every gate green
- [ ] Record the discriminating rollout witness: count plan-source sidecars dated on or after `COVERAGE_SIDECAR_MIN_DATE` that carry a `coverage` object versus those that do not, and record both numbers in the session log; also run `python3 scripts/plan_readiness.py --sweep` and record the informational verdict-coverage line as context only (it tracks verdict-field share, not coverage adoption; no exit-code gate)
- [ ] Commit: `review-runner: document coverage rollout and legacy compatibility`
