# Plan: Phase 2 - Review Effectiveness Telemetry

Depends on: `docs/plans/2026-07-27-five-worker-review-panel.md`

Plan review: `docs/reviews/2026-07-27-plan-review-phase-2-review-telemetry-r2.md` (latest, not ready)

## Terms

- **Baseline corpus**: artifacts captured by the immutable private snapshot before the Phase 1 cutover marker.
- **Growth corpus**: later artifacts whose panel identities prove the five-worker policy.
- **Conservation ledger**: classification of every discovered sidecar as current, legacy, malformed, unsupported, duplicate, baseline-missing, or growth.
- **Accepted finding**: a unique staged finding whose final triage is `fixed` or `deferred`; `dropped` findings are not accepted.
- **Observed token usage**: token counts copied from a captured runtime usage report, with a named adapter and provenance record.
- **Comparable cohort**: reviews with the same review type, panel mode, initial or follow-up role, domain-risk class, and deterministic artifact-size bucket.

## Gist & Examples

Phase 2 measures whether the five-worker policy reduces review cost without reducing useful findings. It uses data already present in review sidecars: worker launches, loaded lenses, raw and staged findings, deduplication, discards, severity calibration, overflow, and final triage.

The first useful report does not depend on provider token APIs or durable cross-session lineage. Worker launches are the primary cost measure. Token totals are included only when a sidecar already contains observed usage with a named adapter and provenance. Missing token data stays missing and is reported as coverage, never estimated.

The historical path-level baseline is private. It is written under `~/.ai-playbook/review-telemetry/`, not committed to this public repository. Tracked tests use neutral generated fixtures. Public output contains aggregate counts only and rejects repository names, ticket identifiers, feature names, absolute paths, and content digests.

Example outcome:

- Baseline median: eight worker launches per initial full review.
- Five-worker median: five worker launches.
- Accepted unique findings per comparable review remain within the effectiveness guardrail.
- Result: retain the five-worker default.

If the post-cutover sample is too small, triage coverage is incomplete, or comparable cohorts do not exist, the result is `inconclusive`; it must not recommend a policy change.

Provider-specific usage adapters and durable review lineage are separate follow-up plans. They are not prerequisites for this phase.

## Evaluation Criteria

**Quality dimensions:**

- Privacy: no tracked file contains private repository paths, review filenames, ticket identifiers, feature names, or historical content digests.
- Conservation: every discovered sidecar belongs to exactly one ledger class, and a missing baseline file cannot be hidden by a new file with the same shape.
- Compatibility: current five-worker sidecars and representative legacy code, plan, RFC, and document sidecars are classified without rewrites.
- Cost: report initial-panel launches, full-cycle launches, and launches per accepted unique finding.
- Effectiveness: report accepted unique findings, discard rate, false-positive rate, overflow rate, and severity-calibration rate by comparable cohort.
- Token accuracy: include token totals only for observed usage with named provenance; always report observed-token coverage.
- Reproducibility: the same private baseline and corpus produce byte-stable aggregate JSON.

**Decision rule:**

- Require at least ten completed reviews in both the baseline and growth sides of a comparable cohort and at least 80% final-triage coverage on each side; otherwise report `inconclusive`.
- Retain the five-worker default when median launches per initial full review fall by at least 25%, accepted unique findings per comparable review do not fall by more than 20%, and the dropped-finding rate does not rise by more than 10 percentage points.
- Report `review needed` when a threshold is missed. Do not automatically change panel policy.
- Treat token cost as supplementary until observed-token coverage reaches 70% in both periods.

**Metric formulas:**

- Accepted unique findings per review = median per-review count of staged findings whose final triage is `fixed` or `deferred`; reviews with pending triage count toward coverage but not the median.
- Synthesis discard rate = total synthesis-discard rows divided by total raw findings; zero raw findings yields `null`.
- Final dropped-finding rate = total staged findings with final triage `dropped` divided by total staged findings with final triage; zero finalized findings yields `null`.
- False-positive rate = discarded rows with reason `false-positive` or `assumption-invalid` divided by total raw findings; zero raw findings yields `null`.
- Cohorts are weighted equally in the final decision. A `null` decision metric or missing workload-comparable cohort makes the result `inconclusive`.

**Release gates:**

- Phase 1 has a fresh review with zero unresolved blocking findings.
- Summarizer self-tests cover current and legacy adapters, corpus discovery, conservation, privacy, cohort comparison, and inconclusive outcomes.
- The private baseline accounts for every discovered historical sidecar by local path and content digest.
- Strict audit reports no unexplained ledger delta.
- The aggregate report contains no repository or artifact identifiers and passes public-hygiene checks.
- No historical review Markdown or sidecar is modified.
- No provider token value is estimated.
- No durable-lineage or strict producer-schema change is introduced.
- No-em-dash and `git diff --check` pass.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope:

**Production code and documentation:**

