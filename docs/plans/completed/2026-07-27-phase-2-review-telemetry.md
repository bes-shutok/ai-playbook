# Plan: Phase 2 - Review Effectiveness Telemetry

Depends on (external prerequisite, not produced by this plan): the Phase 1 plan `docs/plans/completed/2026-07-27-five-worker-review-panel.md` is complete with a fresh review reporting zero unresolved blocking findings. Phase 2 cannot start until Phase 1 is ready; Phase 2 does not itself run a Phase 1 review.

Plan review: `docs/reviews/2026-07-27-plan-review-phase-2-review-telemetry-r6.md` (latest, **ready=yes**, 0 blocking; 1 non-blocking Low F24) · `docs/reviews/2026-07-27-plan-review-phase-2-review-telemetry-r5.md` (ready=no, 1 blocking High F22 on the artifact-size-bucket field mapping for current sidecars, now resolved) · `docs/reviews/2026-07-27-plan-review-phase-2-review-telemetry-r4.md` (ready=yes, 0 blocking; 1 non-blocking Medium F20).

## Terms

- **Baseline corpus**: artifacts captured by the immutable private snapshot before the Phase 1 cutover marker.
- **Growth corpus**: later artifacts whose path/content was not in the baseline snapshot AND whose panel identities satisfy the five-worker set.
- **Period**: the within-cohort discriminator only, `baseline` or `growth`. Period is the sole axis that differs between the two sides of a comparison; it is never a cohort key.
- **Conservation ledger**: classification of every discovered sidecar as current, legacy, unreadable, duplicate, baseline-missing, growth, or audit-anomaly. `unreadable` collapses the former `malformed` and `unsupported` classes, which the plan never distinguished operationally; `audit-anomaly` covers timestamp/panel/schema disagreement with the cutover marker and is a strict-audit signal, never a re-classification.
- **Final-triage values**: the set `{fixed, deferred, dropped}`. `pending` is not a final-triage value. Findings whose triage is `pending` are excluded from numerators and medians but counted toward triage coverage.
- **Accepted finding**: a unique staged finding whose final triage is `fixed` or `deferred`; `dropped` findings are not accepted. The accepted set is a named constant in the summarizer that intentionally differs from the validator's readiness-resolved set (`{done, dropped, fixed}`): `deferred` means "accepted but postponed" for effectiveness accounting, while it remains unresolved for review readiness. The summarizer must name this divergence explicitly.
- **Comparable cohort**: reviews sharing the same values for the cohort keys. Panel mode is deliberately NOT a cohort key, because it is the baseline/growth discriminator (see Period); making it a cohort key would make the two sides structurally incomparable. The cohort keys, with their derivation rules (each must be derivable from BOTH current and legacy sidecars; a key absent from legacy collapses to a single bucket so legacy reviews are not excluded):
  - **Review type (normalized)**: lowercase canonical form of `review_type`. Normalization map: `branch`/`branch review` → `branch`; `plan`/`plan review` → `plan`; `code`/`code review` → `code`; `rfc` → `rfc`; `document`/`doc` → `document`. Sidecars with a `review_type` absent or unnormalizable collapse to bucket `unknown`.
  - **Role**: `initial` when `round` is `r1`/`1`/absent with no `prior_round`; `follow-up` otherwise. Both schemas carry `round`.
  - **Artifact-size bucket**: deterministic bucket over raw finding count, read from whichever count field is present: `counts.raw_findings` (carried by both most current and all legacy sidecars) or `counts.raw_total` (a minority of current sidecars). Schema is NOT a reliable discriminator for this field (current sidecars use both), so the summarizer must try both keys on every sidecar; if both are ever present they must be equal (assert, do not prefer one). Buckets: `0`, `1-5`, `6-15`, `16+`. A review with neither field readable collapses to `unknown`.
  - **Domain-risk class**: coarse normalization of the `domains[]` multi-label set into a single class: `security` if `security`/`privacy` present; `concurrency` if `concurrency`/`SQL` present; `docs` if only `docs`/`docs-only`/`skill-spec` present; `other` otherwise. Empty/absent `domains[]` collapses to `unspecified`. This is a lossy proxy, not a precise risk score; it is documented as such.

Note: Token-usage telemetry is out of scope for this phase (no producer emits it; see `docs/history/feature-notes/2026-07-29-token-usage-telemetry.md`). The former "Observed token usage" term is removed.

