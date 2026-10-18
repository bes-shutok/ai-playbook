# Plan: Land the D-8 review-loop budget policy as durable skill text

Backlog origin: docs/history/backlog/2026-10-09-execute-plan-review-loop-blocker-convergence.md (the PLAN-PROMPTS entry `review-loop-round-budget` carries the operator-confirmed prompt; sanctioning directive D-8 in docs/maintenance/operator-directives.md)
Driving force: token-usage
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-review-loop-round-budget-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 3h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-09-review-loop-round-budget.md (session sess_17e58dd5-8e5f-4d81-bec6-330c62ac65e0)

## Terms

- Full-panel round: one review pass launching all five base workers (correctness-completeness, testing, design-simplicity, contract-docs, risk), counted per the counting rule (whole-plan scope in a plan-scoped loop; roster in standalone loops).
- Delta round: a focused-panel review round whose scope is the fold diff (the classified delta between the digest the previous round reviewed and the current artifact bytes) plus its blind correctness-completeness probe; recorded `panel_mode: focused`; its staging pair records the post-fold whole-plan bytes as its Source digest with the fold-diff scope named in the Selection reason; its panel is the owning worker of each folded finding plus the workers owning domains the fold diff touched, plus the blind probe.
- Full-panel budget: the number of full-panel rounds a loop may launch before the loop pauses for operator direction, derived from the plan's declared execution budget by the formula this plan prescribes.
- Certification round: the review round that carries the certifying clean verdict (a fresh-adversarial round reporting zero unresolved blocking findings).
- Lint-level record validation: the staging validator's `--preflight` report-only pass; its findings never move the exit code, and the orchestrator reads and resolves every reported finding before the round is reported complete.
- Full record validation: the staging validator's `--hard` pass with its source-context flag (`--source-plan`, or the code-source pair), which fails the round on any schema or freshness defect.
- Declared execution budget: the plan header line `Execution budget: <total>h total, largest task <max>h` (the grammar pinned at scripts/plan_readiness.py `PRE_ROUND_BUDGET_LINE_RE`); the total is the complexity proxy.
- Certification-residual routing: certification-round non-blocking findings are recorded in the terminal record's overflow section (the existing sidecar field) with durable backlog capture; the soften watchlist keeps its fix-keyed shape and closure obligations untouched.

## Why

Every queued plan pays per-round whole-plan panel cost: after the initial full panel, each fold round re-reviews the whole plan with fresh workers, re-staging fold-residue and wording as new findings. The machinery audit rated the review-loop budget the #1 blocker (25/25; docs/maintenance/machinery-blocker-audit-2026-10-09.md, suggestion 2) and the freshest witness is the docs-branch plan certified at r14 (docs/history/review-certs/docs-branch-scope-and-tmp-retention.md). The operator confirmed the policy as directive D-8, which binds lanes now; this plan lands it as durable skill text so the policy survives this session and applies in every runtime.

## Gist & Examples

TLDR: the review loop's full-panel budget derives from the plan's declared execution budget, folds re-review as focused delta rounds over the fold diff, certification considers blocking findings only, and per-round record validation runs at lint level with full validation kept at certification.

Before: a 1.5-hour plan spends five whole-plan rounds because each fold round relaunches full panels that re-stage wording as new findings, every round runs the 18,722-line validator at full contract strength, and a clean certification round holding three non-blocking findings loops another round to re-verify them.

After: the same plan gets 2 full-panel rounds (declared 1.5h or less) plus delta rounds over fold diffs that do not consume the budget; only a semantic plan change reopens a whole-plan panel; the certification round records its non-blocking findings into the terminal record's overflow section with durable backlog capture and exits; intermediate rounds validate records with `--preflight` while the certification round keeps the full `--hard` gate.

Edge cases: a plan with no declared `Execution budget:` line keeps the configured interval semantics (the declared budget is the proxy, so the formula is not applicable without it); a standalone code loop with no plan keeps its configured `max_full_panel_rounds` interval; an active churn or reconciliation trigger fires before any budget consideration, exactly as today; the cap-closure terminal shape remains the at-cap exception byte-identically.

