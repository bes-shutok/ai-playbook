# Plan Review: capacity-slot test adjudication (r2)

## Metadata
- Type: Plan Review
- Date: 2026-10-02
- URL or Artifact: `docs/history/plans/2026-10-02-capacity-slot-test-adjudication.md`
- Depth: full panel (five workers: correctness-completeness, testing, design-simplicity, contract-docs, risk)
- Domains: mask-check completeness, mutation-pin coverage, changed-file scope, adjudication-record truthfulness, anchor prose accuracy
- Round: r2
- Prior: r1 (3 staged findings, all fixed in the fold this round reviewed past)
- Review mode: fresh-adversarial
- Changed-risk signals: none
- Prior findings supplied as filter: no
- Last fix commit: none
- Witness ledger: N/A (no public mutators)
- Release-gate ledger: none
- Coverage: clean
- Record kind: canonical
- Findings: 6 staged (9 raw; 2 echoes merged under dedup; 1 overflow item under the per-worker Low budget)
- Status: STAGED (folded: 7 fixed including the overflow item; fresh round follows on the folded digest)

### Attempt ledger

| Attempt | Worker | Lenses | Started | Deadline | Elapsed min | Outcome |
|---------|--------|--------|---------|----------|-------------|---------|
| r2-correctness-completeness | correctness-completeness | implementation, quality | 2026-10-02T11:10:00+01:00 | bounded-wait | 8.3 | complete |
| r2-testing | testing | testing | 2026-10-02T11:10:00+01:00 | bounded-wait | 5.3 | complete |
| r2-design-simplicity | design-simplicity | architecture, simplification | 2026-10-02T11:10:00+01:00 | bounded-wait | 6.7 | complete |
| r2-contract-docs | contract-docs | consistency, documentation | 2026-10-02T11:10:00+01:00 | bounded-wait | 14.9 | complete |
| r2-risk | risk | security | 2026-10-02T11:10:00+01:00 | bounded-wait | 4.4 | complete |

All five workers launched in parallel and completed on the first pass, reviewing the r1-folded digest fresh (no prior-findings filter). Every worker re-derived the load-bearing claims against disk, and three independently re-executed the mechanical extraction proof in scratch clones (RED on base, GREEN after insertion, the anchor single-occurrence counts, the grep pins, the 13-test `-k guard` collection). The r1 fixes were confirmed landed: the corrected anchor rationale, the corrected Sources inspected ranges (all three workers re-derived 1854-1898, 4664-4837, 347-391 as exact), and the race-body grep pin. The findings below are new polish-grade defects; all fold in one batch and a fresh round follows on the folded digest.

## Review Statistics

### Panel

| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| correctness-completeness | implementation, quality | none | complete | 1 | 1 | 0 | no |
| testing | testing | none | complete | 2 | 2 | 0 | no |
| design-simplicity | architecture, simplification | none | complete | 3 | 1 | 1 | no |
| contract-docs | consistency, documentation | none | complete | 2 | 1 | 1 | no |
| risk | security | none | complete | 1 | 1 | 0 | no |

### Counts
- Workers launched: 5
- Staged findings: 6

### Deduplication groups
- F6 merges design-simplicity's `documentation#validation-records-numbering-out-of-order` and contract-docs' `consistency#authoring-records-numbering-out-of-order` (echoes) into correctness-completeness's `documentation#enumeration-order-slip`: all three name the same Authoring-time records defect.

### Discarded findings
None.

### Severity calibration
None.

### Triage outcomes
- fixed: 7 (6 staged + 1 overflow)

## Findings

### Critical

(none this round)
### High

(none this round)
### Medium

(none this round)
### Low

#### F1. Check 6's mask-check does not collect the probe-less fail-closed test that pins the exact branch the stub sidesteps
- **Pattern**: testing#mask-check-misses-fail-closed-pin
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: The plan labels check 6 as "the stub must not mask them", but `-k guard` (13 tests) omits `test_codex_claim_fails_closed_without_probe_capable_adapter` (scripts/test_execute_plan_runtime.py:221), the only test pinning the non-callable-probe fail-closed default the ok-stub deliberately bypasses; a regression making the probe-less default permissive would pass the labeled mask-check and be caught only incidentally by check 7
- **Reachability**: plausible-edge
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Validation Commands check 6; scripts/test_execute_plan_runtime.py:221

#### Comment
Fold accepted: check 6's filter is extended to `-k 'guard or fails_closed_without_probe'` (14 collected, 676 deselected, re-derived on disk), making the no-mask criterion self-contained.

#### Analysis
The stub's entire safety argument is that the fail-closed branch it bypasses stays pinned elsewhere; the mask-check that claims to prove this must collect the pin for that exact branch, not only the drift-refusal family.