## Gist & Examples

Phase 2 measures whether the five-worker policy reduces review cost without reducing useful findings. It uses data already present in review sidecars: worker launches, loaded lenses, raw and staged findings, deduplication, discards, severity calibration, overflow, and final triage.

The first useful report does not depend on provider token APIs or durable cross-session lineage. Worker launches are the primary cost measure. Token-usage telemetry is out of scope for this phase: no producer currently emits observed token usage (verified across the corpus), so the entire token-tracking surface is deferred to a follow-up captured in `docs/history/feature-notes/2026-07-29-token-usage-telemetry.md`. No token value is read, reported, or estimated by this phase.

The historical path-level baseline is private. It is written under `~/.ai-playbook/review-telemetry/`, not committed to this public repository. Tracked tests use neutral generated fixtures. Public output contains aggregate counts only and rejects the following identifier categories everywhere (Gist, Evaluation Criteria, Release gates, Task 3, and the privacy validation use one canonical list): repository names, repository/absolute paths, review filenames, ticket identifiers, feature names, and content digests.

Example outcome:

- Baseline median: eight worker launches per initial full review.
- Five-worker median: five worker launches.
- Accepted unique findings per comparable review remain within the effectiveness guardrail.
- Result: retain the five-worker default.

If the post-cutover sample is too small, triage coverage is incomplete, or comparable cohorts do not exist, the result is `inconclusive`; it must not recommend a policy change.

Provider-specific usage adapters and durable review lineage are separate follow-up plans. They are not prerequisites for this phase.

## Evaluation Criteria

**Quality dimensions:**

- Privacy: no tracked file contains any of the canonical identifier categories (repository names, repository/absolute paths, review filenames, ticket identifiers, feature names, or content digests), enforced by a deny inventory built at audit time from the real corpus, not a fixed regex (see Task 4 `real_deny_inventory`).
- Conservation: every discovered sidecar belongs to exactly one ledger class, and a missing baseline file cannot be hidden by a new file with the same shape.
- Compatibility: current five-worker sidecars and representative legacy code, plan, RFC, and document sidecars are classified without rewrites.
- Cost: report initial-panel launches, full-cycle launches, and launches per accepted unique finding.
- Effectiveness: report accepted unique findings, discard rate, false-positive rate, overflow rate, and severity-calibration rate by comparable cohort.
- Reproducibility: the same private baseline and corpus produce byte-stable aggregate JSON, asserted by a named two-run determinism test.

**Decision rule (computed independently per workload-comparable cohort; no weighted average across cohorts):**

- A comparable cohort is evaluable only when it has at least ten completed reviews on BOTH the baseline and growth sides. Cohorts compare baseline (period=`baseline`) vs growth (period=`growth`) reviews that share the same derived cohort-key tuple (see Terms: review type, role, artifact-size bucket, domain-risk class, each derived by a rule that works on both current and legacy sidecars); period is the only within-cohort discriminator.
- Final-triage coverage is required ASYMMETRICALLY: the growth side must reach at least 80% final-triage coverage; the baseline side is NOT subject to a triage-coverage bar because legacy reviews were never triaged to that standard (baseline findings are raw-only). Baseline contributes its raw finding count and worker-launch count; it does not contribute accepted/dropped triage outcomes.
- Within an evaluable cohort, compute the verdict by applying all three thresholds: retain the five-worker default when median launches per initial full review fall by at least 25%, accepted unique findings per comparable review (growth side; baseline referenced as raw yield) do not fall by more than 20%, and the growth-side dropped-finding rate does not rise by more than 10 percentage points.
- Report `review needed` when any threshold is missed. Do not automatically change panel policy.
- Combining multiple cohorts: report each comparable cohort's verdict separately; the overall result is `retain` only if every evaluable comparable cohort retains, `review needed` if any evaluable cohort fails a threshold. With zero evaluable comparable cohorts (too few reviews, or no cohort has both periods), the result is `inconclusive`. Surface cohort-availability counts so a human can see whether the pipeline is starved.

**Metric formulas (final-triage values = `{fixed, deferred, dropped}`; `pending` excluded from numerators/medians, counted in coverage):**

