# Feature Note: Review Token-Usage Telemetry

Status: **Not started**. Prerequisite: a producer-side change (below). This is a
forward-looking feature note, not an active plan. Filed under `docs/history/feature-notes/`
as a proposal awaiting a producer.

Referenced from: `docs/plans/2026-07-27-phase-2-review-telemetry.md` (token aggregation
deferred out of Phase 2; see its Gist and Out-of-scope section).

## Problem

The review-effectiveness summarizer (`scripts/summarize_review_stats.py`, planned in the
Phase 2 review-telemetry plan) can already report review cost in terms of **worker
launches**. That is a useful proxy but not a direct resource measure. A more direct cost
signal is **provider token usage**: how many prompt/completion tokens each review (and each
worker within a review) consumed.

As of 2026-07-29, verified across 202 review sidecars in two project groups, **no sidecar
contains a token-usage field**. Sidecar top-level keys are `review_type`, `date`,
`artifact_slug`, `round`, `depth`, `domains`, `counts`, `panel`,
`deduplication_groups`, `discarded`, `severity_calibration`, `triage_outcomes`,
`findings`, `overflow` (current schema) or a smaller legacy set
(`agents_launched`, `raw_findings`, `staged_findings`, ...). None carry
`usage`/`tokens`/`adapter`/`provenance`. Therefore a consumer cannot aggregate token cost
today; any token path would be dead code reading a field that is never written. This is why
Phase 2 strips its token-aggregation surface and defers the capability here.

## What needs to change (producer first, then consumer)

Token telemetry is blocked on a **producer**: something must capture provider usage and
write it into the sidecar before any consumer can aggregate it. Order matters.

1. **Capture usage at the review run.** The review-panel skills
   (`agents/skills/review-agents/`, `agents/skills/review-panel-selection.md`) and/or the
   stats emitter in `scripts/validate_review_staging.py` must record, per worker launch and
   per review, the provider usage returned by the model API: prompt tokens, completion
   tokens, total tokens, and the model/adapter name.
2. **Write a `usage` field into the `.stats.json` sidecar** with a named adapter and a
   provenance record (which runtime call, which model, captured from the API response, not
   estimated). This is a producer-schema change; it must be designed as a stats-versioned
   addition so legacy sidecars (no `usage`) remain parseable.
3. **Lineage (optional but needed for per-review attribution).** To attribute a usage
   record to the correct review run deterministically, a stable join key between a runtime
   usage report and a sidecar is required. This overlaps with the "durable review lineage"
   follow-up and may be solved jointly.
4. **Consumer aggregation (Phase 2 follow-up).** Once a producer exists, restore the token
   aggregation that Phase 2 removed: observed-token totals, observed-token coverage, and the
   "token cost is supplementary until coverage reaches 70%" decision rule. Reuse the seam
   left in the Phase 2 summarizer (the aggregation point where worker-launch totals are
   computed) as the attachment point.

## Baseline limitation (state explicitly in any future plan)

Even after a producer ships, **baseline (pre-cutover) reviews will never have token data**,
because they were produced before the usage field existed. Token cost can therefore never be
a *comparative* metric across the Phase 1 cutover; it is only a forward-looking supplement for
growth-period reviews. Any future plan must state this so the decision rule does not require
baseline token coverage.

## Open questions

- **Adapter scope:** one provider-neutral adapter, or per-provider adapters (OpenAI,
  Anthropic, OpenAI-compatible)? The Phase 2 plan deferred "provider-specific usage
  adapters"; decide whether the producer emits a normalized neutral shape or raw
  provider-specific usage that the consumer normalizes.
- **Per-worker vs per-review granularity:** usage is returned per API call; workers may make
  several calls. Decide whether to record per-call, per-worker, or per-review totals (or
  all three).
- **Where capture happens:** inside the agent harness (tooling-level, agent-agnostic), inside
  the review-panel skills (workflow-level), or both. Affects which skill owns the producer.
- **Stats versioning:** how to evolve the sidecar schema without breaking the existing
  `validate_review_staging.py` parser and the Phase 2 summarizer's legacy adapter.

## Non-goals

- Estimating tokens when no observed usage exists (never estimate; missing stays missing).
- Modifying historical sidecars to backfill usage (they are immutable read-only inputs).