- `scripts/summarize_review_stats.py` *(new)*
- `README.md`
- `docs/plans/2026-07-27-phase-2-review-telemetry.md`

**Runtime-private outputs:**

- `~/.ai-playbook/review-telemetry/baseline.json` *(new, local only)*
- `~/.ai-playbook/review-telemetry/effectiveness-report.json` *(new, local only)*
- `~/.ai-playbook/review-telemetry/effectiveness-report.md` *(new, local only)*

**Read-only inputs:**

- Review sidecars under repositories discovered from `personal_projects_root` and `company_projects_root` in `~/.ai-playbook/facts.md`
- Each repository’s resolved `reviews_dir`
- Legacy `docs/history/reviews/` directories

**Plan-related extension**; implementation and review may change an unlisted file only when it is causally required to complete the summarizer, keep its public documentation accurate, or fix a regression introduced by this plan. Add repeatedly affected tracked paths to the explicit list.

**Out of scope; reject unless plan-related:**

- Phase 1 producer, validator, severity, finding-budget, and cycle-policy fixes; owned by Phase 1 Task 3.
- Historical review Markdown and sidecars; immutable read-only inputs.
- A tracked path-level baseline or report containing repository or artifact identifiers.
- Provider-specific token adapters or inferred token estimates.
- Durable review lineage, generation state, cross-session counters, and strict Stats v2 producer activation.
- Automatic changes to the five-worker policy based on the report.

## Design Invariants

1. Historical review artifacts remain immutable.
2. Path-level baseline and conservation data remain local and untracked.
3. Every discovered sidecar is classified exactly once.
4. Aggregate public output contains no repository or artifact identifiers.
5. Worker and lens attribution remain separate through aggregation.
6. Missing token usage remains explicit and is never estimated.
7. Insufficient samples or triage coverage produce `inconclusive`.
8. The report informs a later decision; it never changes review policy automatically.
9. `~/.ai-playbook/review-telemetry/` uses mode `0700`; private files use `0600`, reject symlink targets, and publish by atomic rename.
10. One summarizer process owns the telemetry directory at a time, and each input’s digest and parsed data come from the same immutable byte buffer.

## Validation Commands

```bash
python3 -m py_compile scripts/summarize_review_stats.py
python3 scripts/summarize_review_stats.py --selftest

test -f ~/.ai-playbook/review-telemetry/baseline.json || \
  python3 scripts/summarize_review_stats.py \
    --user-facts ~/.ai-playbook/facts.md \
    --init-baseline ~/.ai-playbook/review-telemetry/baseline.json

python3 scripts/summarize_review_stats.py \
  --user-facts ~/.ai-playbook/facts.md \
  --baseline-manifest ~/.ai-playbook/review-telemetry/baseline.json \
  --strict-audit \
  --json-report ~/.ai-playbook/review-telemetry/effectiveness-report.json \
  --markdown-report ~/.ai-playbook/review-telemetry/effectiveness-report.md

test "$(stat -f '%Lp' ~/.ai-playbook/review-telemetry)" = "700"
test "$(stat -f '%Lp' ~/.ai-playbook/review-telemetry/baseline.json)" = "600"
test ! -e docs/review-stats-baseline.json
! rg -n '/Users/|/home/[A-Za-z0-9._-]+/|[A-Z]{2,10}-[0-9]+' \
  ~/.ai-playbook/review-telemetry/effectiveness-report.json \
  ~/.ai-playbook/review-telemetry/effectiveness-report.md

bash ~/.ai-playbook/scripts/check-no-em-dash.sh touched
git diff --check
```

### Task 1: Build private corpus discovery and conservation

Files:

- `scripts/summarize_review_stats.py` *(new)*
- `README.md`
- `~/.ai-playbook/review-telemetry/baseline.json` *(new, local only)*