- Accepted unique findings per review (growth side) = median per-review count of staged findings whose final triage is in the accepted set `{fixed, deferred}`; reviews with pending triage count toward coverage but not the median.
- Baseline raw yield = per-review count of raw findings on the baseline side (no triage applied); used only as the 20%-guardrail reference.
- Synthesis discard rate = total synthesis-discard rows divided by total raw findings; zero raw findings yields `null`.
- Final dropped-finding rate (growth side) = total staged findings with final triage `dropped` divided by total staged findings with final triage in `{fixed, deferred, dropped}` (pending excluded); zero finalized findings yields `null`.
- False-positive rate = discarded rows with reason `false-positive` or `assumption-invalid` divided by total raw findings; zero raw findings yields `null`.
- A `null` decision metric or a missing evaluable comparable cohort makes that cohort's result `inconclusive`.

**Release gates:**

- External prerequisite (not produced by this plan): the Phase 1 plan is complete with a fresh review reporting zero unresolved blocking findings (see header dependency line).
- Summarizer self-tests cover current and legacy adapters, corpus discovery, conservation, privacy deny inventory, cohort comparison, determinism, and inconclusive outcomes.
- The private baseline accounts for every discovered historical sidecar by local path and content digest.
- Strict audit reports no unexplained ledger delta.
- The aggregate report contains no identifier from the canonical privacy category list and passes public-hygiene checks.
- No historical review Markdown or sidecar is modified (mechanically proven by a digest-comparison test, not a manual checkbox).
- No durable-lineage or producer-schema change is introduced.
- No-em-dash and `git diff --check` pass.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope:

**Production code and documentation:**

- `scripts/summarize_review_stats.py` *(new)*
- `README.md`
- `docs/plans/2026-07-27-phase-2-review-telemetry.md`
- `docs/history/feature-notes/2026-07-29-token-usage-telemetry.md` *(new; token-telemetry deferral)*

**Runtime-private outputs:**

- `~/.ai-playbook/review-telemetry/baseline.json` *(new, local only)*
- `~/.ai-playbook/review-telemetry/effectiveness-report.json` *(new, local only)*
- `~/.ai-playbook/review-telemetry/effectiveness-report.md` *(new, local only)*

**Read-only inputs (discovery is an allowlist, not a glob):**

- Review sidecars under repositories discovered from `personal_projects_root` and `company_projects_root` in `~/.ai-playbook/facts.md`
- Each repository’s resolved `reviews_dir`
- Legacy `docs/history/reviews/` directories
- Explicitly EXCLUDED: any path containing `/tmp/`, `.ai-playbook/tmp/`, `.ai-playbook/reviews/` (agent-runtime reviews), or `.ai-playbook/review-telemetry/`

**Plan-related extension**; implementation and review may change an unlisted file only when it is causally required to complete the summarizer, keep its public documentation accurate, or fix a regression introduced by this plan. Add repeatedly affected tracked paths to the explicit list.

**Out of scope; reject unless plan-related:**

- Phase 1 producer, validator, severity, finding-budget, and cycle-policy fixes; owned by Phase 1 Task 3.
- Historical review Markdown and sidecars; immutable read-only inputs.
- A tracked path-level baseline or report containing repository or artifact identifiers.
- Token-usage aggregation, provider-specific token adapters, and inferred token estimates; deferred to `docs/history/feature-notes/2026-07-29-token-usage-telemetry.md` (blocked on a producer-side change).
- Durable review lineage, generation state, cross-session counters, and strict Stats v2 producer activation.
- Automatic changes to the five-worker policy based on the report.

## Design Invariants

