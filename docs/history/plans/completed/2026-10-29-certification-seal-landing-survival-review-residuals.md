# Plan: Correct certification seal review residuals
Backlog origin: docs/history/backlog/2026-10-21-seal-landing-survival-review-residuals.md
Driving force: code-quality + simplicity
Plan review record: the staging series .ai-playbook/reviews/2026-10-29-plan-review-certification-seal-landing-survival-review-residuals-p09adcb6f-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 6h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-21-seal-landing-survival-review-residuals.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)

## Terms

- **Verification head**: A full commit OID supplied to a validator to pin Git-dependent checks to a specific repository state.
- **Graded refusal**: A validation result that proves a required condition failed and exits with the graded error class.
- **Indeterminate result**: A validation result whose required Git evidence could not be classified, distinct from a proven graded refusal.
- **Seal block**: One round's structured certification record in the certification seal file.
- **Legacy artifact slot**: A plan-review artifact reference parsed from an older ledger row shape.
- **Landing identity**: The matching plan, review series, seal, source worktree, and landed commit identities used by the post-squash diagnostic.
- **Receipt escalation chain**: The existing path for recording diagnostic results and append failures across the primary ledger, fallback ledger, plan closeout, and prompt log.
- **Needs-recert routing**: The maintenance selection outcome that keeps a plan dispatchable for a fresh certification pass after a graded anchor refusal over unchanged plan bytes.

## Why

The certification-seal landing plan left a mixed set of review residuals. Several affect caller-visible correctness: the staging CLI can ignore a supplied verification head outside a Git worktree, an unclassifiable Git state is reported as a graded error, and one malformed seal line makes every round appear absent. The remaining residuals leave unproven test paths, overstate implementation evidence, or repeat lifecycle instructions. The selected backlog row and its cited review record enumerate the full scope.

## Gist & Examples

Title: Correct certification seal review residuals

TLDR: Correct seal validator outcomes and proof coverage, improving code quality while removing duplicated checks and lifecycle instructions.

Before: Certification validation can ignore or misclassify edge inputs, seal parse failures look like missing records, tests leave listed paths unproven, and several plan and skill claims do not match the landed behavior.

After: Both CLIs validate verification heads consistently, graders distinguish refusal from unavailable evidence, malformed seals identify their source, targeted tests discriminate the reviewed edge cases, and lifecycle documentation matches the implementation.

Edge cases: A plan outside a Git worktree, malformed or unavailable verification OIDs, an unparseable round line, legacy ledger rows, a colliding seal with multiple hops, and a post-squash diagnostic after archive.

## Outcome

Resolve the residuals listed in the selected backlog row as one reviewable correction to certification-seal validation and its lifecycle evidence.

- Every residual is handled by an implementation change, a discriminating regression check, or a corrected claim at its named documentation surface.
- Existing valid seal records remain readable, and callers can distinguish proven failure from evidence that Git could not classify.
- The warning-only post-squash diagnostic remains warning-only, resolves review identity with the pre-archive plan path, and reaches both prescribed validators before the archive move while checking the landed post-squash state.

## Gate delta

No gate, validator, lock, ledger, required ceremony, or dispatch condition is added or removed. Existing CLI outcomes are corrected for the listed cases: ignored input becomes a reported tool error, and unclassifiable evidence becomes indeterminate.

## Assumptions

- The selected backlog row and its cited receiving-review record are the complete scope of record. Evidence: `docs/history/backlog/2026-10-21-seal-landing-survival-review-residuals.md` and `.ai-playbook/reviews/2026-10-21-certification-seal-landing-survival-code-review-r1.md`.
- The archived plan and current source files are the implementation contract to reconcile. Evidence: `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md` and the paths listed in Review Scope.
- Test additions and documentation corrections stay limited to proving or describing this seal lifecycle; no adjacent certification subsystem is added. Evidence: all residuals are anchored in the selected row.
Decision points requiring a grill: none remain.

## Evaluation Criteria

- **Correctness:** Verification-head input and Git classification produce distinct, consistent outcomes across both CLIs, and seal parse errors identify the offending line without hiding other round records.
- **Coverage:** Each previously vacuous or unproven path has a discriminating focused check that fails if the relevant CLI threading, collision family, or skip precondition regresses.
- **Documentation:** Plan completion claims, validation coverage, receipt ownership, population boundaries, and archive ordering describe the landed behavior and use one canonical procedure per shared contract.
- **Scope control:** No new gate, ledger, lock, or unrelated certification behavior is introduced.
- **Done when:** Every residual in the origin row maps to an acceptance item in these tasks, and the focused validator checks, plan readiness, and public hygiene scan pass.
- **Ship when:** No external release, deployment, or human-owned prerequisite applies.

## Review Scope

**Code and validation:**
- `scripts/corrections_record.py` (Tasks 2 and 3)
- `scripts/plan_readiness.py` (Task 2)
- `scripts/validate_review_staging.py` (Tasks 1, 2, and 3)
- `scripts/test_corrections_record.py` (Task 1)
- `scripts/test_plan_readiness.py` (Task 1)

