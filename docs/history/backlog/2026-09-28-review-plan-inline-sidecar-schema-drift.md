Status: open
Priority: high
Origin class: learned-skill-defect (review-plan Step 3 inline sidecar schema; witnessed 2026-09-28, execute-plan-codex-worker-terminal-recovery plan review rounds r1-r2)

# review-plan inline sidecar schema drifts from the enforcing validator

## Which skill and step

`agents/skills/review-plan/SKILL.md`, Step 3 ("Sidecar schema (inlined here so it is in context without loading `review-staging`; authoritative copy lives there)") and the Step 4 mechanical gate (`validate_review_staging.py --hard`).

## Observed versus expected

Observed: a producer following the inline schema alone fails the mechanical gate on first submission, then needs the validator's own source to learn the enforced shape. Witnesses from one session (all fixed by reading `validate_review_staging.py` / `plan_readiness.py` source, not the skill):

- `coverage.completed[]` is validated as a LENS list (each entry must have a complete panel row or contributing attempt), not a worker list; a worker-named list fails with "completed lens 'X' has no complete panel row".
- `risk_signals` accepts only the closed tag vocabulary (`cross-service-call`, `generated-or-nullable-model`, `public-api`, `security-or-rollout-boundary`, `serializer`), not free-form strings.
- `coverage.attempts[]` rows require `attempt_id`, `started_at`, `deadline`, `attempt_number`, `outcome` and reject free-form keys (`count`, `note`); `retry_budget` requires positive `per_attempt_timeout_minutes` and `per_worker_max` when attempts are non-empty.
- Findings must be ordered by severity then ascending integer id; a worker with more than two non-blocking Low staged findings exceeds the finding budget and the extras must move to the overflow manifest.
- The staging Markdown must carry `- Record kind:`, `- Coverage:` (equal to `coverage.outcome`), `- Last fix commit: N/A` (exactly, when null), and a `### Attempt ledger` section whose data-row count equals `len(attempts[])`; the ledger header's first cell must be exactly `Attempt` (case-insensitive) to be skipped by the row counter.
- cap-closure: `extensions.cap_closure` requires `plan_section` (exactly `## Residual findings (cap closure)`), `round`, `residuals`, `pre_fold_digest`; the readiness probe ties `residuals` to the count of section entries carrying the `accepted` disposition, and every body line containing a disposition word tallies (prose in the section preamble must avoid `folded`/`accepted`).

Expected: the inline schema either matches the validator or the skill states that the inline copy is a summary and the producer must run (or read) the validator before staging.

## Environment

Runtime: ZCode, macOS; repo copy is the runtime source (`agents/skills/` is the canonical layer). Date: 2026-09-28. The gap cost roughly six failed gate runs across r1 and r2 before the schema was reconstructed from the validator source.

## Suspected root area

The Step 3 inline schema copy predates the coverage/cap-closure validator extensions and was not refreshed when the validator gained the new required set; `review-staging` is named as authoritative but the skill's framing ("so it is in context without loading review-staging") invites producers to trust the stale copy.

## Suggested fix

Either refresh the inline copy against the current validator (with a sync note) or shrink it to the stable core (top-level required set, finding-row shape) plus an explicit rule: "before staging, run the validator; on any schema error, read the validator source for the enforced shape - the inline copy is a summary, not the contract."
