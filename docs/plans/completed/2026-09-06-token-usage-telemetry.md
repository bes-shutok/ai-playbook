# Plan: Review Token-Usage Telemetry (producer first)

Feature note (scope of record): `docs/history/feature-notes/2026-07-29-token-usage-telemetry.md`
Phase 2 predecessor: `docs/plans/completed/2026-07-27-phase-2-review-telemetry.md`
Reviews: `docs/reviews/2026-09-06-plan-review-token-usage-telemetry-r*.md`

## Terms

- **Sidecar**: the `.stats.json` file written next to each review staging Markdown; contract defined in the `review-staging` skill (`agents/skills/review-staging/SKILL.md`), enforced by `scripts/validate_review_staging.py`.
- **Producer**: whoever writes a production sidecar. Verified 2026-09-06: that is the reviewing agent following the `review-staging` skill contract (the validator script's `.stats.json` write sites are selftest fixtures only). Capture reaches production sidecars through (1) the capture module's CLI, run by the agent at sidecar-write time, and (2) a capture step written into the `review-staging` skill spec.
- **Summarizer**: `scripts/summarize_review_stats.py`; aggregates sidecars into review cost/effectiveness reports.
- **Usage record**: the optional top-level `usage` sidecar field this plan adds: observed provider token counts plus a provenance block. Always captured from the runtime store, never estimated.
- **Runtime store**: where an agent runtime persists per-request provider usage on local disk. Two adapters are in scope (both probed live 2026-09-06): **zcode-sqlite**, i.e. `~/.zcode/cli/db/db.sqlite` (tables `model_usage`, `session`); its `started_at`/`completed_at`/`first_token_at` columns are **millisecond** epochs (measured: max `completed_at` = `1788707239036`), so every window bound and provenance timestamp is millisecond and suffixed `_ms`; and **codex-rollout**, per-session JSONL at `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl`, whose `session_meta` line records `cwd` and `session_id` (the PARENT thread id: worker rollouts carry a `parent_thread_id` linkage and their own file uuid differs from `session_meta.session_id`, verified live 2026-09-06) and whose `token_count` events carry a cumulative `total_token_usage` object (`input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`, `reasoning_output_tokens`, `total_tokens`).
- **Post-cutover sidecar**: a sidecar whose `payload["date"]` is `>= USAGE_CUTOVER_DATE` (`"2026-09-06"`, named constant added to the summarizer in Task 3). A sidecar missing `date` counts as post-cutover (lands in the coverage denominator); this is conservative by design: a date-less sidecar without `usage` can only suppress coverage downward, never inflate it. A post-cutover sidecar may legitimately lack `usage` (unreadable store, foreign runtime), so the denominator is NOT "sidecars with usage".
- **Coverage**: fraction of post-cutover sidecars that carry a `usage` record. All pre-cutover sidecars are excluded from the denominator by the classification above.
- **Skill-gate marker**: consent marker refreshed before every gated plan-file write per `agents/hooks/skill-gate/README.md` Marker WRITE RECIPE.

## Assumptions

- assume the ZCode runtime store schema as probed 2026-09-06 (`model_usage` columns: `input_tokens`, `output_tokens`, `reasoning_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `computed_total_tokens`, `provider_id`, `model_id`, `agent`, `query_source`, `status`, `started_at`, `completed_at`, `session_id`; `session` columns: `id`, `directory`, `parent_id`); basis: live `.schema` dump and 14 completed rows observed for the authoring session. Observed distinct `query_source` values: `main_turn`, `subagent`, `compact`, `session_title`, `target_completion_verification`. Worker launches live in separate child sessions (ids like `sess_subagent_agent_*` with `parent_id` pointing at the main session, same `directory`; verified live 2026-09-06), so session identity must be collapsed to the root session before counting candidates (see Gist).
- assume no contract-stable in-session environment variable exposes the current session id (probed 2026-09-06: no such var in the runtime env); basis: live env inspection. This is why session discovery is a bounded look-back window over the repo directory, not a direct join.
- assume reviews of this repo run under the ZCode and Codex runtimes for the growth period this plan targets; Cursor and other IDE runtimes are deferred with evidence (see Out of scope). Basis: current environment plus live probes 2026-09-06.
- assume the Codex rollout's `total_token_usage` is CUMULATIVE per session (last `token_count` event wins) and maps to the usage record as `input_tokens`, `cache_read_input_tokens` from `cached_input_tokens`, `cache_creation_input_tokens` from `cache_write_input_tokens`, `output_tokens`, `reasoning_tokens` from `reasoning_output_tokens`, `computed_total_tokens` from `total_tokens`; basis: live rollout inspection 2026-09-06 (`"cwd"`, `"session_id"`, and `token_count` events all observed in real rollout files).
- assume the runtime store uses WAL journal mode (verified 2026-09-06 via `PRAGMA journal_mode`), so a read-only capture concurrent with runtime writes is safe; the capture connection still sets a bounded `busy_timeout` and any lock timeout returns `None` through the fail-open path.

## Gist & Examples

The feature note asks for provider token usage in review sidecars so the summarizer can report review cost in tokens, not just worker launches. It deferred the work because no producer existed: zero sidecars carried a usage field (0/202 on 2026-07-29; re-verified 0/363 on 2026-09-06).

**Where capture happens (resolved).** Review skills (`agents/skills/review-agents/`, `doing-code-review`) are prompt-instruction sets: they can instruct a model to launch workers and stage findings, but they can never observe what the provider charged. Only the agent runtime sees provider usage, and both in-scope runtimes persist it locally: ZCode in `~/.zcode/cli/db/db.sqlite` (`model_usage` rows per model request, tagged with session, agent, and query_source) and Codex in per-session rollout JSONL files (cumulative `token_count` events, `cwd` and `session_id` in `session_meta`). So capture lives in a new **capture module** (`scripts/review_usage_capture.py`) with one adapter per runtime: it tries `zcode-sqlite` first and falls back to `codex-rollout`, reads only, and prints a `usage` record naming the adapter that produced it; the reviewing agent runs that CLI when writing a sidecar, per a new capture step in the `review-staging` skill spec (the gold source for sidecar production). The review-panel skills get no capture duties; nothing in this plan asks a skill to observe tokens.

**The join key is a window over root sessions, not a contract.** No stable in-session variable exposes the session id, so the capture module first resolves the repo anchor as the realpath of `git rev-parse --show-toplevel` from its cwd, then collects every `model_usage` row with `status='completed'` whose `completed_at` (milliseconds) falls inside a named look-back window ending at capture time, filtered to `session.directory` resolving to the repo anchor or a path inside it (subdirectory sessions count). Each candidate session is then collapsed to its ROOT session by walking `session.parent_id` to the top (worker launches live in child sessions like `sess_subagent_agent_*` under the main session, so the raw candidate set is always multi-session for any worker-launching review); all usage accounting (totals, `by_agent_kind`, ambiguity) is computed per ROOT session, and `provenance.session_ids` lists truncated root ids. One distinct root session gives attributed usage; several give a union flagged `ambiguous`; none, or any error (missing db, missing table, locked file, foreign runtime), yields **no** `usage` output at all. Window duration: **6 hours** (`USAGE_WINDOW_MS = 6 * 60 * 60 * 1000`), sized to cover the longest observed review rounds in this repo; a row that started before the window but completed inside it is included (the filter is on `completed_at` only). The `by_agent_kind` buckets classify rows by `query_source` (`main_turn` as `main`, `subagent` as `subagent`, everything else as `other`), which is unaffected by the root collapse because child sessions carry their own `query_source` values. Attribution is session-grained by design: when one session mixed implementation and review work (the execute-plan pattern), the window sums that session's whole usage into the round's totals with `ambiguous: false`; this over-attribution is an accepted limitation of the window join (durable review lineage is the note's deferred follow-up), and it is one reason token cost stays a supplementary signal rather than a decision metric. The emitting agent's sidecar write must succeed identically in every one of those cases: capture is best-effort and fail-open. Missing stays missing; nothing is ever estimated (note non-goal).

**Baseline limitation (from the note, binding here).** Every sidecar produced before the cutover will never carry token data, because it was written before the field existed. Token cost is therefore a forward-looking supplement for growth-period reviews only. The summarizer's coverage metric and decision rule are computed over post-cutover sidecars only (Terms classification); **no decision rule in this plan may require baseline token coverage**, and token cost must never be compared across the cutover.

**Before (today):** a review round completes under ZCode; the reviewing agent writes `review-r1.stats.json` next to the staging Markdown following the `review-staging` skill. The provider consumed ~680k input and ~4.5k output tokens across the round's workers (observed live for the authoring session), but the sidecar records none of it, and the summarizer can only report worker launches.

**After (this plan):** the same round's sidecar also carries an `usage` record (output of `python3 scripts/review_usage_capture.py --json`, merged by the agent per the updated `review-staging` step):

```json
"usage": {
  "adapter": "zcode-sqlite",
  "provenance": {
    "db": "~/.zcode/cli/db/db.sqlite",
    "session_ids": ["sess_89a0cb7"],
    "ambiguous": false,
    "window_started_at_ms": 1788698397679,
    "window_ended_at_ms": 1788719997679,
    "captured_at_ms": 1788719997680,
    "estimated": false
  },
  "totals": {"input_tokens": 682748, "output_tokens": 4546, "reasoning_tokens": 0,
              "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
              "computed_total_tokens": 687294},
  "by_agent_kind": {"main": {"input_tokens": 120000, "output_tokens": 900},
                     "subagent": {"input_tokens": 560000, "output_tokens": 3600},
                     "other": {"input_tokens": 2748, "output_tokens": 46}}
}
```

and the summarizer report gains `observed_token_totals` and `usage_coverage` lines; reviews without usage keep reporting exactly today's numbers. A Codex-run review gets the same record with `adapter: "codex-rollout"` (rollout files matched by `cwd` within the window, each rollout file's last cumulative `token_count` event, summed per session group); any review where neither store yields data has no `usage` key and aggregates byte-identically to today.

**Edge cases that shaped the design:** parallel review sessions on the same repo (both fall inside the window -> `ambiguous: true` union, never a silent pick); `query_source` rows outside `main_turn`/`subagent` (`compact`, `session_title`, `target_completion_verification`) are bucketed under `other` in `by_agent_kind` and always stay inside `totals` (all values are sums of observed rows); per-worker-per-call attribution needs durable lineage, deferred by the note; legacy sidecars already carry no `usage` key and must keep parsing.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: capture never raises into the sidecar-writing flow (fail-open); every error mode (missing db, missing table, empty window, sqlite error, multiple sessions) is covered by a selftest; usage values are sums of observed rows only; all timestamps are millisecond-scale end to end.
- Compatibility: legacy sidecars (no `usage`) parse and aggregate exactly as today; `usage` enters `V1_OPTIONAL_TOP_LEVEL_FIELDS` so no version bump or migration is needed.
- Honest provenance: every emitted `usage` record names the adapter, the db path, the (truncated) session ids, and the millisecond window bounds, and sets `estimated: false`.
- Baseline honesty: the summarizer's decision rule (token cost is supplementary until coverage reaches 70%) is computed over post-cutover sidecars only via the `USAGE_CUTOVER_DATE` classification; no branch of the summarizer requires or assumes baseline token data.
- Test coverage: RED-then-GREEN order; the usage-ignoring adapter tests at the summarizer seam (~line 4090) are deliberately rewritten, not deleted, and the seam comment (~line 928) is updated to the new contract; the production write path (agent-follows-review-staging + capture CLI) is exercised by the CLI selftests and the skill-spec step, not by validator fixtures.

**Done when:**
- `python3 scripts/review_usage_capture.py --selftest` passes (fixture store built at the store's real millisecond scale).
- `python3 scripts/validate_review_staging.py --selftest` passes with the new `usage`-field tests.
- `python3 scripts/summarize_review_stats.py --selftest` passes with observed-token aggregation tests.
- `agents/skills/review-staging/SKILL.md` carries the capture step that routes `usage` records into newly written sidecars (the production wiring; a later real review round is the observable proof, see Ship when).

**Ship when:**
- A real review round executed after cutover produces a sidecar whose `usage` record matches the store content for that round (human observation; not a checklist item).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/review_usage_capture.py` *(new)*
- `scripts/validate_review_staging.py` (the `V1_OPTIONAL_TOP_LEVEL_FIELDS` constant ~line 106 and its selftest coverage; all other functions frozen)
- `agents/skills/review-staging/SKILL.md` (sidecar-production contract: the new capture step; all other sections frozen)

**Tests:**
- `scripts/review_usage_capture.py` (selftests inside the module, `--selftest` flag, same pattern as the sibling scripts) *(new)*
- `scripts/validate_review_staging.py` selftest functions touching `V1_OPTIONAL_TOP_LEVEL_FIELDS`
- `scripts/summarize_review_stats.py` selftest functions at the reserved seam (comment block ~line 928, adapter tests ~line 4090)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-agents/` and `agents/skills/doing-code-review/`; reason: skills are prompt-instruction sets and receive no capture duties under the resolved capture design (the `review-staging` skill is the single wiring point).
- Historical sidecars under any project group; reason: immutable read-only inputs (note non-goal).
- Cursor and other IDE runtimes; reason: no runtime-exposed usage signal exists on local disk (probed 2026-09-06: `~/.cursor/state.vscdb` is empty, chat `meta.json` files carry no token fields, `ai-code-tracking.db` tracks models but no token counts (Cursor usage lives server-side), so there is nothing to capture; missing stays missing per the note's non-goal.

## Validation Commands

```bash
python3 scripts/review_usage_capture.py --selftest
python3 scripts/validate_review_staging.py --selftest
python3 scripts/summarize_review_stats.py --selftest
# usage is an OPTIONAL v1 field, never required, and never estimated:
# (pre-check each swept file so a missing file aborts instead of inverting to a pass)
for f in scripts/review_usage_capture.py scripts/summarize_review_stats.py; do test -f "$f" || { echo "missing $f"; exit 1; }; done
! grep -inE '"estimated": *(true|True)|estimate_[a-z]+\(' scripts/review_usage_capture.py scripts/summarize_review_stats.py
# the seam comment states the NEW contract (RED today; GREEN only after Task 3).
# The [t] escape is intentional: the plan's own text must not satisfy the grep.
grep -q "token usage IS read when presen[t]" scripts/summarize_review_stats.py
# usage is registered as an optional v1 field (RED today; GREEN only after Task 2).
grep -q 'V1_OPTIONAL_TOP_LEVEL_FIELDS.*"usag[e]"' scripts/validate_review_staging.py
# the review-staging skill carries the production capture step (RED today; GREEN after Task 2).
grep -q "review_usage_capture.p[y]" agents/skills/review-staging/SKILL.md
```

### Task 1: RED - capture module selftests against a fixture runtime store

Files:
- `scripts/review_usage_capture.py` *(new)*

- [x] `review_usage_capture#selftest_single_session`; given a fixture sqlite db built at the store's real millisecond scale from the verified `session`/`model_usage` schema with one session for the repo directory and completed rows inside the window, expects a normalized dict with `adapter="zcode-sqlite"`, integer token totals equal to the row sums, `by_agent_kind` bucketing `main_turn` as `main`, `subagent` as `subagent`, and every other `query_source` (e.g. `compact`) as `other` while keeping all rows in `totals`, and provenance naming db path, session id, and millisecond window bounds with `estimated: false`
- [x] `review_usage_capture#selftest_no_db`; given a home directory with no `~/.zcode/cli/db/db.sqlite`, expects `None` and no exception
- [x] `review_usage_capture#selftest_missing_table`; given a fixture db lacking `model_usage`, expects `None`
- [x] `review_usage_capture#selftest_empty_window`; given a fixture db whose only rows complete before the window starts, expects `None`
- [x] `review_usage_capture#selftest_straddling_row_included`; given a row that started before the window start but completed inside it, expects the row counted (filter is on `completed_at` only)
- [x] `review_usage_capture#selftest_child_sessions_collapse`; given one root session plus two child sessions (`parent_id` at the root, same directory) with completed rows inside the window, expects a single attributed record with the root's (truncated) id in provenance, `ambiguous: false`, and child-session rows counted in `totals` and bucketed by their `query_source`
- [x] `review_usage_capture#selftest_two_sessions_ambiguous`; given two ROOT sessions (no parent linkage) for the same directory with rows inside the window, expects a union dict with both (truncated) root ids and `provenance.ambiguous: true`
- [x] `review_usage_capture#selftest_foreign_directory`; given rows only for a different repo directory, expects `None`
- [x] `review_usage_capture#selftest_never_raises`; given a corrupt (non-sqlite) file at the db path, expects `None` and no exception propagating to the caller
- [x] `review_usage_capture#selftest_locked_db`; given a fixture db held by an open exclusive writer connection (lock timeout, bounded by `busy_timeout`), expects `None` after the bounded wait and no exception
- [x] Run `python3 scripts/review_usage_capture.py --selftest` → expect RED (module does not exist)
- [x] Write minimal implementation: read-only sqlite query (`mode=ro`), `USAGE_WINDOW_MS = 6 * 60 * 60 * 1000` window over `completed_at` with `status='completed'` (milliseconds) plus the git-toplevel directory filter described in the Gist, root-session collapse via the `session.parent_id` walk, normalization with the `main`/`subagent`/`other` buckets, root session ids truncated to their first 12 characters in provenance (opaque ids; truncation keeps committed sidecars minimal while preserving forensics), fail-open `try/except` returning `None` on every error path, and a `--json` CLI entry that prints the usage record for the agent to merge into a sidecar
- [x] Run `python3 scripts/review_usage_capture.py --selftest` → expect GREEN
- [x] Commit: `feat: review usage capture module reading runtime store`

### Task 1b: RED - Codex rollout adapter

Files:
- `scripts/review_usage_capture.py`

- [x] `review_usage_capture#selftest_codex_single_rollout`; given a fixture `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` whose `session_meta` line records `cwd` equal to the repo anchor and whose `token_count` events carry cumulative `total_token_usage` objects, expects a normalized dict with `adapter="codex-rollout"`, `provenance.db` naming the rollout directory, `session_ids` holding the truncated rollout session id, and totals mapped per the Assumptions (cached -> cache_read, cache_write -> cache_creation, reasoning_output -> reasoning, total_tokens -> computed_total); the LAST `token_count` event wins
- [x] `review_usage_capture#selftest_codex_root_collapse`; given a parent rollout plus worker rollouts whose `session_meta.session_id` names the parent thread (linked via `parent_thread_id`, verified live 2026-09-06), expects ONE attributed record with the parent's (truncated) id and `ambiguous: false` (root collapse mirrors the zcode join; worker rollouts never count as distinct candidates)
- [x] `review_usage_capture#selftest_codex_no_match`; given rollout files whose `cwd` is a different repo, expects `None`; and separately, given a matching-`cwd` rollout last modified before the window start, expects `None` (two distinct no-match witnesses, not one OR-ed test)
- [x] `review_usage_capture#selftest_codex_two_rollouts_ambiguous`; given two INDEPENDENT parent rollouts (no parent-thread linkage) for the same repo inside the window, expects a union dict with both (truncated) root session ids and `provenance.ambiguous: true`
- [x] `review_usage_capture#selftest_codex_malformed_jsonl`; given a rollout file containing a truncated/garbage line, expects the parser to skip bad lines and still produce a record from the well-formed prefix (or `None` when no `token_count` event survives), never raising
- [x] `review_usage_capture#selftest_adapter_fallback_order`; given a home dir where the zcode db is absent but a matching codex rollout exists, expects the record with `adapter="codex-rollout"`; given both stores yield data, expects the zcode-sqlite record to win (first adapter in `zcode-sqlite`, `codex-rollout` order)
- [x] Run `python3 scripts/review_usage_capture.py --selftest` → expect RED (codex tests fail: adapter not implemented)
- [x] Write minimal implementation: window pre-filter on rollout file mtime, `session_meta` `cwd` matched against the same git-toplevel anchor as the zcode branch (realpath equal to the anchor or a path inside it, never a bare `startswith` prefix), root collapse by grouping rollouts on `session_meta.session_id` (the parent thread id; worker files' own uuids are not candidates), last-`token_count`-wins parsing with per-line `try/except json` skip, the Assumptions field mapping, and the `zcode-sqlite` -> `codex-rollout` fallback order in the `--json` CLI entry (adapter recorded in the emitted record's `adapter` field). Accepted limitation (symmetric with the zcode session-grain note): mtime pre-filter plus last-cumulative-wins attributes session-lifetime tokens for long-lived sessions, not tokens accrued inside the window alone
- [x] Run `python3 scripts/review_usage_capture.py --selftest` → expect GREEN
- [x] Commit: `feat: codex rollout usage adapter with zcode-first fallback`

### Task 2: RED - sidecar schema accepts optional `usage`; production wiring lands in the review-staging skill

Files:
- `scripts/validate_review_staging.py`
- `agents/skills/review-staging/SKILL.md`

- [x] `validate_review_staging#selftest_usage_optional_v1`; given a v1 sidecar payload carrying a well-formed `usage` record, expects validation to pass with `usage` accepted via `V1_OPTIONAL_TOP_LEVEL_FIELDS`
- [x] `validate_review_staging#selftest_usage_absent_legacy`; given the current v1 payload with no `usage` key, expects validation to pass unchanged (legacy sidecars remain parseable)
- [x] `validate_review_staging#selftest_usage_malformed_tolerated`; given a v1 payload whose `usage` is a bare string, expects validation to pass: the validator allowlists the key only, and shape ownership lives in the capture module's selftests (state this division in a comment beside the constant)
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect RED (new checks fail: `usage` not in optional fields)
- [x] Add `"usage"` to `V1_OPTIONAL_TOP_LEVEL_FIELDS` (~line 106) with the shape-ownership comment
- [x] Add the capture step to the `review-staging` sidecar-production contract (Hard gate section area, `agents/skills/review-staging/SKILL.md`): when writing a `.stats.json` sidecar, run `python3 scripts/review_usage_capture.py --json` and merge its output as the top-level `usage` field when it prints one; when it prints nothing (foreign runtime, unreadable store), write the sidecar without `usage` and proceed unchanged. This is the production write path; the validator only accepts the field
  - Review r2 note: the landed path form in the skill is the runtime-absolute `~/.ai-playbook/scripts/review_usage_capture.py` (each file in the runtime scripts dir symlinks into this repo's `scripts/`), not the repo-relative form recorded above.
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN (including all pre-existing checks)
- [x] Commit: `feat: accept optional usage field and route capture through review-staging`

### Task 3: RED - summarizer aggregates observed tokens and coverage

Files:
- `scripts/summarize_review_stats.py`

- [x] `summarize_review_stats#current_adapter_usage_collected`; given a current-schema payload whose `usage` record carries the seam test's previous fixture values, expects the shared extraction helper to return the observed input/output/total token counts while `aggregate_current` attaches none (the report builder is the single extraction path)
- [x] `summarize_review_stats#current_adapter_no_usage_unchanged`; given the same payload without `usage`, expects normalized totals byte-identical to today's output (launch/dedup/triage numbers unchanged, no token fields)
- [x] `summarize_review_stats#current_adapter_malformed_usage_treated_absent`; given a payload whose `usage` is a bare string or missing `totals`, expects the adapter to treat it as absent (no crash, no token fields) mirroring the validator's tolerance
- [x] `summarize_review_stats#coverage_post_cutover_denominator`; given a corpus of one sidecar with `usage`, one legacy pre-cutover sidecar without, and one post-cutover sidecar (date >= `USAGE_CUTOVER_DATE`) without `usage`, expects coverage computed as 1 of 2 post-cutover sidecars: the legacy sidecar is excluded from the denominator by the `date >= USAGE_CUTOVER_DATE` classification, and the post-cutover sidecar without `usage` is in the denominator but not the numerator (the denominator is NOT "sidecars with usage")
- [x] `summarize_review_stats#decision_rule_supplementary`; given observed-token coverage below 70 percent, expects the report to label token cost supplementary; given coverage at or above 70 percent over post-cutover sidecars, expects the supplementary label dropped; and no branch of the rule reads or requires pre-cutover token data
- [x] Run `python3 scripts/summarize_review_stats.py --selftest` → expect RED
- [x] Add `USAGE_CUTOVER_DATE = "2026-09-06"` (post-cutover = `payload["date"] >= USAGE_CUTOVER_DATE`; missing `date` counts as post-cutover); rewrite the usage-ignoring adapter tests (~line 4090) to the collect-and-report contract and update the seam comment block (~line 928) to say token usage IS read when present, still never estimated; add the observed-token totals and coverage lines to the report
- [x] Run `python3 scripts/summarize_review_stats.py --selftest` → expect GREEN (including legacy-adapter determinism tests)
- [x] Commit: `feat: aggregate observed token usage and coverage in review stats`

### Task 4: Full validation pass

Files:
- none (validation only)

- [x] Run every Validation Command in order → expect each GREEN, including the three pinned greps that were RED before Tasks 2-3 and the negated never-estimate sweep
- [x] Confirm zero sidecars were modified anywhere in the working tree (`git status --short` shows no `.stats.json` paths); reason: historical sidecars are immutable inputs
- [x] Commit (if any residue from Tasks 1-3): `chore: token telemetry validation residue`

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-20-turn-usage-token-probe.md: disposition folded into 2026-09-06-token-usage-telemetry.md (2026-09-25); per-item file deleted.