1. Historical review artifacts remain immutable (mechanically proven by a digest-comparison test against the real corpus).
2. Path-level baseline and conservation data remain local and untracked.
3. Every discovered sidecar is classified exactly once.
4. Aggregate public output contains no identifier from the canonical privacy category list.
5. Worker and lens attribution remain separate through aggregation.
6. Insufficient samples or (growth-side) triage coverage produce `inconclusive`. Baseline is not subject to a triage-coverage bar.
7. The report informs a later decision; it never changes review policy automatically.
8. **Permissions (TOCTOU-safe):** create `~/.ai-playbook/review-telemetry/` with `os.mkdir(..., 0o700)` and private files with `os.open(path, O_CREAT|O_EXCL|O_WRONLY, 0o600)` then `fdopen` (never create-then-chmod); clear the process umask before create since mode args are masked by umask; reject symlink targets. The parent `~/.ai-playbook/` must be mode `0700` (or tightened at start and re-asserted every run); refuse to run if it is group/world-accessible and cannot be tightened. Modes are re-asserted on every run.
9. **Concurrency (lock covers inputs):** one summarizer process at a time holds a process-wide advisory lock (e.g. `flock` on `~/.ai-playbook/review-telemetry/.summarizer.lock`) across the entire discover→digest→parse→aggregate→publish span, serializing reads of the shared INPUT sidecars in other repos, not only the telemetry output dir. Each input is read once into an immutable byte buffer; digest and parse come from that one buffer; on the pre-publish recheck, compare the buffer to the on-disk generation and retry at most a small fixed number of times (3) then fail publication rather than retry forever.
10. **Single growth authority:** a discovered sidecar is `growth` iff its path/content was not in the baseline snapshot AND its panel identities satisfy the five-worker set; everything in the snapshot is `baseline`. Timestamp, panel, and schema are NOT classification inputs; a mismatch with the cutover marker is a separate `audit-anomaly` conservation finding reported in strict audit, never a re-classification.
11. **Delegation boundary:** the summarizer IMPORTS `facts_paths` for all facts/root resolution (extend `facts_paths.py` with `resolve_projects_roots(user_facts)` rather than re-parsing) and DELEGATES per-sidecar current/legacy classification and finding conservation to existing `validate_review_staging.py` public functions. The summarizer's responsibility is cross-repo aggregation and cohort comparison ONLY; it does not fork the facts parser or the sidecar/conservation authority.

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

test "$(stat -f '%Lp' ~/.ai-playbook)" = "700"
test "$(stat -f '%Lp' ~/.ai-playbook/review-telemetry)" = "700"
test "$(stat -f '%Lp' ~/.ai-playbook/review-telemetry/baseline.json)" = "600"
test ! -e docs/review-stats-baseline.json
# Privacy is enforced by a deny inventory built from the real corpus (Task 4 real_deny_inventory),
# not a fixed regex. The summarizer emits the built deny list to a private file; assert none of
# those exact strings appear in the public reports:
python3 scripts/summarize_review_stats.py \
  --user-facts ~/.ai-playbook/facts.md \
  --emit-deny-inventory ~/.ai-playbook/review-telemetry/deny-inventory.txt
! rg -nF -f ~/.ai-playbook/review-telemetry/deny-inventory.txt \
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

