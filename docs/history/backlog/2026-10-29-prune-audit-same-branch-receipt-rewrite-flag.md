# Backlog: prune audit flags a same-branch receipt-line rewrite as RECEIPT-LINE-REMOVED-WITHOUT-WITNESS although the net branch diff only adds the line

- **Filed:** 2026-10-29
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** the landing prune-audit leg (`scripts/check_prompt_log_origins.py --prune-audit`), the pure receipt-line-removal class and its same-commit retoken excusal
- **Cluster:** docs/history/plans/completed/2026-10-28-landing-gate-prune-audit-leg.md (the leg's own landing plan; the removal classes and their excusals live there)
- **Cluster:** docs/history/backlog/2026-10-24-collateral-served-nul-origin-uncaught-valueerror.md (same checker surface scripts/check_prompt_log_origins.py; distinct defect: that row's uncaught ValueError in --collateral-served vs this row's receipt-line flag semantics)
- **Skill/step:** `scripts/check_prompt_log_origins.py`, the receipt-line-removal audit class
- **Class:** diagnostic-class
- **Origin class:** session witness (interactive exec run, ad-hoc landing, 2026-10-29)

## Finding

During the 2026-10-29 ad-hoc exec run's first pick landing (2331ebe8), the wired prune-audit leg flagged `RECEIPT-LINE-REMOVED-WITHOUT-WITNESS` for the branch's receipt line: an earlier branch commit added the `EXEC-PROMPTS-PRUNE` line and a later fold commit reworded it, and the flag named the rewriting commit. The branch's net diff only ever adds the line once; nothing was lost from the log. Squashing the riders and fold commits onto the implementing commit (`git reset --soft`, one re-commit) left a single adding commit and the re-run reported PRUNE-OK, so the landing proceeded with the recomposed branch.

The flag's precise trigger was not re-derived from the run: the checker's receipt-line class carries a same-commit retoken excusal (a commit that removes a receipt line and re-adds one for the same slug is excused), and the witnessed rewrite was a same-commit remove-and-re-add by slug, so the excusal should have applied. Which parse path defeated it (slug normalization, the token pair extraction, or an intermediate state shaped differently than remembered) is unresolved; the pre-squash branch commits survive only in the reflog.

## Expected

Either the flag is intended per-commit-state policing (a branch must not mutate a receipt line mid-branch, which the composition discipline in development_lessons.md #301 now states as practice) and this row closes works-as-designed citing that lesson, or branch-internal introductions are a false-positive shape the retoken excusal was meant to cover and the parse path needs a fix. The diagnostic decides which, from a reproduction, before any checker change.

## Suggested direction

Reproduce on a fixture branch: commit A adds a receipt-ledger line, commit B rewrites its wording in place; run `--prune-audit --base`. If it flags, bisect the excusal conditions in the receipt-line class (`_line_removals`, `newly_added_receipt_pairs`, `receipt_compare_slug`) against the fixture's exact bytes. Land at most a targeted excusal widening or a documentation note; no new gate, and the machinery admission line rides the fixing change if one is filed.

## Evidence

- Witnessed 2026-10-29 during the pick 1 landing window (landing 2331ebe8 carries the final single-commit receipt form; the run's review record `.ai-playbook/reviews/2026-10-29-zero-plan-branch-only-migration-manifest-adhoc-code-review-r2.md` holds the final reviewed digest).
- The excusal sites: `scripts/check_prompt_log_origins.py`, the pure receipt-line-removal loop (the `retoken shape` comment and the `RECEIPT-LINE-REMOVED-WITHOUT-WITNESS` emission).
