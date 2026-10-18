# Plan: Review-metrics findings guard

Backlog origin: docs/history/backlog/2026-10-04-review-metrics-summarizer-typeerror.md
Driving force: code-quality (primary), automation (secondary; the consumer is the recurring weekly-measurement-rider metrics pass whose 2026-10-04 run the witnessed crash aborted)
Plan review record: the staging series docs/reviews/2026-10-04-plan-review-review-metrics-findings-guard-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- findings field: the `findings` key of a review-staging sidecar payload; a list of finding rows when well-formed.
- malformed sidecar: a sidecar payload whose findings field is present and not null and not a list (the witnessed shape: an integer count; a null findings value aggregates as today).
- counts-only sidecar: a sidecar carrying a counts block with the findings field absent; a sanctioned input the metrics pass aggregates today (blocking columns read 0).
- counts block: the sidecar's `counts` object of integer totals (raw, staged, dedup); the aggregation source for counts-only sidecars.
- metrics pass: the summarizer's `--metrics` mode (`run_metrics_pass` / `cmd_metrics`); read-only corpus aggregation into per-band loop metrics.
- effectiveness pass: the summarizer's cohort-effectiveness aggregation (`aggregate_sidecar` consumers, including the strict-audit publish path).
- loop: in the metrics pass, the per-artifact-slug sequence of round records (one sidecar per round) that the per-band aggregates and report columns are built from.
- blocking columns: the report columns counting findings whose blocking flag is true; they read 0 for counts-only sidecars.
- legacy bucket: the metrics pass's single unknown/unusable-sidecar counter (`sidecars_legacy_bucket`); failing sidecars land there instead of failing the pass.
- aggregation seam: a code site that reads the findings field off a payload and iterates or measures it.
- registry selftest: the summarizer's embedded `--selftest` tests (`_registry`, dotted names); each test is mapped to a subset tag in `_SUBSET_OF`.
- weekly-measurement-rider (rider): the recurring maintenance task whose review-metrics pass consumes this summarizer; the witnessed crash happened during its run.
- current-v1 (v1): a sidecar declaring schema version 1, validated by `validate_review_staging.validate_version1_payload`.
- versionless: a legacy sidecar with no schema version; never judged against the version-1 contract (legacy compatibility input).

## Why

A sidecar whose findings field is an integer instead of a list crashes the review-metrics summarizer with `TypeError: 'int' object is not iterable`, and the 2026-10-04 weekly-measurement-rider run died on exactly this shape, producing no metrics report. The version-1 validator does not shape-check this field (probed: zero errors on an int findings payload), so the crash is reachable from both legacy and current-v1 sidecars. The summarizer must skip such a sidecar with a named warning and still produce aggregates over the valid set.

## Outcome

The review-metrics summarizer tolerates a non-list findings field everywhere: the metrics pass skips the malformed sidecar into the legacy bucket with a one-line stderr warning naming the path, and no aggregation seam can raise on the shape.

- A metrics pass over a corpus containing a malformed sidecar exits 0, writes both aggregate outputs, reports the skip on stderr with the sidecar path (repo-relative when it sits under the scanned root; basename plus a fixed `(outside scanned repo root)` placeholder otherwise), and shows the skip count on its stdout summary line.
- The effectiveness pass and every aggregation seam normalize or skip the same shape instead of crashing; the effectiveness pass counts the skipped sidecar in its existing `availability.skipped_malformed` channel, so both passes exclude the class instead of disagreeing.
- Counts-only sidecars keep aggregating exactly as today; no sanctioned input class regresses.

Gate delta: none beyond the witnessed-defect fix. The metrics skip branch is itself the fix-class sanctioned exit (the origin-cited crash leaves no working exit today), so no refusal-path payment is due; no new hard gates, refusal classes, fences, protocol layers, or schema fields are added. The two observability additions are priced by their origin-cited witness (today the crash is the loud signal the rider records, and the skip would remove it): the stdout summary line's malformed-skip count and the effectiveness pass's reuse of its existing skipped-malformed counter restore a human-readable signal for the newly silent class. The skip count travels the pipeline as one underscore-prefixed internal runtime key that `serialize_metrics_json` pops before `json.dumps`, so the tracked report bytes stay aggregate-only and unchanged in schema by construction, not by convention.

