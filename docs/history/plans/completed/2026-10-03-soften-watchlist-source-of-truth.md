# Plan: Soften-watchlist source of truth: declare the record pair, demote the rest

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-02-soften-watchlist-source-of-truth.md`

## Gist & Examples

TLDR: the staging sidecar's `soften_watchlist` array together with its same-round `### Soften watchlist` Markdown rendering is declared the source of truth for row state, every writer of the pair (review-staging, receiving-review) mirrors rows into both halves, review-loop's session-tmp store becomes a derived working copy and commit messages are named the detection input, and a date-fenced validator arm enforces Markdown-section row-count parity against the sidecar array; reliability driving force, because a soften decision recorded in one of four undeclared stores can be silently contradicted by another inside the very mechanism built to catch soften drift (the 2026-07-27 finding, deferred and never adjudicated).

Re-derivation of the four stores from the current tree (recorded per the entry; all four alive, none retired):

1. The staging Markdown `### Soften watchlist` section under `## Review Statistics`: agents/skills/review-staging/SKILL.md step 12 ("Carry forward open rows from the previous round"), the table shape at the record-template section, and the `softened-reaffirmed` disposition code.
2. The sidecar `soften_watchlist` required array: scripts/validate_review_staging.py (required-field list and `_require_array` call) and the SKILL's sidecar guidance ("Multi-round / review-loop orchestrators must carry `open` rows forward", the field table row). Validated in isolation today; no cross-check against the Markdown section exists.
3. The review-loop active-run store: agents/skills/review-loop/SKILL.md, "Maintain a **soften watchlist** for the active loop run (session tmp or the latest staging doc section `### Soften watchlist`)": the undeclared either-or; the row shape and the reaffirm/restage duties live in the same block.
4. Git commit messages as the detection channel: review-loop's detection trigger ("A later commit **reverts** the fix ... with rationale such as soften, keep X, intentional") reads commit messages, which is detection, not state.

Corpus baselines re-derived at authoring (docs/reviews, 2026-10-03): 2084 record files and 1896 sidecars; 847 records carry a `### Soften watchlist` section; 10 carry non-empty `soften_watchlist` arrays; 8 records render rows beside an empty array (true parity violations, all dated 2026-07-27 to 2026-09-08, grandfathered by the landing-dated fence); 238 of the 847 section-bearing records render the section as the document's last heading, the shape the parity arm's extraction must match.

## Terms

- **The record pair:** the sidecar `soften_watchlist` array plus the `### Soften watchlist` Markdown section rendered in the same round's record; together they are the source of truth for row state in the owning skill (review-staging), which renders the sidecar rows, never parallel state. Every writer of a soften row writes both halves in the same pass.
- **Derived working copy:** review-loop's session-tmp watchlist, initialized from the latest round's record at loop start and written back into each new round's record pair; never the origin of record.
- **Detection input:** commit messages whose rationale matches the soften vocabulary; read by review-loop to trigger watchlist re-checks, never held as row state.
- **Parity arm:** the date-fenced validator check that the `### Soften watchlist` section's data-row count equals `len(soften_watchlist)`, mirroring the existing attempt-ledger parity check's shape (regex-extracted section, data-row count, sidecar comparison). It is a deliberate count-mirror: it flags row-count mismatches between the pair's halves and does not adjudicate same-count content drift.
- **Fence exemption:** a sidecar-date-keyed exemption in the `_coverage_fence_exempt` idiom (anti-backdating and straddling fail-closed checks included), parameterized by a new `SOFTEN_WATCHLIST_PARITY_MIN_DATE` constant, applied to canonical records only, exactly like the coverage arm's `coverage_exempt` handling.

## Coordination (binding, not re-litigating)

