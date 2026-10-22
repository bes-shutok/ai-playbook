# Plan: Scope Done Sensitive-Content Scanning by Private Visibility

Backlog origin: docs/history/backlog/2026-10-23-done-sensitive-scan-private-repository-scope.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-23-plan-review-done-sensitive-scan-private-repository-scope-r*.md
Execution budget: 1.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-23-done-sensitive-scan-private-repository-scope.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Content families:** The credential and public-artifact pattern lists used by the staged-diff and untracked-file scan arms.
- **Explicit private visibility:** `artifact_visibility` resolves to the exact value `private`, case-insensitively, through `GateContext.artifact_visibility`.
- **Non-content arms:** The push-range commit-message audit and skills-repository public-hygiene scan in `gate_sensitive_data_scan`.

## Why

A private consumer repository was blocked by public-artifact patterns even though its facts marked the repository private. The gate currently requires a pet project for that visibility value to affect its content checks, leaving a false rejection for missing or unrecognized project types.

## Gist & Examples

TLDR: Let explicit private visibility skip both content families, fixing false rejections while preserving unrelated closeout protections through better code quality.

Before: A repository with `artifact_visibility = "private"` but no recognized `project_type` fails when a staged or untracked file contains a normal internal tracker link or local path. The strict scan also runs for a malformed or absent visibility value.

After: Exact private visibility skips both content families for any project type. A public, missing, malformed, or unrecognized visibility value keeps both families active. The commit-message and skills-repository hygiene arms continue to run for private repositories.

## Outcome

The done sensitive-data gate uses explicit private visibility alone to decide whether its staged and untracked content scans run.

- Private repositories with missing or unrecognized project types pass content that currently triggers a false positive.
- Repositories without an explicit private visibility value retain strict scanning for both content families.
- Commit-message attribution and skills-repository hygiene protections remain active for private repositories.

Gate delta: no gate, refusal class, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition is added or removed; the existing content-scan predicate is narrowed to exact private visibility and its old company-without-private exemption is removed; no blocking review-layer duty is added.

## Assumptions

- The `artifact_visibility` parser remains the source for the exemption and retains its exact case-insensitive match; no facts or bootstrap contract change is needed.
- Company profiles without explicit private visibility become strict, consistent with the origin's visibility-only expected behavior.
- The existing credential and public-artifact pattern lists remain unchanged; only whether arms 1 and 2 consume them changes.
- Arms 3 and 4 remain active for all profiles, including private repositories.
- Maintenance-selected decision receipt: choose the explicit-visibility-only exemption for both content families; source: the 2026-10-23 origin's Expected and Suggested direction, its four-option prompt, and the witnessed private-consumer false rejection; date: 2026-10-23; affected sections: Outcome, Evaluation Criteria, Tasks, Review Scope.
- Sources inspected: the 2026-10-23 origin; `GateContext` and `gate_sensitive_data_scan`; visibility-scoped, push-range, and hygiene-child tests; the completed 2026-10-12 profile-boundary plan and its predecessor origin in the parent of commit `a00267d55`; `docs/AGENTS.md`'s public-pet artifacts policy sentence.
Decision points requiring a grill: Select the explicit-visibility-only exemption for both content families; source: the 2026-10-23 origin Expected and prompt; date: 2026-10-23; affected sections: Outcome, Evaluation Criteria, Tasks, Review Scope.

## Evaluation Criteria

- **Correctness:** Private visibility skips both content families for recognized, missing, and unrecognized project types; the result reports that the content arms were skipped because visibility is private.
- **Strictness:** Public, absent, malformed, and unrecognized visibility values keep both families active and retain positive staged and untracked findings.
- **Preservation:** Private-profile tests still observe the push-range attribution finding and the skills-repository hygiene child outcome.
- **Compatibility:** Pattern constants, the attribution prohibition, employer-brand matching, hygiene behavior, and facts/bootstrap collection remain unchanged.
- **Scope:** Only the existing gate, its focused tests, and the directly related shared policy sentence change.

**Done when:** the focused gate suite passes; the visibility matrix and both non-content-arm private witnesses pass; existing strict-scan controls pass; public-hygiene and no-em-dash scans pass for changed files.

**Ship when:** the plan is implemented and reviewed, and the origin row is archived as covered by this plan after landing.