- [x] `summarize_review_stats#facts_roots`; given the user facts document, expects both workspace roots resolved via `facts_paths.resolve_projects_roots` (imported, not re-parsed) and never embedded in tracked output.
- [x] `summarize_review_stats#review_directory_discovery`; given repositories with configured `reviews_dir` and legacy `docs/history/reviews/`, expects every real sidecar discovered once. Assert the discovery predicate is an ALLOWLIST (per-repo `reviews_dir` + legacy `docs/history/reviews/` only) and that it EXCLUDES any path containing `/tmp/`, `.ai-playbook/tmp/`, `.ai-playbook/reviews/`, or `.ai-playbook/review-telemetry/`. Seed `tmp/reviews`, `.ai-playbook/reviews`, and a telemetry-output sibling and assert none are ingested; follow symlinks rejected; duplicate real paths deduped.
- [x] Create `~/.ai-playbook/review-telemetry/` via `os.mkdir(..., 0o700)` with umask cleared; create private files via `os.open(O_CREAT|O_EXCL|O_WRONLY, 0o600)` then `fdopen` (never create-then-chmod); reject symlink targets; tighten and re-assert the parent `~/.ai-playbook/` to `0700` or refuse to run.
- [x] Define `--init-baseline` as atomic create (`O_CREAT|O_EXCL`) that fails when the manifest exists; define `--strict-audit` as read-only that fails when the baseline is missing, unreadable, replaced, or mismatched; define `--refresh-baseline` as the separate explicit refresh command (named flag) with a concrete transition table.
- [x] Record an explicit Phase 1 policy-cutover marker in the private baseline as the SINGLE growth authority. Treat snapshot members as baseline; classify a discovered sidecar as `growth` iff it is not in the snapshot AND its panel identities satisfy the five-worker set. A timestamp/panel/schema mismatch with the marker is an `audit-anomaly` strict-audit signal, NOT a re-classification.
- [x] `summarize_review_stats#same_shape_replacement`; given one missing baseline path and one new same-shape file, expects strict audit failure.
- [x] `summarize_review_stats#conservation`; given current, legacy, unreadable (collapsed malformed+unsupported), duplicate, baseline-missing, growth, and audit-anomaly fixtures, expects every sidecar in exactly one class.
- [x] `summarize_review_stats#audit_anomaly_classification`; given fixtures with timestamp disagreement, panel-identity disagreement, and schema disagreement against the cutover marker, expects each to land in `audit-anomaly`, be excluded from both baseline and growth cohorts, and appear in strict audit. A growth review carrying a pre-cutover timestamp must still be classified `growth` (not re-classified) and flagged in audit.
- [x] `summarize_review_stats#private_manifest`; given path-level corpus data, expects it only in `~/.ai-playbook/review-telemetry/baseline.json` and never in tracked output.
- [x] `summarize_review_stats#baseline_lifecycle`; given first initialization, overwrite attempt (rejected), missing baseline, unreadable baseline, explicit `--refresh-baseline`, and strict audit, expects the defined safe transition or failure per the transition table.
- [x] `summarize_review_stats#private_permissions`; given permissive parent mode (`~/.ai-playbook/` at `0755`) or symlink targets, expects the parent tightened to `0700`, the child created `0700`/files `0600` atomically (no create-then-chmod window), and hard failure without following a symlink; re-asserted on every run.
- [x] `summarize_review_stats#snapshot_race`; given a second lock holder or a sidecar changing between the digest read and the parse read, expects (a) one writer via the process-wide lock held across discover→publish, and (b) on the success path every published digest matches the byte buffer used for parsing; on change, retry at most 3 times then fail publication rather than publish a mixed-version snapshot.
- [x] Run -> expect RED before the summarizer exists.
- [x] Implement the process-wide advisory lock across discover→digest→parse→aggregate→publish; read each input once into an immutable byte buffer used for both digest and parsing; recheck against on-disk generation before publishing with a bounded (3) retry; publish reports atomically.
- [x] Implement allowlisted facts-driven discovery (importing `facts_paths`), SHA-256 inventory, private baseline lifecycle, single-authority cutover classification, audit-anomaly flagging, and strict conservation audit (delegating per-sidecar classification/conservation to `validate_review_staging.py`).
- [x] Run -> expect GREEN (Task 1 subset): `python3 scripts/summarize_review_stats.py --selftest --subset discovery,conservation,permissions,lifecycle`.
- [x] Commit: `review: add private review corpus audit`

### Task 2: Aggregate cost and finding effectiveness

Files:

- `scripts/summarize_review_stats.py`

