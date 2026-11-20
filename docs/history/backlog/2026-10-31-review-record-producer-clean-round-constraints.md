# 2026-10-31 — review-record producer clean-round constraints (mint-pair flag interactions)

**Why:** three sequential tool_error refusals from `scripts/produce_exec_review_record.py` while minting the hard-mode-clause-pointer-residuals r2 zero-findings pair (2026-10-31 closeout session) — each a documented contract the flags enforce, none discoverable from `--help` alone: (1) `--review-run-id` must be a 32-char lowercase hex id (mint output of `review_usage_capture.py`); (2) `--round` is an integer, not `r2`; (3) a clean (empty-findings) round with `--last-fix-commit` requires `--review-mode fresh-adversarial`, and a clean round requires `--prior-findings-filter no` (prior findings are context, never a filter, on a clean round).

**Fix shape:** one line in the validator/producer usage guidance (or the review-staging skill's mint recipe) naming the three flag constraints together, so a post-fix zero-findings fold round mints on the first invocation.

**Why-not-fixed-now:** the session was mid-landing; the guidance edit is a docs-scale follow-up that belongs to the next authoring cycle, and the refusal messages themselves already name each constraint at fire time (fail-loud contract worked as designed).

`Cluster:` docs/history/backlog/2026-11-15-authoring-lane-record-mint-producer-pointer.md (same producer family: the mint-path wiring that would carry these flag constraints to authoring lanes; the mint-gap sibling row was covered and deleted by the 2026-11-16 ad-hoc landing of the mint-time egress-digest arms).

`Cluster:` docs/history/backlog/2026-11-15-authoring-lane-record-mint-producer-pointer.md (same producer family: the mint-path wiring that would carry these flag constraints to authoring lanes).

`Cluster:` (none; the sibling consumer-flow timing-pointer row was covered and deleted by the 2026-11-14 ad-hoc landing of the Phase 3.1 mint-before-launch pointer).

### Verified follow-up (2026-11-17): plan-identity filename mint gap

**Observed refusal path:** `scripts/review_record_selection.py select --kind plan-review --source-plan ...` emitted the identity-qualified `-p3176dd8f-r4` pair, while `scripts/produce_exec_review_record.py` produced an infix-less `...-r4` pair and did not expose a plan-identity input. Its plan-review arm derives the bare filename from date, type, slug, and round; `--artifact-slug` rejects the identity-qualified tail. The selector and readiness gate can identify an infix-less pair from its `URL or Artifact` metadata, but `review-plan/SKILL.md` requires writing to the selector-emitted identity-qualified pair and its sidecar identity field.

**Impact:** a clean checkbox-progress rebind can produce a discoverable but noncanonical pair. Because the producer cannot target the selector-emitted path or write `extensions.plan_identity`, the caller must rename the pair and add its identity witness manually to meet the review-plan output contract.

**Proposed correction:** extend the tracked producer to consume the selector-emitted plan-review path and identity, then pin a plan-review r2+ fixture proving the filename and `extensions.plan_identity` match `review_record_selection.py`. Until that lands, hand-shape only the missing identity-qualified naming fields from the selector result and record the exact pair transformation in the run log; do not change the validator.

### Verified follow-up (2026-11-20): nonblocking plan finding verdict

**Observed refusal path:** the findings-bearing producer set a plan-review sidecar verdict to `no` whenever the findings array was nonempty and omitted the canonical `## Summary` verdict line, even when the only finding was a nonblocking Low. `plan_readiness.py` then refused the review although `is_review_ready` found zero unresolved blocking findings.

**Impact:** a valid nonblocking documentation follow-up makes the plan unready, forcing either an unnecessary plan edit/review cycle or a record correction.

**Proposed correction:** compute readiness from unresolved blocking findings for plan reviews and emit the canonical `Verdict: ready=yes|no` summary. Until that lands, the caller records the exact source digest and corrects the pair to `ready=yes` only after verifying no blocking findings and passing the review validator.