#### F2. Race-body pin covers only the winner-count expression; blocked-loser and reservations-count assertions are unpinned
- **Pattern**: testing#race-assertion-pin-gap
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: The GREEN step's body pin matches only the winner-count expression (line 388); the blocked-loser assertion (line 389) and `assertEqual(len(reservations), 1)` (line 391) have no pin, so a race body with one of those two assertions weakened or deleted still passes both greps and checks 4-5
- **Reachability**: plausible-edge
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Task 1 GREEN step; scripts/test_runtime_capabilities.py:388-391

#### Comment
Fold accepted: the GREEN step now pins all three race assertions (winner-count, blocked-loser, single-reservation), each verified count 1 on the base file.

#### Analysis
The r1 fold closed the vacuous-witness hole for body deletion but left two of the three race assertions unpinned; the step's claim ("the capacity-race body is intact") now covers exactly the assertions that make the witness discriminating.

#### F3. "No production byte changes" claim has no execution-time diff-scope check
- **Pattern**: testing#missing-diff-scope-check
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: The Outcome/Gate-delta safety argument rests on an assumption no Validation check verifies: nothing pins the changed-file set to the witness test, so a stray behavior-preserving production edit would ride through the whole block undetected
- **Reachability**: plausible-edge
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Outcome / Gate delta vs Validation Commands block

#### Comment
Fold accepted: check 8 added, pinning `git diff --name-only main` to exactly `scripts/test_runtime_capabilities.py` at execution time (the plan bytes are already on main then); the execution-faithful scratch simulation committed the plan to its clone's main first so the check ran under its real execution semantics.

#### Analysis
A scope claim that no check enforces is a hope; the changed-file set is mechanically checkable and now is.

#### F4. Rejected-alternative basis misreads the witness comment it cites and contradicts its own Assumption 1
- **Pattern**: documentation#witness-seed-basis-misattribution
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: The seed-rejection assumption rejects a different seed because it would "decouple the witness from the codex-shaped seed its own comment documents", but the witness comment documents only the presence-only identity gate, not codex specifically, and Assumption 1 already declares the codex seed incidental, making the stated decoupling harm vacuous; the conclusion is correct on unstated stronger grounds
- **Reachability**: expected
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Assumptions section, seed-rejection bullet; scripts/test_runtime_capabilities.py:362-365

#### Comment
Fold accepted: the basis is rewritten to the verified grounds (codex is the only bound runtime in the inventory, every other id a deferral served by UnsupportedAdapter, so a deferral seed builds a manifest shape production cannot produce; the `_fixture_inventory` harness auto-attaches the identical ok-stub to every fixture adapter).

#### Analysis
An adjudication record must stand on its true reasons; the stronger grounds were verified on disk (inventory sections and the fixture harness) before being written in.

#### F5. Anchor prose claims the stub sits immediately after the return line; the fenced bytes keep a blank line between them
- **Pattern**: documentation#anchor-prose-blank-line-mismatch
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: The Task 1 prose describes the insertion position inconsistently with the fenced bytes (which keep the pre-existing blank line after the return line and add the class-closing blank after the stub); an editor keying off the prose instead of the fence produces bytes that differ from "exactly as written"
- **Reachability**: plausible-edge
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Task 1 intro paragraph vs the fenced insertion block

#### Comment
Fold accepted: the prose now defers to the fence as the byte contract and describes the blank-line shape exactly (pre-existing blank after the return line, stub comment, one blank ahead of the named `with` tail).

#### Analysis
When prose and fence describe the same bytes they must agree; the fence is the contract and the prose now says so.

#### F6. Authoring-time records numbered out of order: (3) is followed by (5) then (4)
- **Pattern**: documentation#enumeration-order-slip
- **Severity**: Low
- **Blocking**: false
- **Triage**: fixed
- **Consequence**: The Validation preamble's records read (1), (2), (3), (5), (4) in text order, deviating from the strictly sequential enumeration of the reference plans; a reader following the numbering hits record 5 before record 4, and any later fold that appends an item inherits the ambiguity
- **Reachability**: expected
- **Blast radius**: local
- **Confidence**: verified
- **Anchor**: Validation Commands, Authoring-time records paragraph

#### Comment
Fold accepted: the baselines item moved before the r1 fold receipt and the sequence renumbered (1)-(5), with the r2 fold receipt appended as item (6).

#### Analysis
The r1 fold receipt was appended at its narrative position rather than the sequence's end; the reorder restores the cross-reference order the genre's precision requires.

## Overflow manifest

- simplification/Low (`simplification#validation-check-subset-of-full-suite`, design-simplicity): check 6 is a strict subset of check 7 and passes independently of the change, surviving only as the fail-fast no-mask diagnostic. Fixed in the same fold: check 6 gained the probe-less fail-closed pin, so it is no longer a pure subset of check 7.
