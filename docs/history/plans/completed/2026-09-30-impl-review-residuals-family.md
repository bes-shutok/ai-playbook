# Plan: Impl-review residuals family closeout

Backlog origins (scope of record): `docs/history/backlog/2026-09-29-execute-plan-review-residuals.md`, `docs/history/backlog/2026-09-29-p93-impl-review-nonblocking-residuals.md`, `docs/history/backlog/2026-09-29-residual-exit-impl-review-residuals.md`, `docs/history/backlog/2026-09-30-prelaunch-recovery-impl-review-residuals.md`, `docs/history/backlog/2026-09-30-emdash-residuals-exec-review-residuals.md`
Driving force: reliability
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-impl-review-residuals-family-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The five impl-review residual items close as one family: every residual that demanded a regression pin or a small alignment gets one, and every record-only residual keeps its recorded no-action disposition, so a later touch can no longer silently regress an uncovered fence.

- After this plan, the execute-plan runtime's mid-run fences carry their two missing regression pins (claim_token-mismatch refusal and omission acceptance; closed-claim completion), the acceptance-pin suite carries the three plan-pinned shape sub-cases, the boundary-equality refusal carries its manifest-byte-identity assertion, and the deferred-runtime boundary narrowing carries its pin.
- Two code alignments land: the `recover-run-identity` payload `token` becomes isinstance-strict like its sibling fields, and the vacuous post-equality assertion becomes a real complement check.
- The two recorded decisions (root-less classification, refusal-display elision) land as deliberate pins of the current stricter behavior, amending the plan-letter expectation, so a later reconciliation does not "fix" them blind.
- The no-action residuals stay no-action: the tokenization semantics widening (conservative by the plan's Terms), the RED-evidence process note, the whitespace bookkeeping note, the plan-record formatting note (emdash item 2), the harness-placement acceptance (the three recovery pins live in `EvidenceContractRecoveryCodexTest` and the task commits use house-style messages - recorded in place so a later reconciliation does not fix them blind), the plan-sanctioned constants duplication (shared module only on a third consumer), the em-dash adjacency-pin candidate (rides the next plan that amends the same gate block), and the recover-task-scope sibling of the token coercion (the same `str()` asymmetry one function below, no residual file of its own - recorded here as a known asymmetry, out of the family's scope).

Gate delta: adds eight regression pins to the runtime test suite and two small code alignments (one strictness fix, one real assertion); records two behavior decisions in test comments; removes nothing; priced by the family's own witnesses - five review rounds reported clean while carrying fifteen numbered residuals (eighteen units at this plan's fence/shape granularity), eight of which are uncovered fences a later touch could regress

## Terms

