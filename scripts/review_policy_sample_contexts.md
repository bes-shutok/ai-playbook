# Review policy sample contexts

These cases are executable policy walkthroughs. For each case, read the plan signals, count the recorded rounds, apply `review-panel-selection.md`, then apply the reflection and continuation rules in `review-loop`, `execute-plan`, and `plans`. `R` is total review rounds; `F` is full-panel rounds. Unless a case says otherwise, findings and blockers are explicitly stated and there are no unrelated stop conditions. The transcript below records the round-by-round application of those rules; it is policy evidence, not a claim that the skill documents themselves are runtime programs.

## Sample plans and round records

### A. Former project-root pair, narrow change

Two otherwise identical consumers once lived inside and outside a configured project root. Each plan changes one Markdown contract sentence and one focused pin, with no interaction, behavior, risk, or safety-boundary signal. Both select the same focused docs-only panel, `contract-docs` plus `correctness-completeness` for the normative contract sentence; no code-mutation signal fires, so the risk-signal floor never escalates either root. After round 1, blockers fall from 2 to 1, with no churn or recurrence. The next action is to continue without asking.

### B. Former project-root pair, broad change

The same paired locations now carry a plan changing a public API, persistence state transition, and asynchronous retry interaction across four components. Each has the same complexity evidence, risk signals, and round record. Both select the risk-signal floor, escalating to the full five-worker panel at two risk signals. No location or ownership difference changes selection. After round 1, blockers fall from 4 to 2; continue.

### C. Independent total-round and full-panel intervals

Configure `max_review_rounds=5` and `max_full_panel_rounds=3`. Round records are: r1 full (F1), r2 focused (F1), r3 full (F2), r4 focused (F2), r5 full (F3), r6 full (F4), r7 focused (F4), r8 full (F5), r9 full (F6), r10 focused (F6), r11 full (F7), r12 focused (F7), r13 full (F8), r14 focused (F8), r15 full (F9). Reflect at total rounds 5, 10, 15 and full-panel rounds 3, 6, 9. Coincidences at r5 and r15 each produce one reflection recording both interval labels; r10 is a total-round-only reflection.

### D. Five-round intervals through coincidence

Configure both intervals to 5 and continue the sequence through r15. Total-round checkpoints: r5, r10, r15. Full-panel checkpoints: F5, F10, F15. For the paired coincident trajectory, all 15 rounds are full-panel rounds, so the two counters coincide at r5, r10, and r15. Record exactly one reflection at each checkpoint, with both interval labels recorded. A checkpoint does not itself stop or reconcile.

### E. Convergence at a checkpoint

At r5, open blockers fell from 3 at r4 to 1, with no active churn or recurrence. Record finding classes, counts, open blockers, and both interval labels if they coincide. Continue the next review without asking; do not reconcile solely because r5 is a configured interval.

### F. Active churn despite falling blockers

At r5, open blockers fell from 3 to 2, but fold-defect plus wording findings exceed half of staged findings. This active trigger takes precedence over the otherwise falling blocker count: run review-reconciliation before another review or fix pass, then attempt at most one concrete simplification or refactor. If none is available, pause before another review. If the first changed alternative receives a fresh review and the same blockers remain, pause before launching another review.

### G. Bounded self-heal trajectories

**No alternative available:** a recurrence trigger fires; run reconciliation, inspect for one concrete simplification/refactor, find none, then pause for operator direction before another review.

**First alternative unsuccessful:** a recurrence trigger fires; run reconciliation, apply one concrete simplification, then run one fresh review. The same blockers remain, so pause for operator direction before a second alternative or another review. Never attempt a second automatic alternative.

**Authorization and run-wide allowance:** When the plan explicitly authorizes one concrete simplification attempt, reconciliation may make that one attempt and records `self_heal_attempt={"status":"consumed","run_id":"<stable-run-id>","round":"rN","source_digest":"<current-sidecar-source-digest>"}` before changing the branch. When the plan does not authorize it, pause before changing the branch. If a later trigger fires after the run has already used its attempt, a resumed workflow reads the retained consumed value and pauses before any second attempt, even if the later blockers differ. Missing or malformed prior evidence becomes `unknown`, which also pauses before self-heal.

### J. Churn trigger boundary examples

