# Plan: operator-provided run inputs get a named delivery home and a parked-run mirror

Authoring claim: docs/tmp/authoring-claims/post-implementation-review-summary-handoff.md (session sess_automation-c34d8271)

Backlog origin: docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md
Driving force: reliability; off-taxonomy justification: the contract protects resumability of a run stopped for an operator-provided input and survivability of a parked run's state, continuity properties outside the five driving principles; park-triage would not take it because the witnessed run paid a full Phase 0 before discovering the missing delivery location and the same stop re-bites on every future operator-provided input
Plan review record: the staging series .ai-playbook/reviews/2026-10-18-plan-review-post-implementation-review-summary-handoff-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h

## Terms

- Operator-provided input: an input a plan declares that only the operator or the review-evidence owner can supply (the witnessed case: an anonymized finding-to-review summary).
- Run-scoped gitignored home: the existing per-run directory `{tmp_dir}/execute-plan/<PLAN_SLUG>/` in the primary checkout (the manifest-documented run home); it stays gitignored and gains no tracked twin.
- Supplier: the operator or the review-evidence owner who delivers the declared input; never the run itself.
- Coverage verification: the run's check, at the primary home, that a delivered input carries the per-finding entries the plan declares (owning stage, covered digests, related records, triage disposition), recording fields it cannot verify as unavailable.
- Parked run: a run stopped before its closeout with its worktree still standing (for example by a missing declared input, a quota pause, or a lane hold).
- Unavailable recording: recording a field the run cannot verify as unavailable instead of inferring it, leaving no associated lens or triage edit.

## Why

The witnessed 2026-10-15 execution run stopped before its first task because the certified plan required an operator-provided anonymized summary and no durable delivery location, supplier, or coverage check existed; the run resumed only through an operator-directed plan revision, and its whole gitignored state survived the park only through a hand-executed mirror. Two sentences in the Worktree-first standard make that class resumable without weakening the no-inference protections or adding machinery.

## Gist & Examples

TLDR: gives operator-provided plan inputs a named run-scoped delivery home with per-finding coverage verification at that home, and mirrors a parked run's run-created gitignored state to the primary checkout, so a stopped run resumes without inference; declared force reliability.

Before: an execution run stops before its first task because the plan requires an operator-provided anonymized summary and no durable delivery location, supplier, or coverage check exists; the run's whole gitignored state lives only in its worktree and survives the park only through a hand-executed mirror copied by an investigating session.

After: the plan declares the input and its coverage shape; the supplier delivers it to the run-scoped gitignored home; the run reads and verifies the per-finding coverage at that primary home and records fields it cannot verify as unavailable; a run parked before its closeout mirrors the gitignored artifacts its run created or modified to the primary checkout's run homes, never overwriting a newer primary-home file, so the resume contract survives worktree loss.

Edge cases: the run never constructs or infers a missing input, and an absent declared input keeps the plan's own stop response; no new gate, validator, ledger, or tracked artifact type exists (the home stays gitignored and tracked artifacts stay banned); a plan declaring no operator-provided input is unchanged; the witnessed run already resumed through the operator-directed repository-only revision arm (the revival plan), so this contract binds future runs; a mirror copy that fails verification is reported, never silently dropped.

## Outcome

An operator-provided input for a plan run has a named delivery home, a named supplier, and a coverage verification that records gaps as unavailable, and a parked run's state survives worktree loss.
- The delivery and mirror clauses ride the two existing Worktree-first lifecycle bullets they extend, so the reading surface for runs carries them without new sections.
- No run constructs, infers, or guesses a declared input; the no-inference protections the certified plans carry are untouched.
- Gate delta: none.

## Assumptions

- assume this contract binds future runs, not the witnessed one; basis: the witnessed run resumed through the operator-directed repository-only revision arm (the revival plan docs/history/plans/2026-10-17-post-implementation-review-invariant-coverage-revival.md, verified executing at r5-clean per its manifest updated 2026-10-17T21:30:48Z, re-derived from disk 2026-10-18; the canonical plans-root path moves to docs/history/plans/completed/ when that execution lands), so no active run waits on this contract.
- assume the run-scoped gitignored home is the delivery home and one of the mirror homes; basis: `{tmp_dir}/execute-plan/<PLAN_SLUG>/` is the manifest-documented run home the closeout implementation already names, beside the reviews and metrics homes the closeout baseline already spans, and no new artifact type or tracked path is added.
- assume the change alters no machine-checked behavior; basis: it is two sentences appended to two lifecycle bullets in an instruction document; the pins suite holds no pins over these bullets (verified pre-round against scripts/check_maintenance_pins.sh).

