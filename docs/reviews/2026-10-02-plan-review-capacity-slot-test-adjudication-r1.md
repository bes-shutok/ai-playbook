# Plan Review: capacity-slot test adjudication (r1)

## Metadata
- Type: Plan Review
- Date: 2026-10-02
- URL or Artifact: `docs/history/plans/2026-10-02-capacity-slot-test-adjudication.md`
- Depth: full panel (five workers: correctness-completeness, testing, design-simplicity, contract-docs, risk)
- Domains: mechanism truthfulness, anchor byte-accuracy, mutation-witness adequacy, plan conventions, production-byte safety
- Round: r1
- Prior: none
- Review mode: fresh-adversarial
- Changed-risk signals: none
- Prior findings supplied as filter: no
- Last fix commit: none
- Witness ledger: N/A (no public mutators)
- Release-gate ledger: none
- Coverage: clean
- Record kind: canonical
- Findings: 3 staged (4 raw; 1 echo merged under dedup)
- Status: STAGED (folded: 3 fixed; fresh round follows on the folded digest)

### Attempt ledger

| Attempt | Worker | Lenses | Started | Deadline | Elapsed min | Outcome |
|---------|--------|--------|---------|----------|-------------|---------|
| r1-correctness-completeness | correctness-completeness | implementation, quality | 2026-10-02T09:55:00+01:00 | bounded-wait | 5.4 | complete |
| r1-testing | testing | testing | 2026-10-02T09:55:00+01:00 | bounded-wait | 8.1 | complete |
| r1-design-simplicity | design-simplicity | architecture, simplification | 2026-10-02T09:55:00+01:00 | bounded-wait | 5.7 | complete |
| r1-contract-docs | contract-docs | consistency, documentation | 2026-10-02T09:55:00+01:00 | bounded-wait | 8.8 | complete |
| r1-risk | risk | security | 2026-10-02T09:55:00+01:00 | bounded-wait | 3.5 | complete |

All five workers launched in parallel and completed on the first pass. Every worker verified the plan's load-bearing claims against disk: the RED reproduction (`'blocked' != 'success'` at scripts/test_runtime_capabilities.py:372 on base 01685b35), the guard's pass condition (`status == "ok"` only, scripts/execute_plan_runtime.py:1854-1898), the parallel-group checkpoint ahead of membership evaluation (4710-4713), the mechanical anchor application (count 1, GREEN flip in scratch clones), the fixture precedents (three ok-stubs in scripts/test_execute_plan_runtime.py), the `-k guard` collection of 13 guard-contract tests, and the witness-predates-guard history (witness string from 083c6e88 2026-09-25; guard landed 50b2b6bc 2026-10-01). The testing worker mutation-verified its finding in a throwaway worktree. All three staged findings fold in one batch; a fresh round follows on the folded digest.

## Review Statistics

### Panel

| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| correctness-completeness | implementation, quality | none | complete | 1 | 1 | 0 | no |
| testing | testing | none | complete | 1 | 1 | 0 | no |
| design-simplicity | architecture, simplification | none | complete | 1 | 0 | 1 | no |
| contract-docs | consistency, documentation | none | complete | 1 | 1 | 0 | no |
| risk | security | none | complete | 0 | 0 | 0 | no |

### Counts
- Workers launched: 5
- Staged findings: 3

### Deduplication groups
- F2 merges design-simplicity's `documentation#anchor-note-inaccuracy` (echo) into correctness-completeness's `quality#anchor-rationale-return-line-count-wrong`: both name the same Task 1 prose defect (the return-line occurrence claim).

### Discarded findings
None.

### Severity calibration
None.

### Triage outcomes
- fixed: 3

## Findings

### Critical

(none this round)
### High

(none this round)
### Medium

#### F1. No validation check discriminates a vacuous witness (stub present with the capacity-race body deleted passes every check)
- **Pattern**: testing#vacuous-witness-mutation-gap
- **Severity**: Medium
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: If Task 1's stub lands but the witness's race body (barrier, two-thread `_mark_claim_launched`, the three race assertions) is ever lost, the witness passes vacuously and the plan's core outcome claim ("runs the capacity race it exists to exercise") is silently false with all gates green (worker mutation-verified: stub plus a pass-body passes checks 4-5)
- **Reachability**: plausible-edge
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Validation Commands checks 4-5 and the Task 1 GREEN checklist step; witness body scripts/test_runtime_capabilities.py:347-391

#### Comment
Fold accepted: the Task 1 GREEN step gains a second grep pin (`sum(outcome is None for outcome in outcomes.values())` returns exactly 1) so a stub without the race body cannot pass the step vacuously.

#### Analysis
The witness's discriminating power currently rests on procedural constraints (verbatim block, count-1 anchor, named tail) that bind the prescribed edit but not a follow-up mutation; the body-presence grep closes that hole at the only step that runs the witness.

### Low

#### F2. Task 1 anchor rationale misstates the return line's occurrence count
- **Pattern**: quality#anchor-rationale-return-line-count-wrong
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: The plan asserts the return line alone is not single-occurrence across the file as the justification for the full-block anchor; on disk the return line occurs exactly once (count 1, sole `observe_inventory` in the file), so a reader auditing the plan's verified claims against disk finds a false statement (design-simplicity echoed the same defect as documentation#anchor-note-inaccuracy)
- **Reachability**: expected
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Task 1 intro paragraph ("the return line alone is not single-occurrence across the file") vs scripts/test_runtime_capabilities.py:348-352

#### Comment
Fold accepted: the rationale is rewritten to state the true counts (return line and full block each verified count 1) and the real reason for the block anchor (the insertion binds the class head, the return line, and the named tail into one position).

#### Analysis
The occurrence claim was carried over from the sibling file's idiom (test_execute_plan_runtime.py has its own InventoryAdapter); on this file both the return line and the full block are single-occurrence, and the anchor's justification is positional binding, not uniqueness scarcity.

#### F3. Sources inspected line ranges overshoot the witness and the parallel-group arm
- **Pattern**: documentation#sources-inspected-line-ranges-imprecise
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: A reader re-deriving the inspection provenance finds the witness test spans 347-391 (the next test's def starts at 393), `claim_parallel_group` spans 4664-4837 (`_mark_claim_launched` starts at 4838), and the guard ends at 1898; the recorded ranges overshoot each span
- **Reachability**: expected
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: plan Assumptions Sources inspected bullet vs scripts/test_runtime_capabilities.py:391-393 and scripts/execute_plan_runtime.py:4838

#### Comment
Fold accepted: the ranges are corrected to 1854-1898, 4664-4837, and 347-391.

#### Analysis
The ranges were recorded from the authoring session's read windows rather than the enclosing-definition spans; the corrected values are the def-to-def spans re-derived on the base tree.

## Overflow manifest

None (every worker within budget).
