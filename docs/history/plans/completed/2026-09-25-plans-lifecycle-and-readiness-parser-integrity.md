# Plan: plans lifecycle and readiness parser integrity (move-not-copy routing, fence balance, origins grammar, stale-origin dispositions)

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-25-archive-routing-copy-not-move-duplicates.md`
- `docs/history/backlog/2026-09-24-plans-origins-block-blank-line-trap.md`
- `docs/history/backlog/2026-09-24-plan-readiness-unbalanced-fence-masks-tail.md`
- `docs/history/backlog/2026-09-23-plans-classification-tag-continuation-line-invisible.md` (verified already satisfied by landed work; this plan verifies and records the disposition, completion routes it done)
- `docs/history/backlog/2026-09-23-plan-rule36-reverse-duplicate-simulation.md` (verified already satisfied by landed 28534e4a; this plan verifies and records the disposition, completion routes it done)

Driving force: efficiency (secondary: code-quality)
Force note: the origins declare workflow reliability / lost-work prevention, which sits outside the closed force taxonomy; efficiency is the taxonomic carrier (every silent misparse or duplicated queue entry costs later sessions real work to discover), and each origin is a witnessed incident, not speculative hardening.

## Terms

- **Routing primitive**: the completion-flow step that discharges a backlog item or archives an executed plan, recording the ownership-registry row and removing or relocating the live file per the pinned lifecycle bullets.
- **Move-with-mutation**: archive discipline where the recorded content is produced by mutating the live file in place and the live path is deleted or renamed in the same commit, so the failure signature (a new archive file `A` with no matching `D`/`R` of the live basename in the same commit) cannot occur.
- **Failure signature**: an added archive file (`A`) whose basename has no matching delete or rename (`D`/`R`) of the live path in the same commit.
- **Origins block**: the plan header region that starts at the `Backlog origins (scope of record):` line and carries the bulleted origin list consumed by `check_plan_origins_closed.py`.
- **Dispositions annotation**: a dated line added to an open backlog item recording that its requested fix already landed, naming the landing evidence (a commit for a code fix, the observed landed behavior for a behavior fix), so the completion pass can route the item done with provenance.

## Assumptions

- assume the origins-block parser tolerates exactly one blank line between the header line and the first list item, rather than only pinning author-side contiguity; basis: the witnessed frozen archived plan carries the blank-line shape and cannot be edited, so parser-side tolerance is the only arm that repairs the corpus without rewriting certified bytes (origin 2 sanctions either arm).
- assume the origins dispositions cross-check rides the `--plan` invocation of `check_plan_origins_closed.py` (the completion-gate path), not the corpus scan or the readiness pre-round; basis: the per-plan invocation is where a plan's own origins and dispositions are both in hand, and review round r1 verified the pre-round path has no origins check to extend.
- assume the duplicate-detector gate is basename-collision only; the routed-without-discharge check lives in the execute-plan archive step as process discipline, not in the pins suite; basis: review round r1 counted 22 `completed/` and about 70 `deferred/` copies reading `Status: open` on the real tree (deferred items are open by design), so a tree-wide discharge gate is permanently red against archives this plan freezes out of scope.
- assume origins 4 and 5 are already satisfied by landed work (the tag-placement parser behavior and the joint rule 36 simulation wording exist at HEAD); this plan verifies both against their origins' Expected clauses, adds the dispositions annotations, and their routing to done happens in this plan's completion pass with the landing commit as provenance; basis: review round r1 verified the landed behavior and the landing commit 28534e4a for rule 36.
- assume the review-plan and review-agents surfaces need no edit: review round r1 verified review-plan's fold verification already reads as joint and testing.md carries no duplicate-simulation duty; basis: r1 worker verification with grep evidence recorded in the r1 artifact.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the plan-lifecycle machinery gets one integrity pass: archive routing becomes auditable move-with-mutation with a live-vs-archive basename gate, the readiness parsers stop silently misreading malformed plans (unclosed fences, blank-line origins blocks), and two already-fixed origins get their dispositions recorded so the queue stops overstating work.

**Before (today):** an executor archives an executed plan by writing a new `completed/<basename>` file and never deleting the live pre-execution snapshot, so the open plans queue presents already-executed work as open (the witnessed p37 twins). A plan author leaves one fence unclosed and certification scores only the document prefix before the fence, passing clean. An origins block with a blank line after the header parses as zero origins and every promoted item is ungated. Two backlog items whose fixes already landed stay open, overstating the queue.

**After (this plan):** the completion flow pins move-with-mutation in both skill surfaces (aligned with the pinned lifecycle bullets, adding only the failure-signature sentence and the routed-without-discharge check at the execute-plan archive step), an additive pins-suite section with a root override fails on any basename present in both a live root and its archive subtree, `plan_readiness.py` hard-fails an unclosed fence naming the line number before probes consume the stripped text, the origins parser tolerates the blank-line shape while the `--plan` gate warns when parsed origins undercount the dispositions list, and the two stale origins carry dated dispositions annotations.

Edge cases: a legitimate revival routes through the normal lifecycle and never lands a live-plus-archive pair; the fence balance check counts fence delimiter lines only, so fence-like content inside fenced blocks never trips it; the basename gate's root override is honored only by the new section, leaving every pinned span anchored at the real toplevel.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the fence-balance failure and the origins blank-line tolerance each have a both-directions test in the existing test files, verified by `python3 scripts/test_plan_readiness.py` and `python3 scripts/test_check_plan_origins_closed.py`.
- reliability: the duplicate detector fires on a synthetic live-plus-archive basename pair through the root override and stays green on the real tree via the pins suite.
- compatibility: the pins suite and shared-body runtime-neutrality test pass; frozen archived plans are never edited; the pinned lifecycle wording is extended, never contradicted.

**Done when:**
- The unbalanced-fence hard failure and the origins blank-line tolerance each have a passing both-directions test.
- The origins `--plan` gate prints the dispositions undercount warning and it never changes the exit status.
- The pins-suite duplicate section exits 0 on the real tree and fails the synthetic fixture pair through the root override.
- The plans and execute-plan skill text carries the failure-signature sentence and the routed-without-discharge check.
- Origins 4 and 5 carry dated dispositions annotations naming their landed fixes.
- `bash scripts/check_maintenance_pins.sh` exits 0.

**Ship when:**
- Consumer repos pick the corpus up on their next vendored sync; the routing-discipline change binds at the next completion flow that runs in this repo.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py`
- `scripts/check_plan_origins_closed.py`
- `scripts/check_maintenance_pins.sh`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