Decision points requiring a grill: delivery location resolved to the existing run-scoped gitignored home with the run reading and verifying at that primary home as a named sanctioned crossing, because the transfer-in fence creates the worktree's scratch empty and the delivered input must reach the consuming task without an improvised cross-checkout read (source: the routing entry's delivery shape and the round-1 contract-docs finding on the unowned route, 2026-10-18; affected section: Task 1); park-time mirror resolved to one lifecycle sentence appended to the transfer-out bullet rather than a new lifecycle step, scoped to run-created-or-modified artifacts with a never-overwrite-a-newer-primary-home bound, because the witnessed hand mirror is recorded practice and the closeout implementation's scoped-copy arm already owns the verification pattern (source: the routing entry's scope arms, the witnessed mirror, and the round-1 risk findings on mirror scope, 2026-10-18; affected section: Task 1).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the delivery sentence names the declared input, the supplier with the run excluded, the run-scoped gitignored home, the primary-home read route, the per-finding coverage shape, the unavailable recording, and the stop preservation; the mirror sentence names the park shape, the run-created-or-modified scope, the no-clobber bound, and byte-equal verification; verbatim-span greps over agents/skills/execute-plan/SKILL.md.
- safety: the run never infers a missing input and never authors one; the mirror never sweeps foreign state and never clobbers a newer primary-home file; no gate, validator, ledger, or tracked artifact type is added; both original bullets keep their bytes byte-intact; polarity greps.
- minimality: two sentences in one existing file; pins suite and public-hygiene scan green; no section added.

**Done when:**
- Both prescribed spans are present verbatim in the execute-plan Worktree-first lifecycle, and both original bullets are byte-intact.
- scripts/check_maintenance_pins.sh exits 0; the public-hygiene scan exits 0; the no-em-dash scan over the added lines is clean.

**Ship when:**
- none; the change is fully repository-verifiable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (the Worktree-first standard's lifecycle steps 2 and 5 bullets only; all other sections frozen)

**Tests:**
- none; validation is span-grep and suite based

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/plans/2026-10-17-post-implementation-review-invariant-coverage-revival.md`; a certified, executing plan whose evidence contract is its own reviewed surface, and this plan binds future runs instead
- `agents/skills/plans/SKILL.md`; plan-declared inputs ride each plan's own Terms under existing authoring guidance, so no plans-skill text changes
- `docs/history/backlog/2026-10-17-parked-run-input-fallback-option.md` and the missing-input response contract; that sibling entry (frozen, peer-authored) owns the missing-input response arms, and neither plan rewrites the other's span
- `docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md`; the origin row's lifecycle is this landing's riders (the coverage gate's mark-covered flip writing the Status: covered witness) with the row deleted at this plan's execution completion per the repo commit guidelines; no executor edit

## Validation Commands

Validation preamble (authoring-time record): the plans skill's Validation Commands authoring-rules pre-round battery ran before round 1 with these recorded outcomes: the no-em-dash touched scan over the plan bytes (clean), the public-hygiene scan (clean), and the readiness structural pre-round gate (pass). RED-today evidence: the two full-bullet pin greps and the three polarity greps below each exit 1 against the pre-change agents/skills/execute-plan/SKILL.md (rc 1 all five on 2026-10-18). The authoring-time mechanical audit: both full-bullet pin spans, both appended sentences, and the three polarity spans were extracted from this plan and matched once each against the simulated post-change bullets; the two structural gates (bullet counts, numstat confinement) were simulated against a scratch copy carrying both insertions; bash -n over this block is clean.

```bash
# RED-today proven: these full-bullet whole-line pins exit 1 before Task 1 (rc 1 on 2026-10-18).
# Each contiguous fixed string pins placement, verbatim presence, whole-line equality, and the bullet's byte-intactness.
grep -qxF -- "2. **Transfer the inputs in for worktree placement.** Copy the run's gitignored input artifacts into the worktree before any work: the project facts file and any other gitignored inputs the run needs (for example, the reviews directory the readiness gate resolves). A fresh worktree's gitignored directories start empty, so nothing resolves until it is copied in. The **Transfer-in implementation** below owns how. For the primary placement, inputs already resolve in the primary checkout; do not copy them or create a worktree. An operator-provided input a plan declares (for example a review-evidence summary) is delivered by the operator or the review-evidence owner, never the run itself, to the run-scoped gitignored home \`{tmp_dir}/execute-plan/<PLAN_SLUG>/\` in the primary checkout before the consuming task, one entry per declared finding with the coverage fields the plan names; the run reads and verifies that coverage at that primary home, a named sanctioned crossing under the worktree placement, records fields it cannot verify as unavailable instead of inferring them, and an absent declared input keeps the plan's own stop response." agents/skills/execute-plan/SKILL.md || { echo "FAIL: post-change transfer-in bullet not present verbatim"; exit 1; }
grep -qxF -- "5. **Transfer the artifacts out and verify.** Before any cleanup, move all run artifacts (review staging documents, stats sidecars, telemetry, and the Phase 4 metrics archive copy under the resolved \`{metrics_dir}\`) from the worktree back to the primary checkout and verify them present there. Gitignored run artifacts never ride the branch commits, so the primary checkout is their only durable home. The **Transfer-out-and-deletion implementation** below owns how. A run parked before its closeout with its worktree still standing mirrors the gitignored artifacts its run created or modified from the worktree to the primary checkout's run homes, never a blanket sweep and never overwriting a newer primary-home file, byte-equal copies verified and a failed copy reported, never silently dropped, so the resume contract survives worktree loss." agents/skills/execute-plan/SKILL.md || { echo "FAIL: post-change transfer-out bullet not present verbatim"; exit 1; }
# Safety polarity witnesses (independent, diagnosable): no-inference, mirror scope, and mirror verification must be present verbatim.
grep -qF "records fields it cannot verify as unavailable instead of inferring them" agents/skills/execute-plan/SKILL.md || { echo "FAIL: no-inference polarity missing"; exit 1; }
grep -qF "never a blanket sweep and never overwriting a newer primary-home file" agents/skills/execute-plan/SKILL.md || { echo "FAIL: mirror scope polarity missing"; exit 1; }
grep -qF "byte-equal copies verified and a failed copy reported" agents/skills/execute-plan/SKILL.md || { echo "FAIL: mirror verification polarity missing"; exit 1; }
# The two lifecycle bullets stay one bullet each: no new list items.
test "$(grep -c '^2\. \*\*Transfer the inputs in for worktree placement' agents/skills/execute-plan/SKILL.md)" -eq 1 || { echo "FAIL: transfer-in bullet count changed"; exit 1; }
test "$(grep -c '^5\. \*\*Transfer the artifacts out and verify' agents/skills/execute-plan/SKILL.md)" -eq 1 || { echo "FAIL: transfer-out bullet count changed"; exit 1; }
# Scope freeze enforcement: execute-plan SKILL.md's whole diff since the merge base is exactly two modified lines.
test "$(git diff --numstat "$(git merge-base HEAD refs/heads/main)" -- agents/skills/execute-plan/SKILL.md)" = "$(printf '2\t2\tagents/skills/execute-plan/SKILL.md')" || { echo "FAIL: execute-plan diff is not exactly two modified lines"; exit 1; }
# Shared-body gates over the changed bytes.
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite"; exit 1; }
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD refs/heads/main)" || { echo "FAIL: em-dash in added lines"; exit 1; }
( cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh ) || { echo "FAIL: public-hygiene scan"; exit 1; }
```

### Task 1: Land the delivery-contract and parked-run-mirror sentences in the Worktree-first standard

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/execute-plan/SKILL.md`