## Outcome

A review loop's cost scales with the plan's declared complexity instead of a flat whole-plan-per-round spend, and the operator, not the loop, authorizes any spend beyond the budget.

- In every loop that carries a plan's declared budget, the full-panel budget derives from that declared budget; in such loops delta rounds never consume it regardless of roster, and delta-round spend is checked by the existing total-round reflection checkpoints and the churn trigger rather than budgeted; standalone loops keep the configured intervals and the roster-keyed counting; breach pauses the loop for operator direction per review-plan's Scope and complexity policy duty, and an unattended lane parks and reports.
- The certification round considers blocking findings only; its non-blocking findings are recorded in the terminal record's overflow section with durable backlog capture (a backlog row for every consequence-bearing residual, in every family) and never force a re-round or a plan fold.
- Per-round record validation runs at lint level; the certification round and every round-close and execution-boundary gate keep full validation.
- The witnessed 4096-byte extraction-cap collision is dispositioned out of scope with its own fix row filed in this repository's backlog.

Gate delta: checked-condition-set growths on existing protocol items only (the round-cap rule's reflection gains the budget check; the per-round staging-validation duty's check set is partitioned lint versus full; the certification round's non-blocking findings gain the certification-residual routing (terminal-record overflow plus durable backlog capture); the fold re-review gains the delta-round scope rule; the review-plan pause duty gains the breach mechanics and the cap-closure rule's trigger gains the breach-alike authorization condition; the terminal-round workflow-reflection paragraph's enumeration gains the row-by-row backlog verification); one backlog row filed (documentation, not machinery); the guard liveness ledger's current catch-to-incident ratio at authoring time is 19 catches to 24 incidents (`python3 scripts/gate_liveness_ledger.py show`, TOTAL: catches=19 incidents=24 ratio=19:24 overrides=7, re-derived 2026-10-10), cited per the ledger-citation duty. No refusal class, hard gate, fence, protocol layer, or schema state field is added or removed; no new review-layer counted addition (every amended duty lives in an existing protocol item whose sanction text already blocks); no validator code change (`--preflight` is consumed as it exists); no new state schema, ledger, or collection duty.

## Assumptions

- D-8 clause (4) lands as the existing `--preflight` report-only mode, not a new validator flag or check partition: the audit's own implementation wording is "Demote the nine-shape record validation to a lint-level preflight for non-certification rounds", the mode already runs the full inventory report-only over absent or present inputs, and the prompt forbids new machinery. Basis: docs/maintenance/machinery-blocker-audit-2026-10-09.md suggestion 2 wording, `python3 scripts/validate_review_staging.py --help` (`--preflight`: "findings never move the exit code (exit 0)"), and the prompt's reuse-only constraint.
- The lint demotion's freshness story is family-scoped and honest about the residual: in the plan family, the plans skill's post-round digest-integrity check (rule 9, the loop-side shasum comparison) stays on every round; in the code family (standalone review-loop and execute-plan Phase 3), rule 9 does not apply, so the compensating controls are the round-close and certification full gates plus the duty that `--preflight` findings are resolved before the round's triage and counter decisions are consumed, and the residual is recorded: a loop that terminates without certifying rests on a lint-only record. The commit-boundary hook (cursor/hooks/review-staging-gate.sh) keeps its hard enforcement as the retained backstop. Basis: the plans numbered-rules block preamble (the sentence scoping those rules to plan reviews with source_kind "plan"), the round-close full-gate precondition, scripts/gate_liveness_ledger.json (review-staging-validator entry, whose credited 2026-10-07 catch was an intermediate-round nine-shape rejection now landing at the full gates), and the hook's hard invocation.
- A plan carrying no declared `Execution budget:` line keeps the configured interval semantics: D-8 names the declared budget "the complexity proxy", and a formula over an absent proxy is not applicable. Basis: D-8 clause (3) wording and the plan-sizing plan's optional-member rule (docs/history/plans/completed/2026-10-05-plan-sizing-execution-budget.md).
- A standalone code loop with no plan (review-loop outside execute-plan) keeps its configured `max_full_panel_rounds` interval and gains the delta-round accounting, the blocking-only certification, and the lint split; the formula binds only loops that carry a plan's declared budget. Blocking-only certification composes with review-loop's byte-identical exit criteria because certification residuals route to the terminal record's overflow plus durable backlog capture and never enter the soften watchlist, so the watchlist-closure exit criteria stay satisfiable with no review-loop exit wording changed. Basis: D-8's proxy is plan-declared; review-loop's Limits table already separates total-round from full-panel counting; review-loop's exit criteria (watchlist closed) with the certification-residual routing.
- The breach pause binds to the live authorization owner: review-plan's Scope and complexity policy pause-for-operator-direction duty. D-8 clause (3)'s wording ("the landed round-cap operator gate's ask continues to govern breach") predates the cap rework (90a36850e) that removed the three-choice ask from the skills, so this plan re-anchors rather than resurrects: at breach the loop pauses for operator direction, where extend means raising the derived budget by a stated number of full-panel rounds, continue means launching one further full-panel round, and park means stopping and reporting; an unattended lane parks and reports. Basis: review-plan's Scope and complexity policy ("pause for operator direction"), the removed ask's witness (90a36850e; plans rule 16, review-plan rule 8), and D-8 clause (3).
- The delta classifier stays the sole fold arbiter: a classified round-launching fold takes the delta round; an unclassified or operator-acked delta keeps today's stop-and-adjudicate path, and a semantic plan change that proceeds reopens a whole-plan panel. Basis: plans rule 2 and D-8 clause (1) "decided by the existing delta-classifier arm".
- Exempt folds are untouched: a fully exempt fold still records one correction row and continues at zero rounds. Basis: the prompt's minimal-fold reconciliation clause and plans rule 2.
- The mechanical fixture is pins rows plus span gates over the prescribed prose, and no validator gate is added: process-gate design with no production surface, same fixture class as the round-cap operator gate plan. Basis: that plan's Assumptions and its landed pins.
- `budget_readiness_reviews` (execute-plan Phase 3 manifest line, "fresh whole-plan review rounds per run, default 3") becomes derived from the declared budget under the same formula; the declared line is an optional member, so a plan without it keeps the flat default 3 on the Phase 3 surface (the same absent-line fallback the other surfaces carry, stated in execute-plan's own text). Basis: the Phase 3 tracking-list line text, D-8 scope covering execute-plan Phase 3, and the plan-sizing plan's optional-member rule.

- D-8's "watchlist" noun for certification residuals is realized as the terminal record's overflow section plus durable backlog capture: the soften watchlist is fix-keyed (the row shape is review-loop's watchlist section; review-staging recording rule 12 owns the array as source of truth), its open rows are carried within a run by each new round's initialization from the latest record pair with re-examination obligations, and review-loop's frozen exit criteria require every watchlist item reaffirmed or restaged in an earlier round, so fresh residuals entering that shape would deadlock exit exactly when the directive says to exit; the overflow field is an existing sidecar member, so the sidecar schema stays byte-identical; and the record pair lives in the gitignored reviews_dir, so the durable backlog row is the routing's single durable leg, verified row-by-row by the per-family terminal certification duties (the plan family's workflow-reflection paragraph, plans rule 6; the code family's exit-report tally) per Task 1. Basis: review-loop's watchlist section and exit criteria, review-staging recording rule 12, the standing schema-identity constraint, and D-8's own "never force a re-round" requirement.

- Residual accepted: in a plan-scoped loop, a classified fold whose diff touches every domain launches a roster-large delta round at zero full-panel budget, and the total-round intervals are reflection checkpoints, not stops, so a long convergence loop can spend beyond a full-panel-equivalent cost without breaching the budget; the brakes are the existing reflection checkpoints and the measured churn trigger, and D-8's budget counts full-panel rounds only, so no new ask is added. Basis: review-plan's Scope and complexity policy, review-loop rule 5, and D-8 clause (3).

Decision points requiring a grill: none remain (the operator confirmed the policy program as D-8; the PLAN-PROMPTS entry records the rejected alternatives, including the operator correction that sized the budget proportionally rather than flat).

## Standing constraints

- The cap-closure terminal shape, the sidecar schema, and the personal-class limit stay byte-identical; the plan adds trigger and routing text only.
- review-plan's Plan-review boundary and its blocking boundary stay byte-identical: public behavior, ownership, invariants, safety, and observable acceptance remain blocking; implementation fixture wiring does not.
- The reconciliation-before-churn trigger (review-loop rule 5, review-plan's Reconciliation gate) keeps precedence over any budget consideration: an active churn or recurrence trigger reconciles before another panel regardless of remaining budget.
- No validator code change: `scripts/validate_review_staging.py` is read-only in this plan.
- No machine-specific absolute paths in any edited file; the hygiene scan passes before each commit.
- Execution runs on a branch kept rebased onto current main at each fold. At each task start the executor re-verifies the currency - pins suite exit 0 and no commit in `git log HEAD..main` touching the plan's anchor files or the pins script - and on a red baseline, a vanished anchor, or a stale rebase stops and reports instead of proceeding; hand-reconciling PLAN-PROMPTS.md is never the repair.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the four arms are each stated once per owning skill in the prescribed prose, the formula's worked examples (2h or less gets 2, 3-4h gets 3, 5-6h gets 4, above 6h gets no larger budget) appear in the plans skill text, and every amended duty keeps its existing sanction and mechanics byte-identical apart from the named growths.
- regression safety: the pins suite passes; the boundary-fixture regression (`scripts/test_plan_review_boundary_examples.py`) passes over the edited skills; the em-dash scan (file mode over the touched paths) and the public hygiene scan pass.
- scope discipline: the changes touch only the five skill files, the pins script, and the one filed backlog row; `scripts/validate_review_staging.py` and `scripts/plan_readiness.py` bytes are unchanged.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0.

**Ship when:**
- The next plan-review loop that folds a finding launches a delta round over the fold diff instead of a whole-plan panel, a loop reaching its derived full-panel budget pauses for operator direction before another full-panel round, a certification round with non-blocking residuals records them into the terminal record's overflow section with durable backlog capture and exits without a re-round, and intermediate rounds validate records at lint level while the certification round runs the full gate; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (the Plan Quality Gate: the budget formula sentence beside the round-cap rule, the delta-round scope sentence in the fold re-probe rule, the certification-residual routing (blocking-only) sentence beside the exit rule, and the staging-validation lint/full split in the staging-pair duty paragraph; all other spans frozen)
- `agents/skills/review-plan/SKILL.md` (Step 4 mechanical-gate split, the certification-residual routing beside Step 5, the Scope and complexity policy budget sentence by reference, and the Iteration Discipline rule 8 trigger extension; the Plan-review boundary and its fixtures stay byte-identical)
- `agents/skills/review-loop/SKILL.md` (the Limits-table budget sentence and the mechanical-gate lint split; the exit criteria stay byte-identical)
- `agents/skills/review-staging/SKILL.md` (one record-validation-levels subsection naming the lint and full forms and their round classes, the delta-round record semantics, and one certification-residual routing note (terminal-record overflow plus durable backlog capture))
- `agents/skills/execute-plan/SKILL.md` (the Phase 3 tracking-list `budget_readiness_reviews` line and the review end-condition table rows)

**Docs:**
- `docs/history/backlog/2026-10-09-driver-extraction-cap-readiness-drift.md` (created by Task 5; the 4096-byte extraction-cap fix row)

**Tests:**
- `scripts/check_maintenance_pins.sh` (the pins rows are the mechanical fixture for the prescribed prose spans)

**Read-only (referenced, never edited):**
- `docs/maintenance/operator-directives.md` (D-8, the policy of record)
- `docs/history/plans/completed/2026-10-07-review-round-cap-operator-gate.md` (historical witness of the removed round-cap ask)
- `scripts/validate_review_staging.py` (the `--preflight` and `--hard` modes consumed as they exist)
- `scripts/plan_readiness.py` (the `PRE_ROUND_BUDGET_LINE_RE` grammar referenced)
- `scripts/review_record_selection.py` (the selection helper the delta round's post-fold digest records through)
- `docs/history/backlog/2026-10-09-execute-plan-review-loop-blocker-convergence.md` (the origin row; flipped covered by the landing rider, not by a task)
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (the #1-blocker evidence)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-09-execute-plan-review-loop-blocker-convergence.md (Status: open; the landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## review-loop-round-budget` (frozen under docs/tmp/authoring-claims/2026-10-09-review-loop-round-budget.md)

## Validation Commands

**Production:**
```bash
grep -c "plus 1 full-panel round per additional started 2 hours" agents/skills/plans/SKILL.md   # expect 1
grep -c "is a delta round, a focused-panel review round scoped to the fold diff" agents/skills/plans/SKILL.md   # expect 1
grep -c "considers blocking findings only" agents/skills/plans/SKILL.md   # expect 1
grep -c "runs at lint level" agents/skills/plans/SKILL.md   # expect 1
grep -c "per the plans skill's Plan Quality Gate budget formula" agents/skills/review-plan/SKILL.md   # expect 1
grep -c "per the plans skill's Plan Quality Gate budget formula" agents/skills/review-loop/SKILL.md   # expect 1
grep -c "lint level" agents/skills/review-staging/SKILL.md   # expect >=1
grep -c "derived from the plan's declared execution budget" agents/skills/execute-plan/SKILL.md   # expect >=1
test -f docs/history/backlog/2026-10-09-driver-extraction-cap-readiness-drift.md   # the filed fix row
```

**Tests:**
```bash
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )   # exit 0, including the new pins
python3 scripts/test_plan_review_boundary_examples.py   # exit 0 over the edited skills
bash scripts/check-no-em-dash.sh file agents/skills/plans/SKILL.md agents/skills/review-plan/SKILL.md agents/skills/review-loop/SKILL.md agents/skills/review-staging/SKILL.md agents/skills/execute-plan/SKILL.md   # exit 0
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: plans skill budget, delta-round, certification, and validation-split text

Files:
- `agents/skills/plans/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `Plan Quality Gate` in `agents/skills/plans/SKILL.md`, owns the authoring review-loop round rules this plan amends.

- [x] In the Plan Quality Gate's staging-pair hard-validation duty paragraph, add the lint/full split: per-round validation runs at lint level, the `--preflight` report-only pass whose reported findings the orchestrator reads and resolves before the round is reported complete. [class: IMPLEMENTATION_REQUIRED]
- [x] Complete the lint/full split: the certification round keeps the full `--hard --source-plan` gate before its verdict is recorded; the round-close full-gate precondition and the execution and finalization boundaries keep their existing full readiness validators, keeping the ledger's review-staging-validator certification and round-close catches protected. [class: IMPLEMENTATION_REQUIRED]
- [x] In the fold re-probe rule, add the delta-round scope: the round a classified round-launching fold triggers is a delta round, a focused-panel review round scoped to the fold diff plus the mandatory blind correctness-completeness probe, its panel the owning worker of each folded finding plus the workers owning domains the fold diff touched. [class: IMPLEMENTATION_REQUIRED]
- [x] In the fold re-probe rule, complete the delta-round scope: only a semantic plan change (an unclassified or operator-acked delta under the same classifier arm) reopens a whole-plan panel; a delta round never consumes the full-panel budget regardless of its roster and keeps counting toward the total-round interval. [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the re-probe counting rule: only whole-plan-scope rounds count as full-panel rounds; the all-five-worker re-probe counts as a full-panel round only when the re-probe scope is the whole plan, so a delta round never counts regardless of its roster. [class: IMPLEMENTATION_REQUIRED]
- [x] Beside the exit rule, add the certification-residual routing (blocking-only): the certification round considers blocking findings only; its non-blocking findings are recorded in the terminal record's overflow section (the existing sidecar field), and never force a re-round or a plan fold; the soften watchlist keeps its fix-keyed shape untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] Beside the exit rule, complete the certification-residual routing's durable backlog capture: a backlog row in this repository's backlog for every consequence-bearing residual, filed as part of the per-family terminal certification duties in every family and verified row-by-row before the run exits. [class: IMPLEMENTATION_REQUIRED]
- [x] Beside the exit rule, name the capture homes in the same routing: in the plan family in the terminal round's workflow-reflection paragraph (plans rule 6); in the code family in the exit report's fixed-vs-backlogged tally; the record pair lives in the gitignored reviews_dir, so the backlog row is the only durable copy of a consequence-bearing residual. [class: IMPLEMENTATION_REQUIRED]
- [x] In plans rule 6's terminal-round workflow-reflection paragraph enumeration, grow the checked set with the row-by-row certification-residual backlog verification (the plan family's leg of the durable-capture check). [class: IMPLEMENTATION_REQUIRED]
- [x] Beside the round-cap rule, add the budget formula: the full-panel budget is 2 full-panel rounds for a declared execution budget of 2 hours or less, plus 1 full-panel round per additional started 2 hours (a 3-4 hour plan gets 3, a 5-6 hour plan gets 4); a declaration beyond 6 hours never buys a larger budget (the ceiling is D-8 clause (3)'s policy, not a plan-sizing threshold), and such a plan remains the plan-sizing doctrine's split business at the task level. [class: IMPLEMENTATION_REQUIRED]
- [x] Complete the budget rule: a plan carrying no declared line keeps the configured interval semantics; delta rounds never consume the budget; breaching it pauses the loop for operator direction per review-plan's Scope and complexity policy duty (extend the derived budget by a stated number of full-panel rounds, continue for one further full-panel round, or park and report; an unattended lane parks and reports) before another full-panel round launches. [class: IMPLEMENTATION_REQUIRED]
- [x] Add pins rows to scripts/check_maintenance_pins.sh pinning each new span with the existing pin style, each count-gated to exactly 1 on the post-edit tree: the formula sentence (including its no-line fallback and breach-pause completion), the delta-round sentence (including its semantic-reopen completion), the counting-rule sentence, and the certification-residual routing sentence (including its durable-capture completion and capture homes). [class: REPOSITORY_TEST]
- [x] Add pins rows to scripts/check_maintenance_pins.sh for the remaining new spans, same pin style and count-gating to exactly 1 on the post-edit tree: the reflection-paragraph growth sentence and the lint-split sentence (including its boundary-retention completion); then run the pins suite, the boundary-fixture regression, and the em-dash scan (file mode) over the edited file. [class: REPOSITORY_TEST]

### Task 2: review-plan skill mirror text

Files:
- `agents/skills/review-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `Step 4: Output` in `agents/skills/review-plan/SKILL.md`, owns the plan-review round record and mechanical gate this plan splits.

- [x] In Step 4's mechanical-gate paragraph, split the validation classes by reference: intermediate rounds whose staged record carries unresolved blocking findings and that cannot record the certifying verdict run the lint-level `--preflight` pass and resolve its findings; a round in doubt or able to certify runs full; the certification round keeps the full `--hard --source-plan` gate before its verdict is recorded, per review-staging's record-validation-levels subsection. [class: IMPLEMENTATION_REQUIRED]
- [x] Own the standing-mandate subordination: review-plan's standing Step 4 mechanical-gate sentence is subordinated to the partition (lint-level pass at non-certification rounds whose staged record carries unresolved blocking findings; the full gate at certification rounds, round-close, and the execution and finalization gates; a round in doubt or able to certify runs full); Task 3's fill-order subordination references this checkbox as the review-plan leg's owner. [class: IMPLEMENTATION_REQUIRED]
- [x] Beside Step 5's fold rules, add the certification-residual routing by reference per review-staging's certification-residual routing note: at certification, non-blocking findings are recorded in the terminal record's overflow section with durable backlog capture and never force a re-round or a plan fold; intermediate-round fold discipline is unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] In the Scope and complexity policy, add the budget sentence by reference: the full-panel round budget derives from the plan's declared execution budget per the plans skill's Plan Quality Gate budget formula, delta rounds never consume it, and breach pauses the loop for operator direction per this same policy's pause duty; the reconciliation triggers keep precedence. [class: IMPLEMENTATION_REQUIRED]
- [x] In the Scope and complexity policy's pause duty, grow the checked set with the breach mechanics: extend the derived budget by a stated number of full-panel rounds, continue for one further full-panel round, or park and report; an unattended lane parks and reports. The plans skill's budget rule (Task 1) is the pinned mirror of this owner duty and carries the same mechanics; both spans are pinned, so a later mechanics change finds both. [class: IMPLEMENTATION_REQUIRED]
- [x] In the Iteration Discipline cap-closure rule, extend the trigger wording: the operator-authorization requirement applies at the configured round cap and at full-panel budget breach alike, the closure mechanics byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the review-plan pins rows beside Task 1's, count-gated to exactly 1 each: the budget-by-reference sentence, the certification-residual routing sentence, the pause-mechanics sentence, the lint-split sentence, the standing-mandate subordination sentence (the subordinated Step 4 mechanical-gate sentence), and the rule 8 trigger-extension sentence; then run the pins suite, the boundary-fixture regression, and the em-dash scan (file mode). [class: REPOSITORY_TEST]

### Task 3: review-loop and review-staging text

Files:
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `Limits` in `agents/skills/review-loop/SKILL.md`, owns the loop's round counters and interval semantics.

- [x] Under the Limits table, add: when the loop carries a plan's declared execution budget, the full-panel budget derives from it per the plans skill's Plan Quality Gate budget formula and breach pauses the loop for operator direction per review-plan's Scope and complexity policy duty; standalone loops keep the configured intervals. [class: IMPLEMENTATION_REQUIRED]
- [x] Under the Limits table, add the plan-scoped counting rule: in a plan-scoped loop, delta (focused) rounds never consume the full-panel counter and the whole-plan review scope, not the panel roster, decides the full-panel count. [class: IMPLEMENTATION_REQUIRED]
- [x] In review-loop's Orchestration rule 3, scope-key the full-panel counting sentence: a post-fold round counts as a full-panel round only when its scope is the whole plan (plan-scoped loops); delta (focused) rounds never increment the full-panel counter regardless of roster; standalone loops keep the roster-keyed counting unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] In the counting rule, add the scope key: in a plan-scoped loop, the all-five-worker post-fold round counts as a full-panel round only when its scope is the whole plan, so a delta round never counts regardless of its roster; standalone loops keep the roster-keyed counting unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] In the mechanical-gate paragraph, split the validation classes per review-staging's record-validation-levels subsection: intermediate rounds run the lint-level `--preflight` pass over the staging pair with the same source context and resolve its findings before the round's triage and counter decisions are consumed; the certification round keeps the full `--hard` source-context gate before its verdict is recorded. [class: IMPLEMENTATION_REQUIRED]
- [x] In review-staging, add one record-validation-levels subsection defining the lint level (the `--preflight` report-only pass whose findings the orchestrator resolves; non-certification rounds) and full validation (the `--hard` pass with the source context; certification rounds, round-close, and the execution and finalization gates). [class: IMPLEMENTATION_REQUIRED]
- [x] In the same record-validation-levels subsection, add the round-class decision rule: a round that could record the certifying clean verdict (any fresh-adversarial round with zero staged unresolved blocking findings, and any round in doubt) runs the full `--hard` source-context gate; lint is reserved for rounds whose staged record carries unresolved blocking findings and that cannot record the certifying verdict. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same record-validation-levels subsection, name the ledger's review-staging-validator entry as the protected certification catches and state the code-family residual: a loop that terminates without certifying rests on a lint-only record. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same subsection, subordinate review-staging's fill-order step-6 `--hard` sentence to the partition: its full-strength gate applies at certification rounds, round-close, and the execution and finalization gates; non-certification rounds whose staged record carries unresolved blocking findings run the lint-level pass; a round in doubt or able to certify runs full. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same subordination clause, name the peer half by reference: review-plan's standing sentence is subordinated by Task 2's owning checkbox, not by this task. [class: IMPLEMENTATION_REQUIRED]
- [x] In review-staging's orchestrator recording rules, add one rule beside the watchlist rule fixing the delta round's record semantics - its Source digest is the SHA-256 of the post-fold whole plan bytes (recording compatibly with scripts/review_record_selection.py's differing-digest new-round path), the fold-diff scope is named in the Selection reason, and `panel_mode` stays focused. [class: IMPLEMENTATION_REQUIRED]
- [x] Beside the watchlist section, add the certification-residual routing note: certification-round non-blocking findings are recorded in the terminal record's overflow section (the existing sidecar field) with durable backlog capture (a backlog row for every consequence-bearing residual), never force a re-round, and never enter the soften watchlist, whose fix-keyed shape and closure obligations stay untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the review-loop and review-staging pins rows, count-gated to exactly 1 each: the Limits budget sentence, the counting-rule scope-key sentence, the mechanical-gate split sentence, the record-validation-levels subsection heading, the delta-round recording rule, and the certification-residual routing note; then run the pins suite and the em-dash scan (file mode) over both files. [class: REPOSITORY_TEST]
- [x] Add the remaining review-loop and review-staging pins rows, same pin style and count-gating to exactly 1 each: the review-loop plan-scoped counting-rule sentence, the ledger lint-only-record sentence, the rule 3 post-fold scope-key sentence, the round-class gate-selection sentence, and the fill-order subordination sentence. [class: REPOSITORY_TEST]

### Task 4: execute-plan Phase 3 budget derivation

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `Phase 3: Review / Fix Loop` in `agents/skills/execute-plan/SKILL.md`, owns the execution-side review loop this plan re-budgets.

- [x] In the Phase 3 tracking list, reword `budget_readiness_reviews` from the flat default 3 to derived: fresh whole-plan review rounds per run, derived from the plan's declared execution budget per the plans skill's Plan Quality Gate budget formula; plans without a declared line keep the flat default 3. [class: IMPLEMENTATION_REQUIRED]
- [x] In the review end-condition table, amend the full-panel interval row, keeping the reflection duty in the row and preserving the row's existing reflection literal byte-for-byte: the full-panel reflection interval stays today's reflection checkpoint and is not a stop limit. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same full-panel interval row, add the budget mechanics beside the reflection duty: the full-panel round budget derives from the plan's declared execution budget (plans without a declared line keep the flat default 3); delta (focused) rounds never consume it; breach pauses the loop for operator direction per review-plan's Scope and complexity policy pause duty and its breach mechanics before another full-panel round. [class: IMPLEMENTATION_REQUIRED]
- [x] In execute-plan's Phase 3 tracking list, scope-key the `full_panel_rounds` increment rule to match: increment only on whole-plan-scope rounds; a delta (focused) round never increments the counter regardless of roster. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the execute-plan pins rows beside Task 3's, count-gated to exactly 1 each: the tracking-line derivation sentence (including the default-3 fallback), the amended end-condition row, and the increment-rule scope-key sentence; then run the pins suite and the em-dash scan (file mode) over the edited file. [class: REPOSITORY_TEST]

### Task 5: extraction-cap fix row and final verification

Files:
- `docs/history/backlog/2026-10-09-driver-extraction-cap-readiness-drift.md` *(new)*

Primary class anchors:
- `check_maintenance_pins.sh` in `scripts/check_maintenance_pins.sh`, the pins suite whose full pass certifies the executed tree.

- [x] File the 4096-byte extraction-cap fix row: the driver refusing Phase 0 over checklist class labels the readiness oracle does not measure (the 4556-byte refusal witnessed in the origin row), classed as the readiness-versus-driver extraction contract-drift seam owned by the contract single-sourcing family, with the origin row's evidence cited. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full verification battery on the executed tree: the pins suite, both validation-command blocks, the boundary-fixture regression, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]
