# Plan: done guard-stack liveness read side and review declaration

Backlog origin: docs/history/backlog/2026-10-05-done-guard-stack-liveness-economics.md
Driving force: simplicity + efficiency (both closed-taxonomy principles; the plan prices the guard stack for retirement through a measured ratio, so the section 64 fewer-moving-artifacts rule gains its stack-level counter)
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-done-gate-liveness-retirement-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- guard liveness ledger: the tracked recorder at `scripts/gate_liveness_ledger.py` plus `scripts/gate_liveness_ledger.json` (live since the 2026-10-05 partial landing) holding per-guard catch, incident, and basis rows.
- catch-to-incident ratio: the ledger's stack-level tally of live true catches against guard-attributable incidents, printed by the `show` subcommand.
- observation window: the ledger's `window.started` date (2026-10-05) through the operator-recorded `closed` date (YYYY-MM-DD) in the ledger's `window` object (a documented manual edit; the recorder gains no close subcommand and the read side never writes), the period a guard must survive with zero `catch` rows before its removal-or-narrow candidacy can be filed; while no `closed` date is recorded the window is open and the read side stays report-only.
- removal-or-narrow candidate: a guard the read side flags for retirement or posture narrowing, adjudicated under `projects/.ai-playbook/agent_workflow_guidelines.md` section 64.
- read side: the friction-audit lane's duty to read the ledger each run and generate candidates; the write side (done Step 7 appends) already landed.
- review-side declaration: the Gate delta line's duty to cite the ledger ratio when a plan adds a gate or fence, audited by review-plan's Declaration findings.
- solo-closeout hygiene gate: a done-closeout gate whose failure mode is blocking a closeout at the commit boundary (the class the origin's posture arm names), as opposed to the witnessed-damage landing fences.

## Why

The done guard stack was assembled guard-by-guard against witnessed incidents, and nothing ever counted its stack-level cost: the wired ledger's printed tallies stand at 4 catches against 11 incidents (2 verified plus 2 partial catches), the origin's broader backlog-row census prices 2 verified live catches against 13 to 15 guard-attributable incidents, and the skill regrew to 700 lines within ten days of the 453-line dismantling. The ledger recorder landed same-day; what it still lacks is a reader and a pricing duty, so the measured ratio never reaches the retirement adjudication or a new gate's review.

## Outcome

The friction-audit lane reads the ledger every run and turns guards with zero `catch` rows into section 64 removal-or-narrow candidates after the observation window, and every plan that adds a gate or fence prices the addition against the ledger's catch-to-incident ratio in its Gate delta line.

- The friction-audit lane reports per-guard liveness each run and files removal-or-narrow candidates when the window closes, so retirement decisions read measurements instead of anecdotes.
- A plan adding a gate or fence cites the ledger ratio in its Gate delta line, and review-plan's declaration audit checks the citation, giving the fewer-moving-artifacts rule its global counter.
- The posture flips for the named solo-closeout hygiene gates that still hold zero `catch` rows when the window closes emerge from the lane's candidates, per the origin's own rejection of a wholesale flip; a gate with any catch row (the dirt-regression gate holds a partial catch row) is never a candidate, and the claim-or-foreign classification preflight must first hold a ledger guard row or take an explicit section 64 route before the lane can name it.
- Gate delta: grows the friction-audit lane's checked-condition set (the ledger read-side duty) and the plans and review-plan declaration surfaces (the ledger-citation duty and its audit); no refusal class, hard gate, fence, protocol layer, or schema state field is added, and nothing is removed. Priced by the cited completed-integrity-failure witnesses in the origin row: the wired ledger's printed 4:11 tally (2 verified plus 2 partial catches against 11 incidents) and the origin's separately attributed 2-against-13-to-15 backlog-row census, alongside the ten-day 453-to-700-line regrowth, all re-derived from git history in the investigate pass, with the recorder itself landed by the same origin's partial landing.

## Assumptions

- assume the posture flips for the named solo-closeout hygiene gates are out of this plan's scope: the flips emerge from the read side's candidates after the observation window closes, for gates that still hold zero `catch` rows at that point (the dirt-regression gate's partial catch row excludes it, and the claim-or-foreign classification preflight needs a ledger guard row or an explicit section 64 route before it can be named); basis: the origin's rejected alternative rejects converting gates to the softer posture in one landing because a wholesale flip would churn every pinned span at once, the window opened 2026-10-05 so flipping on day-zero data contradicts the observation-window design, and the origin's own reasoned precedent is fold-and-narrow after observed windows.
- assume the entry's provenance claim that the flips ride the dirt-gate and post-landing-staging plans no longer holds: the dirt-gate plan's posture content is fail-closed shape handling and the post-landing-staging plan (executed and archived by a peer today) pins its strict legs explicitly, and the ledger JSON's own dirt-regression-gate note still carries the stale ride-on claim as a carrier record left in place (the ledger is out of scope); basis: grep of both plans found no fail-loud flip arms.
- assume the friction-audit registry task file is the only wiring surface for the read side; basis: the maintenance skill's friction-audit consult stub delegates to the task file as the procedure of record and the origin says no new runner.
- assume the ledger citation is an ordinary (non-blocking) declaration finding; basis: the review-plan Declaration findings paragraph's own pricing ladder reserves blocking for unpaid counted-class additions, and the citation is a pricing-evidence duty, not a new counted class.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: The guard liveness ledger gains its reader and its pricing duty, so retirement decisions and new-gate reviews read the measured catch-to-incident ratio (simplicity + efficiency).

**Before (today):** The ledger records every guard firing, but nothing reads it: the friction-audit lane runs its quantitative session pass and never opens the ledger, so a guard with zero `catch` rows sits unpriced forever, and a plan adding a new gate declares its Gate delta with no stack-level counter in sight. The printed 4:11 tally stays an anecdote in a ledger file.

**After (this plan):** Each friction-audit run prints the ledger's per-guard tallies, names every guard with zero `catch` rows as a removal-or-narrow candidate, and files the candidate through the normal backlog capture when the observation window closes, with the section 64 adjudication attached. A plan whose Gate delta adds a gate or fence cites the ledger's current catch-to-incident ratio on the line, and review-plan's declaration audit flags a missing citation as an ordinary finding.

Edge cases: a guard with a catch row is never a candidate regardless of incidents; a window that has not closed yields candidates reported in the audit report only, never filed; a ledger that cannot be read is reported as the run's tool evidence and never fabricated.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the declaration fixture passes and the ledger's `show` subcommand output carries the catch-to-incident ratio the new duties cite.
- regression safety: the pins suite stays green; the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: the read side writes nothing to the ledger; the review-side citation applies only to Gate delta lines declaring a gate or fence addition.

**Done when:**
- `( cd "$REPO" && python3 scripts/test_gate_liveness_wiring.py )` exits 0.
- The full Validation Commands block exits 0 on the executed tree.

**Ship when:**
- The next friction-audit run reports per-guard liveness and the next gate-adding plan cites the ledger ratio; both are routine-turn behaviors requiring no further human action in this repository beyond the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `docs/maintenance/recurring-tasks/friction-audit.md` (the new Guard liveness read-side section after the Filing rule; all other sections are frozen)
- `agents/skills/plans/SKILL.md` (the new rules-list bullet beside the classification-tag rule; all other sections are frozen)
- `agents/skills/review-plan/SKILL.md` (the Declaration findings paragraph's final sentence region for the citation audit; all other sections are frozen)

**Tests:**
- `scripts/test_gate_liveness_wiring.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/gate_liveness_ledger.py` and `scripts/gate_liveness_ledger.json`; reason: the recorder landed with the partial landing and its contract is not touched.
- `agents/skills/done/SKILL.md`; reason: the Step 7 append duty already landed; this plan adds no done-skill bytes.
- the four named solo-closeout hygiene gates' block postures; reason: the flips emerge from the read side's candidates after the observation window per the recorded assumption.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed `python3 scripts/plan_readiness.py --pre-round` with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against the three skill targets (the new-duty spans returned no match; the preserved spans matched); the rule 22 mechanical audit verified every pinned span occurs exactly once in its owning prescribed snippet (rule 36 mirrors included; the preserved spans matched against the current target bytes) and `bash -n` accepted the Validation Commands block. Round-start state for r3: authoring worktree ai-playbook-wt-dgl, branch 2026-10-05-done-gate-liveness-retirement, plan bytes at the r2 fold commit (the r2 verification panel adjudicated all eight r1 folds fixed with zero blocking findings and stood five fresh non-blocking findings, folded in one pass).

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && python3 scripts/test_gate_liveness_wiring.py -v )
( cd "$REPO" && python3 scripts/gate_liveness_ledger.py show )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: Pin the liveness wiring contract (RED fixture suite)

Files:
- `scripts/test_gate_liveness_wiring.py` *(new)*

Evidence:
- `( cd "$REPO" && python3 scripts/test_gate_liveness_wiring.py )`; covers the RED-today criterion: the declaration tests fail on the absent spans while the ledger-output test passes

- [x] Create `scripts/test_gate_liveness_wiring.py` as a unittest module that resolves the repository root from its own file location and contains two groups: the declaration group asserting fixed-string spans against the three skill targets, and one behavior group running the ledger's `show` subcommand against the real ledger [class: REPOSITORY_TEST]
- [x] `LivenessWiringDeclarationTest#test_friction_audit_read_side_declared`; given docs/maintenance/recurring-tasks/friction-audit.md, expects the file to contain `Guard liveness read-side`, `gate_liveness_ledger.py show`, `removal-or-narrow candidate`, and `when the observation window closes` [class: REPOSITORY_TEST]
- [x] `LivenessWiringDeclarationTest#test_gate_delta_citation_declared`; given agents/skills/plans/SKILL.md, expects the file to contain `Gate delta ledger citation` and `gate_liveness_ledger.py show` [class: REPOSITORY_TEST]
- [x] `LivenessWiringDeclarationTest#test_review_plan_audit_declared`; given agents/skills/review-plan/SKILL.md, expects the file to contain `cites no ledger ratio` and `the plans skill's Gate delta ledger citation bullet` [class: REPOSITORY_TEST]
- [x] `LivenessWiringBehaviorTest#test_ledger_show_prints_stack_ratio`; given the repository's real ledger, expects `python3 scripts/gate_liveness_ledger.py show` to exit 0 with a final `OUTCOME: pass` line and output naming the per-guard tallies and the catch-to-incident ratio [class: REPOSITORY_TEST]
- [x] `LivenessWiringDeclarationTest#test_preserved_anchors_stay_pinned`; given the three skill targets, expects the preserved spans `Filing rule` and `Caps` (friction-audit.md headings), `scope_classification_problem` (plans/SKILL.md), and `Declaration findings` (review-plan/SKILL.md) to remain present [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd "$REPO" && python3 scripts/test_gate_liveness_wiring.py )` fails with the declaration tests erroring or failing on the absent spans, while the behavior and preserved tests pass [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the guard liveness wiring contract (RED)` [class: REPOSITORY_TEST]

### Task 2: Read side and review declaration (GREEN)

Files:
- `docs/maintenance/recurring-tasks/friction-audit.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

Evidence:
- `( cd "$REPO" && python3 scripts/test_gate_liveness_wiring.py )`; covers the GREEN criterion: all fixture tests pass
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-reconciliation criterion: no pin row's literal broke

- [x] Insert the following section into `docs/maintenance/recurring-tasks/friction-audit.md` immediately after the `## Filing rule` section's body (the heading `## Filing rule` is the unique anchor; the new section sits between it and `## Caps`) [class: IMPLEMENTATION_REQUIRED]

```markdown
## Guard liveness read-side

After the quantitative pass and before filing findings, run `python3 scripts/gate_liveness_ledger.py show` (repo-local copy first, then the deployed home copy), read the per-guard tallies from its output, and read the ledger's `window.started` field and close-date presence from the ledger JSON: every guard with zero `catch` rows across the observation window is a removal-or-narrow candidate, named in this run's report with its guard name, its incident count, and the window start date. While the observation window is open (the ledger's `window` object records no `closed` date), candidates are report-only; when the observation window closes (the operator records a `closed` date in the ledger's `window` object), each zero-catch-row candidate is filed per the Filing rule as a removal-or-narrow backlog item carrying the section 64 adjudication (the fewer-moving-artifacts ranking against the guard's witnessed harm class, with the honest-concurrency, fail-closed, and accidental-damage carve-outs checked before any retirement proposal). The read side never writes to the ledger; a ledger that cannot be read is reported as this run's tool evidence and never fabricated.
```

- [x] Insert the following bullet into `agents/skills/plans/SKILL.md` immediately after the Classification tag rule bullet (the Rules-list bullet whose body contains the unique span `` `scope_classification_problem` reports the placement instead of classifying the item untagged. ``), inserting after the bullet's end [class: IMPLEMENTATION_REQUIRED]

```markdown
- **Gate delta ledger citation:** when a plan's `Gate delta` line declares an addition of a gate or fence (two of the five counted classes), the line also cites the guard liveness ledger's current catch-to-incident ratio (run `python3 scripts/gate_liveness_ledger.py show` at authoring time), so the section 64 fewer-moving-artifacts rule reads a measured catch-to-incident ratio instead of a per-mechanism judgment alone; a plan adding no gate or fence cites nothing.
```

- [x] In `agents/skills/review-plan/SKILL.md`, replace the span `Review-layer duties whose sole sanction is an ordinary finding sit outside the counted set; a review-layer duty whose violation blocks is a review-layer counted addition declared on the Gate delta line, and its own text records the explicit-user-decision witness that names its surface, as this clause does with the 2026-09-28 adjudication and the 2026-09-29 operator direction recorded in the symmetry origin's Source field.` (the Declaration findings paragraph's final sentence, quoted in full so the pre-image is sentence-terminated; verified unique on disk) at the end of the Declaration findings paragraph with `A Gate delta line that declares a gate or fence addition and cites no ledger ratio (the guard liveness ledger's catch-to-incident ratio per the plans skill's Gate delta ledger citation bullet) is an ordinary declaration finding. Review-layer duties whose sole sanction is an ordinary finding sit outside the counted set; a review-layer duty whose violation blocks is a review-layer counted addition declared on the Gate delta line, and its own text records the explicit-user-decision witness that names its surface, as this clause does with the 2026-09-28 adjudication and the 2026-09-29 operator direction recorded in the symmetry origin's Source field.` (the original final sentence is quoted in full in the replacement side, so the preserved witnesses are pinned verbatim) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd "$REPO" && python3 scripts/test_gate_liveness_wiring.py )` passes all five tests (four declaration plus one behavior); the pins suite exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: guard liveness read side and review-side ledger citation` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full validation

Evidence:
- The full `## Validation Commands` block; covers every Done-when criterion on the executed tree

- [x] Run → expect GREEN: the full Validation Commands block exits 0 line by line; the em-dash added-lines scan and the hygiene scan report no findings on the changed files [class: REPOSITORY_TEST]
- [x] Verify span uniqueness: for each new-duty span pinned in Task 1, `grep -cF` over its owning file returns exactly 1 after the edits, and for the four preserved spans it returns at least 1 [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-done-gate-liveness-retirement.md`; expect exit 0 with `OUTCOME: pass` at the certification boundary [class: REPOSITORY_TEST]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-dglr (branch plan-done-gate-liveness-retirement-exec) by the standing maintenance execution lane. Task 1 (0534f70f): scripts/test_gate_liveness_wiring.py pins the five-test wiring contract with the prescribed RED split (three declaration tests fail on absent spans; behavior and preserved-anchors pass). Task 2 (a03faaca): the Guard liveness read-side section lands between Filing rule and Caps in docs/maintenance/recurring-tasks/friction-audit.md; the Gate delta ledger citation bullet lands after the Classification tag rule bullet in agents/skills/plans/SKILL.md; the review-plan Declaration findings paragraph gains the missing-citation ordinary-finding sentence with the original final sentence preserved verbatim as the tail.

Validation: the wiring selftest 5/5 OK; the ledger show behavior test reports the live tallies (TOTAL: catches=4 incidents=11 ratio=4:11) with the window open, so the read side is report-only today; pins suite exit 0; em-dash added-lines scan and hygiene scan exit 0; span uniqueness holds with all preserved anchors present. Exec review r3 (fresh-adversarial, one worker) found zero findings, with two informational plan-bound observations (the plan-mandated deployed-copy locator parenthetical; the plan-pinned section placement) recorded in the round notes; records at docs/reviews/2026-10-05-plan-review-done-gate-liveness-retirement-r3.{md,stats.json}.

Deferred residuals: none from execution; the observation-window close remains an operator-recorded event by design (the read side never writes). Origin row docs/history/backlog/2026-10-05-done-guard-stack-liveness-economics.md is covered by this execution and folded in the landing.
