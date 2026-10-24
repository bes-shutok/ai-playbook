# Plan: Align Done Plan-Readiness Exemption and Child Diagnostics

Backlog origin: docs/history/backlog/2026-10-18-done-plan-readiness-child-tool-error.md
Driving force: simplicity + reliability
Plan review record: .ai-playbook/reviews/2026-10-24-plan-review-done-plan-readiness-child-tool-error-r*.md
Execution budget: 1.5h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-18-done-plan-readiness-child-tool-error.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Active manifest exemption:** The existing time-bounded rule that excludes a plan from the done readiness sweep while its execute-plan manifest is actively owned.
- **Feature slug:** The canonical plan directory name produced by `plan_readiness.feature_slug`, without the plan date prefix.
- **Child diagnostic:** The bounded excerpt from the `plan_readiness.py` subprocess output reported when it exits without a final `OUTCOME` record.

## Why

The composed done sweep constructs an active-manifest path with a dated plan stem, while the manifest is stored under the canonical feature slug. When the readiness child crashes without an `OUTCOME`, the gate can also report only a traceback header instead of actionable exception evidence.

## Gist & Examples

TLDR: Reuse canonical plan slug lookup and retain useful child crash evidence, improving reliability through simpler shared behavior.

Before: A plan such as `2026-10-17-archive-ceremony-review-evidence-mismatch.md` looks for a manifest under a directory that includes `2026-10-17-`, so composed readiness can miss the fresh active manifest that direct candidate derivation recognizes. A child that prints a traceback header and exits 1 without `OUTCOME` can be reduced to that header in the gate report.

After: Both paths use the canonical feature slug to find the same manifest and verify that its recorded `plan_path` is the exact candidate. When a child exits without `OUTCOME`, the gate keeps its tool-error classification and reports a diagnostic excerpt of at most 200 characters, retaining the useful end of traceback output when available.

Edge cases: Absent, stale, inactive, unrelated, or same-slug wrong-path manifests stay candidates; a missing child `OUTCOME` remains a tool error and emits at most 200 characters of diagnostic evidence.

## Outcome

The done plan-readiness sweep makes the same active-manifest exemption decision as direct candidate derivation and exposes useful evidence for a validator child failure.

- Fresh active manifests are recognized for date-prefixed plan paths.
- Absent, stale, inactive, unrelated, or same-slug wrong-path manifests do not gain an exemption.
- A missing child `OUTCOME` remains a tool error and stale review digests remain refused for non-exempt candidates.

Gate delta: no gate, refusal class, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition is added or removed; existing exemption and tool-error behavior are corrected; no blocking review-layer duty is added.

## Assumptions

- Reuse `plan_readiness.feature_slug()` as the canonical manifest path source; basis: it is already imported and used by direct candidate derivation, and the live probe confirmed that `_manifest_exempts` retains the date prefix.
- Preserve the active-state and freshness criteria while requiring exact `plan_path` ownership; basis: the backlog records the exemption as intentional, and execute-plan manifests bind an exact repository-relative plan path.
- Bound and prioritize diagnostic evidence without changing the child exit classification; basis: the origin requests the exception evidence and expects `tool_error`, not a modeled stale-review result.
- Maintenance-selected decision receipt: fix the lookup path and child diagnostic while retaining both the exemption and digest check; source: the origin's Expected, Origin assessment, and live probes; date: 2026-10-24; affected sections: Outcome, Evaluation Criteria, Tasks, Validation Commands.
- Sources inspected: the origin and related plan-digest handoff row; `done_sweep_gates_lib.py`; `plan_readiness.py`; focused gate tests; completed `2026-09-04-done-deliverables-log-dedupe-and-anchors.md`; live synthetic probes.
Decision points requiring a grill: Reuse the feature-slug helper and retain the exemption plus digest check; source: origin Expected and live reproduction; date: 2026-10-24; affected sections: Outcome, Evaluation Criteria, Tasks.

## Evaluation Criteria

