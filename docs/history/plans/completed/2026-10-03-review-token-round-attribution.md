# Plan: Review token usage round attribution

Feature note (scope of record): `docs/history/feature-notes/2026-07-29-token-usage-telemetry.md`
Deferring plan: `docs/history/plans/completed/2026-09-06-token-usage-telemetry.md` (names durable review lineage its deferred follow-up)
Origin: `docs/history/backlog/2026-10-02-round-scoped-review-token-metrics.md`
Plan review record: `docs/reviews/2026-10-03-plan-review-review-token-round-attribution-r*.md` (+ `.stats.json` sidecars)

## Driving force

The token-usage telemetry plan shipped the 6-hour window join as deliberately best-effort and named durable review lineage its deferred follow-up. The corpus probe re-derived 2026-10-03 over `docs/reviews`: 1,897 sidecars, 314 usage-bearing, 312 of those marked `provenance.ambiguous: true` - observed-token totals and usage coverage are not decision-grade today. Live witness: `docs/reviews/2026-10-02-plan-review-machinery-inventory-upkeep-r3.stats.json` carries a union of SIX root sessions and 123,237,402 input tokens in one round record, because six peer sessions shared the repo directory inside one 6-hour window.

A fresh runtime-store probe (2026-10-03, read-only, `~/.zcode/cli/db/db.sqlite`) materially changes the design space since the 2026-09-06 probe the telemetry plan recorded:

- `session` gained `time_created`, `time_updated`, `trace_id`, `project_id`, `workspace_id`, `slug`, `path` (the columns the current adapter queries still exist; all drift is additive, so today's capture still runs).
- `model_usage` gained `logical_request_id`, `turn_id`, `trace_id`, `attempt_index` (row id now text).
- NEW table `turn_usage`: one row per turn with `session_id`, `turn_id`, `status`, `started_at`, `completed_at` (ms), and the same six token fields as `model_usage`; 7,680 completed rows spanning 2026-09-04 to 2026-10-03, same span as `model_usage` (178,234 completed rows). Turn grain avoids per-attempt double counting across `attempt_index` rows. The table carries NO `query_source` and NO `agent` column (r1 F4).
- NEW tables `dwf_run` (dynamic-workflow runs with `parent_session_id`, `cwd`, `spent_tokens`, status) and others; none is required by this plan.
- Environment re-probe 2026-10-03: `ZCODE_*` variables carry app metadata only (`ZCODE_APP_VERSION`, `ZCODE_PROCESS_LABEL`, ...); still no contract-stable in-session session-id variable, so identity comes from the emitting agent's own record and invocation, exactly as the entry words it.

## Outcome

- `scripts/review_usage_capture.py` gains a `mint` subcommand (review-run identity minted at round start) and an identity invocation (`--review-run-id`, `--review-started-at-ms`) whose zcode adapter attributes usage by INTERVAL over turn-grain rows, marking a record attributable only when exactly one root session contributes rows inside `(review_started_at_ms, captured_at_ms]`. The bare `--json` invocation keeps today's byte-identical stdout as the documented compatibility path (a one-line stderr notice that the record is non-attributable is added; stdout stays untouched).
- The `review-staging` skill's usage-capture step mints the identity at round start, carries the mint output verbatim through the staging record, and passes it at sidecar-write capture; capture stays fail-open and never estimates.
- `scripts/summarize_review_stats.py` publishes four usage counts (present, attributable, ambiguous, missing), collapses multi-sidecar rounds by review-run identity, sums decision-grade observed tokens from one surviving attributable record per round, reports ambiguous totals as a separate non-decision-grade line, and binds the supplementary decision threshold to attributable coverage over post-attribution-cutover sidecars.
- The summarizer's review-corpus metrics pass compares initial (r1) versus follow-up rounds by complexity band and by the sidecar's `panel_mode`, with token usage alongside accepted unique findings, staged findings, blocking findings, and readiness, marking token-based conclusions inconclusive until attribution and sample coverage are adequate.

## Gate delta (machinery priced additions)

1. `mint` subcommand plus identity arguments plus additive provenance fields (`review_run_id`, `review_started_at_ms`, `attribution`, `attributable`, `by_session`, `source_grain`); priced on the 312-of-314 ambiguity corpus and the six-session 123M-token witness above.
2. `turn_usage`-preferred interval source with a missing-table-only fallback to `model_usage`; priced on the fresh schema probe (the 2026-09-06 schema assumptions are stale).
3. Summarizer attribution classification and round collapse; priced on the telemetry plan's own deferral record (durable review lineage is the named follow-up this plan lands). The initial-versus-follow-up analysis section is priced separately on the origin row's Expected paragraph (r1 F21).

## Terms

- **Review-run identity**: a `uuid4` hex string minted once per review round by `review_usage_capture.py mint`, carried through the staging record into the sidecar `usage` provenance as `review_run_id`. The identity invocation validates it against `^[0-9a-f]{32}$` and treats an invalid value as absent (window-legacy path, non-attributable) with a tilde-abbreviated stderr diagnostic (r1 F18).
- **Mint**: the `mint` subcommand. It ALWAYS prints `{"review_run_id", "minted_at_ms", "candidate_root_session_ids"}` - the identity itself needs no store; the candidate list is best-effort discovery and may be empty. Mint never raises and never reads token counts.
- **Interval join**: attribution over usage rows with `completed_at` in `(review_started_at_ms, captured_at_ms]` for the repo anchor's sessions, replacing the fixed 6-hour look-back as the authority. The window survives only as the mint's discovery bound and as the legacy fallback.
- **Contributing root session**: a root session of the anchor (after the `parent_id` walk) with at least one completed usage row inside the interval.
- **Attributable**: a usage record whose `provenance.attribution == "interval-identity"`: identity was passed and validated, the source is row-accurate (`zcode-sqlite` turn grain), and exactly one root session contributed. The model-attempt fallback emits `attribution: "interval-fallback"` and is NEVER attributable (its grain double-counts `attempt_index` retries). Everything else is non-attributable.
- **Interval-boundary contract**: the fallback is taken ONLY on the missing-table condition (the `"no such table"` sqlite error substring or an `sqlite_master` probe); any other `sqlite3.OperationalError` (locked, no such column, disk I/O) takes the existing fail-open None path (r1 F6). The identity invocation requires BOTH arguments; either alone is an argparse error (exit 2) before any store read (r1 F6, F14).
- **Window-legacy**: today's 6-hour window join behavior, preserved byte-compatibly (stdout) for the bare `--json` invocation and forced for `codex-rollout` (its cumulative per-file counters cannot be sliced into intervals without estimation, which the contract prohibits).
- **Superseded capture**: among the attributable sidecar records sharing one `review_run_id` (the workers of one round write one sidecar each, against nested intervals with the same start), only the record with the maximum `captured_at_ms` survives into decision-grade sums; its interval already spans mint-to-last-capture. Earlier records of the same run count as usage present but are excluded from sums and published as a `sidecars_superseded_captures` count; rows completing after the last capture are a named honest gap (r1 F1).
- **Attributable coverage**: attributable sidecars divided by post-`ATTRIBUTION_CUTOVER_DATE` sidecars, where `ATTRIBUTION_CUTOVER_DATE` is this plan's landing date. Historical post-cutover sidecars can never gain attribution (immutable inputs), so binding the threshold to them would freeze the ratio near zero forever; the legacy post-cutover presence coverage stays published for context, and the published `coverage` fraction key keeps its presence-based meaning (r1 F2, F3).

## Assumptions

- assume `turn_usage` is the preferred interval source and `model_usage` the fallback taken ONLY on the missing-table condition; a present-but-empty `turn_usage` result is an honest empty (returns no record), not a fallback trigger - pinned by a fixture where the turn table is present but empty for the anchor AND `model_usage` carries in-interval rows, expecting None (a fallback would produce a record and fail). Basis: fresh probe 2026-10-03 (coverage spans above; turn grain carries the same six token fields pre-summed per turn).
- assume turn-grain interval records bucket all rows under `other` in `by_agent_kind` (mirroring the codex adapter convention) because `turn_usage` has no `query_source`; this loss of the agent-kind split on the preferred source is a recorded accepted limitation, the `model_usage` fallback keeps `query_source` bucketing, and provenance names the serving source as `source_grain: "turn"` or `"model-attempt"` (r1 F4). Basis: live `PRAGMA table_info(turn_usage)` probe 2026-10-03.
- assume identity comes from the mint invocation, never from an environment variable, and the values recorded and passed are the mint output's `review_run_id` and `minted_at_ms` VERBATIM, never re-derived (r1 F19). Basis: env re-probe 2026-10-03 plus the 2026-09-06 probe recorded in the telemetry plan.
- assume the bare `--json` stdout stays byte-identical to today (no new keys), so legacy consumers and legacy sidecars keep parsing byte-compatibly; every new provenance key appears only on the identity invocation. Basis: the entry's compatibility constraint and the telemetry plan Task 2 contract.
- assume `codex-rollout` cannot honor interval attribution (cumulative per-file counters; slicing them would be estimation) and stays `window-legacy`/non-attributable even when identity is passed; `review_run_id` is still carried in its provenance for forensics. Basis: capture module docstring accepted limitations (per-file cumulative sums).
- assume the reviewing session's own in-interval usage counts as review cost (orchestration is review cost), and residual over-attribution from non-review activity the SAME session performs inside the interval is a named accepted limitation the report never hides (attribution quality is published per record). Basis: interval-grain design; the entry's fixture (c) only demands pre-review implementation usage stays out.
- assume attribution requires exactly one contributing root session; per-row `session_id` is never used to PICK among concurrent contributors (that would need a runtime-side linkage this plan does not assume), so concurrent reviews stay ambiguous with per-session detail preserved in `by_session` (keys truncated to `SESSION_ID_PREFIX_LEN`; a 12-char prefix collision sets `by_session_collided: true` and the record stays non-attributable). Basis: entry fixture (b) and the no-env-var constraint.
- assume real runtime worker sessions populate `session.parent_id` is a VALIDATED assumption, not a given: Task 5 probes the live store's linkage (r1 F12) and on NULL linkage the completion record states the honest fallback (only single-root rounds are attributable). Basis: fixtures populate linkage by hand; the live population was not probed at authoring.
- assume the `review-staging` skill stays the single wiring point (mint duty + identity invocation live in its capture step); `review-agents` and `doing-code-review` skills receive no capture duties. Basis: the telemetry plan's resolved capture design.
- assume the validator is untouched: `usage` remains an allowlisted optional v1 field and provenance shape ownership lives in the capture module's selftests. Basis: the shape-ownership comment beside `V1_OPTIONAL_TOP_LEVEL_FIELDS` (telemetry plan Task 2).
- assume the operator execution-lane closure of 2026-10-02 stands: this plan is authored only, not executed, in this cycle.

Decision points requiring a grill: mint carrier in the staging record; turn_usage-versus-model_usage source preference and its missing-table discriminator; the attributable rule for concurrent contributors; codex-rollout interval honesty; the analysis sample-adequacy floor (resolved in-plan as USAGE_ANALYSIS_MIN_ROUNDS = 3).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/review_usage_capture.py` *(modified; mint subcommand, interval join, additive provenance fields; its contract selftests are in-module under the `--selftest` flag, extended in place)*
- `scripts/summarize_review_stats.py` *(modified; attribution classification, four counts, round collapse, attributable-only totals, threshold rebind, initial-vs-follow-up analysis; its contract selftests are in-module under the `--selftest` flag, extended in place)*
- `agents/skills/review-staging/SKILL.md` *(modified; the Usage capture step gains the mint duty and the identity invocation)*

**Tests:** both scripts carry their contract selftests in-module (`--selftest` flag, sibling-script pattern); there is no separate test-file path, so no path is listed in this category.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; reason: `usage` is already an allowlisted optional v1 field and the validator must stay shape-agnostic (shape ownership lives in the capture selftests); changing validator shape checks is out of scope.
- `codex-rollout` interval slicing; reason: rollout counters are cumulative per file, so interval slicing would be estimation, which the capture contract prohibits (documented limitation, not a defect).
- `agents/skills/review-agents/` and `agents/skills/doing-code-review/`; reason: the review-staging skill is the single wiring point per the telemetry plan's resolved capture design.
- `docs/history/backlog/2026-10-02-review-approval-digest-byte-coupling.md`; reason: the whole-file approval digest binding is an operator-gated decision recorded in that item and stays out of scope here per the entry's coordination clause.
- Historical sidecars under any reviews directory; reason: immutable read-only inputs (telemetry plan non-goal).
- `scripts/check_maintenance_pins.sh`; reason: no new pins rows; the identity and aggregation contract is carried by selftests (pins may ride along only in a later plan per the entry's rejected-alternatives note).

## Validation Commands

```bash
python3 scripts/review_usage_capture.py --selftest
python3 scripts/summarize_review_stats.py --selftest
python3 scripts/validate_review_staging.py --selftest
# the review-staging skill carries the mint step (RED today; GREEN only after Task 2).
# The [t] escape is intentional: the plan's own text must not satisfy the grep.
grep -q "review_usage_capture.py min[t]" agents/skills/review-staging/SKILL.md
# the never-estimate sweep stays green: no estimation identifiers anywhere.
for f in scripts/review_usage_capture.py scripts/summarize_review_stats.py; do test -f "$f" || { echo "missing $f"; exit 1; }; done
! grep -inE '"estimated": *(true|True)|estimate_[a-z]+\(' scripts/review_usage_capture.py scripts/summarize_review_stats.py
```

### Task 1: RED then GREEN - capture mint subcommand and interval join (zcode adapter)

Files:
- `scripts/review_usage_capture.py`

- [ ] `review_usage_capture#selftest_mint_prints_identity`; given a fixture home with a store carrying one anchor session active in the last window, `mint` prints a JSON object whose `review_run_id` is 32-char lowercase hex, whose `minted_at_ms` equals the injected now, and whose `candidate_root_session_ids` lists that root truncated to 12 chars; given a fixture home with NO store, mint still prints the identity fields with `candidate_root_session_ids: []` and never raises [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_interval_single_contributor_attributable`; given identity arguments and one root session whose turn rows complete inside `(review_started_at_ms, captured_at_ms]`, expects `provenance.attribution == "interval-identity"`, `provenance.attributable is True`, `provenance.review_run_id` carried verbatim, `provenance.review_started_at_ms` carried verbatim, `provenance.source_grain == "turn"`, `by_agent_kind` bucketing everything under `other` (the turn-grain convention), and totals equal ONLY the in-interval rows [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_interval_excludes_pre_review_rows`; given the same session carrying rows both before and inside the interval (the mixed implementation-and-review session), expects totals to exclude every pre-interval row (implementation usage never enters the round record) [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_interval_two_contributors_ambiguous`; given two root sessions (no parent linkage) each contributing rows inside the interval (two concurrent reviews), expects `attribution == "interval-ambiguous"`, `attributable is False`, both truncated ids in `session_ids`, a `by_session` map carrying each contributor's own interval subtotals with every key at most 12 chars and matching a `session_ids` entry, and `totals` equal to the union (never silently assigned to one session) [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_adjacent_rounds_disjoint`; given one session and two mints M1 < M2 with rows partitioned across `(M1, M2]` and `(M2, now]`, INCLUDING a row completing exactly at M2 and a row completing exactly at M1, each round's capture is attributable, the M2 row counts in round 1 only, the M1 row counts in neither round (the open-start boundary), and the two totals are disjoint and additive (adjacent rounds sharing a session never double-count); the fixture capture helper takes explicit window and identity parameters (today's fixture helper hardcodes now) [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_interval_turn_usage_preferred_with_fallback`; the fixture `_Fixture` gains a `turn_usage` table builder mirroring the PROBED columns exactly (no `query_source`, no `agent`) plus a drop-table mode: (a) with divergent totals (two `model_usage` attempt rows of 100 and one `turn_usage` row of 100 in the interval) the interval totals equal 100 - turn grain, witnessing the double-count avoidance; (b) with the `turn_usage` table DROPPED, the same interval falls back to `model_usage` rows with `attribution == "interval-fallback"`, `attributable is False`, and `source_grain == "model-attempt"`; (c) with `turn_usage` present but EMPTY for the anchor while `model_usage` carries in-interval rows, the capture returns None (honest empty; a fallback would produce a record and fail) [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_fallback_discriminator_and_locks`; given a fixture store with `turn_usage` present held by an exclusive writer (locked), the capture returns None and NEVER a model_usage fallback record; the fallback fires only on the missing-table condition [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_identity_no_usable_runtime_data`; given a fixture home with no db plus identity arguments, expects None; given a store whose rows all complete before the interval start plus identity arguments, expects None (never an empty-totals attributable record, never a codex fallback when no codex store exists) [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_codex_identity_stays_legacy`; given a codex rollout fixture and identity arguments, expects the record with `attribution == "window-legacy"`, `attributable is False`, `review_run_id` carried, and totals from the unchanged cumulative parsing (never interval-sliced) [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_bare_invocation_byte_compat`; given the bare `--json` invocation, expects the printed record to contain NO `attribution`, `attributable`, `review_run_id`, `review_started_at_ms`, `source_grain`, or `by_session` keys (today's exact shape) for BOTH adapters, while all pre-existing selftests keep passing unchanged [class: REPOSITORY_TEST]
- [ ] `review_usage_capture#selftest_identity_invocation_arity_and_shape`; run `main()` with injected argv only (no store access): `--review-run-id` without `--review-started-at-ms` (and the inverse) exits 2 via argparse; a `review_run_id` not matching `^[0-9a-f]{32}$` or a non-positive start is treated as absent (the window-legacy path) with a tilde-abbreviated stderr diagnostic; selftests drive injected seams only (`mint_identity(home=, cwd=, now_ms=)` mirroring `capture_usage`), and subprocess/CLI-level tests are prohibited unless home, cwd, and now are pinned explicitly [class: REPOSITORY_TEST]
- [ ] Run `python3 scripts/review_usage_capture.py --selftest` -> expect RED (mint subcommand and identity arguments do not exist) [class: REPOSITORY_TEST]
- [ ] Implement: `mint` subcommand (`uuid.uuid4().hex`, injected-now `minted_at_ms`, candidate discovery reusing the window-plus-directory match and the root collapse walk); `--review-run-id` and `--review-started-at-ms` (integer) arguments with the arity and shape rules above; a `_capture_zcode_interval` path preferring `turn_usage` with the missing-table-only fallback; per-contributor subtotals with truncated `by_session` keys; the additive provenance fields on the identity invocation only; the codex adapter carrying identity as `window-legacy`; a one-line stderr notice on the bare invocation that the record is non-attributable (stdout unchanged); fail-open on every error path; update the module docstring's "Window and grain semantics" section to state interval attribution as primary with the 6-hour window surviving as the mint's discovery bound and the legacy/codex fallback (r1 F11); no new `estimate` identifiers anywhere [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 scripts/review_usage_capture.py --selftest` -> expect GREEN (all pre-existing selftests still pass) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: review usage capture mints review-run identity and joins by interval` [class: IMPLEMENTATION_REQUIRED]

### Task 2: RED then GREEN - review-staging capture step mints at round start and passes identity at write

Files:
- `agents/skills/review-staging/SKILL.md`

- [ ] Run the Validation Commands -> expect the mint-step grep RED (the skill's Usage capture paragraph has no mint duty today) [class: REPOSITORY_TEST]
- [ ] Amend the `**Usage capture (production write path):**` paragraph: at the START of staging a review round (before launching the round's workers), run `python3 ~/.ai-playbook/scripts/review_usage_capture.py mint` and carry the printed JSON through the round; record `review-run-id: <review_run_id>` and `review-started-at-ms: <minted_at_ms>` in the staging record's metadata block - the two values are the mint output's fields VERBATIM, never re-derived; at sidecar write run `python3 ~/.ai-playbook/scripts/review_usage_capture.py --json --review-run-id <review_run_id> --review-started-at-ms <minted_at_ms>` and merge its output as the top-level `usage` field when it prints one; keep the existing sentences: when it prints nothing write the sidecar without `usage` and proceed unchanged, and never estimate or hand-author a `usage` record; state that the bare `--json` form remains the documented fallback for a round that lost its mint (its record stays non-attributable) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the Validation Commands -> expect the mint-step grep GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `docs: review-staging capture step mints review-run identity at round start` [class: IMPLEMENTATION_REQUIRED]

### Task 3: RED then GREEN - summarizer attribution classification, round collapse, and attributable-only totals

Files:
- `scripts/summarize_review_stats.py`

- [ ] `summarize_review_stats#current_adapter_usage_attribution_classes`; given post-cutover payloads carrying (a) an identity record with `attribution == "interval-identity"`, (b) a legacy record with `ambiguous: true` and no attribution field, (c) a telemetry-era record with `ambiguous: false` and no attribution field, and (d) no `usage` key, expects the classification helper to return attributable, ambiguous, ambiguous, and absent respectively (absence of the attribution field is NEVER attributable) [class: REPOSITORY_TEST]
- [ ] `summarize_review_stats#coverage_four_counts`; given a corpus mixing the four classes over post-cutover sidecars, expects the usage coverage block to publish `sidecars_with_usage` (present), `sidecars_attributable`, `sidecars_ambiguous`, and `sidecars_missing` (post-cutover sidecars without a usage record), with the pre-cutover exclusion unchanged and the published `coverage` fraction key keeping its presence-based meaning [class: REPOSITORY_TEST]
- [ ] `summarize_review_stats#round_collapse_superseded_captures`; given two attributable sidecar records sharing one `review_run_id` (the second captured later), expects the per-round decision-grade total to equal the LATER record's totals, not the sum, with the earlier record counted as present, excluded from sums, and published in a `sidecars_superseded_captures` count (nested intervals within one round never multiply-count) [class: REPOSITORY_TEST]
- [ ] `summarize_review_stats#observed_totals_attributable_only`; given one attributable and one ambiguous record (distinct run ids), expects `observed_token_totals` to equal the attributable record's totals ONLY, and a separate `ambiguous_observed_token_totals` block to carry the ambiguous union labeled non-decision-grade (visible, never merged, never silently assigned) [class: REPOSITORY_TEST]
- [ ] `summarize_review_stats#decision_rule_binds_attributable_coverage`; the threshold decision binds attributable coverage over post-`ATTRIBUTION_CUTOVER_DATE` sidecars only: given presence coverage at or above 70 percent but attributable coverage below it, expects the supplementary label kept; given attributable coverage at or above 70 percent, expects it dropped; an EXACT-0.70 attributable corpus (7 of 10 post-attribution-cutover sidecars attributable) pins the boundary, and pre-attribution-cutover legacy records are asserted absent from the attributable-coverage denominator [class: REPOSITORY_TEST]
- [ ] Rewrite the pre-existing current-adapter usage selftests in place to the attributable contract (the telemetry plan's rewrite-not-delete pattern): `coverage_post_cutover_denominator` and `decision_rule_supplementary` gain attribution-bearing fixtures with totals and threshold expectations re-pinned, plus ambiguous-only fixture variants asserting the excluded totals land in `ambiguous_observed_token_totals`; add ambiguous-only corpus fixtures asserting the five new provenance keys are read tolerantly and a legacy record without them stays parseable [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 scripts/summarize_review_stats.py --selftest` -> expect RED [class: REPOSITORY_TEST]
- [ ] Implement: `ATTRIBUTION_CUTOVER_DATE = "2026-10-03"` (this plan's landing date; post-cutover classification unchanged); the classification helper; the four counts plus `sidecars_superseded_captures`; the per-run collapse (max `captured_at_ms` per `review_run_id` among attributable records); the attributable-only `observed_token_totals`; the `ambiguous_observed_token_totals` block; the threshold rebind; rewrite the usage comment block (~965-978) and the report-builder limitation text (~1907-1912) to the attributable-only basis - retiring the overlapping-window limitation for attributable records while keeping it for ambiguous/legacy unions (r1 F11); duplicate `review_run_id` occurrences across distinct rounds are reported as a corpus-hygiene count in the coverage block (r1 F18); the report-line wording states the attributable-only basis [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 scripts/summarize_review_stats.py --selftest` -> expect GREEN (usage selftests rewritten to the attributable contract; legacy worker-shape adapter determinism tests unchanged) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: summarizer classifies usage attribution and sums one attributable record per round` [class: IMPLEMENTATION_REQUIRED]

### Task 4: RED then GREEN - initial versus follow-up round token analysis

Files:
- `scripts/summarize_review_stats.py`

- [ ] `summarize_review_stats#usage_by_round_initial_vs_followup`; given loops with r1/r2/r3 sidecars where token usage is readable only from attributable records, expects per-round token totals (after the round collapse) joined alongside accepted unique findings per round (final triage in `ACCEPTED_TRIAGE_VALUES`, pulled from the effectiveness-pass seam) AND the existing staged per-round findings, blocking, and ready counts, with r1 reported as the initial round and r2+ as follow-ups [class: REPOSITORY_TEST]
- [ ] `summarize_review_stats#usage_by_band_and_mode`; given a multi-band, multi-mode corpus with distinct attributable totals per record, expects the analysis tables segmented by the same complexity bands as the existing tables PLUS a NEW `panel_mode` axis (`full`/`focused`, legacy sidecars lacking the field in an `unknown` cell; the mode axis is new segmentation machinery - only the band grouping exists today), with each table cell equal to exactly its own records' totals and sibling cells zero or absent (aggregate-only output: no slugs, no paths, no per-file rows) [class: REPOSITORY_TEST]
- [ ] `summarize_review_stats#token_conclusions_inconclusive_on_thin_samples`; with `USAGE_ANALYSIS_MIN_ROUNDS = 3` named in the source: given attributable coverage below the decision threshold, or any analysis cell holding fewer than 3 collapsed attributable rounds, expects every token-based conclusion line in that cell marked inconclusive; a CONTRAST cell at or above the floor with adequate attributable coverage carries NO marker (the marker is data-derived, never decorative) [class: REPOSITORY_TEST]
- [ ] Run `python3 scripts/summarize_review_stats.py --selftest` -> expect RED [class: REPOSITORY_TEST]
- [ ] Implement: the initial-versus-follow-up usage tables in the review-corpus metrics pass, segmented by band and the new `panel_mode` axis, reading collapsed attributable records only, joining accepted unique findings alongside the staged counts, with `USAGE_ANALYSIS_MIN_ROUNDS = 3` and the inconclusive markers; keep the privacy invariant (aggregate counts only) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 scripts/summarize_review_stats.py --selftest` -> expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `feat: review-corpus metrics compare round token usage with inconclusive markers` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Full validation pass and completion

Files:
- none (validation and bookkeeping only)

- [ ] Run every Validation Command in order -> expect each GREEN, including the mint-step grep that was RED before Task 2 and the negated never-estimate sweep [class: REPOSITORY_TEST]
- [ ] Confirm zero sidecars were modified anywhere in the working tree (`git status --short` shows no `.stats.json` paths); historical sidecars are immutable inputs [class: REPOSITORY_TEST]
- [ ] Confirm the fresh-probe evidence recorded in Driving force: re-run BOTH read-only store counts (the `turn_usage` and `model_usage` completed-row totals) AND the three corpus counts over `docs/reviews` (sidecar total, usage-bearing, ambiguous); a material drift in any of them is a plan-relevant finding, not a silent proceed [class: REPOSITORY_TEST]
- [ ] Run one live identity-invocation capture against the real store (mint, then `--json` with the minted identity) and confirm a record prints; record its `attribution` and `source_grain` values as completion evidence [class: REPOSITORY_TEST]
- [ ] Probe the live store's parent linkage read-only (the fraction of recent anchor sessions with non-null `parent_id`, and the root count of the most recent review round's sessions) and record it as completion evidence; on NULL linkage the completion record states the honest fallback (only single-root rounds are attributable) [class: REPOSITORY_TEST]
- [ ] Check the round's own fresh sidecars (post-landing review rounds) carry `review_run_id` in usage provenance, or the completion report names the skipped-mint gap explicitly [class: REPOSITORY_TEST]
- [ ] Run the duplicate-origin coverage gate for the cited origin and mark it covered per the completion duty [class: REPOSITORY_TEST]
- [ ] Commit (if any residue): `chore: review token round attribution validation residue` [class: IMPLEMENTATION_REQUIRED]