- [x] `summarize_review_stats#current_adapter`; given a five-worker sidecar, expects worker and lens launch, dedup, discard, calibration, overflow, and triage totals. No token field is read or reported.
- [x] `summarize_review_stats#legacy_adapters`; given neutral legacy code, plan, RFC, and document sidecars (legacy schema: `agents_launched`, `raw_findings`, agent-keyed panels), expects compatible normalized totals without rewriting the fixture. The legacy-vs-current decision must match `validate_review_staging.py`'s classification for a shared fixture (drift canary).
- [x] `summarize_review_stats#accepted_unique`; given fixed, deferred, dropped, and pending findings, expects only `fixed` and `deferred` in accepted yield (a named constant that explicitly diverges from the validator's readiness set, which excludes `deferred`), `pending` excluded from the median but counted in coverage.
- [x] Run -> expect RED before aggregation exists.
- [x] Implement launch, cycle, finding-outcome, severity, overflow, and calibration aggregation (no token aggregation; token telemetry is out of scope per the feature note).
- [x] Run -> expect GREEN (Task 2 subset): `python3 scripts/summarize_review_stats.py --selftest --subset aggregation`.
- [x] Commit: `review: aggregate review cost and effectiveness`

### Task 3: Produce a privacy-safe policy report

Files:

- `scripts/summarize_review_stats.py`
- `README.md`
- `~/.ai-playbook/review-telemetry/effectiveness-report.json` *(new, local only)*
- `~/.ai-playbook/review-telemetry/effectiveness-report.md` *(new, local only)*

- [x] `summarize_review_stats#cohort_key_derivation`; given current sidecars in BOTH count shapes (`review_type=Branch Review`, `round=r2`, `counts.raw_total=12`, `domains=[concurrency,SQL]`) AND (`review_type=Plan Review`, `round=r1`, `counts.raw_findings=8`, `domains=[docs-only]`, `panel_mode=full`), plus legacy sidecars (`review_type=branch`, `round=r1`, `counts.raw_findings=3`, `domains=[docs-only]`, no `panel_mode`), expects each cohort key derived per the Terms rules: review type normalized, role from round, size bucket read from whichever of `raw_findings`/`raw_total` is present (both current shapes must yield a non-`unknown` bucket), domain-risk class from the domains set. Assert every sidecar derives a concrete (non-`unknown`-where-derivable) key set so neither current nor legacy reviews are excluded wholesale. Assert two sidecars differing ONLY in panel mode derive the same key tuple.
- [x] `summarize_review_stats#comparable_cohorts`; given a baseline review (period=`baseline`) and a growth review (period=`growth`) that derive the SAME cohort-key tuple but DIFFER in panel mode, expects them to land in the SAME comparable cohort with period as the only within-cohort discriminator. Also given mixed key tuples, expects comparisons only inside matching cohorts. Assert at least one real-shape legacy baseline review maps into a comparable cohort with a growth review; report cohort-availability counts.
- [x] `summarize_review_stats#inconclusive_sample`; given a cohort with fewer than ten reviews on either side, expect `inconclusive`. Given a cohort with enough reviews but growth-side triage coverage below 80%, expect `inconclusive`. Baseline-side triage coverage does NOT gate (baseline is raw-only).
- [x] `summarize_review_stats#retain_policy`; given an evaluable cohort (≥10 per side, growth triage ≥80%) with at least 25% launch reduction, accepted-finding change within the 20% guardrail (growth accepted vs baseline raw yield), and growth drop-rate change within 10 percentage points, expects `retain`.
- [x] `summarize_review_stats#review_needed`; given an evaluable cohort where any threshold is missed, expects `review needed` and no automatic policy mutation. Given two cohorts where one retains and one fails, expects overall `review needed`.
- [x] `summarize_review_stats#per_cohort_verdict`; given multiple evaluable cohorts, expects each reported separately and overall `retain` only if every cohort retains (per-cohort conjunction, no weighted average).
- [x] `summarize_review_stats#determinism`; given the same neutral fixtures run twice with shuffled discovery order, expects byte-identical aggregate JSON (stable key ordering, stable trailing newline). A real-report variant runs the report twice against an unchanged snapshot and asserts byte-identity.
- [x] `summarize_review_stats#public_output`; given a private ledger containing real repository names, repository/absolute paths, review filenames, ticket IDs, feature names, and content digests, expects the aggregate JSON and Markdown reports to contain NONE of those exact strings (deny-inventory check, not a fixed regex).
- [x] Run -> expect RED before report generation exists.
- [x] Implement byte-stable aggregate JSON (canonical key order) and a concise Markdown report with per-cohort `retain`, `review needed`, or `inconclusive` plus an overall verdict and cohort-availability counts.
- [x] Run every command under `## Validation Commands`; expect green.
- [x] Commit: `review: report five-worker panel effectiveness`

### Task 4: Validate the Phase 2 release

Files:

- `scripts/summarize_review_stats.py`
- `README.md`
- `docs/plans/2026-07-27-phase-2-review-telemetry.md`

- [x] Inspect the full per-file diff and verify no lineage state, producer-schema activation, or private identifier entered tracked files.
- [x] Run the strict real-corpus audit; expect zero unexplained ledger entries.
- [x] `summarize_review_stats#real_deny_inventory`; build the deny list at audit time from the real corpus (discovered repository names, path components, staged review filenames, artifact identifiers, recorded content digests) and assert none of those exact strings appear in the real `effectiveness-report.json`/`.md`. Keep the fixed regex only as a coarse pre-filter.
- [x] `summarize_review_stats#historical_immutability`; before the first real-corpus run, record SHA-256 for every discovered historical Markdown and sidecar into a private temp manifest, run the summarizer end-to-end against the real corpus, then re-hash every recorded path and assert byte-identity; reject any unexpected new file in historical directories; include an adapter-write attempt that must fail.
- [x] Run one fresh five-worker plan review of the current source digest; expect zero unresolved blocking findings.
- [x] Commit: `review: validate review effectiveness telemetry`
