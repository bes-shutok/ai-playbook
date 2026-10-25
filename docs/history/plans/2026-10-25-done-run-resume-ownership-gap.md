# Plan: Done setup adoption preserves review ownership claims

Backlog origin: docs/history/backlog/2026-10-25-done-run-resume-ownership-gap.md
Driving force: efficiency
Plan review record: .ai-playbook/reviews/2026-10-25-plan-review-done-run-resume-ownership-gap-p577c0eb8-r*.md
Execution budget: 1.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-25-done-run-resume-ownership-gap.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Adopted boundary:** A new done-run manifest linked with `adopted_from` to an existing interrupted manifest while carrying forward its start commit and ownership claims.
- **Exact re-entry:** Resuming the existing manifest named by `--from-manifest` without creating or changing a manifest.
- **Foreign review classification:** Review staging paths explicitly recorded as owned by another session and retained as foreign during setup adoption.
- **Completed integrity failure:** The witnessed review artifact passed review and digest gates but was absent from the done manifest until manual recovery, as recorded in the origin evidence.

## Why

When a done setup is interrupted after it records its boundary, a later review may need to join that run's owned set. The setup wrapper currently refuses the interrupted boundary before its accepted `--adopt` option reaches the existing manifest writer. This adds recovery work and can leave the wrapper's `--from-manifest` remedy silently ignoring new claims.

## Gist & Examples

TLDR: Route setup `--adopt` through the existing manifest writer, keeping `--from-manifest` exact, to improve recovery efficiency after new review artifacts appear.

Before: A caller supplies `setup --adopt <run-id>` with a new review claim, but partial-boundary classification stops before the writer runs. Using `--from-manifest` re-enters the original boundary and ignores that claim.

After: Explicit `setup --adopt <run-id>` passes the classified interrupted boundary to the existing writer, which preserves the old start commit and ownership classifications and records the new review claim. `--from-manifest` remains exact re-entry and rejects added ownership claims with a named `--adopt` remedy.

## Outcome

Done setup can recover an interrupted boundary through its supported wrapper, with all review ownership visible in the adopted manifest.

- A valid explicit adoption preserves the prior start commit and ownership claims while adding the newly supplied review claims.
- Exact re-entry continues to use the existing manifest unchanged.
- A caller who combines exact re-entry with new ownership claims receives the supported adoption command instead of silently losing those claims.

Gate delta: One refusal class covers incompatible transition inputs: `--from-manifest` with new ownership claims, or `--from-manifest` together with `--adopt`. The backlog origin's two suggested options and the selected route are recorded separately from prompt-only context:

| Choice | Evidence and disposition |
|---|---|
| Add claims to the existing current boundary | This is one of the origin's two suggested options. It conflicts with the fixed-at-write-time ownership contract established by the completed post-setup ownership plan, so do not mutate an existing manifest. |
| Add a named wrapper operation that adopts the existing manifest | This is the origin's second suggested option and the selected sanctioned exit: `setup --adopt`. Route it through the existing writer and link a new manifest, preserving the old start commit and ownership history. Directly invoking the low-level writer leaves the wrapper defect in place. |
| Keep `--from-manifest` exact | This is the existing contract, not an origin-listed alternative: return the named manifest without adding claims or writing a replacement. The mixed-input refusal points to `--adopt`. |

Rule 42 pricing for this refusal: the sanctioned exit is the explicit `--adopt` operation; false-positive removal does not apply because the flags request different transitions and silently dropping claims caused the witnessed ownership loss; simplifying to one overloaded resume operation is rejected because it would silently change exact re-entry into adoption or drop claims. The separate operations preserve the established contract and make the boundary-changing choice explicit. The completed integrity failure is the witness paying for this one refusal class. The three options sometimes described as origin rejections (direct writer, in-place widening, unrelated fresh run) are present only in the rolling PLAN-PROMPTS entry, not the backlog origin, and are not recorded as origin text here. No gate, lock, validator, schema field, protocol layer, or ceremony is added or removed.

## Assumptions

