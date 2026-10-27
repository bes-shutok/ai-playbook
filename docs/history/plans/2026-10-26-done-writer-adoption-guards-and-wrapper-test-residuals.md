# Plan: Done Writer Adoption Guards and Wrapper Test Residuals

Backlog origin: docs/history/backlog/2026-10-26-done-writer-adoption-guards-and-wrapper-test-residuals.md
Driving force: reliability (outside the default taxonomy because a witnessed ownership leak can promote a foreign review document into owned output; park triage should take this because it breaks ownership attribution and accepts closed run boundaries)
Plan review record: .ai-playbook/reviews/2026-10-27-plan-review-done-writer-adoption-guards-and-wrapper-test-residuals-r*.md
Execution budget: 2h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-26-done-writer-adoption-guards-and-wrapper-test-residuals.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms

- **Adopted run**: the prior run whose unfinished work a new done run continues.
- **Run boundary**: the identity and completion state represented by a run's canonical manifest and any same-run shadow records.
- **Interrupted orphan**: a run boundary classified as `orphan` by `classify_run_boundary`; the only boundary eligible for adoption.
- **Owned review path**: a staging review document the active run claims as its work.
- **Foreign review path**: a staging review document the active run preserves as work from another owner.
- **Forward arm**: the wrapper's adoption path that selects an adoption target from the newest terminal record.
- **Boundary verdict**: the classifier result for a run identity, including `orphan`, `finalized`, `adopted`, `dispositioned`, or `unreadable`. A same-run shadow record can close the canonical boundary.
- **Owned done lock**: the current run lock whose directory and token match the caller environment and whose metadata identifies this repository root.

## Why

The manifest writer currently trusts an adoption target's individual manifest fields without resolving its complete run boundary, and it can combine contradictory owned and foreign review claims. That can make a closed boundary look adoptable or make a foreign document pass as owned.

## Gist & Examples

TLDR: Validate adoption against the canonical run boundary and reject conflicting review ownership claims, improving reliability.

Before (today): a direct writer invocation can adopt a boundary while its owning done run still holds the lock, request a manifest whose run id is already closed by a disposition or shadow record, and claim a path as both owned and foreign. The wrapper catches some target shapes, but the writer remains directly callable and the forward arm has terminal-target gaps.

After (this plan): only a target classified as an interrupted orphan can be adopted by a caller that proves ownership of this repository's current done lock. If the adopted record marks a path foreign and the caller claims that path as owned, the writer refuses before writing a new manifest. Valid orphan composition keeps its current behavior.

Edge cases: an unknown target lock or a held target lock without matching caller ownership, a terminal record on any same-run manifest including a shadow copy, a dispositioned run, an unreadable target, a missing or mismatched caller lock, and an owned/foreign path intersection all refuse; an ordinary orphan with disjoint claims and the matching done lock still adopts.

## Outcome

Done-run manifest adoption accepts only an open interrupted boundary and preserves clear review ownership.

- A directly invoked writer cannot adopt without the matching current done lock or adopt an already adopted, finalized, dispositioned, or unreadable boundary, including closure carried by a same-run shadow record.
- A path declared both owned and foreign cannot be written into the adopted manifest as owned.
- Wrapper regressions separately cover the forward arm targeting an already-adopted run and a dispositioned run, and shared setup helpers live once.

Gate delta: add writer-side refusals for missing or mismatched lock ownership, non-orphan run boundaries, and intersecting owned/foreign review claims, grounded in the witnessed failures recorded by the backlog and review. Remove no existing refusal, check, or field; add no schema field or machinery. Existing blocking review-layer duties remain unchanged.

## Assumptions