- The cluster sibling `docs/history/backlog/2026-10-02-reviews-home-alignment.md` is owned by the landed plan `docs/history/plans/2026-10-02-revert-set-clobber-and-reviews-home.md`: that plan owns the reviews-home path; this plan touches record content only and never the home.
- The validator's existing fence machinery (EXTENDED_SIDECAR_MIN_DATE, COVERAGE_SIDECAR_MIN_DATE, RECORD_KIND_SIDECAR_MIN_DATE, `_date_fence`, `_coverage_fence_exempt`) is the base; the parity arm adds one fence constant and one exemption sibling beside them and re-derives nothing.
- The attempt-ledger parity check (`validate_coverage_markdown_agreement`) is the mirrored shape; the parity arm is its sibling, not a refactor of it. The mirror is structural, not literal: the soften table's header cell, section shape, and fence idiom are the soften arm's own (the coverage/attempt-ledger literals are not copied).
- The one-pass cross-cutting migration rule binds receiving-review into this plan: it is the canonical soften-row writer, so its writer steps migrate in the same pass that declares the pair.
- The operator execution-lane closure of 2026-10-02 stands: authoring only.

## Review Scope

Every task's Files path, inventoried:

- agents/skills/review-staging/SKILL.md
- agents/skills/receiving-review/SKILL.md
- agents/skills/review-loop/SKILL.md
- scripts/validate_review_staging.py
- docs/history/plans/2026-10-03-soften-watchlist-source-of-truth.md

Gates re-checked but not edited: scripts/plan_readiness.py, scripts/check_maintenance_pins.sh (no pins in scope; the entry prices no pins arm). Test harness touched: the validator's in-script `--selftest` suite (the fixtures live inside scripts/validate_review_staging.py; no external test file exists for the validator). Reviewers verify the declaration names one store pair and demotes (not deletes) the others, the parity arm mirrors the attempt-ledger shape without refactoring it while pinning its own header cell, fence idiom, and end-of-document extraction, the writer mirror closes the receiving-review gap, and the date fence exempts pre-constant records exactly like the existing fences.

## Tasks

### Task 1: review-staging declares the record pair the source of truth

Files:
- `agents/skills/review-staging/SKILL.md`

Evidence:
- grep probes below; `bash scripts/check-no-em-dash.sh added-lines --base HEAD` and the hygiene scan stay clean

- [x] RED: `grep -c "source of truth" agents/skills/review-staging/SKILL.md` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Rewrite step 12 ("Soften watchlist") to declare the store: the sidecar `soften_watchlist` array, together with the `### Soften watchlist` Markdown section rendered in the same round's record, is the source of truth for row state; the section renders the sidecar rows and carries them forward by rendering the carried rows, never holding parallel state; the "None." empty-rendering rule stays [class: IMPLEMENTATION_REQUIRED]
- [x] Update the sidecar guidance ("Multi-round / review-loop orchestrators must carry `open` rows forward") to the pointer sentence, which contains the phrase "source of truth" once: the sidecar array is the state of record (the source of truth beside its same-round rendering), and a row-count mismatch between the pair's halves is a defect the parity arm (Task 4) flags; the arm is a deliberate count-mirror and does not adjudicate same-count content drift [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: "source of truth" appears exactly twice in the file (the step 12 declaration and the sidecar guidance pointer, each containing the phrase once) [class: REPOSITORY_TEST]
- [x] Commit: `skills: review-staging declares the soften record pair the source of truth` [class: IMPLEMENTATION_REQUIRED]

### Task 2: receiving-review's soften writers mirror the pair

Files:
- `agents/skills/receiving-review/SKILL.md`

Evidence:
- grep probes below

