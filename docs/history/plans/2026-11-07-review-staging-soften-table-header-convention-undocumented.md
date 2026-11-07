# Plan: Soften-watchlist parity error names the table header convention

Backlog origin: docs/history/backlog/2026-10-31-review-staging-soften-table-header-convention-undocumented.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-review-staging-soften-table-header-convention-undocumented-r*.md (the highest rN for this source-plan path is authoritative)
Execution budget: 0.5h total, largest task 0.5h
Executed: no

Authoring claim: 2026-10-31-review-staging-soften-table-header-convention-undocumented.md (session sess_a4477963-524c-4ffd-a571-93a12913e6ee)

## Terms

- soften watchlist: the `### Soften watchlist` section of a review staging record plus the sidecar's `soften_watchlist` array; the pair carries softened findings across review rounds.
- parity check: `validate_soften_watchlist_agreement` in `scripts/validate_review_staging.py`; it counts the section's table data rows and fails when the count differs from the sidecar array's length.
- header convention: the record-shape example in `agents/skills/review-staging/SKILL.md` renders the section's table with a header row whose first cell is `Round`.
- counting rule: the parity check reads only rows written between outer pipes (`| ... |`) and counts such a row as data unless it is the separator row, its first cell is empty, or its first cell is `Round` (any letter case).
- empty form: the literal `None.` that renders the section when the sidecar array is empty.
- producer: any session or tool that writes a staging record and its sidecar.
- sidecar: the `.stats.json` file written beside a staging record; it carries the record's structured fields.
- hard gate: the validator run in hard mode, which fails the record (and the round that wrote it) on any error.
- arm: one candidate way to fix the origin problem.
- pin: a selftest assertion that fixes one behavior so a later change cannot silently alter it.

## Why

A record whose soften table is headed `| Pattern | Status | Note |` fails the parity check with a bare count mismatch (`rows 2 != sidecar 1`), because the header row is counted as data. The error never says which header form is accepted, so the producer must read validator source to fix a one-line shape problem, costing one failed hard-gate run each time.

## Gist & Examples

TLDR: the soften-watchlist parity error names the accepted `Round`-first header and the `None.` empty form, and the review-staging skill states the same table form, so a producer fixes the shape in one iteration without reading validator source; the driving force is efficiency.

**Before (today):** a producer renders a one-row soften table headed `| Pattern | Status | Note |` beside a one-row sidecar array. The hard gate fails with `soften disagreement: Soften watchlist rows 2 != sidecar soften_watchlist 1 (the soften record pair is the source of truth; render the same rows)`. Nothing in the message or in the skill's soften bullet says the header must lead with `Round`; the 2026-10-31 authoring closeout spent one failed hard-gate run and a source read to learn it.

**After (this plan):** the same record fails with the same counts, and the message continues with the counting rule as a plain statement: a table row counts as data unless it is the separator row, its first cell is empty, or its first cell is `Round`; every sidecar row is rendered as one data row, and the section reads `None.` when the sidecar array is empty. The statement holds for both mismatch directions (too many rows or too few). The skill's soften-watchlist bullet points at the same rule. The producer sees that its `Pattern` header was counted, re-renders the header, and passes on the next run.

**Edge cases:** the counting rule is unchanged, so a genuinely extra data row (real drift) still fails exactly as today; a `Round`-headed table and the `None.` form keep passing; the missing-section error is unchanged; records dated before `SOFTEN_WATCHLIST_PARITY_MIN_DATE` stay exempt from the check as today.

## Outcome

A producer who renders the soften table in the wrong shape learns the accepted shape from the error itself and from the skill text, without reading validator source.

- The parity check's mismatch error states the counting rule (separator, empty first cell, and `Round` header are not data) and the `None.` empty form, correct for both mismatch directions.
- The review-staging skill's soften-watchlist bullet points at the `Round`-first header of its own example, paid for by tightening the bullet's existing wording.
- The counting behavior is byte-for-byte the same, so drift detection is not weakened.

Gate delta: none (explicit). The parity check keeps its refusal class, trigger condition, and counting rule; only the refusal message text gains the convention, and one skill sentence documents it. No gate, fence, schema field, or refusal class is added or removed, so no ledger citation is required.

## Assumptions

- assume the counting rule above is the whole rule; basis: `validate_soften_watchlist_agreement` in `scripts/validate_review_staging.py` matches rows with `^\|(.+)\|\s*$`, skips a first cell that is empty or made only of `-`, `:`, and spaces, then skips a first cell equal to `round` case-insensitively, and the skill's record-shape example table opens `| Round | Pattern / finding | Anchor | Prior fix | Soften reason | Status |`.
- assume existing selftest pins match message substrings, not the whole message; basis: the soften parity selftest checks `"soften disagreement" in e`, the two counts, and `"source of truth" in e`, so appending text after the existing message keeps them passing.
- assume no producer parses this error text; basis: the message is human-facing validator output, and the record producers (`scripts/produce_exec_review_record.py` and the review skills) read only the final `OUTCOME:` line and pass or fail.