- The backlog has no `Class:` line; its witnessed behavior and proposed repairs classify it as a real reliability defect, not a cleanup-only item. Evidence: the origin records scratch-repo and wrapper probes demonstrating ownership leakage and closed-boundary acceptance.
- `classify_run_boundary` is the canonical identity-level read: it reads run identity across canonical and same-run shadow records and sees adopted and dispositioned status; it is read-only. The writer must also check target-lock state because the classifier does not inspect locks. Source: `scripts/done_sweep_gates_lib.py`.
- Conflicting owned/foreign claims should refuse rather than silently prefer foreign, because either declaration alone could be intentional but their intersection is contradictory input.
- The wrapper's observable refusals remain stable; writer validation adds the lower-level enforcement.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: only a boundary classified as `orphan` is accepted by `write-manifest --adopt`.
- Ownership safety: the writer refuses before manifest creation when owned and foreign review paths intersect.
- Maintainability: the three wrapper fixture helpers have one shared implementation.

**Done when:** direct writer and wrapper regressions cover the refusal and valid-orphan cases, and the relevant suites pass.

**Ship when:** none; this is repository-local behavior.

## Documentation Impact Assessment

The `docs/` inventory contains no user-facing reference that needs a behavior update. A wording correction to the completed predecessor plan remains deferred because its registry requires a dated audit override and explicit user authorization. This plan does not modify completed history.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (Task 1)
- `scripts/done_run.sh` (Task 2)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (Task 1)
- `scripts/test_done_run_wrapper.py` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py` adoption behavior unrelated to boundary eligibility or review ownership; reason: outside the backlog's writer-side residuals.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
```

### Task 1: Guard direct writer adoption

Context surface: the plan's Terms and this task.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `classify_run_boundary` in `scripts/done_sweep_gates_lib.py`
- `_cmd_write_manifest` in `scripts/done_sweep_gates_lib.py`

- [ ] `write_manifest` requires the caller's `DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` to identify the current lock for this repository and match its recorded token and root; absent, malformed, or mismatched evidence refuses before writing. The root-matched target lock may be held by this caller; refuse unless the caller token proves that ownership, and refuse unknown or held-by-another-owner state. [class: IMPLEMENTATION_REQUIRED]
- [ ] `write_manifest` accepts only a target classified as an interrupted orphan when the target lock is held by this caller, as proven by the matching lock directory, token, and recorded repository root; unknown state or a held lock without matching caller ownership refuses, as does any other run-boundary verdict, with no new manifest. [class: IMPLEMENTATION_REQUIRED]
- [ ] `write_manifest` preserves ownership separation: given an owned review path that is also foreign in the adopted record, expects refusal and no adopted manifest; given disjoint claims for an orphan, expects successful composition. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add direct regression cases for a valid matching caller lock, absent and mismatched caller-lock evidence, the target lock held without matching caller ownership and an unreadable or unknown target lock, terminal records on canonical and same-run shadow copies, and conflicting owned/foreign claims. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the new regression checks fail against the current writer behavior. [class: REPOSITORY_TEST]
- [ ] Write minimal implementation. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: reject unsafe done manifest adoption`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Cover wrapper adoption residuals and share fixtures

Context surface: the plan's Terms and this task.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `classify_partial` in `scripts/done_run.sh`

- [ ] The forward arm refuses separately when `--adopt` names an already-adopted target and when it names a dispositioned target, even though the newest record is terminal; each case leaves no new marker or manifest. [class: IMPLEMENTATION_REQUIRED]
- [ ] The forward arm preserves the writer's boundary contract for a mismatched orphan id and a valid orphan target. [class: IMPLEMENTATION_REQUIRED]
- [ ] Wrapper adoption retains valid-orphan behavior: given an eligible orphan target, expects the adopted run to continue with the existing ownership and start-commit composition. [class: IMPLEMENTATION_REQUIRED]
- [ ] `FixtureMixin` supplies `rewrite_manifest`, `craft_manifest_file`, and `session_names`, and the adoption test has no duplicate helper implementations. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the new forward-arm cases fail or duplicated helpers remain against the current wrapper tests. [class: REPOSITORY_TEST]
- [ ] Consolidate the fixture helpers and add the regressions. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN. [class: REPOSITORY_TEST]
- [ ] Commit: `test: cover done adoption boundary refusals`. [class: IMPLEMENTATION_REQUIRED]
