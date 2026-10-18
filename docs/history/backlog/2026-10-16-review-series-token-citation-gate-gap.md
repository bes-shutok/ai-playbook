# Backlog: the worktree-removal gate's series parser cannot match the canonical tokened round names

- **Filed:** 2026-10-16 (witnessed during the prompt-log-collateral-served-prune authoring teardown)
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** witnessed defect (machinery contract disagreement)
- **Class:** fix-class
- **Skill/step:** `scripts/worktree_closeout_migrate.py` gate-removal (`_extract_citations`/`_series_prefix_fragment`) beside `scripts/review_record_selection.py`'s emitted naming contract
- **Cluster:** docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md; docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md; docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md

## Observed vs expected

Observed: `review_record_selection.py select` emits canonical plan-review record names carrying the path-derived identity token (`...-p5947faf4-r1.md`) per the review-plan naming rule, and the readiness gate's `--check-review-name` binds them; the teardown's gate-removal derives the expected series from the plan header's citation (written per the plans template, which makes the token infix optional) and translated it verbatim, so the probe looked for `...-prompt-log-collateral-served-prune-r*.md`, matched none of the tokened members, and refused the removal: `missing: .ai-playbook/reviews/...-prune-r*.md`. The receiving-review-bind r2 certification records the mirror surface: the template's literal `-r*.md` citation resolves no actual record filename for any tokened run (the dangling-pointer Low overflowed in that series' r2 record), so both sides of the disagreement live in this row.

Expected: the gate's series parser implements the plans template's full citation grammar (the optional `-p<identity-token>` infix between the slug and `-r<N>`), so a plan citing the template form and a run holding the canonical tokened records passes gate-removal.

## Evidence

- gate-removal output, 2026-10-16 ~14:5x local: `missing: .ai-playbook/reviews/2026-10-16-plan-review-prompt-log-collateral-served-prune-r*.md` while the primary reviews home holds the seven tokened records r1 through r7 (`...-prune-p5947faf4-r1..r7.md` + sidecars), all `--hard`-validated.
- Second witness, gate-removal output 2026-10-16 (the receiving-review-bind teardown): `series pattern (zero members): .ai-playbook/reviews/2026-10-16-plan-review-receiving-review-bind-local-work-to-live-pr-head-r*.md` while the primary home holds the tokened r1+r2 records; the gate's documented `--claims` input verified all four tokened paths and the series refusal still fired independently, so the two checks are additive and no claims file substitutes for the parser fix.
- `scripts/worktree_closeout_migrate.py` `_series_prefix_fragment`: every non-placeholder prefix is escaped verbatim; no token-infix arm exists.
- The plans template's citation form: `{reviews_dir}/YYYY-MM-DD-plan-review-<artifact-slug>[-p<identity-token>]-r*.md`.
- Third witness, gate-removal output 2026-10-17 (an exec run's receiving-review-bind teardown): the same infix-less citation refusal fired a third time; the run used the bounded citation-only remedy (follow-up commit adding the `-p` infix, re-land, re-run) and the defect was generalized into project lesson #69 (`docs/maintenance/development_lessons.md`), which does not substitute for the parser fix.
- Fourth witness, execute-plan closeout on 2026-10-18: the archived revival plan cites the template form without an identity token, while its canonical plan-review r1-r5 records carry `-p1f3867f1`; `worktree_closeout_migrate.py verify-records` reported zero members for the cited series even though all five records had been transferred to the primary reviews home. A temporary same-home symlink to the actual r5 record let the check resolve the citation without copying or inventing review content; the optional-token parser fix remains the durable resolution.

## Fix shape

Add the optional `-p<8-hex>` infix to the series fragment grammar (one regex alternation beside the date-normalization arms), with fixtures for the tokened and tokenless citation forms; the sibling date-form gap already fixed upstream by closeout-gate-review-series-expansion is the precedent shape. Until landed, a refusal keeps the worktree standing per the gate's own duty (this run's sanctioned park).
