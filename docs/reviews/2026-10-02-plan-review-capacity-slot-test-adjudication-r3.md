# Plan Review: capacity-slot test adjudication (r3)

## Metadata
- Type: Plan Review
- Date: 2026-10-02
- URL or Artifact: `docs/history/plans/2026-10-02-capacity-slot-test-adjudication.md`
- Depth: full panel (five workers: correctness-completeness, testing, design-simplicity, contract-docs, risk)
- Domains: assumption-basis precision, mask-check composition truthfulness, precondition verification, pin strength claims
- Round: r3
- Prior: r1 (3 findings, fixed), r2 (6 findings, fixed)
- Review mode: fresh-adversarial
- Changed-risk signals: none
- Prior findings supplied as filter: no
- Last fix commit: none
- Witness ledger: N/A (no public mutators)
- Release-gate ledger: none
- Coverage: clean
- Record kind: canonical
- Findings: 6 staged (6 raw; no echoes; no overflow)
- Status: STAGED (folded: 6 fixed; fresh round follows on the folded digest)

### Attempt ledger

| Attempt | Worker | Lenses | Started | Deadline | Elapsed min | Outcome |
|---------|--------|--------|---------|----------|-------------|---------|
| r3-correctness-completeness | correctness-completeness | implementation, quality | 2026-10-02T12:05:00+01:00 | bounded-wait | 8.4 | complete |
| r3-testing | testing | testing | 2026-10-02T12:05:00+01:00 | bounded-wait | 6.9 | complete |
| r3-design-simplicity | design-simplicity | architecture, simplification | 2026-10-02T12:05:00+01:00 | bounded-wait | 4.5 | complete |
| r3-contract-docs | contract-docs | consistency, documentation | 2026-10-02T12:05:00+01:00 | bounded-wait | 13.8 | complete |
| r3-risk | risk | security | 2026-10-02T12:05:00+01:00 | bounded-wait | 5.3 | complete |

All five workers launched in parallel and completed on the first pass, reviewing the r2-folded digest fresh. The r2 fixes were confirmed landed (the extended check 6 filter collecting exactly 14, the four grep pins, check 8, the corrected seed-rejection grounds, the anchor prose, the sequential records), with workers independently re-executing the mechanical extraction proof and the RED/GREEN flip in scratch clones. All six findings below are precision-grade; all fold in one batch and a fresh round follows on the folded digest.

## Review Statistics

### Panel

| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| correctness-completeness | implementation, quality | none | complete | 1 | 1 | 0 | no |
| testing | testing | none | complete | 1 | 1 | 0 | no |
| design-simplicity | architecture, simplification | none | complete | 0 | 0 | 0 | no |
| contract-docs | consistency, documentation | none | complete | 2 | 2 | 0 | no |
| risk | security | none | complete | 2 | 2 | 0 | no |

### Counts
- Workers launched: 5
- Staged findings: 6

### Deduplication groups
None.

### Discarded findings
None.

### Severity calibration
None.

### Triage outcomes
- fixed: 6

## Findings

### Critical

(none this round)
### High

(none this round)
### Medium

(none this round)
### Low

#### F1. Seed-rejection clause overstates: a deferred runtime id IS producible at the seeding boundary
- **Pattern**: documentation#assumption-basis-precision
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: The rejection basis says a deferral seed "would build a manifest shape production cannot produce", but the create boundary writes the canonicalized id verbatim, so the shape is producible; what production cannot do is execute one (deferred ids resolve to the fail-closed UnsupportedAdapter), and the guard skips non-codex ids, so the seed would dodge the contract under adjudication
- **Reachability**: expected
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Assumptions seed-rejection bullet; scripts/execute_plan_runtime.py create path; scripts/runtime_capabilities.py:451-463,470,698-708

#### Comment
Fold accepted: the basis is corrected to producible-but-unexecutable, with the create-boundary and resolution facts stated.

#### Analysis
The rejection stands on the verified grounds; only the producibility phrasing overstated.

