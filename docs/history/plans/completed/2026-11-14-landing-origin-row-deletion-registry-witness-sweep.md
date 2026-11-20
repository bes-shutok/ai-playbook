# Plan: deletion-side witness sweep at the completion fold

Backlog origin: docs/history/backlog/2026-11-14-landing-origin-row-deletion-registry-witness-sweep.md
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-14-plan-review-landing-origin-row-deletion-registry-witness-sweep-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 0.5h
Executed: yes (recorded tip 6447e7f71)
Authoring claim: 2026-11-14-landing-origin-row-deletion-registry-witness-sweep.md (session sess_3e11def7-3433-4a54-b6b1-62d451db2ab7)

## Terms

- Witness ref: the `witness.ref` value a machinery registry entry carries; the inventory check resolves it as a tracked path and fails the check when it dangles (`scripts/machinery_inventory.py`).
- Durable home: the citation home a record's consumers re-point to when its living path is fold-deleted: the covering plan's `docs/history/plans/completed/` twin (citation precedence; a `docs/history/backlog/completed/` twin is legacy state, never a citation home).
- Completion fold (completion pass): the plans skill's completion pass (`plan-lifecycle.md`) that archives the covering plan, appends the registry rows, and deletes the promoted origin row.
- Deletion-side witness sweep: the ordered duty this plan adds: before the pass's deleting change is built, grep the machinery registry and the pins suite for every tracked path the pass's diff deletes or moves, re-point each hit to its verified durable home in the same change, and run the inventory check green before the deleting change lands.
- Pins suite: `scripts/check_maintenance_pins.sh`, the pinned-literal guard over the maintenance skill files.
- Inventory check: `python3 scripts/machinery_inventory.py --check`.
- Verified durable home: a twin confirmed present with `git ls-tree` plus a content-head check, never exit code alone.
- Byte cap: `agents/skills/plans/plan-lifecycle.md`'s per-file cap in `scripts/skill_text_budget_caps.json` (25491 bytes).

## Why

The completion pass that archives a plan and deletes its origin row keeps missing the registry witness sweep lesson #312 orders: the duty row its own Task 4 created (`duty:carrier-liveness-missed-fire`) has stood red since the 2026-11-13 survey catch, the class's second instance in three days, because the re-point duty lives in the registry note's prose where the executing pass does not read it at the right moment.

## Gist & Examples

TLDR: the standing registry red is re-pointed to the completed twin and the completion pass gains its ordered deletion-side witness sweep, so origin-row deletions re-point their witnesses in the same change instead of being rediscovered by a later survey, which is why the automation force applies: the loop keeps its own machinery inventory green without manual direction.

