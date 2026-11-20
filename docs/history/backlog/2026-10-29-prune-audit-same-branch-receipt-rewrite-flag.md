# Backlog: prune audit flags a same-branch receipt-line rewrite as RECEIPT-LINE-REMOVED-WITHOUT-WITNESS although the net branch diff only adds the line

- **Filed:** 2026-10-29
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** the landing prune-audit leg (`scripts/check_prompt_log_origins.py --prune-audit`), the pure receipt-line-removal class and its same-commit retoken excusal
- **Cluster:** docs/history/plans/completed/2026-10-28-landing-gate-prune-audit-leg.md (the leg's own landing plan; the removal classes and their excusals live there)
- **Cluster:** docs/history/backlog/2026-10-24-collateral-served-nul-origin-uncaught-valueerror.md (same checker surface scripts/check_prompt_log_origins.py; distinct defect: that row's uncaught ValueError in --collateral-served vs this row's receipt-line flag semantics)
- **Cluster:** docs/history/backlog/2026-11-01-prune-audit-standing-flags-unowned-accumulation.md (same checker; distinct class: that row owns the standing true-positive flag accumulation and its missing repair route, this row owns the net-add rewrite false positive)
- **Cluster:** the collateral sibling-receipt deletion class was closed by the warning-only COLLATERAL-RECEIPT-REMOVAL arm (landing 618565f8f, diagnostic verdict undetected; the origin row 2026-11-17-prune-audit-collateral-sibling-receipt-deletion-undetected.md was deleted per the covered-row rule)
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

## Witness extension 2026-11-16 (interactive exec run, landed-receipt rewrite class)

An interactive exec run's follow-up commit rewrote a receipt line already landed on main (clarifying the reconcile closure receipt's inventory arithmetic) and the landing refused `RECEIPT-LINE-REMOVED-WITHOUT-WITNESS` against that rewriting commit, matching this row's flag class on the LANDED side of the same checker surface: the same-commit retoken excusal did not apply because the re-added line carried new tokens (the clarifications), so the commit held a removal without a same-slug retoken. With the removal commit immutable on main, the squash remedy from the Finding was unavailable; the working shape was additive: an `EXEC-PROMPTS-RECEIPT-RIDER: <slug>` line appended beside the landed receipt (the landed line byte-unchanged) passed the audit as a pure addition. A second surface witness in the same run: the first rider landing missed its own append because the append was unstaged when `git commit --amend` consumed only the index; the r2 verification round caught the gap. Candidate remedy direction for the checker: a net-additive commit whose only receipt-line delta is an appended `*-RECEIPT-RIDER` line naming an already-landed commit could be excused from the rewrite flag the way the same-commit retoken excusal covers the branch-internal case.