**Tests:**
- `scripts/test_plan_readiness.py`
- `scripts/test_check_plan_origins_closed.py`

**Origin records (Task 7 dispositions):**
- `docs/history/backlog/2026-09-23-plans-classification-tag-continuation-line-invisible.md`
- `docs/history/backlog/2026-09-23-plan-rule36-reverse-duplicate-simulation.md`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/*`, `docs/history/backlog/completed/*`, and `docs/history/backlog/deferred/*`; frozen or by-design archives are never edited; the roughly 22 `completed/` and 70 `deferred/` copies reading open are pre-existing residue outside this plan's gates.
- `agents/skills/receiving-review/SKILL.md`; no origin requires editing it.
- `agents/skills/review-plan/SKILL.md` and `agents/skills/review-agents/*`; review round r1 verified neither surface carries the one-directional duty, so the sweep task was dropped.
- `scripts/check_backlog_claimed.py`; the claimed-origin checker is a different gate (ownership, not duplication).

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1

# Readiness parser fix: both directions, existing suite
python3 scripts/test_plan_readiness.py || { echo "FAIL: plan_readiness tests"; exit 1; }

# Origins parser: existing suite plus the corpus-wide scan on the real tree
python3 scripts/test_check_plan_origins_closed.py || { echo "FAIL: origins tests"; exit 1; }
python3 scripts/check_plan_origins_closed.py >/dev/null || { echo "FAIL: origins corpus scan"; exit 1; }

# Duplicate detector rides the pins suite; no pinned span broke
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite"; exit 1; }

# Shared skill bodies stay runtime-neutral (plans and execute-plan SKILL.md are edited here)
python3 scripts/test_execute_plan_runtime.py -k "*shared_skill_bodies*" || { echo "FAIL: shared-body neutrality"; exit 1; }
```

### Task 1: parser defect tests (RED first)

Files:
- `scripts/test_plan_readiness.py`
- `scripts/test_check_plan_origins_closed.py`

- [x] `PlanReadinessFenceBalanceTest#test_unclosed_fence_fails_closed_naming_line`; given a plan fixture whose last fence opener has no closer, expects BOTH readiness entries to exit non-zero with a structural failure naming the opener's line number: the full certification gate and the pre-round invocation, each produced before any probe evaluates the stripped text (the CLI exit and message are asserted, not a Python exception surface); the full-gate arm's fixture carries a current-dated, digest-matched review sidecar so the gate runs its full probe set instead of routing around the date gate with a dateless builder [class: REPOSITORY_TEST]
- [x] `PlanReadinessFenceBalanceTest#test_balanced_fences_still_pass`; given the same fixture with the closer restored, expects the readiness structural probes to run over the full document [class: REPOSITORY_TEST]
- [x] `OriginsBlockGrammarTest#test_blank_line_between_header_and_list_tolerated`; given a plan fixture whose origins block carries exactly one blank line between the header and the first bullet, expects `extract_origin_basenames` to return every bulleted basename; given a blank line between two bullets, expects the block to end at the first break [class: REPOSITORY_TEST]
- [x] `OriginsBlockGrammarTest#test_dispositions_undercount_warning`; given a plan fixture whose dispositions section lists more basenames than the origins block parses, expects the `--plan` invocation to print a warning naming both counts while exiting 0 [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_plan_readiness.py` and `python3 scripts/test_check_plan_origins_closed.py` (the new tests fail against current behavior: the stripper masks the tail and exits clean, the origins parser returns zero origins on the blank-line shape, no undercount warning exists) [class: REPOSITORY_TEST]
- [x] Commit: `test: parser defect fixtures for fence balance and origins grammar` [class: IMPLEMENTATION_REQUIRED]

### Task 2: fence balance in plan_readiness (flips the fence tests GREEN)

Files:
- `scripts/plan_readiness.py`

- [x] Extend `_strip_fences` with a delimiter-line balance check: an opener with no closer is reported as the offending opener line number; BOTH readiness entries surface it as a structural failure through the same problem-reporting channel the other structural probes use, exit non-zero, before any probe evaluates the stripped text: the full certification gate's probe chain and the pre-round chain [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_plan_readiness.py` (full suite passes) [class: REPOSITORY_TEST]
- [x] Commit: `fix: plan_readiness unclosed-fence hard failure` [class: IMPLEMENTATION_REQUIRED]

### Task 3: origins grammar and undercount warning (flips the origins tests GREEN)

Files:
- `scripts/check_plan_origins_closed.py`

- [x] Amend `extract_origin_basenames`: tolerate exactly one blank line between the header line and the first list item; any blank line after list items begin ends the block [class: IMPLEMENTATION_REQUIRED]
- [x] Add the dispositions undercount warning to the `--plan` invocation: when the parser extracts fewer basenames than the plan's origins dispositions section lists, print a warning naming both counts; a warning never changes the exit status [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_check_plan_origins_closed.py` and `python3 scripts/check_plan_origins_closed.py` on the real tree (exit 0; the frozen blank-line plan now parses its full origin list) [class: REPOSITORY_TEST]
- [x] Commit: `fix: origins block blank-line tolerance and undercount warning` [class: IMPLEMENTATION_REQUIRED]

### Task 4: plans skill text (origins shape, lifecycle failure signature)

Files:
- `agents/skills/plans/SKILL.md`

- [x] Pin the origins-block shape in the Plan Format metadata-block guidance: the bulleted list is contiguous with the header line or separated by exactly one blank line; a blank line after the list begins ends the block [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the Plan Lifecycle archive bullet with the failure-signature sentence, extending the pinned wording without contradicting it: the archive step's commit must not add an archive file whose live basename survives the same commit un-deleted and un-renamed; a surviving live twin is a defect the completion pass fixes before commit [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py -k "*shared_skill_bodies*"` and `bash scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
- [x] Commit: `docs: plans origins shape and archive failure signature` [class: IMPLEMENTATION_REQUIRED]

### Task 5: execute-plan archive step (move-with-mutation and discharge check)

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Extend the Phase 4/5 archive ordering checklist with the move-with-mutation discipline aligned to the pinned lifecycle bullets: the archived plan snapshot is produced by mutating the live plan file in place and the live path is deleted or renamed in the same commit; the failure signature is a defect the executor fixes before commit [class: IMPLEMENTATION_REQUIRED]
- [x] Add the routed-without-discharge check at the same step: an item or plan entering an archive with its content still asserting open or unchecked required boxes fails the archive step with an explicit message, so the receiving-review incident class is caught at route time [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py -k "*shared_skill_bodies*"` and `bash scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
- [x] Commit: `docs: execute-plan move-with-mutation archive and discharge check` [class: IMPLEMENTATION_REQUIRED]

### Task 6: duplicate detector in the pins suite (fixture-proven RED, real-tree GREEN)

Files:
- `scripts/check_maintenance_pins.sh`

- [x] Add an additive read-only section honoring a `PINS_DUPLICATE_ROOT` environment override for that section only: for each live root (`docs/history/backlog/`, `docs/plans/`) assert no basename also exists in its archive subtrees (`completed/`, `deferred/`, `rejected/` where present under the resolved root), failing with the offending pairs; default root is the git toplevel exactly as every pinned span uses [class: IMPLEMENTATION_REQUIRED]
- [x] Give the new section a lasting failure-arm guard: the duplicate check is implemented as a function taking the root as its argument, and an inline selftest sub-section the suite runs on every invocation calls that function directly (never a whole-suite re-invocation, which dies for the wrong reason on a temp fixture or recurses on an in-repo one), building its own `mktemp -d` fixture (a live basename duplicated into a fake archive subtree), asserting the non-zero result and the offending-pairs message naming the fixture pair, and removing the temp tree with explicit `rm -rf` teardown; a selftest failure fails the suite [class: IMPLEMENTATION_REQUIRED]
- [x] Prove the failure mode once at implementation time by running the full pins suite with `PINS_DUPLICATE_ROOT` pointing at a hand-built fixture root and recording the observed non-zero exit and offending-pairs message in the task log (the lasting selftest then guards the same arm on every later run) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` on the real tree exits 0 with the new section running (the d5ba4807 cleanup removed the real duplicates; the synthetic fixture carries the RED proof) [class: REPOSITORY_TEST]
- [x] Commit: `feat: pins-suite live-vs-archive basename gate with root override` [class: IMPLEMENTATION_REQUIRED]

### Task 7: stale-origin verification and dispositions annotations

Files:
- `docs/history/backlog/2026-09-23-plans-classification-tag-continuation-line-invisible.md`
- `docs/history/backlog/2026-09-23-plan-rule36-reverse-duplicate-simulation.md`

- [x] Verify the tag-placement behavior against origin 4's Expected clause (a tag on a non-checkbox line is flagged naming the placement, not silently classified untagged) by exercising the readiness probe on a wrapped-item fixture; record the observed behavior in the task log [class: REPOSITORY_TEST]
- [x] Verify rule 36's landed wording (commit 28534e4a) covers the joint direction origin 5 expects (all count gates over a file re-simulated against a temp copy carrying all prescribed insertions); record the observed wording in the task log [class: REPOSITORY_TEST]
- [x] Append a dated disposition line to each origin item naming the landed fix (parser behavior as observed; 28534e4a for rule 36), shaped `Disposition: <date> (annotated via <this plan's landing reference>): <one-line resolution naming the landing evidence: the commit, or the observed landed behavior for a parser-behavior fix>` beside the item's existing header Status lines, so the completion pass routes both items done with provenance [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/check_plan_origins_closed.py` exit 0 (the annotations do not disturb the origins scan) [class: REPOSITORY_TEST]
- [x] Commit: `docs: dispositions for tag-placement and rule-36 origins (fixes already landed)` [class: IMPLEMENTATION_REQUIRED]

### Task 8: full gate run over the final tree

Files: none (verification only)

- [x] Run the complete Validation Commands block in order and expect every command green on the final tree [class: REPOSITORY_TEST]

## Execution record (2026-09-25, in-session worktree execution)

All tasks 1-8 executed in order; every checkbox ticked; the full Validation Commands block exits 0 end to end on the final tree. Deviations and findings folded during execution:

- The fence-balance core was extracted as `_scan_fences` (returns stripped text plus the unclosed opener's 1-based line) with `_strip_fences` as a thin wrapper, so the balance probe and the stripper share one scanner and can never disagree; `fence_balance_problem` is the probe both readiness entries call, first in the pre-round chain and unconditionally in the full gate right after the plan bytes are read (decode failures keep their own later reason family).
- Two internal selftest arms of the decision-marker family (`trailer_unterminated_fence_fails`, `trailer_swallowed_by_earlier_unterminated_fence_fails`) were re-pinned from the old swallow-drop reason to the new fence-balance first-failure reason (lines 7 and 3 respectively); they pin the same fail-closed property at the same gate entry, and the full internal selftest passes.
- The origins parser's header line must not mark the block as list-started (the header itself falls through to the span scan), or the tolerated single blank line would immediately end the block; fixed during Task 3 and covered by the tolerance test.
- The dispositions undercount comparison set is defined as the backtick backlog basenames under a case-insensitive `## Origins dispositions` heading; the warning rides stderr, names both counts, and never changes the exit status.
- The pins-suite duplicate gate is placed after the suite's legacy final exit guard, so it required its own `[ "$fail" -eq 1 ] && exit 1` before the unconditional exit 0 (caught by the fixture proof: the first run printed the PIN FAIL but exited 0); the fixture proof ran with `PINS_DUPLICATE_ROOT` over a hand-built twin pair (observed rc 1 and the offending-pairs message naming the fixture pair), and the lasting inline selftest guards the same arm on every run.
- Origin 4 verification: `scope_classification_problem` on a wrapped-item fixture reports the tag on the non-checkbox line naming the placement (observed output recorded in the session log). Origin 5 verification: rule 36's joint-direction wording present at HEAD via 28534e4a.