**Documentation:**
- `agents/skills/maintenance/decisions.md` (Tasks 2 and 4)
- `agents/skills/plans/SKILL.md` (Task 4)
- `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md` (Task 4)
- `docs/history/backlog/completed/2026-10-07-corrections-graded-freshness-post-squash.md` (Task 4)
- `docs/history/certification-seal-landing-diagnostics.md` (Task 4)
- `docs/history/certification-seal-landing-diagnostic-write-failures.md` (Task 4)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 4)

## Validation Commands

```bash
set -eo pipefail
python3 scripts/validate_review_staging.py --selftest
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_corrections_record.py scripts/test_plan_readiness.py -q
python3 scripts/plan_readiness.py docs/history/plans/2026-10-29-certification-seal-landing-survival-review-residuals.md
```

### Task 1: Add failing checks for certification seal residuals

Context surface: The verification-head CLIs, shared seal parser, legacy artifact-slot reader, and the staging validator's embedded selftest fixtures.

Primary class anchors:
- `_validate_verification_head` in `scripts/corrections_record.py`, the shared verification-head checker.
- `main` in `scripts/plan_readiness.py`, the readiness CLI call path.
- `main` in `scripts/validate_review_staging.py`, the staging CLI call path.
- `parse_seal` in `scripts/corrections_record.py`, the structured seal parser.
- `_legacy_row_entry` in `scripts/corrections_record.py`, the legacy ledger-row parser.

Files:
- `scripts/test_plan_readiness.py`
- `scripts/test_corrections_record.py`
- `scripts/validate_review_staging.py`

- [x] RED: Given malformed OIDs, unavailable Git, or absent commits, expects distinct tool-error outcomes from both CLIs; given a graded refusal or unclassifiable anchor, expects the existing refusal wording or an indeterminate result as appropriate. [class: REPOSITORY_TEST]
- [x] RED: Run each CLI test in a scratch repository with pinned cwd, temporary HOME, fixture facts paths for plans and reviews inside the scratch repository, minimal PATH pinned to the intended Git and Python, and controlled or cleared `GIT_*` overrides. [class: REPOSITORY_TEST]
- [x] RED: Given a supplied verification head and a source plan outside a Git worktree, expects both CLIs to validate the supplied value rather than ignore it; given byte-identical plan bytes after a graded anchor refusal, expects the unchanged-bytes predicate used by maintenance routing to match, and given changed bytes expects it not to match. [class: REPOSITORY_TEST]
- [x] RED: Given an annotated round followed by another valid round, expects the later record to resolve. Given a malformed round beside a valid round in one file, expects the offending line named, the malformed round unresolved, and the valid round resolvable. [class: REPOSITORY_TEST]
- [x] RED: Given a request to resolve the malformed round, expects fail-closed grading; given a valid seal without a matching entry, expects absence to differ from parse failure. [class: REPOSITORY_TEST]
- [x] RED: Given a legacy artifact slot ending at the `bytes)` boundary, expects the intended path to resolve and malformed suffix fragments not to become a path. [class: REPOSITORY_TEST]
- [x] RED: Given an older matching candidate behind a candidate-read failure, expects refusal without consuming the older match; given the seal-example producer precondition is skipped, expects the check to fail and the stale clause to be reported absent from producer skills. [class: REPOSITORY_TEST]
- [x] RED: Given a plan-family collision and a threaded multi-hop verification-head case, expects the valid threaded path to emit no refusal and the unthreaded companion to refuse; each fixture must fail if its named call path or precondition is removed. [class: REPOSITORY_TEST]
- [x] Commit the focused regression checks and selftest fixtures. [class: REPOSITORY_TEST]

### Task 2: Unify verification-head checks and Git outcome classes

Context surface: The duplicated verification-head helper and both CLI call paths, plus the maintenance selection rule that consumes graded anchor refusals.

Primary class anchors:
- `_validate_verification_head` in `scripts/corrections_record.py`, the shared verification-head checker.
- `main` in `scripts/plan_readiness.py`, the readiness CLI call path.
- `main` in `scripts/validate_review_staging.py`, the staging CLI call path.

Files:
- `scripts/corrections_record.py`
- `scripts/plan_readiness.py`
- `scripts/validate_review_staging.py`
- `agents/skills/maintenance/decisions.md`

- [x] Move verification-head validation to one shared helper in `scripts/corrections_record.py`; both CLIs call it for every supplied value, including when the source plan is outside a Git worktree. [class: IMPLEMENTATION_REQUIRED]
- [x] Report malformed OIDs, unavailable Git, and absent commits as distinct tool-error reasons in both CLIs, while preserving the existing refusal wording for the graded checks. [class: IMPLEMENTATION_REQUIRED]
- [x] Route the unclassifiable commit-object anchor leg to the indeterminate result, and constrain needs-recert routing and its claim to graded anchor refusals over byte-identical plan bytes. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove the outcome-redundant top-level probe or document the distinct result it is required to establish; remove the unreachable family conjunct unless its reachability is demonstrated. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the shared helper and CLI outcome changes. [class: IMPLEMENTATION_REQUIRED]