- [ ] `summarize_review_stats#facts_roots`; given the user facts document, expects both workspace roots to resolve without embedding their values in tracked output.
- [ ] `summarize_review_stats#review_directory_discovery`; given repositories with configured `reviews_dir`, legacy `docs/history/reviews/`, symlinks, and duplicate real paths, expects every real sidecar to be discovered once.
- [ ] Create `~/.ai-playbook/review-telemetry/` as `0700`; create private files as `0600`, reject symlink targets, and use exclusive temporary files plus atomic rename.
- [ ] Define `--init-baseline` as atomic create that fails when the manifest exists; define `--strict-audit` as read-only and fail when the baseline is missing, malformed, replaced, or mismatched; any refresh is a separate explicit command.
- [ ] Record an explicit Phase 1 policy-cutover marker in the private baseline. Treat snapshot members as baseline, accept later growth only when the five required panel identities are present, and quarantine timestamp, panel, or schema disagreements.
- [ ] `summarize_review_stats#same_shape_replacement`; given one missing baseline path and one new same-shape file, expects strict audit failure.
- [ ] `summarize_review_stats#conservation`; given current, legacy, malformed, unsupported, duplicate, baseline-missing, and growth fixtures, expects every sidecar in exactly one class.
- [ ] `summarize_review_stats#private_manifest`; given path-level corpus data, expects it only in `~/.ai-playbook/review-telemetry/baseline.json` and never in tracked output.
- [ ] `summarize_review_stats#baseline_lifecycle`; given first initialization, overwrite, missing baseline, malformed baseline, explicit refresh, and strict audit, expects the defined safe transition or failure.
- [ ] `summarize_review_stats#private_permissions`; given permissive parent modes or symlink targets, expects corrected `0700`/`0600` modes or hard failure without following the link.
- [ ] `summarize_review_stats#snapshot_race`; given concurrent runs or a sidecar changing during scan, expects one writer and retry or failure before publication.
- [ ] Run -> expect RED before the summarizer exists.
- [ ] Implement single-writer locking; read each input once into bytes used for both digest and parsing; recheck corpus generation before publishing; publish reports atomically.
- [ ] Implement facts-driven discovery, SHA-256 inventory, private baseline lifecycle, cutover classification, quarantine, and strict conservation audit.
- [ ] Run -> expect GREEN: `python3 scripts/summarize_review_stats.py --selftest`.
- [ ] Commit: `review: add private review corpus audit`

### Task 2: Aggregate cost and finding effectiveness

Files:

- `scripts/summarize_review_stats.py`

- [ ] `summarize_review_stats#current_adapter`; given a five-worker sidecar, expects worker and lens launch, dedup, discard, calibration, overflow, and triage totals.
- [ ] `summarize_review_stats#legacy_adapters`; given neutral legacy code, plan, RFC, and document sidecars, expects compatible normalized totals without rewriting the fixture.
- [ ] `summarize_review_stats#accepted_unique`; given fixed, deferred, dropped, and pending findings, expects only fixed and deferred findings in accepted yield and reports pending coverage separately.
- [ ] `summarize_review_stats#observed_usage`; given a named adapter plus captured usage provenance, expects provider-neutral token totals and documented inclusion semantics.
- [ ] `summarize_review_stats#usage_unavailable`; given no captured usage, expects null token totals and explicit missing coverage.
- [ ] `summarize_review_stats#usage_unproven`; given non-null tokens without adapter and provenance, expects strict failure.
- [ ] Run -> expect RED before aggregation exists.
- [ ] Implement launch, cycle, finding-outcome, severity, overflow, calibration, and observed-token coverage aggregation.
- [ ] Run -> expect GREEN: summarizer self-tests.
- [ ] Commit: `review: aggregate review cost and effectiveness`

### Task 3: Produce a privacy-safe policy report

Files:

- `scripts/summarize_review_stats.py`
- `README.md`
- `~/.ai-playbook/review-telemetry/effectiveness-report.json` *(new, local only)*
- `~/.ai-playbook/review-telemetry/effectiveness-report.md` *(new, local only)*

- [ ] `summarize_review_stats#comparable_cohorts`; given mixed review types and panel modes, expects comparisons only inside matching cohorts.
- [ ] `summarize_review_stats#inconclusive_sample`; given fewer than ten post-cutover reviews or less than 80% final-triage coverage, expects `inconclusive`.
- [ ] `summarize_review_stats#retain_policy`; given at least 25% launch reduction, accepted-finding change within the 20% guardrail, and drop-rate change within 10 percentage points, expects `retain`.
- [ ] `summarize_review_stats#review_needed`; given any missed guardrail, expects `review needed` and no automatic policy mutation.
- [ ] `summarize_review_stats#token_supplement`; given less than 70% observed-token coverage in either period, expects token results marked supplementary.
- [ ] `summarize_review_stats#public_output`; given private repository names, paths, ticket IDs, artifact titles, and content digests in the private ledger, expects aggregate reports with none of those values.
- [ ] Run -> expect RED before report generation exists.
- [ ] Implement byte-stable aggregate JSON and a concise Markdown report with `retain`, `review needed`, or `inconclusive`.
- [ ] Run every command under `## Validation Commands`; expect green.
- [ ] Commit: `review: report five-worker panel effectiveness`

### Task 4: Validate the Phase 2 release

Files:

- `scripts/summarize_review_stats.py`
- `README.md`
- `docs/plans/2026-07-27-phase-2-review-telemetry.md`

- [ ] Inspect the full per-file diff and verify no provider adapter, lineage state, strict producer activation, or private identifier entered tracked files.
- [ ] Run the strict real-corpus audit; expect zero unexplained ledger entries.
- [ ] Run the report privacy checks; expect zero path, ticket, repository, artifact, or digest leakage.
- [ ] Verify historical review Markdown and sidecars remain unchanged.
- [ ] Run one fresh five-worker plan review of the current source digest; expect zero unresolved blocking findings.
- [ ] Commit: `review: validate review effectiveness telemetry`
