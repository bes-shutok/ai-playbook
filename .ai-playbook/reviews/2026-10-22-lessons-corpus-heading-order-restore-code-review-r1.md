# Code Review: Branch adhoc/2026-10-22-lessons-corpus-heading-order → main (ad-hoc landing, lessons-corpus-heading-order-restore)

## Metadata
- Type: Branch Review (ad-hoc backlog arm landing review)
- Record kind: canonical
- Review mode: fresh-adversarial
- Date: 2026-10-22
- Branch: adhoc/2026-10-22-lessons-corpus-heading-order → main
- Findings: 2 (both minor, non-blocking)
- Status: POSTED
- Base resolved non-interactively: main (repo default; ad-hoc exec run)
- Changed-risk signals: none (pure-move content reorder of one docs corpus + covered-row origin-row deletion; no code paths, no mutators)
- Panel mechanism note: one fresh-adversarial general-purpose review worker over `git diff main...HEAD` at final head 2a47e561e, invariants re-derived from git independently of the run's claims
- Prior findings supplied as filter: none (round 1)
- Last fix commit: 2a47e561e (reviewed bytes; no folds)
- Source digest: 67875c23c151a39adc775a32af1ee196652a09c66c07ff07346c78038424a599 (sha256 over `git diff main...HEAD` at final head 2a47e561e)

## Verification (worker, re-derived from git)
1. Census/order: 176 headings, zero duplicates, strictly ascending after the move; fence-aware count equals naive count; number 9 absent from 6..182 pre-existing on main (byte-identical heading sets), out of scope by the entry's pure-move mandate.
2. Pure move: HEAD file is an exact permutation of main's lines (3203 lines both, line multisets byte-equal, identical byte size 269887).
3. No intra-block edits: every HEAD block byte-identical to the same-numbered main block; preamble byte-identical; exactly blocks {160,161,162,163,164,165} relocated (main: 153 → [160,161,162,165] → 154..159 → [163,164] → 166; HEAD: 153 → 154..166).
4. Consumers: no position-relative language in the corpus; 108 same-corpus citations all resolve; scripts/lessons_corpus.iter_lessons parses the reordered file as 176 ascending lessons; scripts/lessons.py selftest 5/5; test_check_lesson_scope 38/38; lessons_recall sorts by number (order-independent); lessons_adopt derives heading indices per run; skill_gate corpus-write path order-blind.
5. Row deletion: deleted row's commissioned direction (one-shot pure-move reorder) satisfied exactly; single commit touches exactly the two authorized paths; no covering plan (rg over docs/history/plans clean).
6. Hygiene: zero net-added prose; no em dashes, no secrets, no absolute personal paths.

## Findings
- Minor: live EXEC-PROMPTS entry transiently cites the deleted row path until closeout prune (the prune rides this landing commit; defect class self-discharged).
- Minor (informational): deleted row's census figure stale (173 vs actual 176); entry mandated disk re-derivation, honored.

## Verdict
ready=yes, zero blocking findings.