### Task 3: Preserve usable seal records and diagnose malformed inputs

Context surface: The shared seal parser and the legacy artifact-slot reader in `corrections_record.py`, with the staging validator's caller-facing warning.

Primary class anchors:
- `parse_seal` in `scripts/corrections_record.py`, the structured seal parser.
- `_legacy_row_entry` in `scripts/corrections_record.py`, the legacy ledger-row parser.

Files:
- `scripts/corrections_record.py`
- `scripts/validate_review_staging.py`

- [x] Distinguish a malformed seal entry from a valid file with no resolving entry, identify the offending line, keep the malformed round unresolvable while preserving unrelated valid round entries in the same file, and fail closed when resolution depends on the malformed round. [class: IMPLEMENTATION_REQUIRED]
- [x] Tighten or normalize legacy artifact-slot extraction so valid historical rows resolve their intended artifact and malformed suffix fragments cannot silently become an artifact path. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep valid current and legacy seal records compatible, and preserve the staging validator's existing fail-closed posture while making its warning distinguish parse failure from absence. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the seal parser and legacy extraction changes. [class: IMPLEMENTATION_REQUIRED]

### Task 4: Correct certification claims and single-home lifecycle guidance

Context surface: The archived source plan, its originating backlog witness, the receipt ledgers, the maintenance D1 selection rule, and the plans skill's landing lifecycle.

Files:
- `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md`
- `docs/history/backlog/completed/2026-10-07-corrections-graded-freshness-post-squash.md`
- `docs/history/certification-seal-landing-diagnostics.md`
- `docs/history/certification-seal-landing-diagnostic-write-failures.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/decisions.md`
- `docs/history/backlog/PLAN-PROMPTS.md`

- [x] Reword the archived completion claim to describe the files that actually received byte deletions, and correct the focused-suite coverage sentence, post-landing deferral boundary, and degraded-grading term to match the landed text. [class: IMPLEMENTATION_REQUIRED]
- [x] Compress the post-squash diagnostic witness to its canonical lifecycle pointer, and single-home the receipt escalation chain with concise links from its consumers. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove the duplicate informational override wording, document both the legacy-row extraction boundary and the `round_start_digest` auto-recovery population boundary (graded-correction-modified plans route through needs-recert), and keep that maintenance selection claim limited to graded anchor refusals over byte-identical plan bytes. [class: IMPLEMENTATION_REQUIRED]
- [x] Order the warning-only diagnostic so it resolves review identity against the pre-archive plan path and reaches both validators before archive move while still checking post-squash state; preserve the existing outcome matrix and append-only receipt contract. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify each documentation claim against its owning procedure and commit the focused edits. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

Origin row docs/history/backlog/2026-10-21-seal-landing-survival-review-residuals.md (deleted at archive per the covered-row convention); every residual below landed in this plan's tasks:

- Task 1 (RED checks, cb35d09c4): C4 (older matching candidate staged behind the read failure), T3 + D7 (fail-loud skip arms and the stale-clause negative sweep), T5 (plan-family-over-colliding-seal selftest integration arm), r2-F1 (multi-hop threaded discriminator with refusal-absence arms).
- Task 2 (verification-head unification, 2667ec0cd): C2 (staging supplied-head validation hoisted out of the worktree guard), C3 (unclassifiable commit-object anchor routed to indeterminate exit 2 in both CLIs), D1 (shared validate_verification_head in corrections_record.py), D2 (outcome-redundant toplevel probe removed), D3 (unreachable family conjunct removed with comment), R4 (distinct tool-error reasons per condition), CD3 (needs-recert claim narrowed to graded anchor refusals over byte-identical plan bytes).
- Task 3 (seal parser, 3e687634e): C8 (malformed rounds fail closed with the offending line named; unrelated rounds keep resolving; absence kept distinct), R2 (legacy artifact slot normalized at the bytes) boundary).
- Task 4 (docs claims, 4b7e2982b): C1 (completion claim reworded to the files that actually received byte deletions), T2 (coverage sentence narrowed to the suite-exercised predicate), T4 (deferral boundary recorded beside the matrix-destination clause), D4 (post-squash witness compressed to the canonical pointer), D5 (receipt escalation chain single-homed in the write-failures ledger), D6 (remaining interactive-override twins removed), R3 (round_start_digest auto-recovery population boundary documented), r2-F2 (degraded-grading term re-synced).
- L1 (landing witness): diagnostic ordering landed in the plans skill (runs before the archive move, resolving review identity at the pre-archive active path while Git-side checks still verify post-squash state).
