# Backlog: Exec-review record producer gaps (overflow input, verification-only clean rounds, exec-receipt sidecar)

Priority: medium
Origin class: self-serving
Review origin: strand-adoption exec session 2026-11-02 (digest-handoff-drift landing)
Cluster: docs/history/backlog/EXEC-PROMPTS.md##exec-review-producer-egress-digest-mint-gap (same producer script, complementary arms: this row owns overflow input, clean verification-only rounds, and the exec-completion receipt mint; the sibling owns the egress-digest arm)

Three producer-side gaps witnessed in one landing:

1. `scripts/produce_exec_review_record.py` has no overflow input: the per-worker Low budget (max 2) forces hand-patching the overflow items onto BOTH surfaces (Markdown overflow manifest + sidecar `overflow` list) after production, an unassisted edit the validator then checks. Accept an `overflow` array in the findings JSON and render both surfaces.
2. A clean (0-finding) post-fix round is refused as `verification-only` ("a verification-only pass never satisfies the clean-round condition"), so r2 verification reviews must be recorded as `fresh-adversarial` with `--last-fix-commit`; either support clean verification-only rounds or document the mapping at the helper.
3. The exec completion receipt (`*-exec-r<N>.md` + `.stats.json`) has no producer helper; the pair was hand-copied field-for-field from a passing pair (schema_version 1, extensions.convergence, certified_range). Add a `--kind exec-completion` arm to the producer so the receipt is minted, not transcribed.

Witness update 2026-11-02 (plan-review side of arm 2, maintenance-self-heal-first-on-blocks authoring run): the round-shape mapping gap is pipeline-wide, not exec-only. A focused delta certification round (non-clean, `Last fix commit` set) also has no `review_mode` value in the validator's enum, so the record declares `fresh-adversarial` although the panel was focused; and the discard reason a worker legitimately emitted for a below-threshold finding is absent from the validator's set, forcing a substitute code that misdescribes the disposition (tracked as a second discard-code drift witness on the closed-enums row's Acceptance). Any arm that adds round-shape expressiveness should cover the plan-review producer and validator pair in the same change.
