Status: open
Priority: high
Cluster: docs/history/backlog/EXEC-PROMPTS.md EXEC-PROMPTS-PRUNE receipt receipt-runner-summary-witness-and-dispatch-failed-pin
Cluster: docs/history/backlog/2026-10-22-review-staging-scaffold-simplification-residuals.md
Origin class: self-serving
Quarantine: 2026-11-01
Class: fix-class

# doing-code-review's staging-doc gate lacks the scaffold-first cross-reference

## Observed

The doing-code-review skill's hard gate says "Always produce the staging doc" and its Modes section calls the staging doc the deliverable, but the skill never points at the review-staging skill's Finding-construction recipe (scaffold before drafting) or the validator's `--scaffold` mode - the canonical construction path for the exact artifact the gate mandates. A session that runs the panel machinery correctly can still author the record pair by imitating a recently landed record, because the validator's required shape (severity groups including empty ones, per-finding Comment and Analysis blocks, the Review Statistics section, the minted run-id pair, the soften table, per-finding calibration fields) grows faster than records land; even same-day records predate the current gate trio.

Witnessed 2026-10-30: one interactive session authoring two ad-hoc landing records imitated same-day records and needed six-plus validator-refusal rounds per record (missing `### Critical..Low` groups, missing `#### Comment`/`#### Analysis`, missing `## Review Statistics`, missing `review-run-id`/`review-started-at-ms`, soften-section parity, integer finding ids with `consequence`/`reachability`/`blast_radius`/`confidence`) before the first pass - every refusal a shape the review-staging recipe already prescribes. Lesson #321 in the project corpus records the rule; this row owns the skill-side fix.

## Expected

One cross-reference line at the doing-code-review staging-doc gate (the "Always produce the staging doc" hard-gate cluster or the Modes table's Staged row) pointing at the review-staging skill's Finding-construction recipe (scaffold before drafting) as the record pair's construction path, the same single-home discipline the guidelines' Integration Points rule uses. Note: `agents/skills/doing-code-review/SKILL.md` is the panel of record and is banned from ad-hoc-edit (plan route only), so this fix routes through a covering change, not a direct ad-hoc edit.

## Suggested shape

- One sentence in the hard-gate list: the staging record pair is drafted per the review-staging skill's scaffold-first recipe (`validate_review_staging.py --scaffold`), never by imitating a recent record.

## Class

Fix-class (one cross-reference line; no behavior, no machinery).