| Trigger | Non-trigger witness | Trigger witness | Decision |
|---|---|---|---|
| Fold-defect plus wording must be strictly greater than half of staged findings | 2 of 4 is exactly half | 3 of 4 is greater than half | 2 of 4 does not trigger; 3 of 4 triggers reconciliation |
| Staged finding totals are checked across the two most recent rounds | 4 to 3 decreases | 4 to 4 is flat; 4 to 5 increases | 4 to 3 does not trigger; 4 to 4 and 4 to 5 trigger reconciliation |
| Positive blocker counts are checked across two consecutive rounds | 2 to 1 decreases | 2 to 2 stays positive and flat | 2 to 1 does not trigger; 2 to 2 triggers reconciliation |

### H. Paired no-progress operator pauses

Configure a five-round total interval. Both trajectories have unchanged blocker counts and no churn trigger. In H1, an independent operator pause arrives after r5, exactly when the configured reflection checkpoint is reached: record the reflection and permit the existing cap-closure terminal mechanics. In H2, the same pause arrives after r4, between checkpoints: pause under the independent operator request without invoking cap closure; the interval itself grants no terminal shape. A cap is never a stop by itself.

### I. Complete 5/3 recurring schedule

Configure `max_review_rounds=5` and `max_full_panel_rounds=3`; all 15 rounds use the full panel, so R and F counters advance together. At r3, reflect for F3 while R=3 is below 5. At r5, reflect for R5 while F=5 is below 6. Continue with single reflections at r6/F6, r9/F9, and r10/R10. At r12/F12, reflect once. At r15, reflect once for both R15 and F15. This single trajectory demonstrates both independent first hits, both complete schedules through round 15, and the later coincidence.

## Observed outcomes

### Walkthrough transcript

| Case and step | Input / counters | Policy application | Recorded outcome / next action |
|---|---|---|---|
| A, both roots, r1 | One docs contract sentence and focused pin; 2 blockers become 1; no churn | Same docs-only scope and complexity select the same focused panel (`contract-docs` plus `correctness-completeness`) for each root | Continue both without asking |
| J, fresh loop r1 | Positive blockers; no prior blocker count and no churn or recurrence trigger | No trajectory baseline exists yet, so the shared policy allows one round to establish it | Continue one round, then apply the measured convergence rule |
| B, both roots, r1 | API, persistence transition, async retry across four components; 4 blockers become 2; two risk signals | Same broad scope and risk floor select the full five-worker panel for each root | Continue both; root location has no effect |
| C, r1-r4 | Full/F1, focused/F1, full/F2, focused/F2 | Increment total on every row, F only on full rows; no checkpoint | Continue |
| C, r5 | Full/F3; R=5, F=3 | Both configured intervals are due; emit one reflection with total-5 and full-3 labels | Converging trajectory continues |
| C, r6-r9 | Full/F4, focused/F4, full/F5, full/F6 | No total checkpoint; F=6 reaches full-panel interval | At r9 emit one full-6 reflection; continue |
| C, r10 | Focused/F6; R=10 | Total-10 only; no duplicate full checkpoint | Emit one total-10 reflection; continue |
| C, r11-r14 | Full/F7, focused/F7, full/F8, focused/F8 | No configured interval due | Continue |
| C, r15 | Full/F9; R=15, F=9 | Both intervals due; emit one reflection with total-15 and full-9 labels | Continue after reflection |
| D, r5/r10/r15 | All rounds full; R=F=5/10/15 | Each paired checkpoint is a single reflection with both labels | Continue after each reflection |
| I, r1-r2 | Full/F1, full/F2; R=2, F=2 | Counters advance together; no checkpoint | Continue |
| I, r3 | Full/F3; R=3, F=3 | Full-panel first hit; total counter remains below 5 | Reflect once; continue |
| I, r4 | Full/F4; R=4, F=4 | No checkpoint | Continue |
| I, r5 | Full/F5; R=5, F=5 | Total first hit while F remains below 6 | Reflect once; continue |
| I, r6-r8 | Full/F6, full/F7, full/F8; R=6-8 | F6 checkpoint at r6 only | Reflect at r6; continue through r8 |
| I, r9-r10 | Full/F9, full/F10; R=9-10 | F9 at r9; total R10 at r10 | Reflect once at each; continue |
| I, r11-r14 | Full/F11, full/F12, full/F13, full/F14; R=11-14 | F12 checkpoint at r12 only | Reflect at r12; continue |
| I, r15 | Full/F15; R=15, F=15 | R15 and F15 coincide | Emit one combined reflection |
| F, r5 | 3 blockers become 2; fold-defect + wording exceed half | Active churn overrides blocker decline | Reconcile, try at most one concrete simplification/refactor |
| G, unauthorized alternative | Plan does not authorize the refactor | Authorization gate prevents mutation | Pause before changing the branch |
| G, later trigger after attempt | The run already used its one authorized attempt | Allowance does not renew on later rounds | Pause before a second attempt |
| G, authorized attempt | New artifact chain starts at r1 with unused state bound to its `review-run-id` | Reserve consumed state with the stable `run_id` before mutation | Apply one attempt and carry the consumed state unchanged |
| G, unauthorized attempt | Plan does not authorize; state is unused | The authorization gate prevents mutation | Pause before changing the branch |
| G, resumed after attempt | Latest state is consumed for r3 with stable `run_id` and digest | Resume reads and preserves the consumed marker | Pause before a second attempt |
| G, legacy resume | Prior record or sidecar is missing or malformed | Record `unknown` with this round's `review-run-id`; validator rejects `unused` | Pause before self-heal |
| G, new invocation | A new artifact chain starts at r1 with a newly minted `review-run-id` | Orchestrator writes `unused` with matching `run_id` | New invocation receives its own one-attempt allowance |
| J, exact half | 2 of 4 findings | Strictly greater-than-half condition is false | 2 of 4 does not trigger reconciliation |
| J, above half | 3 of 4 findings | Strictly greater-than-half condition is true | 3 of 4 triggers reconciliation |
| J, staged totals | 4 to 3 / 4 to 4 / 4 to 5 | Only flat or increasing totals trigger | 4 to 3 continues; 4 to 4 and 4 to 5 reconcile |
| J, blocker totals | 2 to 1 / 2 to 2 | Only positive non-decrease triggers | 2 to 1 continues; 2 to 2 reconciles |
| G, no alternative | Recurrence; reconciliation finds no concrete option | One bounded search is exhausted | Pause before another review |
| G, first alternative fails | Recurrence; one change and one fresh review leave same blockers | One automatic alternative attempt is exhausted | Pause before a second alternative or another review |
| H1, r5 | No progress; independent operator pause coincides with total-5 reflection | Record reflection, then apply explicit pause authorization | Existing cap-closure mechanics are available |
| H2, r4 | No progress; independent operator pause before any checkpoint | Apply pause request only | Pause; cap closure is unavailable |