#### F2. Check 6 comment labels all 13 guard-substring tests as model-guard contract tests; two belong to other guard families
- **Pattern**: consistency#guard-contract-label-overcovers-substring-matches
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: Two of the 13 `-k guard` matches exercise other guard mechanisms (the resume-watcher budget-guard cleanup and the launch-drift guard), so "the 13 guard-contract tests" over-covers; counts and fail-closed behavior unaffected
- **Reachability**: expected
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Validation Commands check 6 comment; scripts/test_execute_plan_runtime.py:1905,14910

#### Comment
Fold accepted: the comment now states the true composition (11 codex model-guard contract tests, two adjacent guard-family tests, the probe-less pin).

#### Analysis
The filter is substring-based; the comment now matches its real membership.

#### F3. Seed-rejection assumption attributes the fixture harness to the wrong suite
- **Pattern**: documentation#fixture-harness-suite-attribution
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: "The suite's own fixture harness (`_fixture_inventory`)" is ambiguous in a section whose salient suite is the witness's file, but the harness lives in scripts/test_execute_plan_runtime.py; a reader verifying against the witness's file finds nothing
- **Reachability**: expected
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Assumptions seed-rejection bullet; scripts/test_execute_plan_runtime.py:86,92-95

#### Comment
Fold accepted: the attribution now names the file (scripts/test_execute_plan_runtime.py).

#### Analysis
Same edit as F1's fold; the harness claim's substance was verified true.

#### F4. Check 8 changed-file pin does not self-verify its branch-containment precondition
- **Pattern**: testing#changed-file-pin-precondition-unverified
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: The pin compares against the local main tip without asserting main is an ancestor of the execution branch, so legitimate states (main advancing past the branch point, the plan landing moving the shared ref before a fast-forward) abort the block after the suite has already spent its runtime; failure is fail-closed and recoverable but the precondition is unverified and the diagnostic imprecise
- **Reachability**: plausible-edge
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Validation Commands check 8

#### Comment
Fold accepted: check 8 gains a branch-containment arm (`git rev-parse main` equals `git merge-base main HEAD`) that aborts with a precise message before the scope comparison.

#### Analysis
A scope pin must verify the reference it scopes against; the containment arm makes the precondition explicit and the failure actionable.

#### F5. Check 6's expected collection count (14) is documented but not pinned
- **Pattern**: testing#guard-filter-count-unpinned
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: A guard test renamed off the filter would silently shrink the mask-check net while check 6 still exits 0 and the comment's 14 would lie; only total filter loss is caught (pytest exit 5)
- **Reachability**: plausible-edge
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Validation Commands check 6

#### Comment
Fold accepted: a collection-count pin (grep -c '::' equals 14, fail-closed) now follows the check 6 invocation.

#### Analysis
The count pin closes the silent-shrink path; verified at 14 on the current tree.

#### F6. GREEN step over-claims mutation adequacy for comparator-weakening that keeps the race green
- **Pattern**: testing#green-step-mutation-adequacy-overclaim
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: "A race body with any assertion weakened, cannot pass this step" is too strong: a comparator-weakening edit preserving the needle substring (assertEqual to assertTrue with >= 1) keeps all four greps at 1 and the suite green (worker mutation-verified), so the pins catch omission and removal, not strength changes
- **Reachability**: plausible-edge
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Task 1 GREEN step; scripts/test_runtime_capabilities.py:388-391

#### Comment
Fold accepted: the claim is scoped to presence pinning, with checks 4-5 named as the fail-closed runtime catch for strength changes.

#### Analysis
The greps' guarantee is presence; the sentence now says exactly that and points at the checks that own strength.

## Overflow manifest

None (the testing worker considered two further candidates and declined to file them below threshold: check 6's zero delta-discrimination, which is deliberate no-mask evidence serving a stated criterion, and check 8's blindness to untracked files, which the landing contract and hygiene scan already cover).