Simpler-design comparison for the selected arm: the origin offers two arms. Widening the header skip to a header vocabulary (for example `Pattern`) is rejected because every new skipped first cell is a value a real data row can no longer carry without being silently uncounted, which weakens drift detection; the PLAN-PROMPTS entry rejects only accepting any header row and leaves a documented vocabulary open, so this rejection rests on the silent-uncount argument, not on that entry. A message-plus-docs arm changes no counting behavior, adds no vocabulary, and fixes the observed cost (a source read per incident) at the point where the producer reads, so it is the smaller arm.

Decision points requiring a grill: arm selection resolved on the maintenance-selected path: message-plus-docs arm, no parse change (receipt: the origin's Expected and Suggested direction name "reduce the error message to name the Round-first convention" with the skill record-shape statement as a candidate arm; comparison in the Simpler-design paragraph above; decided 2026-11-07 by sess_a4477963 under the operator-directed blocked-lane recovery mandate)

## Evaluation Criteria

**Quality dimensions:**
- correctness: a `Pattern`-headed one-row table beside a one-row array still fails, and its error states the counting rule naming `Round` and `None.`; a `Round`-headed table and the `None.` form still pass.
- behavior preservation: the counting loop in `validate_soften_watchlist_agreement` is byte-unchanged; only the mismatch message string changes.
- precision: the error states exactly the counting rule in Terms (separator row, empty first cell, `Round` first cell are not data; `None.` when empty), matching `validate_soften_watchlist_agreement`'s skips, and the skill wording does not contradict it.

**Done when:**
- `python3 scripts/validate_review_staging.py --selftest` passes, including a new pin for the `Pattern`-headed table.
- the skill's soften-watchlist bullet points at the `Round`-first header with no net growth of the bullet.

**Ship when:**
- none (repository-verifiable only).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py` (Task 1)
- `agents/skills/review-staging/SKILL.md` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the parity check's counting rule and header skip; changing what is counted is the rejected vocabulary-widening arm.
- `docs/history/backlog/2026-10-22-review-staging-scaffold-simplification-residuals.md` scope; that row owns scaffold residuals on the same validator surface.

## Validation Commands

```bash
python3 scripts/validate_review_staging.py --selftest
```

### Task 1: Name the soften table header convention in the parity error and the skill

Context surface: the plan's Terms and this task (`## Standing constraints` not declared; absent).

Files:
- `scripts/validate_review_staging.py`
- `agents/skills/review-staging/SKILL.md`

Primary class anchors:
- `validate_soften_watchlist_agreement` in `scripts/validate_review_staging.py`

- [ ] `validate_soften_watchlist_agreement` delivers the convention-naming mismatch error: given a staging record whose `### Soften watchlist` table is headed `| Pattern | Status | Note |` with one data row beside a one-row sidecar `soften_watchlist`, expects a hard-mode failure whose error keeps the existing `soften disagreement`, both counts, and `source of truth` text and also states the counting rule, naming `Round` and the `None.` empty form. [class: IMPLEMENTATION_REQUIRED]
- [ ] The rule statement is direction-neutral: given a `Round`-headed table with zero data rows beside a one-row array, expects a failure carrying the same rule statement with no advice that assumes too many rows. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (drift detection unchanged): given a `Round`-headed table with two data rows beside a one-row array, expects the same failure as today; given a `Round`-headed one-row table beside a one-row array, or `None.` beside an empty array, expects no soften disagreement. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: add the `Pattern`-headed selftest pin to the soften parity selftest block and run `python3 scripts/validate_review_staging.py --selftest`; the new pin fails because today's message names neither `Round` nor `None.`. [class: REPOSITORY_TEST]
- [ ] Write minimal implementation: extend only the mismatch message string in `validate_soften_watchlist_agreement` with the counting rule as a direction-neutral statement (no imperative that assumes too many rows); leave the counting loop, the header skip, and the missing-section message unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/review-staging/SKILL.md`, edit the soften-watchlist bullet (item 12 of `## Orchestrator recording rules`): add one short clause that the table's header row leads with `Round` as in the record-shape example (any other header row counts as a data row), and pay for it in the same bullet by tightening existing wording so the bullet does not grow. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest` passes with every existing soften parity pin unchanged. [class: REPOSITORY_TEST]
- [ ] Commit: `review-staging: name the Round-first soften table header in the parity error and skill` [class: IMPLEMENTATION_REQUIRED]