Before: `python3 scripts/machinery_inventory.py --check` exits 1 (the duty row's witness cites the deleted origin path `docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md`), the real-tree suite cell fails on the same ref, and the next completion pass that deletes a row misses the sweep again.

After: the check exits 0 and the suite is green, and every completion pass that deletes or moves a tracked path greps the registry and the pins suite, re-points hits to the verified durable home in the same change, and lands the deleting change only with the check green.

Edge cases: a sweep finding no hits costs two greps and one check run; a registry row the same pass created is swept like any other (the witnessed miss class); a hit whose durable twin cannot be verified stops the pass for operator disposition rather than re-pointing blind.

## Outcome

The machinery inventory reads green again, and the completion pass carries the sweep duty in its own ordered text so the witnessed miss class cannot recur silently.

- `python3 scripts/machinery_inventory.py --check` exits 0: the `duty:carrier-liveness-missed-fire` family's five dead citations resolve to the completed twin.
- The real-tree suite cell (`RealTreeCheck::test_real_tree_checks_green`) passes.
- A later completion pass deleting an origin row re-points its registry and pins citations in the same change and lands with the check green, with the survey-time machinery regrowth guard consult as the standing backstop.

Gate delta: net addition of one prose-only ordered sweep duty in the completion pass (no refusal class, hard gate, fence, protocol layer, or schema field is added or removed; the survey-time inventory consult remains the backstop); removals: none. Priced by the origin row's witnessed recurrence (two instances in three days, currently red), not a refusal-path addition.

Follow-up disposition: none anticipated: the sweep's ongoing operation is guarded by the existing survey-time machinery regrowth guard consult, so a future instance surfaces as that consult's survey finding, not a new backlog row.

## Assumptions

- assume the re-point target is `docs/history/plans/completed/2026-11-12-maintenance-indefinite-operation-stop-gaps.md`; basis: verified present on disk, the registry note's own duty sentence names it, and the `docs/history/backlog/completed/` twin confirmed absent (`git ls-tree` count 0, 2026-11-14).
- assume Task 1 sweeps the family's five dead citations (the entries-row witness ref, the two note mentions, the pre-registered removals row's witness ref citing the plan's living pre-archive path, and that removals row note's `plan <living path> Task 4` citation), not the ref alone; basis: lesson #312 covers citations the change renders dead, and Task 2 lands the same rule as standing text, so a ref-only fix would leave the repaired family half-swept; the removals-row citations disk-verified at review r1 (removals[27], witness.ref and note citing `docs/history/plans/2026-11-12-maintenance-indefinite-operation-stop-gaps.md`, the inventory check not validating removals-row refs, so the re-point is lesson-312 compliance rather than check-driven).
- assume no dedicated battery cell is added for the re-pointed ref; basis: the real-tree suite cell is the enforcing verification and flips red-to-green with Task 1 (measured 2026-11-14); a dedicated pin would be unpaid machinery with no witnessed false negative.
- assume warning-first posture: no gate, validator, or required ceremony is added; the sweep is ordered text duty and the survey's machinery regrowth guard consult (survey-arms.md) remains the backstop; basis: the origin row's pricing and the repository admission protocol.
- assume byte-budget posture: `plan-lifecycle.md` carries 7468 bytes of headroom (18023 of the 25491 cap, measured 2026-11-14), so Task 2's insertion stays within headroom and the byte-cap witness (the plan's own `wc -c` needle and the budget gate) keeps the cap enforced.
- assume the sweep greps the registry JSON and the pins shell script as text surfaces; basis: both carry path literals the lesson names, and the sweep is a grep duty, not a parsed scan.