Primary class anchors:
- `Transfer the inputs in for worktree placement` in `agents/skills/execute-plan/SKILL.md`, the Worktree-first lifecycle step 2 bullet this task extends (prose anchor; the bullet's lead phrase)
- `Transfer the artifacts out and verify` in `agents/skills/execute-plan/SKILL.md`, the Worktree-first lifecycle step 5 bullet this task extends (prose anchor; the bullet's lead phrase)

Prescribed insertions (verbatim, each one sentence appended to its bullet's end):
- Step 2 (transfer-in) appended sentence: "An operator-provided input a plan declares (for example a review-evidence summary) is delivered by the operator or the review-evidence owner, never the run itself, to the run-scoped gitignored home \`{tmp_dir}/execute-plan/<PLAN_SLUG>/\` in the primary checkout before the consuming task, one entry per declared finding with the coverage fields the plan names; the run reads and verifies that coverage at that primary home, a named sanctioned crossing under the worktree placement, records fields it cannot verify as unavailable instead of inferring them, and an absent declared input keeps the plan's own stop response."
- Step 5 (transfer-out) appended sentence: "A run parked before its closeout with its worktree still standing mirrors the gitignored artifacts its run created or modified from the worktree to the primary checkout's run homes, never a blanket sweep and never overwriting a newer primary-home file, byte-equal copies verified and a failed copy reported, never silently dropped, so the resume contract survives worktree loss."

- [x] The transfer-in bullet carries the delivery contract: given a plan that declares an operator-provided input with its coverage shape, expects the policy to name the supplier with the run excluded, the run-scoped gitignored home, the run's primary-home read route, the per-finding entry shape, the unavailable recording for unverifiable fields, and the stop preservation for an absent input. [class: IMPLEMENTATION_REQUIRED]
- [x] The transfer-out bullet carries the parked-run mirror: given a run parked before its closeout with its worktree still standing, expects the policy to mirror the run-created-or-modified gitignored artifacts to the primary checkout's run homes, never a blanket sweep and never overwriting a newer primary-home file, byte-equal copies verified. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (no-inference boundary): given a reading of the delivery contract as license to construct, author, or infer a missing input, expects the clause to withhold run authorship verbatim and record unverifiable fields as unavailable so the certified plans' no-inference contracts still bind. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the two full-bullet pin greps and the three polarity greps over agents/skills/execute-plan/SKILL.md fail (spans absent; verified 2026-10-18, grep rc 1 all five). [class: REPOSITORY_TEST]
- [x] Write minimal implementation: append the task's two Prescribed insertion sentences, byte-verbatim, each after one space following the bullet's current final byte, to the ends of the transfer-in (step 2) and transfer-out (step 5) lifecycle bullets. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both full-bullet pins and all three polarity greps pass, the two bullet-count gates and the numstat scope-freeze gate pass, and the pins suite, em-dash added-lines scan, and public-hygiene scan each exit 0. [class: REPOSITORY_TEST]
- [x] Commit: `skills: give operator-provided run inputs a named delivery home and a parked-run mirror` [class: IMPLEMENTATION_REQUIRED]
