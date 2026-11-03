# Backlog: review-driven plans lack finding inventory closure

Status: open
Priority: high
Class: fix-class
Origin class: consumer-feedback (company)
Consumer urgency: Consumer projects using the shared planning skill need this source-to-plan completeness step; do not defer it as skills-repository formal hardening.
Driving force: performance
Added: 2026-11-03, learn Step 1.8 capture from a review-driven planning session

## Observed versus expected

A plan intended to explain and address multiple findings from a code review was drafted without mapping every archived finding to plan scope and validation scenarios. A later plan review found a malformed-payload metric-tag finding missing from the inventory and worker sample (review record F3). It also found a retry example that predicted normal completion while the submitted source reconsumed the message (F1). Both were corrected before plan certification. The inaccurate retry example is already covered by the plans skill's source-probe instruction and is not a second issue here. The omitted finding required a corrective review pass before the plan represented the requested scope.

Expected: when a plan is explicitly based on multi-finding review feedback, read the complete relevant review and thread records and compare each behavior against the identified source snapshots. Classify each finding as present in the reviewed snapshot, introduced later, conditional or unverified, or invalid. Map every actionable finding to a task and acceptance scenario, or record an evidence-based exclusion. Do not infer exact comment counts or authorship when review records combine comments.

## Exact location

- agents/skills/plans/SKILL.md, Phase 1 requirements discovery and Exploration discipline.
- The review-driven plan is docs/history/plans/2026-11-02-review-freshness-and-code-coverage-gaps.md.

## Reproduction evidence

- .ai-playbook/reviews/2026-11-03-plan-review-review-freshness-and-code-coverage-gaps-p5bcb951b-r16.md, findings F1 and F3: the submitted-source retry callback contradicted the sample, and a reported metric-tag behavior was absent from the inventory. The plan was amended before certification.
- The plan's Decision points trailer and Task 3 now preserve the source-backed finding inventory and its evidence classifications.

## Suspected root area

The plans skill's Phase 1 has source rules for tracker-linked requests and requires probes for behavioral claims, but no conditional source-to-plan inventory for plans based on a review with multiple findings. The plan-review skill caught the omission; this item concerns authoring completeness, not a missing reviewer lens.

## Fix shape

Add a conditional, prose-only source-to-plan completeness step to the plans skill for review-driven plans: enumerate the source findings, classify their snapshot status and evidence, then link each actionable finding to plan work and an observable acceptance scenario or to an explicit evidence-based exclusion. Keep it limited to plans derived from multi-finding review feedback; add no validator, gate, worker, or review round.

Acceptance: a later plan review does not need a corrective round to add an actionable source finding omitted from the plan's inventory.

## Severity and source

Severity: Medium, blocking at plan review until corrected; the plan was corrected before certification.
Source reference: .ai-playbook/reviews/2026-11-03-plan-review-review-freshness-and-code-coverage-gaps-p5bcb951b-r16.md, F1 and F3.

## Why not fixed now

The certified plan addresses the consumer code-review gaps. This is a separate planning-skill improvement and can be handled as a focused skill update.

## Dedup probe

Searched open backlog filenames and problem bodies for review-finding inventories, review-driven plans, and source-to-plan coverage. The nearest item is docs/history/backlog/2026-11-02-review-freshness-and-code-coverage-gaps.md, now covered by the plan named above; it fixes current-head freshness and reviewer evidence for code findings, but does not require plans to close a multi-finding source inventory before drafting. The open docs/history/backlog/2026-11-02-review-freshness-plan-certification-residuals.md covers wording and plan-structure residuals from a later review round, not source inventory. The completed docs/history/plans/completed/2026-10-01-plans-tracker-source-reconciliation.md requires live tracker and linked-contract sources, not review-thread inventories. These are adjacent but distinct failure modes.

Environment: Codex desktop, 2026-11-03; repository skill source, with the shared runtime path resolving to the same file.
Capture hygiene: scan-public-hygiene --files pass; check-no-em-dash.sh file pass.