- **Residual family**: the five cross-clustered backlog items recording non-blocking findings from executed plans' implementation reviews (task-local-verifier, p93 continuation-admission, residual-exit ordering, prelaunch-recovery, emdash-residuals); one grouped plan because the work is one shape - pins and small alignments in the same two runtime files.
- **Uncovered fence**: a judged-safe guard behavior with no dedicated regression test, so a refactor could silently drop it.
- **Recorded decision**: a residual whose fix is to pin the current behavior deliberately (test comment plus this plan's record), amending the original plan-letter expectation instead of the code.
- **No-action residual**: a residual whose own file already records the disposition (conservative-by-Terms, process note, formatting note, plan-sanctioned duplication, conditional ride-along); this plan changes nothing for it and the execution-time fold closes it.

## Assumptions

- assume the root-less classification residual resolves to pinning the current stricter behavior (containment classification when no root is supplied) rather than aligning to canonicalization identity: production paths always resolve a root, so the library-caller over-refusal is the documented cost of a stricter default; basis: the item's own "align or pin deliberately" offer and the runtime's fail-closed house direction.
- assume the refusal-display residual resolves to amending the plan-letter expectation (byte-count-only display stays): the current form is stricter and test-consistent, and the item itself marks the first-line variant as the alternative; the shape-1 "embeds" wording fix rides the same comment.
- assume the em-dash adjacency-pin candidate stays a recorded ride-along (its own file scopes it to "the next plan that amends the same gate block", which this plan is not); no code change here.
- assume the runtime test suite is the family's regression surface: `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime` (529 tests at the witnessing review) must stay green with the eight new pins.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the five impl-review residual items close in one pass - eight regression pins and two strictness fixes land in the runtime and its test suite, the two behavior decisions get pinned deliberately, and the no-action notes keep their recorded dispositions - so the reliability force turns a pile of recorded non-blockings into covered fences.

**Before (today):** Five review rounds said clean while their residual files recorded fifteen numbered findings: a claim_token-mismatch refusal and a closed-claim completion with no tests, three plan-pinned acceptance shapes that verified only in unstaged variants, a boundary-equality refusal whose sibling carries a byte-identity assertion it lacks, a deferred-runtime narrowing no test pins, a claim_token-omission acceptance with no pin, a payload token accepted by `str()` coercion, and an assertion that is vacuously true after the equality check it follows.

**After (this plan):** Each of those eight fences has a named pin test guarding it; the payload token refuses non-strings like its siblings; the assertion checks the complement state for real; and anyone reading the runtime sees the two deliberate-behavior comments naming this plan as the pin.

## Evaluation Criteria

**Quality dimensions:**

- coverage exactness: the coercion-rejection test is RED against current code (a non-string token is accepted today), and each characterization pin is checked RED against an ancestor checkout or a deliberate guard mutation before landing green; every new test names the residual it closes; no test duplicates an existing pin's shape.
- strictness alignment: the payload `token` fix matches its sibling fields' isinstance form; the complement assertion asserts a distinct state, not a restatement.
- no-chill: the no-action residuals stay untouched (no shared constants module, no adjacency pin, no formatting rules); the recorded decisions pin current behavior rather than changing it.

**Done when:**

- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime` exits 0 including the eight new pins.
- The Validation Commands block below exits 0 end to end.
- The em-dash gate (`scripts/check-no-em-dash.sh touched`) exits 0 on the changed tree, and the hygiene scan named by `public_hygiene_scan_script` in the user facts exits 0.

**Ship when:**

- None; test pins and two small alignments only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/execute_plan_runtime.py` (payload token strictness; the two deliberate-behavior comments)

**Tests:**

- `scripts/test_execute_plan_runtime.py` (all eight pins)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**. If the link is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- A shared constants module for the declaration problem strings (third-consumer condition unmet).
- The em-dash gate block's adjacency pin (rides the next plan amending that block).
- The tokenization semantics in `scripts/execute_plan_runtime_codex.py` (conservative by the p93 plan's Terms).

## Validation Commands

```bash
# Tasks 1-3: the eight regression pins and the coercion pin exist and the suite is green (each token below is verified absent from the test file at authoring time, so a skipped task fails its grep)
grep -qF 'test_recovery_prior_checkpoint_claim_token_mismatch_refuses' scripts/test_execute_plan_runtime.py || { echo "FAIL: fence pin 1 missing"; exit 1; }
grep -qF 'test_recovery_prior_checkpoint_claim_token_omitted_accepted' scripts/test_execute_plan_runtime.py || { echo "FAIL: fence pin 2 missing"; exit 1; }
grep -qF 'test_startup_reconciliation_closed_claim_completes' scripts/test_execute_plan_runtime.py || { echo "FAIL: fence pin 3 missing"; exit 1; }
grep -qF 'test_acceptance_nested_namesake_src_reports_shape' scripts/test_execute_plan_runtime.py || { echo "FAIL: shape pin 1 missing"; exit 1; }
grep -qF 'test_acceptance_tail_boundary_marker_body_shape' scripts/test_execute_plan_runtime.py || { echo "FAIL: shape pin 2 missing"; exit 1; }
grep -qF 'test_acceptance_same_or_earlier_marker_body_shape' scripts/test_execute_plan_runtime.py || { echo "FAIL: shape pin 3 missing"; exit 1; }
grep -qF 'test_boundary_equality_refusal_preserves_manifest_bytes' scripts/test_execute_plan_runtime.py || { echo "FAIL: boundary pin missing"; exit 1; }
grep -qF 'test_deferred_runtime_boundary_narrowing_refusal' scripts/test_execute_plan_runtime.py || { echo "FAIL: deferred-runtime pin missing"; exit 1; }
grep -qF 'test_recover_run_identity_payload_token_rejects_non_string' scripts/test_execute_plan_runtime.py || { echo "FAIL: coercion pin missing"; exit 1; }
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime || { echo "FAIL: runtime suite"; exit 1; }

# Task 1: the deliberate-behavior comments carry the pin marker
grep -qF 'deliberate behavior pinned by' scripts/execute_plan_runtime.py || { echo "FAIL: decision pin marker missing"; exit 1; }

# Negative guard: the no-action surfaces stay byte-untouched
if git diff "$(git merge-base main HEAD)" -- scripts/execute_plan_runtime_codex.py | grep -qE '^[+-]'; then echo "FAIL: tokenization semantics touched"; exit 1; fi

# Em-dash gate on the changed tree
bash scripts/check-no-em-dash.sh touched || { echo "FAIL: em dash in changed tree"; exit 1; }
```

### Task 1: Deliberate-behavior pins in the runtime

Files:

- `scripts/execute_plan_runtime.py`

Evidence:

- The Validation block's decision-pin marker grep; covers the recorded-decisions criterion.

- [x] Add a comment at the root-less classification site (around line 592-598) reading "deliberate behavior pinned by the impl-review residuals family plan: containment classification when no repository root is supplied; production paths always resolve a root", and amend the same site's docstring parenthetical that still asserts the plan-letter "identity when no repository root is supplied" wording to point at the pin [class: IMPLEMENTATION_REQUIRED]
- [x] Add the same-form comment at the refusal-display site (byte-count-only display, plus fixing the shape-1 wording from "embeds" to "exact-equality token") [class: IMPLEMENTATION_REQUIRED]

### Task 2: The eight regression pins

Files:

- `scripts/test_execute_plan_runtime.py`

Evidence:

- The Validation block's eight regression pin greps plus the coercion pin grep and the suite run; each pin names the residual it closes in its docstring.

- [x] `test_recovery_prior_checkpoint_claim_token_mismatch_refuses`: a handoff intent whose prior checkpoint record carries a mismatched claim_token refuses [class: IMPLEMENTATION_REQUIRED]
- [x] `test_recovery_prior_checkpoint_claim_token_omitted_accepted`: the same shape with the record omitting claim_token is accepted [class: IMPLEMENTATION_REQUIRED]
- [x] `test_startup_reconciliation_closed_claim_completes`: a closed claim on a requeued-pending task completes instead of quarantining [class: IMPLEMENTATION_REQUIRED]
- [x] `test_acceptance_nested_namesake_src_reports_shape`: the plan-pinned `src/reports/report.txt` nested-namesake shape (the landed variant used `other/reports/`) [class: IMPLEMENTATION_REQUIRED]
- [x] `test_acceptance_tail_boundary_marker_body_shape`: the plan-pinned marker-bearing body embedding `reports/report.txt.bak` (the landed variant was a flag-assignment token) [class: IMPLEMENTATION_REQUIRED]
- [x] `test_acceptance_same_or_earlier_marker_body_shape`: the plan-pinned marker-bearing body for the same-or-earlier carve-out (the landed variant was pure-path) [class: IMPLEMENTATION_REQUIRED]
- [x] `test_boundary_equality_refusal_preserves_manifest_bytes`: a dedicated pin test asserting the retargeted at-or-after strictness arm's refusal preserves manifest bytes (the assertion its strictly-past sibling carries) [class: IMPLEMENTATION_REQUIRED]
- [x] `test_deferred_runtime_boundary_narrowing_refusal`: a CLI-validated `--runtime <deferred-id>` pair on a legacy manifest refuses at the claim gate [class: IMPLEMENTATION_REQUIRED]

### Task 3: The two strictness alignments

Files:

- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:

- The Validation block's coercion pin grep and the suite run.

- [x] Make the `recover-run-identity` payload `token` isinstance-strict (string required) matching its sibling fields, replacing the `str()` coercion [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the vacuous `assertNotIn(..., {"claimed","launched","blocked"})` after `assertEqual(..., "closed")` with a real complement assertion (the state set without "closed" excludes the observed value, or assert the exact closed-state contract directly) [class: IMPLEMENTATION_REQUIRED]
- [x] `test_recover_run_identity_payload_token_rejects_non_string`: a non-string token payload refuses [class: IMPLEMENTATION_REQUIRED]

### Task 4: Validation execution

Files:

- none (execution-only task)

Evidence:

- The Validation Commands block, run end to end from the executing worktree root; covers every Done-when criterion.

- [x] Run the Validation Commands block end to end and record its exit 0, then run the hygiene scan named by `public_hygiene_scan_script` in the user facts over the changed tree and record exit 0 [class: REPOSITORY_TEST]