## Review Scope

**Explicit must-fix:** Findings on the paths below are always in scope.

**Production code:**
- `scripts/done_sweep_gates_lib.py` (`GateContext.artifact_visibility` documentation, the `gate_sensitive_data_scan` exemption predicate and result message, and the profile comment above the pattern constants only; all other methods and gate behavior are frozen)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (the visibility-scoped tests and the existing push-range and hygiene-child witnesses only; all other tests are frozen)

**Documentation:**
- `docs/AGENTS.md` (the public-pet artifacts policy bullet only; all other guidance is frozen)

**Plan-related extension:** Other findings are in scope only when they implement this visibility contract, preserve the non-content arms, or correct a regression caused by the plan.

**Out of scope:**
- `agents/skills/bootstrap-ai-playbook/SKILL.md`; the origin and selected scope call for consuming explicit visibility in the existing gate, not changing the facts interview or adding a field.
- `scripts/facts_paths.py`; its TOML resolution is already used by `GateContext.artifact_visibility` and remains unchanged.
- `scripts/scan-public-hygiene.sh`; the gate's child behavior is preserved and exercised, not changed.
- The completed profile-boundary plan and historical origins; cited as evidence, not edited.
- Any new gate, bypass, classification, or persistent machinery.

## Validation Commands

Run from the repository root:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest -q scripts/test_done_sweep_gates_lib.py -k "visibility_scoped or push_range_audit or hygiene_child"
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh --files scripts/done_sweep_gates_lib.py scripts/test_done_sweep_gates_lib.py docs/AGENTS.md
```

The focused visibility selector must exercise private visibility with missing and unrecognized project types, recognized pet and company types, and public, missing, malformed, and unrecognized visibility. Retain positive staged and untracked findings for strict states, and assert both content families remain active. In private-profile fixtures, assert the push-range audit still rejects a `Co-authored-by` trailer and the hygiene child still runs and reports its outcome. Confirm the result message distinguishes private content-arm skipping from strict scanning.

### Task 1: Base both content arms on explicit private visibility

Context surface: this plan's Terms, Outcome, Assumptions, and Evaluation Criteria; the origin's Expected and Evidence sections; the completed 2026-10-12 profile-boundary plan's Outcome and Edge cases.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `docs/AGENTS.md`

Primary class anchors:
- `GateContext` in `scripts/done_sweep_gates_lib.py`
- `gate_sensitive_data_scan` in `scripts/done_sweep_gates_lib.py`

- [ ] `gate_sensitive_data_scan` skips both staged-diff and untracked-file content matching when `artifact_visibility` resolves to `private`, with no dependency on `project_type`; given private facts with `project_type` absent or unrecognized and matching staged public-artifact plus untracked credential content, expects a clean result that names private visibility as the reason. [class: IMPLEMENTATION_REQUIRED]
- [ ] Visibility matrix: given private visibility with pet, company, absent, or unrecognized `project_type`, expects both content families skipped; given public, absent, malformed, or unrecognized visibility, expects both families to remain active and matching staged or untracked content to fail. [class: REPOSITORY_TEST]
- [ ] Positive strict-scan witnesses: given strict visibility with public-artifact content in a staged file and credential content in an untracked file, expects findings from both content families; retain strict pet and company controls where their visibility is not explicitly private. [class: REPOSITORY_TEST]
- [ ] Non-content safety witness for arm 3: given a private repository with no recognized project type and a pushed commit whose message contains a `Co-authored-by` trailer, expects the gate to fail on the attribution finding. [class: REPOSITORY_TEST]
- [ ] Non-content safety witness for arm 4: given a private repository configured as the skills repository and a hygiene child that reports a finding, expects the child finding to reach the gate result. [class: REPOSITORY_TEST]
- [ ] The `GateContext.artifact_visibility` documentation, gate comment, result message, and shared policy sentence describe the same rule; keep both pattern families, employer-brand and attribution checks, and hygiene scan behavior unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: the revised private-with-missing/unrecognized-type witnesses fail against the current company/private-pet predicate. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the focused visibility, push-range, and hygiene-child selector passes with strict and preserved-arm controls. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: scope done content scan to explicit private visibility` [class: IMPLEMENTATION_REQUIRED]