- The existing `write-manifest --adopt` path remains the adoption authority and continues to validate root identity, completion state, and start-commit resolvability. Basis: `scripts/done_sweep_gates_lib.py` adoption path.
- When partial-boundary classification finds an orphan, only its run ID may be adopted; when no orphan boundary is classified, the existing writer validations remain authoritative. Basis: `classify_partial` returns the authoritative `mid` and verdict before writing a new marker.
- Setup adoption carries forward prior owned and foreign review classifications, and merges the newly supplied claims using the existing writer. Basis: the writer's current adopted-manifest construction.
- `--from-manifest` means exact re-entry; it does not create or rewrite a manifest. Basis: `classify_partial` and the wrapper's existing exact-reentry regression.
- Supplying new ownership claims with `--from-manifest` should be rejected with a named `--adopt` remedy instead of silently dropping them. Basis: the witnessed defect and the origin's rejected alternatives.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: explicit wrapper adoption retains the prior boundary and adds the requested review ownership only for the boundary selected by partial classification.
- Compatibility: exact re-entry is unchanged, and invalid interrupted boundaries remain fail-closed.
- Regression coverage: wrapper tests pin successful adoption, exact re-entry, and the mixed-option refusal with both marker and manifest state unchanged.

**Done when:** The focused wrapper and manifest-writer tests pass, proving the original start commit, prior owned and foreign classifications, newly added review ownership, exact re-entry, refusal of mismatched or non-orphan targets, and no durable marker or manifest after rejected adoption.

**Ship when:** The plan's implementation and validation land through the repository's normal closeout.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production code:**
- `scripts/done_run.sh` (Task 1)

**Tests:**
- `scripts/test_done_run_wrapper.py` (Task 1)
- `scripts/test_done_sweep_gates_lib.py` (Task 1)

**Plan-related extension:** A finding is in scope when it is causally related to setup adoption or the exact re-entry contract changed by this plan.

**Out of scope; reject unless plan-related:**
- Manifest schema and lower-level adoption behavior; reason: the existing writer already carries the prior boundary and is the intended authority.
- New recovery gates, validators, locks, or ceremony steps; reason: the origin and machinery admission rules call for using the existing adoption path.

## Documentation Impact Assessment

The existing done skill describes the setup boundary and ownership arguments. The wrapper's emitted recovery remedy is the actionable contract for this defect, so no separate documentation edit is needed unless implementation evidence shows another maintained copy of that remedy.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
```

### Task 1: Restore wrapper-visible adoption and protect exact re-entry

Context surface: the plan's Terms, this task, and `## Assumptions`.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `classify_partial` in `scripts/done_run.sh`
- `cmd_setup` in `scripts/done_run.sh`

- [ ] Given a partial-boundary classifier result of `orphan` with run ID `mid`, expects `setup --adopt <mid>` to reach the existing writer and preserve the prior boundary while adding new review claims. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an `orphan` result for `mid` and `--adopt` naming a different run ID, expects refusal before writing a new marker or manifest, with prior manifest bytes unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a classified non-orphan boundary (including terminal or already-adopted) and an attempt to adopt that classified ID, expects refusal with no durable marker or manifest change. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given no partial boundary, expects the wrapper to preserve the existing `write-manifest --adopt` validations; when that writer rejects a target, expects the wrapper to remove its newly written marker and leave the manifest set unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given successful setup adoption, expects the new manifest to preserve the prior start commit, owned review claims, and foreign review classifications while adding the newly supplied owned review claims. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given `setup --from-manifest <run-id>` alone, expects exact re-entry to return the existing manifest without writing a replacement or changing its claims. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given `--from-manifest` combined with ownership options, expects a named refusal that points to `--adopt` and leaves both marker and manifest state unchanged; `--from-manifest` and `--adopt` together also refuse as conflicting modes without durable residue. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a corrupt boundary, expects the existing fail-closed classification with no durable marker or manifest change. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given either current-boundary or stale-marker recovery guidance, expects the wrapper to name `--adopt` for adoption and `--from-manifest` only for exact re-entry; wrapper regressions pin both remedies. [class: REPOSITORY_TEST]
- [ ] Add focused wrapper and manifest-writer regressions for adoption with a review created after initial setup, preserved prior ownership and start commit, unchanged foreign classifications, exact re-entry, mixed-option refusal with unchanged marker and manifest state, classified-ID mismatch, non-orphan target, corrupt boundary, and writer-rejected target with no durable residue. [class: REPOSITORY_TEST]
- [ ] Run the validation commands in this plan and commit the change as `fix: make done setup adoption reachable`. [class: IMPLEMENTATION_REQUIRED]
