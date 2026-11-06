Status: open
Priority: high
Class: fix-class
Origin class: skills-corpus defect (2026-11-06 cross-session learn+investigate harvest over the prior 24h)
Cluster: docs/history/backlog/2026-11-05-plan-prompts-shared-rules-pruned.md (same dispatch-surface contract family; that row owns the rolling logs' lost shared contract, this row owns the backlog rows' survey-selector shape)
Capture hygiene: scan-public-hygiene pass (2026-11-06)

# A review-residual backlog batch lands without the survey selector fields and is invisible to the open-row survey

## Problem

The closeout-migrate-supplemental execution landing (cd385e428, 2026-11-06) filed seven review-residual backlog rows whose headers carry a review-findings template (Driving force / Source / Finding / Remedy / Acceptance) but none of the corpus contract's selector fields: no `Status: open`, no `Priority:`, no `Class:`, no `Origin class:`. The survey contract reads the literal `Status: open` field at the top level of the backlog home (learn Step 1.8/1.9), and the maintenance loop's open-row candidate survey selects on the same field, so all seven rows were invisible to both: they could not be deduped against, prioritized, claimed, or dispatched. This harvest found them only by grepping the landing's diff. No validator covers selector presence (the three `scripts/check_backlog_*.py` validators own claimed rows, inbox location, and root closure; none reads Status), so a certified landing with the migrate suite green carried the defect straight to main.

## Observed vs expected

Observed: seven 2026-11-06 rows filed by the execution flow's review-residual arm without selector fields; the rows sat in the backlog home while the fleet could not see them.
Expected: every row filed into the open-backlog home carries the selector block at filing time; the filing step's text pins the shape so the batch cannot drift.

## Evidence (trimmed)

- The seven rows (all landing cd385e428, each `grep -c '^Status:'` = 0 before this repair), under docs/history/backlog/: 2026-11-06-closeout-migrate-guard-crash-loses-landed-restore-rows.md, 2026-11-06-closeout-migrate-nested-target-case-insensitive-false-refusal.md, 2026-11-06-closeout-migrate-noop-route-failure-rows-unmanifested.md, 2026-11-06-closeout-migrate-rescan-span-error-containment.md, 2026-11-06-closeout-migrate-sanitize-add-git-config-parameters.md, 2026-11-06-closeout-migrate-test-fidelity-residuals.md, 2026-11-06-closeout-migrate-vintage-batch-zero-differ-early-return.md.
- Survey contract: agents/skills/learn/step-1-extract.md Step 1.8 ("survey open items (`Status: open`, top level of the backlog home, excluding the completed and deferred subdirectories)").
- No gate: the three scripts/check_backlog_*.py validators contain no Status handling (grep over the three files returns zero Status references).
- Harvest repair: the same harvest pass restored the selector block on all seven rows (this change set); this row owns the prevention arm only.

## Suspected root area

The execution flow's review-residual filing step (execute-plan light-boundary backlogged-candidates arm, plus the done closeout's equivalent where it files residual rows): the step files rows without naming the backlog row shape contract (learn Step 1.8/1.9 fields, receiving-review's Backlog capture shape). Pointer-class sentences at the filing step text; no validator.

## Ship when

The filing step's text names the selector block (Status, Priority, Class, Origin class) as a filing-time requirement on each surface that files residual rows; the next review-residual filing lands rows that the open-row survey selects; hygiene scan green; no gate or validator added.