## Assumptions

- A malformed sidecar is skipped whole in the metrics pass (not coerced to a counts-only loop); basis: origin Expected line "skips a malformed one with a named warning line" and origin Suggested fix shape line "aggregates over the valid set" (docs/history/backlog/2026-10-04-review-metrics-summarizer-typeerror.md, 2026-10-04).
- All findings-iteration seams in the summarizer harden together (metrics and effectiveness passes share the same `or []` pattern and the same crash class); the two pass-boundary gates own the malformed class on live paths, and the seam hardenings stay as defense-in-depth because the seams are module-level functions any future caller or selftest invokes directly, so each normalizes at read; basis: seam probe of 2026-10-04 (all four seams raise TypeError on the shape) and the family-mask rule (user-level lesson #317).
- The version-1 validator contract is not widened; the summarizer's own gate owns the shape for v1 sidecars too; basis: probe of 2026-10-04 (`validate_version1_payload` returns zero errors on an int findings v1 payload) and the origin scoping the fix to the summarizer's load path.
- The warning goes to stderr and names the sidecar path (repo-relative when it sits under the scanned root; basename plus the fixed `(outside scanned repo root)` placeholder otherwise); tracked report bytes never carry paths; basis: origin fix shape ("log a one-line skip naming the sidecar path") plus the summarizer's privacy invariant that public outputs stay aggregate-only and the strict-audit publish note's paths-stay-private stderr precedent.
- Both passes exclude the malformed class rather than disagreeing: the metrics pass skips it into the legacy bucket with the named warning, and the effectiveness pass skips it per-sidecar through its existing malformed-sidecar channel (`availability.skipped_malformed`, surfaced by the existing strict-audit stderr note); basis: the r1 dual-surface parity finding and the pre-existing skip channel in `build_effectiveness_report`.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: guard the review-metrics summarizer against a non-list findings sidecar field, so the weekly metrics pass cannot crash, per the witnessed rider failure.

Today a `*.stats.json` sidecar carrying `"findings": 5` kills the whole pass:

```
TypeError: 'int' object is not iterable
  ... in accepted_unique_count  (for f in findings)
```

After this plan the same corpus aggregates over the valid sidecars, the malformed one is counted into the legacy bucket, and stderr carries one line naming it, for example:

```
metrics: skipping docs/history/reviews/2026-10-04-plan-review-x-r1.stats.json: findings field is not a list
```

A counts-only sidecar (findings absent, counts block present) is untouched: it still aggregates as a loop with blocking columns reading 0, and so do a null findings value and an empty list; a falsy-present non-list scalar (`0`, `false`, the empty string) instead skips with a warning (the recorded behavior change Task 2's gate makes).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the probed CLI crash (exit 1, TypeError at `accepted_unique_count`) flips to exit 0 with outputs over the valid set; every hardened seam has its own registry canary.
- regression safety: counts-only sidecars still aggregate; the metrics and aggregation selftest subsets stay ALL PASS; the full selftest suite stays ALL PASS.
- maintainability: one shape-normalizing helper replaces every unguarded findings read; no duplicated isinstance ladders.

**Done when:**
- `python3 scripts/summarize_review_stats.py --selftest --subset metrics` and `--subset aggregation` report ALL PASS including the new canaries.
- The full `--selftest` reports ALL PASS.
- The em-dash added-lines gate and the public-hygiene scan exit 0 over the touched file.
- No tracked file outside scripts/summarize_review_stats.py changed.

**Ship when:**
- None; repository-internal tooling with no deploy surface.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/summarize_review_stats.py` (partially in scope: the new findings-shape helper; `aggregate_current`; `aggregate_legacy`; `accepted_unique_count`; `triage_coverage`; `_loops_from_sidecars`; `run_metrics_pass`'s `_loops_from_sidecars` call site and its `build_metrics_report` call (the repo-root and skip-count plumbing lines plus the accumulation variable); `build_metrics_report`'s signature and its single internal-key assignment; `serialize_metrics_json`'s single internal-key pop before `json.dumps`; `serialize_metrics_markdown`'s legacy-bucket legend string; the per-sidecar malformed-skip loop in `build_effectiveness_report` and its docstring's `availability.skipped_malformed` membership sentence; `cmd_metrics`'s stdout summary line; the docstrings of `_loops_from_sidecars`, `run_metrics_pass`, `cmd_metrics`; the `_registry`/`_SUBSET_OF` selftest additions. All other functions and regions in this file are frozen; reject any review finding that touches them and file it as a separate note instead.)

**Tests:**
- none listed separately; the registry selftests are embedded in `scripts/summarize_review_stats.py` (the new canaries live beside the existing `metrics_legacy_tolerance` and aggregation tests), so the Production code entry above covers the test layer too

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; the version-1 validator contract is not widened (assumption3; the summarizer gate owns the shape)
- `scripts/hooks_log_summary.py`; a different tool with no witnessed failure of this class
- `docs/maintenance/recurring-tasks/weekly-measurement-rider.md`; the CLI contract is unchanged, so the rider needs no doc delta

## Validation Commands

```bash
base="$(git merge-base main HEAD)"
python3 scripts/summarize_review_stats.py --selftest --subset aggregation || { echo "FAIL: aggregation subset"; exit 1; }
python3 scripts/summarize_review_stats.py --selftest --subset metrics || { echo "FAIL: metrics subset"; exit 1; }
python3 scripts/summarize_review_stats.py --selftest || { echo "FAIL: full selftest"; exit 1; }
bash scripts/check-no-em-dash.sh added-lines --base "$base" -- scripts/summarize_review_stats.py || { echo "FAIL: em-dash added-lines"; exit 1; }
( cd "$(git rev-parse --show-toplevel)" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" --files scripts/summarize_review_stats.py ) || { echo "FAIL: hygiene scan"; exit 1; }
scope_violations="$(git diff --name-only "$base" -- . | grep -v -x 'scripts/summarize_review_stats.py')"
grep_rc=$?
if [ "$grep_rc" -ge 2 ]; then echo "FAIL: scope check tool error rc=$grep_rc"; exit 1; fi
if [ -n "$scope_violations" ]; then echo "FAIL: unexpected tracked change:"; echo "$scope_violations"; exit 1; fi
```

### Authoring-time gate record

- Defect probe (2026-10-04, worktree tree at main 07c8b76a bytes): the real CLI `--metrics --metrics-markdown` over a temp corpus containing one v1 int-findings sidecar, one legacy int-findings sidecar, and one valid v1 sidecar exits 1 with `TypeError: 'int' object is not iterable` at accepted_unique_count (line 1466) reached from `_metrics_round_record` (line 3078); outputs not written. Seam probe: `accepted_unique_count` and `triage_coverage` raise `TypeError: 'int' object is not iterable`; `aggregate_current` and `aggregate_legacy` raise `TypeError: object of type 'int' has no len()` (the len() default fires before the tally loops). Validator probe: `validate_version1_payload` over a v1 payload with `"findings": 5` returns zero errors.
- Rule 19 RED-today evidence: the four seam probes above were executed against today's code and recorded verbatim; the metrics-pass skip canaries are behavioral RED after Task 1 (malformed sidecar aggregated as a loop, stderr silent) and their expectation lines state that intermediate tree state.
- Em-dash self-check at authoring: `bash scripts/check-no-em-dash.sh touched` over the authoring tree exits 0 (the plan bytes carry no U+2014); the execution gate uses `added-lines` against the execution merge base because the file carries four pre-existing U+2014 in frozen docstrings (whole-file scan unsatisfiable per rule 28).
- Public-hygiene scan at authoring: exits 0 (`OUTCOME: pass`) over the plan file.
- plan_readiness pre-round (2026-10-04, this worktree): OUTCOME: pass after two structural fixes (the summarizer was first listed under both Review Scope categories; three Commit items carried no classification tag). Validation block: `bash -n` rc 0; the em-dash added-lines command exits 0 today (no plan-work lines exist in the target file yet; the execution gate binds the added-lines class per rule 28 because the file carries four pre-existing U+2014 in frozen docstrings).
- r1 fold batch (2026-10-04): all 10 non-blocking findings folded (Terms coverage, Gate delta pricing, falsy-boundary predicate and canaries, repo-relative warning form, stdout skip count, effectiveness-side skip via the existing malformed counter, sized-non-list canary leg, teardown discipline, area-prefix commit subjects, merge-base gate base). The validation block's base moved from the raw main ref to the execution merge base (r1 F10).
- r2 fold batch (2026-10-04): all 9 findings folded, including the blocking observability-carrier contradiction (F1: the skip count now travels as an underscore-prefixed internal runtime key popped by `serialize_metrics_json`, with the plumbing slivers named in the Review Scope), the falsy-present scalar skip decision and its canary, the both-subsets RED line, the bounded fallback and control-character strip, the per-invocation stderr capture windows, the Terms malformed-definition alignment, the reordered Task 3 diagnosis, the origin-quote attribution, and the defense-in-depth assumption restatement.
- r3 fold batch (2026-10-04): all 6 findings folded, led by the blocking pop-ordering clause (F1: the serializer pops from a shallow copy with a default, so the caller's dict survives to the stdout read); the falsy-boundaries fixtures pinned versionless with identity, the JSON key-absence assertion leg added to the v1 skip canary, the Gist falsy-shape sentence rewritten to the amended three-class shape, the coined pre-clean phrase replaced with the code's own words, and the gate-record base paraphrase updated.
- r4 fold batch (2026-10-04): all 5 findings folded (the gate pinned before the validation-fail branch, the legend and effectiveness-docstring description slivers named and reworded, the falsy-boundaries fixtures pinned slug-distinct, the Outcome and Assumptions path promises qualified to the fallback policy, and the basename non-uniqueness tradeoff recorded in the docstring policy).
- r5 cap-closure fold (2026-10-04): the cap round's 3 non-blocking findings rode the terminal shape (the adversarial out-of-root and control-character canary, whose unsupported-schema fixture also arbitrates the pinned gate order, and the harness recipe scoped to the metrics-subset canaries); the sidecar re-binds to the post-fold bytes with residuals 0.

### Task 1: Harden the findings-iteration seams

Files:
- `scripts/summarize_review_stats.py`

Evidence:
- `python3 scripts/summarize_review_stats.py --selftest --subset aggregation`; covers the four seam canaries plus the pre-existing aggregation tests staying green.

- [x] Add four registry canaries in the aggregation subset (executed 2026-10-04) (register each in `_SUBSET_OF` under `aggregation`), each building its payload in-process with a temp-tree-free direct call: `summarize_review_stats#findings_guard_accepted_unique`; given a payload `{"findings": 5}`, expects return value 0 and no exception. `summarize_review_stats#findings_guard_aggregate_current`; given a current-shaped payload whose findings field is 5 and whose counts block carries `{"staged_findings": 3}`, expects a normalized dict with the staged total 3 and zeroed triage and severity tallies, no exception; the same canary carries a sized-non-list leg pinning the helper's zeroed totalizing semantics: a payload whose findings field is the string `abc` with an empty counts block expects `staged_findings` 0 (today's `len()` default would count 3). `summarize_review_stats#findings_guard_aggregate_legacy`; given a versionless payload whose findings field is 5, expects a normalized dict with zeroed finding tallies, no exception. `summarize_review_stats#findings_guard_triage_coverage`; given a one-element list of payloads each carrying `{"findings": 5}`, expects coverage 1.0, no exception. [class: REPOSITORY_TEST]
- [x] Run → RED confirmed (executed 2026-10-04: ERROR TypeError on exactly the four new canaries, every pre-existing aggregation test PASS) and PASS on every pre-existing aggregation test (whole-suite outcome at this task point; the metrics subset is untouched by this task). [class: REPOSITORY_TEST]
- [x] Add one module-level helper (`_findings_list`, the shared isinstance(value, list) rule) and replace the four unguarded reads (anchors re-derived from live bytes) and returns it only when it is a list and an empty list otherwise; the one `isinstance(value, list)` rule in this helper is the shared rule the Task 2 skip gate also uses. Replace the four unguarded reads (`aggregate_current` around line 1324, `aggregate_legacy` around line 1353, `accepted_unique_count` around line 1466, `triage_coverage` around line 1482; anchors re-derive from live bytes, the line numbers are the 2026-10-04 main-state witnesses). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: aggregation subset ALL PASS (executed 2026-10-04)
- [x] Commit: `scripts: normalize non-list findings at the summarizer aggregation seams` (c4f05150) [class: IMPLEMENTATION_REQUIRED]

### Task 2: Metrics-pass skip and warn for malformed findings sidecars

Files:
- `scripts/summarize_review_stats.py`

Evidence:
- `python3 scripts/summarize_review_stats.py --selftest --subset metrics`; covers the skip-and-warn canaries, the falsy-boundaries regression guard, and the pre-existing metrics tests staying green.
- `python3 scripts/summarize_review_stats.py --selftest --subset aggregation`; covers the effectiveness-skip canary and the pre-existing aggregation tests staying green.

- [x] Add six registry canaries (executed 2026-10-04; the effectiveness exclusion assertion reads the report's availability_counts shape: cohorts 1 and comparable_cohorts 1); each metrics-subset canary builds a temp tree with `_write_private_sidecar`, `run_metrics_pass`, then a `cmd_metrics` command-layer leg, modeled on `metrics_legacy_tolerance` including its cleanup discipline (try/finally rmtree plus the dedicated teardown-check assertion), while the aggregation-subset effectiveness canary runs in-process over classified baseline/growth pairs: `summarize_review_stats#metrics_skips_non_list_findings_legacy` (metrics subset); given a valid two-round loop beside a versionless sidecar that carries `artifact_slug` and `round` (so the loop-identity path cannot mask the shape gate) and whose findings field is 3, expects the legacy bucket count 1, the loop's series intact, exit 0, both outputs written, and exactly one stderr line naming the malformed sidecar's path in repo-relative form. `summarize_review_stats#metrics_skips_non_list_findings_v1` (metrics subset); given a valid loop beside a v1 sidecar whose findings field is 5 (the validator stays silent on this shape), expects the same skip, count, warning, and exit 0 behavior, and its `cmd_metrics` command-layer leg also parses the written JSON output and asserts the underscore-prefixed internal key is absent (the tracked-bytes-unchanged guarantee is verified, not just implemented). `summarize_review_stats#metrics_skips_falsy_present_scalar` (metrics subset); given a valid loop beside a versionless sidecar carrying `artifact_slug` and `round` whose findings field is `0` (falsy-present non-list: the not-None predicate skips it, a recorded behavior change from today's silent pass), expects the legacy bucket count 1, one warning line, and the valid loop intact. `summarize_review_stats#metrics_skips_out_of_root_sidecar` (metrics subset); given a repo whose own facts set an absolute external `reviews_dir` (inside the temp tree, outside the repo root) containing a malformed sidecar with schema version 99 and findings 5, and an in-repo malformed sidecar whose filename carries a tab character, expects the legacy bucket count 2 and, per invocation, exactly two stderr warning lines: the external sidecar's line carries its basename plus the fixed `(outside scanned repo root)` placeholder and no absolute-path substring of the external tree appears anywhere in stderr (the warning also arbitrates the pinned gate-before-validation order: a gate placed after the validation branch would bucket this unsupported-schema class silently and this assertion fails), and the control-character filename still yields exactly one line (the strip prevented forged extra lines). `summarize_review_stats#metrics_falsy_findings_aggregate` (metrics subset); given three versionless sidecars, each carrying `artifact_slug` and `round` with a DISTINCT artifact_slug per fixture, distinct from the valid loop's slug (the versionless class is load-bearing: the v1 validator rejects a null findings value, so a v1 null fixture lands in the legacy bucket and the expectation would be unsatisfiable; and loops count per slug, so same-slug or colliding authoring under-counts), namely a counts-only sidecar (counts block, findings key absent), a sidecar with `"findings": null`, and a sidecar with `"findings": []`, beside a valid loop, expects all four loops aggregated, legacy bucket 0, and no stderr warning line (the not-present, null, and empty-list classes never skip). `summarize_review_stats#effectiveness_skips_malformed_findings` (aggregation subset); given classified baseline/growth pairs including one malformed-findings payload, expects the payload counted in `availability.skipped_malformed` and excluded from the cohort buckets. The skip canaries also assert the stdout summary line carries the malformed-skip count while the falsy canary asserts the line stays in today's shape. Capture stderr per invocation: around the `run_metrics_pass` leg assert the expected warning line count and shapes, reset the buffer, then around the `cmd_metrics` leg assert the same again (both legs emit; an unscoped capture would double the count). [class: REPOSITORY_TEST]
- [x] Run → RED confirmed (executed 2026-10-04: the four skip canaries FAIL exactly as the expectation lines state; falsy canary and pre-existing tests PASS) (after Task 1 the malformed sidecars no longer crash but aggregate as loops: legacy bucket 0, stderr silent, stdout line unchanged) and PASSes the falsy-boundaries canary plus every pre-existing metrics test; `--subset aggregation` FAILs exactly the effectiveness canary (`skipped_malformed` 0, payload inside the buckets) and PASSes every pre-existing aggregation test (whole-suite outcome at this task point, both subsets the Evidence names). [class: REPOSITORY_TEST]
- [x] Add the skip gate, skip-count plumbing (triple return, run_metrics_pass accumulation, build_metrics_report internal key `_malformed_findings_skips`, serializer pop with default, zero-suppressed stdout count), the warning helper (repo-relative, basename-plus-placeholder fallback, isprintable control-character strip, no new import), the docstring updates, and the two reader-facing description rewords: when the findings value is present (not None) and not a list, per the same `isinstance(value, list)` rule the Task 1 helper uses (a null findings value and an empty list aggregate as today, so the gate and the seams treat falsy shapes identically; a falsy-present non-list scalar such as `0`, `false`, or the empty string IS malformed under this predicate and skips, which is a recorded behavior change from today's silent pass), count the sidecar into the legacy bucket, write one stderr line of the form `metrics: skipping <repo-relative sidecar path>: findings field is not a list` (pass the repo root being scanned into `_loops_from_sidecars` so the path prints relative to it; an out-of-root path emits its basename plus a fixed `(outside scanned repo root)` placeholder instead of the resolved absolute path, and the interpolated path string passes through a one-line control-character strip before emission), and continue (the sidecar never becomes a loop record; the gate sits before the validation branch, so an unsupported-schema malformed sidecar also gets the warning and the count). Return the skip count from `_loops_from_sidecars` (its return becomes `(loops, legacy_count, malformed_skips)`) and thread it through `run_metrics_pass`, which accumulates the count across repos and passes it into `build_metrics_report`; the report stores it under one underscore-prefixed internal key beside the public fields, `serialize_metrics_json` pops that one key from a shallow copy with a default before `json.dumps` (never mutating the caller's dict and tolerating its absence, so the tracked JSON bytes stay unchanged, the key-less frozen fixture keeps passing, and `cmd_metrics`'s post-write stdout read still sees the count), the named-key markdown serializer ignores it, and `cmd_metrics` reads it for the zero-suppressed stdout count. Update the docstrings of `_loops_from_sidecars`, `run_metrics_pass`, and `cmd_metrics` to state the skip-and-warn semantics, the widened legacy-bucket meaning, and the stderr path policy (repo-relative form, basename-plus-placeholder fallback, control-character strip; the basename form is intentionally non-unique across external review trees, the accepted privacy tradeoff, so a collision is never fixed by restoring absolute paths; matching the strict-audit publish note's paths-stay-private precedent with the origin's named-warning demand satisfied by the relative form). Reword the two reader-facing descriptions of the widened counters in the same task: the legacy-bucket legend string inside `serialize_metrics_markdown` gains the skipped-for-malformed-findings class beside validation failures and unusable identity, and the `availability.skipped_malformed` membership sentence in `build_effectiveness_report`'s docstring names the shared predicate (no selftest pins either string; no schema or JSON byte change). [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the effectiveness per-sidecar skip with the same present-and-not-list predicate counting into availability.skipped_malformed (executed 2026-10-04), so a malformed sidecar counts into the existing `availability.skipped_malformed` counter (the existing strict-audit publish stderr note already surfaces that counter; no new public field and no path emission on this surface). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: metrics and aggregation subsets ALL PASS (executed 2026-10-04) [class: REPOSITORY_TEST]
- [x] Commit: `scripts: skip malformed findings sidecars in the metrics pass with a named warning` (64331ec2) [class: IMPLEMENTATION_REQUIRED]

### Task 3: Final validation gate

Files:
- `scripts/summarize_review_stats.py`

Evidence:
- The full Validation Commands block; covers the whole-suite green state, the formatting gates, and the single-file scope check.

- [x] Run the full Validation Commands block; every command exits 0 (executed 2026-10-04; the scope-check leg run with the plan's own grep_rc split so a fully-filtered grep reads as clean; no Task 3 commit needed) (the selftest runs report ALL PASS; the em-dash gate and hygiene scan pass; the scope check lists nothing outside the one file). If the scope check names a file outside the in-scope file, check the executor's own tree first (`git status --short`; a genuine out-of-scope working-tree edit is the primary producer and is fixed in place), then treat an absorbed main advance as the residual hypothesis (re-derive the merge base and rerun); the em-dash leg is path-limited to the in-scope file and cannot name foreign files. [class: REPOSITORY_TEST]
- [x] Commit: `scripts: certify the review-metrics findings guard gates` skipped per the task's own clean-run clause (no gate-driven residue) [class: REPOSITORY_TEST]

## Residual findings (cap closure)

The cap round's staged findings are all resolved in the plan text; entries below record each disposition beside its pattern id.

- security#warning-fallback-strip-unpinned: disposition folded (the adversarial out-of-root and control-character canary in Task 2)
- testing#missing-gate-needle: disposition folded (the same canary's unsupported-schema fixture arbitrates the pinned gate order)
- testing#canary-recipe-wrong-surface: disposition folded (the harness recipe scoped to the metrics-subset canaries)

## Disposition

Executed 2026-10-04/05 from worktree ai-playbook-wt-rmfgx (branch plan-rmfg-exec). Task 1 landed as c4f05150 (RED: ERROR TypeError on exactly the four new aggregation canaries; `_findings_list` helper, four seam replacements, GREEN). Task 2 landed as 64331ec2 (skip gate before the validation branch, triple return with skip-count plumbing into `_malformed_findings_skips`, serializer pop with default, zero-suppressed stdout count, warning helper with repo-relative/placeholder fallback and control-character strip, effectiveness per-sidecar skip into `availability.skipped_malformed`; six canaries RED-then-GREEN). Exec review r1 ready=no with one blocking finding (three metrics canaries lacked the prescribed cmd_metrics legs and stdout assertions); folded additively as cd05fcaf. Exec review r2 ready=yes zero blocking, 1 Low adjudicated done (scope-check leg at the tip names the plan's own receipts commit; clean at the gate-run boundary). Full selftest 557 PASS; em-dash and hygiene gates pass. Origin row folded with this landing.
