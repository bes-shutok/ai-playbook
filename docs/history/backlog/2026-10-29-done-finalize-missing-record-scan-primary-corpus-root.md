# Done finalize's missing-review-record scan must root its corpus home at the primary checkout

- **Filed:** 2026-10-29, learn over the 2026-10-28 21:39 exec run
- **Status:** covered (docs/history/plans/2026-10-29-done-finalize-missing-record-scan-primary-corpus-root.md)
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** closeout advisory correction (report-only scan over-report witnessed in a worktree finalize, re-derived at the primary)
- **Class:** fix-class (a script-internal checkout-relative facts resolution audits a partial corpus copy)
- **Driving force:** simplicity
- **Surface:** `scripts/done_run.sh` finalize, the report-only missing-review-record scan (trace_stage `missing-review-record-scan`); operating rule recorded as the canonical-home direction arm of development_lessons.md #74
- - **Cluster:** docs/history/backlog/2026-10-31-done-finalize-manifest-leg-refuses-after-worktree-removal.md (same done finalize manifest/teardown ordering surface; the open origin of the family's diagnosability entry)
**Environment context:** this repository's done closeout flow; witnessed 2026-10-28 in an ad-hoc worktree finalize, re-derived 2026-10-29 at the primary checkout
- **Dedup probe:** searched open backlog filenames and bodies for missing-review-record, missing review record, and reconstruction duty; no existing row covers the scan's corpus-root resolution or the over-report class. Nearest rows cover done advisory sentence pinning and receipt-loss reconciliation; neither touches this scan.

## Problem

The finalize scan resolves `reviews_dir` from `.ai-playbook/facts.md`; the facts value is checkout-relative, and the scan's `facts_rooted` joins it to `repo_top`, the checkout `done_run.sh` runs in. In an ad-hoc worktree finalize that is the worktree root, so the scan consults the worktree's transfer-in partial reviews home instead of the canonical corpus: every record name cited by an archived plan but absent from the partial copy is reported missing. The 2026-10-28 run's finalize reported 72 missing records on that basis, and the run carried that number into `.ai-playbook/scheduler-state.json` as an advisory witness. Re-running the scan verbatim at the primary checkout reports 18, several of which are fixture-shaped names embedded in archived plans' text and missing by construction. The scan is report-only by design, so the harm is advisory noise and a misleading durable witness, not a blocked run.

Expected behavior: a scan over the canonical reviews corpus roots that corpus at the primary checkout. The scan already derives the primary from `git worktree list --porcelain` for its fallback branch; the facts-relative branch should root there too. `plans_completed_dir` can stay rooted at the running checkout because archived plans are tracked content present in every checkout.

## Suggested investigation

Root the facts branch of `reviews_dir` (and any other gitignored-home facts value the scan consults) at the derived primary checkout. Decide whether the fixture-shaped false positives warrant a name-exclusion arm or stay report-only noise. Consider annotating the scan's output line with the corpus root it consulted, so a future reader can tell a partial-copy over-count from a real gap without re-deriving the resolution.

## Evidence

- 2026-10-29 re-derivation at the primary checkout, scan logic copied verbatim from `scripts/done_run.sh`: the corpus resolves to the primary checkout's `.ai-playbook/reviews/` (8777 files) and the scan reports 18 missing records; first hits include `2026-04-01-foo-plan-review-r1.md` and `2026-09-01-plan-review-fixture-r1.md`, cited by archived plans as fixture text.
- 2026-10-28 run witness: the worktree finalize reported 72 missing records; the number is carried in `.ai-playbook/scheduler-state.json` (note ts 2026-10-28T23:05:00+00:00), annotated with this correction on 2026-10-29.
