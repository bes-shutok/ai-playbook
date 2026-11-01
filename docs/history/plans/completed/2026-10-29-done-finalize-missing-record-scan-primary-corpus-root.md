# Plan: Root the finalize review scan at the primary checkout

Backlog origin: docs/history/backlog/2026-10-29-done-finalize-missing-record-scan-primary-corpus-root.md
Driving force: simplicity
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-done-finalize-missing-record-scan-primary-corpus-root[-p<identity-token>]-r*.md
Execution budget: 1.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-29-done-finalize-missing-record-scan-primary-corpus-root.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms

- **Primary checkout:** the canonical repository checkout listed first by `git worktree list --porcelain`.
- **Running checkout:** the checkout whose `done_run.sh finalize` invocation is producing the scan.
- **Reviews corpus:** the gitignored review-record directory configured by `reviews_dir` in `.ai-playbook/facts.md`.

## Why

The finalize scan reports review records cited by archived plans when it cannot find their basenames in the configured reviews corpus. In a worktree, the current relative-path resolution points at the worktree's partial copy. A witnessed run reported 72 missing records there, while re-running the scan at the primary checkout reported 18, including fixture-shaped citations. This plan makes the scan consult the canonical corpus and identify the root it used, while preserving the report-only behavior and the tracked completed-plan scan.

## Gist & Examples

TLDR: Resolve the relative reviews corpus from the primary checkout and print its root, improving clarity through simplicity.

Before, a worktree finalize scans its partial reviews copy and can over-report missing records.

After, the scan reads the canonical primary-checkout corpus for relative `reviews_dir` values and prints the resolved corpus root beside its count.

When `reviews_dir` is absolute, keep that configured path. Keep `plans_completed_dir` rooted at the running checkout because its tracked files are present in every worktree.

Fixture-shaped citations remain visible in the report-only count; the scan stays advisory and never blocks or fabricates review records.

## Outcome

A worktree finalize reports missing review records based on the same canonical reviews corpus available to the primary checkout, and its summary names the corpus root used.

- Relative `reviews_dir` values resolve from the primary checkout already derived by the scan.
- Absolute `reviews_dir` values and the running-checkout resolution for `plans_completed_dir` retain their current behavior.
- The wrapper test proves a record present in the primary corpus is not reported missing merely because the worktree copy lacks it.

Gate delta: no gate, validator, lock, ledger, schema, ceremony, or dispatch pause is added, removed, or changed; the existing report-only scan remains report-only.

## Assumptions

- The first checkout from `git worktree list --porcelain` remains the primary checkout, matching the scan's existing fallback resolution. Basis: `scripts/done_run.sh` and the worktree standard.
- `reviews_dir` values are normally relative to a checkout; absolute values retain their current meaning. Basis: `.ai-playbook/facts.md` and the existing `facts_rooted` helper.
- Fixture-shaped citations remain reportable because the primary re-derivation observed them and no harm from that noise is recorded. Basis: the origin backlog evidence.

Decision points requiring a grill: none remain. Maintenance-selected receipt: accept the origin's two scope arms; preserve absolute values, the tracked completed-plan root, and report-only behavior; omit a name-exclusion arm because no witnessed harm exists. Source: the origin's Suggested investigation and EXEC-PROMPTS entry, 2026-10-29.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: a worktree run resolves a relative reviews corpus at the primary checkout and does not report records that exist there solely because the worktree copy is partial.
- Compatibility: absolute `reviews_dir` values, tracked `plans_completed_dir` resolution, and the non-blocking scan behavior remain unchanged.
- Clarity: the scan summary reports the resolved reviews corpus root.

**Done when:**
- The wrapper suite covers a linked-worktree run with a deliberately partial reviews copy and a matching record in the primary corpus.
- The focused test passes and the scan output identifies the primary corpus root.

**Ship when:**
- None; this changes repository-owned closeout reporting only.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/done_run.sh` (Task 1)

**Tests:**
- `scripts/test_done_run_wrapper.py` (Task 1)

**Plan-related extension:** implementation and review may adjust the fixture setup needed to represent a linked worktree and a partial transfer-in copy, while retaining the same assertions about report-only behavior. The run scope also includes `scripts/test_invocation_telemetry.py` for the `_FINALIZE_SCAN_TAIL` re-baseline the summary-suffix change requires (lesson 343 scope record).

**Out of scope; reject unless plan-related:**
- `docs/maintenance/development_lessons.md`; reason: lesson 74 already states the canonical-home rule used by this change.
- Review-record name exclusions; reason: fixture-shaped citations are known report-only noise and no harm is witnessed.
- Any gate or refusal tied to this advisory scan; reason: the existing scan is explicitly non-blocking.

## Validation Commands

Run from the repository root:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/done_run.sh scripts/test_done_run_wrapper.py
bash scripts/scan-public-hygiene.sh --files scripts/done_run.sh scripts/test_done_run_wrapper.py
```

### Task 1: Resolve the reviews corpus from the primary checkout

Context surface: the plan's Terms and the `missing-review-record-scan` block in `scripts/done_run.sh`.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `facts_rooted` in `scripts/done_run.sh`
- `test_finalize_reports_missing_review_records_report_only` in `scripts/test_done_run_wrapper.py`

Evidence:
- The scan derives the primary checkout but currently joins the relative `reviews_dir` to the running checkout (`scripts/done_run.sh`, `missing-review-record-scan`).
- The primary checkout's reviews home is canonical for a shared gitignored corpus, while a worktree transfer-in can be partial (development lesson 74).
- The existing wrapper fixture asserts that a missing-record report does not block or fabricate records (`scripts/test_done_run_wrapper.py`).

- [x] Resolve a relative `reviews_dir` from the primary checkout; preserve the existing handling of an absolute value and keep `plans_completed_dir` rooted at the running checkout. [class: IMPLEMENTATION_REQUIRED]
- [x] Include the resolved reviews corpus root in the scan summary while preserving the report-only warning and no-fabrication behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a linked-worktree fixture where a cited review exists only in the primary corpus; assert no missing-record warning and print the primary root. [class: REPOSITORY_TEST]
- [x] Add an absolute `reviews_dir` fixture where the cited review exists only in the configured alternate corpus; assert no missing-record warning and print that root. [class: REPOSITORY_TEST]
- [x] Add a completed-plan fixture where the cited plan exists only under the running checkout; assert its citation is scanned and the warning remains report-only. [class: REPOSITORY_TEST]
- [x] Commit: `fix: root finalize review scan at primary checkout` [class: IMPLEMENTATION_REQUIRED]

## Disposition of the origin row

Origin row docs/history/backlog/2026-10-29-done-finalize-missing-record-scan-primary-corpus-root.md deleted per the covered-row rule when this plan archived (2026-11-01, landing of this completed twin). Both scope arms landed: the relative reviews corpus roots at the primary checkout with the corpus root printed in the summary; absolute values and the running-checkout-rooted plans_completed_dir kept their behavior; no name-exclusion arm added (report-only noise, no witnessed harm). Residuals: watchlist notes on the telemetry pin's format-only protection and pre-existing facts_rooted spelling/tilde classes (see the r2 review record).