- [x] RED: `grep -c "both halves" agents/skills/receiving-review/SKILL.md` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Migrate the canonical soften-row writer so the declared pair stays consistent: the soften step's "append a row to `### Soften watchlist` in the current (or newest) staging doc" instruction and the triage-outcomes item "update `### Soften watchlist` in the same pass" each gain the mirror duty, writing the row into both halves of the record pair in the same pass: the Markdown section row and the matching row in the staging doc's sidecar `soften_watchlist` array; unmirrored writes are the defect the parity arm (Task 4) refuses, and the mechanical gate that re-runs the validator after a triage update passes only when both halves agree [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: "both halves" appears exactly twice (once per writer site) [class: REPOSITORY_TEST]
- [x] Commit: `skills: receiving-review soften writers mirror the record pair` [class: IMPLEMENTATION_REQUIRED]

### Task 3: review-loop demotes session tmp and names commit messages the detection input

Files:
- `agents/skills/review-loop/SKILL.md`

Evidence:
- grep probes below

- [x] RED: `grep -c "derived working copy" agents/skills/review-loop/SKILL.md` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Rewrite the watchlist block's opening ("Maintain a **soften watchlist** for the active loop run (session tmp or the latest staging doc section `### Soften watchlist`)") to demote the tmp store: the active-run watchlist is a derived working copy initialized from the latest round's record pair (the sidecar array and its rendered section) and written back into each new round's record; session tmp is a cache, never the origin of record [class: IMPLEMENTATION_REQUIRED]
- [x] In the same block, name the commit-message channel: the revert-rationale trigger reads commit messages as the detection input that schedules a watchlist re-check; commit messages never hold row state [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: "derived working copy" appears exactly once, and "detection input" exactly once [class: REPOSITORY_TEST]
- [x] Commit: `skills: review-loop watchlist is a derived copy, commit messages the detection input` [class: IMPLEMENTATION_REQUIRED]

### Task 4: validator parity arm with a date-fenced, canonical-scoped, end-of-document-safe extraction

Files:
- `scripts/validate_review_staging.py`

Evidence:
- `python3 scripts/validate_review_staging.py --selftest`; covers the parity arm's agreement and disagreement fixtures (including a trailing-section pair), the fence exemption, and every pre-existing selftest arm

- [x] RED: add selftest fixtures proving the arm is absent, dated on or after the new `SOFTEN_WATCHLIST_PARITY_MIN_DATE` and enriched to clear the freshness and record-kind fences the post-constant date activates (the `supplemental_payload`-style builder enrichment; a fixture that dodges those fences by dating pre-constant vacates the arm and is the refused shape): a mismatch fixture whose `### Soften watchlist` section carries two data rows while the sidecar `soften_watchlist` array carries one, its agreement twin, and a trailing-section pair whose section is the document's last heading (extraction must still find it); run the selftest expect RED on the parity error specifically [class: REPOSITORY_TEST]
- [x] Implement `validate_soften_watchlist_agreement` beside `validate_coverage_markdown_agreement`, mirroring its structure with the soften arm's own literals: extract the `### Soften watchlist` section from the heading to the next `### ` or `## ` heading or end of document (`(?=^### |^## |\Z)`; the lookahead without the end-of-document alternative cannot match a section rendered last, the dominant corpus shape), count data rows excluding separator rows (dash/colon first cell) and the header row whose first cell is `Round` (the attempt-ledger check's header skip is name-keyed to its own table and does not transfer), and refuse when the count differs from `len(soften_watchlist)`; a record with an empty sidecar array and a `None.`-style empty rendering or no section at all agrees at zero, and a non-empty array with no section refuses (fail-closed) [class: IMPLEMENTATION_REQUIRED]
- [x] Invoke it in the shared path beside the coverage twin's call site, scoped to canonical records (skipped for declared non-canonical kinds via the existing `_declared_noncanonical_kind` handling) and fenced by a `_coverage_fence_exempt`-idiom sibling parameterized by the new `SOFTEN_WATCHLIST_PARITY_MIN_DATE` constant (sidecar-date-keyed, anti-backdating and straddling fail-closed checks included; the bare `_date_fence` helper lacks those checks and is not the fence idiom here) [class: IMPLEMENTATION_REQUIRED]
- [x] The refusal names both counts and the declaration ("the soften record pair is the source of truth; render the same rows"), so the remedy is render-side, never a silent array edit [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 scripts/validate_review_staging.py --selftest` GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: soften-watchlist Markdown/sidecar parity arm` [class: IMPLEMENTATION_REQUIRED]

### Task 5: whole-plan gates and the reconciliation record

Files:
- `docs/history/plans/2026-10-03-soften-watchlist-source-of-truth.md`

Evidence:
- the full Validation Commands block; the plan's own Disposition section below carries the reconciliation note the origin's Expected names

- [x] Run the full Validation Commands block GREEN (the selftest suite, the grep count gates, the em-dash and hygiene gates) [class: REPOSITORY_TEST]
- [x] Verify the reconciliation record is complete: the Gist's re-derivation list names all four stores with their dispositions (the pair declared, session tmp demoted to derived working copy, commit messages named detection input), which is the reconciliation note the origin's Expected requires, and the Disposition section below names the former backlog path [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: soften-watchlist reconciliation record` [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

```
PY=$HOME/.agents/venvs/ai-playbook-test/bin/python3
$PY scripts/validate_review_staging.py --selftest
grep -c "source of truth" agents/skills/review-staging/SKILL.md    # exactly 2
grep -c "both halves" agents/skills/receiving-review/SKILL.md      # exactly 2
grep -c "derived working copy" agents/skills/review-loop/SKILL.md  # exactly 1
bash scripts/check-no-em-dash.sh added-lines --base HEAD
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Evaluation Criteria

1. The declaration names exactly one store pair (sidecar array plus same-round Markdown rendering) as the source of truth inside the owning skill, and the carry-forward rule says render-the-same-rows (count gates, Task 1).
2. Both canonical soften writers (review-staging and receiving-review) mirror rows into both halves in the same pass, closing the unmirrored-write class the parity arm refuses (count gate, Task 2).
3. Review-loop's session tmp is a derived working copy initialized from the latest round's record, and commit messages are the detection input, never state (count gates, Task 3).
4. The parity arm mirrors the attempt-ledger structure with its own literals (end-of-document-safe extraction, the `Round` header skip, the `_coverage_fence_exempt`-idiom fence, canonical-only scoping), refuses count mismatches fail-closed including the trailing-section and missing-section shapes, and both the selftest suite and the count gates are GREEN (Task 4).
5. The reconciliation record (the Gist's store list plus the Disposition section) names all four stores' dispositions and the former backlog path (Task 5).

## Done When

- Every checkbox is `[x]`, the Validation Commands are GREEN, and the review rounds returned ready with zero blocking findings.
- The plan is landed; per the execution lane closure (operator directive, 2026-10-02) this plan is authored and landed, never executed.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-02-soften-watchlist-source-of-truth.md`: the soften-watchlist state stores are dispositioned as follows: the sidecar `soften_watchlist` array and its same-round `### Soften watchlist` Markdown rendering are the declared source of truth (agents/skills/review-staging/SKILL.md), with receiving-review's soften writers mirroring both halves (agents/skills/receiving-review/SKILL.md); review-loop's session tmp is demoted to a derived working copy and commit messages are named the detection input, never state (agents/skills/review-loop/SKILL.md); the parity arm in scripts/validate_review_staging.py enforces the record pair's row agreement. No new store is created; no store is deleted.

## Assumptions

- The four stores' current bytes are as re-derived in the Gist; a peer landing that moves the anchored lines before execution re-keys this plan's fragments.
- The parity arm's fence constant dates from this plan's landing, which grandfathers the eight witnessed pre-fence parity-violating records (2026-07-27 to 2026-09-08) exactly like the existing fences' pre-constant records.
- The attempt-ledger parity check is mirrored structurally, not refactored or copied literally; basis: the machinery delta doctrine prices the small sibling arm on the witnessed divergence risk, not a validator rewrite.
- The count-mirror boundary (same-count content drift is not adjudicated) is the arm's declared scope; basis: the entry prices row parity on the attempt-ledger model, and deepening to row-identity comparison is a validator rewrite the doctrine declines.

Decision points requiring a grill: none remain.