| Case | Panel choice | Reflection checkpoints | Next action |
|---|---|---|---|
| A, both former roots | Same focused docs-only panel; `contract-docs` plus `correctness-completeness` | None by r1 | Continue; blocker count fell |
| J, fresh loop r1 | Any panel selected by scope/complexity | None; this is the baseline round | Continue once to establish the blocker trajectory |
| B, both former roots | Same risk-signal floor/full five-worker panel | None by r1 | Continue; blocker count fell |
| C | Full/focused as recorded | Total r5, r10, r15; full-panel F3, F6, F9; each coincidence combined | Continue after each reflection when converging |
| D | Full panel for each recorded F checkpoint | r5, r10, r15; r15 is one combined reflection | Continue after each reflection when converging |
| E | Per scope/complexity selection | r5 | Continue without asking; no reconciliation |
| F | Per scope/complexity selection | r5 | Reconcile, then one simplification/refactor attempt; pause if unavailable or unsuccessful |
| G, no alternative | Per scope/complexity selection | Trigger-driven | Pause immediately after the single search finds no option |
| G, unsuccessful first alternative | Per scope/complexity selection | Trigger-driven | Fresh review once, then pause before another review |
| H1, pause at checkpoint | Per scope/complexity selection | r5 | Reflection plus existing cap-closure mechanics are available because the independent pause coincides with the checkpoint |
| H2, pause between checkpoints | Per scope/complexity selection | None at r4 | Cap closure is unavailable; pause only under the independent operator request |
| I, complete 5/3 schedule | Full panel each round | Full-panel F3/F6/F9/F12/F15; total R5/R10/R15; r15 combined; R5 occurs at F5 | Continue after each reflection; first hits at F3/R3 and R5/F5 are independent |