Decision points requiring a grill: none remain; sweep-text homing in the completion-pass bullet of `agents/skills/plans/plan-lifecycle.md` rather than the landing-closeout bullet or the repository guidelines (decided 2026-11-14 under the standing authorization; simpler-design comparison: the completion pass is the fold that executes the delete, so its text is read at the right moment, a landing-closeout insertion would duplicate the closeout rider list, and a guidelines rule disperses the duty from the operating fold); Task 1 scope covering the family's five dead citations rather than the witness ref alone (decided 2026-11-14 under the standing authorization, extended at review r1 with the removals-row citation and at review r3 with that row's note citation; simpler-design comparison: the origin entry scopes the ref, but dead citations beside a fixed one re-create the lesson-312 defect inside the repaired family and contradict the sweep text Task 2 lands); the note-rewrite parenthetical naming the fold-deleted row by date-plus-slug, never the full living-path literal (decided 2026-11-14 at review r1; simpler-design comparison: a full-path parenthetical would re-introduce the literal the plan's own absent-count needle forbids, while the date-slug form stays grep-distinct and readable).

## Standing constraints

- Warning-first: nothing in this plan adds a gate, validator, refusal path, or required ceremony; the survey-time machinery regrowth guard consult remains the backstop.
- Task 1's note rewrite preserves the row's admission record and its pre-registered removals review date bytes; only the citation paths and the duty-sentence form change.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the inventory check exits 0 and the duty row carries zero dead citations.
- wiring: the sweep duty text lands exactly once with its ordered steps readable at the deleting legs.
- byte-budget: `plan-lifecycle.md` stays within its 25491-byte cap and the budget gate passes.
- regression safety: the machinery inventory suite and the pins suite stay green.

**Done when:**
- `python3 scripts/machinery_inventory.py --check` exits 0.
- `scripts/test_machinery_inventory.py` passes (the real-tree cell flipped green).
- The sweep duty text is present in the completion pass bullet with the count needle exactly once.
- `python3 scripts/skill_text_budget.py --check` passes and the byte-cap witness holds.

**Ship when:**
- The next origin-row-deleting completion pass executes the sweep without a survey-time catch surfacing first; human-owned observation, prose only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/machinery_registry.json` (Task 1)
- `agents/skills/plans/plan-lifecycle.md` (Task 2)

**Tests:**
- `scripts/test_machinery_inventory.py` (review-only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/machinery_inventory.py`; reason: the checker is correct today; it fails only because the cited path is gone.
- `docs/maintenance/development_lessons.md`; reason: lesson #312 already carries the rule and its two witnesses; no text edit is in scope.
- `docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md`; reason: the origin row of the duty row is already fold-deleted; its history is immutable.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
python3 scripts/machinery_inventory.py --check || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_machinery_inventory.py -q || exit 1
python3 scripts/skill_text_budget.py --check || exit 1
test "$(wc -c < agents/skills/plans/plan-lifecycle.md)" -le 25491 || exit 1
test "$(grep -oF 'docs/history/plans/completed/2026-11-12-maintenance-indefinite-operation-stop-gaps.md' scripts/machinery_registry.json | wc -l)" -ge 1 || exit 1
test "$(grep -oF 'docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md' scripts/machinery_registry.json | wc -l)" -eq 0 || exit 1
test "$(grep -oF 'deletion-side witness sweep' agents/skills/plans/plan-lifecycle.md | wc -l)" -eq 1 || exit 1
bash scripts/check_maintenance_pins.sh || exit 1
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || exit 1
```

Validation preamble (authoring-time preflight record, 2026-11-14):

- Inventory check RED today: `python3 scripts/machinery_inventory.py --check` exits 1 with exactly one FAIL line, the `duty:carrier-liveness-missed-fire` witness ref naming the deleted origin path (measured 2026-11-14 at the worktree base 2e5b7e766); GREEN after Task 1's re-point.
- Suite RED today: `scripts/test_machinery_inventory.py` is 1 failed, 28 passed; the failing cell `RealTreeCheck::test_real_tree_checks_green` asserts the check's exit 0 and fails on the same ref (measured 2026-11-14); GREEN after Task 1.
- Registry count needles RED today: the completed-twin path appears 0 times in `scripts/machinery_registry.json` and the deleted origin path appears 3 times (the witness ref plus both note mentions; occurrence count via `grep -oF | wc -l`, measured 2026-11-14); after Task 1 the twin count is at least 1 and the deleted count is 0.
- Sweep-phrase needle RED today: `deletion-side witness sweep` appears 0 times in `plan-lifecycle.md` (measured 2026-11-14); exactly once after Task 2.
- Byte-cap witness: `wc -c < agents/skills/plans/plan-lifecycle.md` measured 18023 at authoring (cap 25491), passing today, enforced after Task 2's insertion.
- Budget gate: `python3 scripts/skill_text_budget.py --check` recorded `OUTCOME: pass` (0 blocking ceiling breaches; the advisory ratchet rows and rolling-log informational rows are the recorded pre-existing ones, measured 2026-11-14).
- Pins suite and hygiene scan measured at the authoring-time pre-review sweep (recorded beside the gist report).
- Em-dash authoring-time self-check: the write-time fixer ran over the plan bytes with 0 substitutions before round 1 and re-runs after every fold batch.
- Rule 22 authoring-time mechanical audit: the Validation Commands block passes `bash -n` (every fallible line carries `|| exit 1`), the plan pins fixed-string needles against files this plan edits only, and the count needles' RED-today state was measured against the real tree, not asserted.
- Pre-round FILES-COVERAGE adjudication (2026-11-14): the four warning-only items are Task 2 prose references to surfaces the sweep duty greps or resolves at execution time (`scripts/machinery_registry.json` sibling-declared by Task 1; `scripts/check_maintenance_pins.sh`, `docs/history/plans/completed/`, and `scripts/machinery_inventory.py` operational references, not edit targets), so no `Files:` additions follow; Task 2's only edit target remains `plan-lifecycle.md`.
- Review r1 outcome (2026-11-14): ready=yes, zero blocking, 2 Medium + 2 Low non-blocking; F1 (the removals-row dead citation, disk-verified) and F2 (the parenthetical-form contradiction) and F4 (the byte-cap witness misattribution) folded in the same pass, F3 (a presence pin over the sweep text) rejected on the warning-first standing constraint and recorded in the staging record's watchlist; the fold's classification rides the delta classifier CLI.
- Review r2 outcome (2026-11-14, delta round): ready=yes, zero blocking, 1 Medium fold_defect (the fold landed F1's ref arm but not the removals note's citation, and the Outcome bullet carried the stale three-citation count); folded in this pass (the removals item extended to the note arm, the Outcome count corrected to the family's four citations); churn assessment: fold_defect count 1 below the trigger threshold, blocker counts 0 then 0, trajectory converging, no reconciliation trigger.
- Review r3 outcome (2026-11-14, certification round, interrupted once by a usage wall and resumed after the reset): ready=yes, zero blocking, 1 Medium fold_defect (the r2 fold extended Task 1's removals arm to the row note citation, five dead literals in the family, while this Outcome bullet and the Assumptions enumeration still counted four); folded in this pass (the Outcome count corrected to the family's five dead citations, the Assumptions enumeration extended with the removals note arm); the blind probe's living-path count 5 traced to the two adjudicated pre-existing note-prose debts in entries[39]/[107]/[154], not an expectation error; churn assessment: fold_defect count flat at 1 across r2 and r3, blocker counts 0 throughout, the fold closes the finding's own defect, no reconciliation trigger.
- Review r4 outcome (2026-11-14, focused confirm): ready=yes, zero blocking, 1 Medium fold_defect (the Decision points receipt's Task-1-scope clause still carried the family's four-citation count, the r1 fold's own propagation target, while the Outcome bullet, Assumptions enumeration, and Task 1 checkboxes agreed on five; the two remaining "four" strings in the round-history lines adjudicated append-only, not operative); folded in this pass (the Decision points clause corrected to the family's five dead citations with the r3 note-citation extension marker added); an exhaustive count-bearing-surface sweep across the plan preceded the fold so the correction is total, not pairwise; churn assessment: fold_defect count flat at 1 across r2, r3, and r4 (the count-propagation-lag root class each time), blocker counts 0 throughout, the operative count now agrees on every surface, no reconciliation trigger.
- Review r5 outcome (2026-11-14, focused confirm): ready=yes, zero blocking, zero findings (the exhaustive count sweep held: every operative surface agrees on the family's five dead citations, the one remaining "four citations" string adjudicated append-only round history); needles, RED gate, byte cap, and prior record pairs re-measured as negative controls.
- Round-close full-gate outcome (2026-11-14): the readiness validator's full-gate mode over the post-r5 bytes failed on Task 1's fourth criterion exceeding the 512 UTF-8 byte item limit (667 bytes; the r2 fold's note-arm extension had grown the criterion past the cap the create boundary enforces, a defect class invisible to the focused delta rounds that ran only the staging and name gates); repaired in this pass by splitting the criterion into two independently verifiable checkboxes (the removals witness-ref re-point; the removals note-citation re-point) preserving complete acceptance coverage, and the gate re-run inside the same round-close step per the round-close repair class; the resulting digest change rides the delta classifier and takes the fresh-round default (r6).

### Task 1: Re-point the duty row's citations to the durable twin

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/machinery_registry.json`

- [x] Pre-change verification: the durable twin's presence verified with `git ls-tree` plus a content-head check and the `docs/history/backlog/completed/` twin's absence confirmed the same way; the verification receipt recorded in the task log [class: IMPLEMENTATION_REQUIRED]
- [x] The witness ref of the `duty:carrier-liveness-missed-fire` row is re-pointed from `docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md` to `docs/history/plans/completed/2026-11-12-maintenance-indefinite-operation-stop-gaps.md` [class: IMPLEMENTATION_REQUIRED]
- [x] The row note's two dead citations of the deleted origin path are re-pointed to the completed twin: the origin-row citation gains a parenthetical naming the fold-deleted row by date-plus-slug (for example `2026-11-12-missed-carrier-fire-liveness-watchdog`), never the full living-path literal, and the duty sentence is rewritten to its executed form naming the executing plan by slug, preserving the admission record and the pre-registered removals review date bytes [class: IMPLEMENTATION_REQUIRED]
- [x] The pre-registered removals row for the same duty id (the removals entry whose `witness.ref` cites the plan's living pre-archive path) has its witness ref re-pointed to the completed twin `docs/history/plans/completed/2026-11-12-maintenance-indefinite-operation-stop-gaps.md`, preserving its witness class bytes [class: IMPLEMENTATION_REQUIRED]
- [x] The same removals row note's `plan <living path> Task 4` citation is re-pointed to the same completed twin (the twin is a tracked-path literal, distinct from the entries-row note's date-plus-slug discipline whose needle forbids the deleted backlog literal) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/machinery_inventory.py --check` exits 0 (RED today with exactly the one known FAIL line, measured 2026-11-14) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `scripts/test_machinery_inventory.py::RealTreeCheck::test_real_tree_checks_green` passes (RED today on the same ref, measured 2026-11-14) [class: REPOSITORY_TEST]
- [x] Commit: `fix: re-point the carrier-liveness duty row citations to the completed twin` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Completion-fold deletion-side witness sweep text

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/plan-lifecycle.md`

- [x] The completion pass bullet (the promoted-backlog pass that deletes the origin row) gains the ordered duty containing the exact phrase `deletion-side witness sweep`: before the pass's deleting change is built, grep `scripts/machinery_registry.json` and `scripts/check_maintenance_pins.sh` for every tracked path the pass's diff deletes or moves [class: IMPLEMENTATION_REQUIRED]
- [x] The duty orders re-pointing each hit to its verified durable home in the same change (`git ls-tree` plus a content-head check; citation precedence: the covering plan's `docs/history/plans/completed/` twin), explicitly including registry rows the same pass created [class: IMPLEMENTATION_REQUIRED]
- [x] The duty orders `python3 scripts/machinery_inventory.py --check` green before the deleting change lands and states the warning-first posture: an ordered text duty, not a new gate; the survey's machinery regrowth guard consult remains the backstop [class: IMPLEMENTATION_REQUIRED]
- [x] The insertion stays within the 25491-byte cap (the byte-cap witness, the plan's own `wc -c` needle above and the budget gate, keeps it enforced; the same-change payment duty applies if the cap would be crossed) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the sweep-phrase count needle (exactly once) and the byte-cap witness pass; Commit: `docs: order the deletion-side witness sweep in the completion pass` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

| Former backlog path | Disposition |
|---|---|
| docs/history/backlog/2026-11-14-landing-origin-row-deletion-registry-witness-sweep.md | covered by this plan; executed 2026-11-19 (Task 1 re-pointed the removals row's citations; Task 2 landed the deletion-side witness sweep in the completion pass; the pass's own sweep re-pointed this plan's two registry citations to this completed twin) |