- **Candidate parity:** Direct derivation and composed sweep recognize a fresh active manifest for the same dated plan path.
- **Exemption boundaries:** Missing, stale, inactive, and unrelated manifests remain candidates; ordinary candidates still fail when their review digest is stale.
- **Crash evidence:** A child exit without `OUTCOME` remains a tool error and reports useful bounded stderr/stdout evidence rather than only an uninformative traceback header.
- **Scope:** Existing readiness checks and manifest lifecycle remain unchanged.

**Done when:** focused regression cases for manifest lookup and missing-OUTCOME diagnostics pass with the existing done-sweep gate suite; no-em-dash and public-hygiene scans pass for changed files.

**Ship when:** this plan lands and its backlog origin is archived as covered.

## Review Scope

**Explicit must-fix:** Findings on these paths are always in scope.

**Production code:**
- `scripts/done_sweep_gates_lib.py` (`_manifest_exempts` path construction and `gate_plan_readiness` missing-OUTCOME diagnostic selection only)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (focused plan-readiness candidate and subprocess diagnostic tests only)

**Plan-related extension:** Other changes are in scope only when needed to preserve parity, exemption boundaries, tool-error classification, or diagnostic bounds.

**Out of scope:**
- `scripts/plan_readiness.py`; its digest validation and canonical feature-slug helper remain authoritative.
- Execute-plan manifest creation, state transitions, freshness window, or ownership semantics.
- General checkbox-to-review digest handoff work owned by `2026-10-10-execute-plan-plan-digest-handoff-drift.md`.
- Any new gate, validator, lock, ledger, schema field, or required ceremony.

## Validation Commands

Run from the repository root:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest -q scripts/test_done_sweep_gates_lib.py
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh --files scripts/done_sweep_gates_lib.py scripts/test_done_sweep_gates_lib.py
```

The regression matrix must cover a dated plan path with a fresh active manifest at the canonical slug and exact `plan_path`, plus a different dated plan with the same slug; absent, stale, inactive, and unrelated manifests remain candidates. Direct and composed derivation must agree, and a non-exempt candidate with a stale source digest remains refused. For child diagnostics, cover a traceback wholly on stderr, traceback on stdout with a useful stderr message, plain stderr evidence, empty output, and a detail longer than 200 characters; assert the useful exception detail, the 200-character maximum, and unchanged tool-error classification.

### Task 1: Align active-manifest lookup with canonical plan slug

Context surface: Terms, Outcome, Assumptions, Evaluation Criteria; origin Expected and Evidence; existing direct candidate derivation and manifest tests.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `PlanReadinessDerivation` in `scripts/done_sweep_gates_lib.py`

- [ ] Resolve the manifest directory with `plan_readiness.feature_slug(plan_rel)` and exempt only when its recorded repository-relative `plan_path` exactly matches `plan_rel`; keep active-state and freshness checks. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add parity coverage: a fresh active manifest at the canonical slug and exact plan path exempts the same dated candidate in direct derivation and the composed sweep. [class: REPOSITORY_TEST]
- [ ] Add boundary coverage: absent, stale, inactive, unrelated, and same-slug wrong-path manifests do not exempt the candidate; stale review digests remain refused for candidates. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the fresh-active-manifest dated-path regression fails against the current date-prefixed lookup. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: focused parity and boundary cases pass with existing manifest cases. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: align done active manifest lookup` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Preserve useful evidence for readiness child crashes

Context surface: Terms, Outcome, Assumptions, Evaluation Criteria; origin's done-boundary result and the gate's current missing-OUTCOME branch.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `GateResult` in `scripts/done_sweep_gates_lib.py`

- [ ] When child output has no final `OUTCOME`, select the final non-empty detail from a traceback stream, retain current useful plain stderr selection, cap evidence at 200 characters, and preserve tool-error classification. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add subprocess fixtures for traceback wholly on stderr, stdout traceback plus useful stderr, plain stderr, empty output, and oversized detail; assert useful evidence, the 200-character cap, and unchanged tool-error classification. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: a traceback wholly on stderr reports its header instead of its final exception detail under current selection. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: all diagnostic fixtures pass and the existing gate suite remains green. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: retain readiness child crash detail` [class: IMPLEMENTATION_REQUIRED]
