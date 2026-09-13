# Backlog: check_lesson_scope residual duplicate-evasion classes (r1 findings 2 and 4)

Status: open
Priority: low
Origin: branch review r1 (2026-09-13) of docs/plans/2026-09-12-check-lesson-scope-closeout.md, staging doc docs/reviews/2026-09-13-2026-09-12-check-lesson-scope-closeout-code-review-r1.md, findings 2 and 4 (both Low, non-blocking, accepted-boundary residuals)

Two residual duplicate-evasion classes left as accepted boundaries by the closeout plan. Both are valid defects; neither is fixed in this scope.

## Finding 2: headed-file degenerate block (silent clean pass)

- Problem: the zero-block WARNING fires only for a headingless file with no
  non-whitespace content (the plan narrowed the headingless case). A file
  that DOES carry a heading but only whitespace beneath it — corpus
  `# H\n\n   \n` — parses to one degenerate block whose normalized text is
  under MIN_RULE_WORDS, so it is skipped in comparison: exit 0, empty
  stderr, silent clean pass through the done gate.
- Evidence: probed 2026-09-13 against the fixed copy (corpus `# H\n\n   \n`
  vs a normal master): exit 0, no WARNING line.
- Exact location: `scripts/check_lesson_scope.py` `parse_blocks` (headingless
  zero-block branch and the degenerate-block path it does not cover) and
  `_load_blocks` (WARNING emission condition).
- Why not fixed now: pre-existing class; the plan explicitly narrowed the
  headingless case only. Closing the headed variant would entangle the
  WARNING contract with the MIN_RULE_WORDS witness floor (a headed file
  whose only block is a short witness pointer is legitimate, so "parses to
  blocks but none comparable" cannot simply become a WARNING without
  redefining the cold-start contract gate consumers stop on). Decision
  recorded by the executing agent per the r1 staging triage disposition.
- Candidate options: (a) keep as documented tradeoff (state the headed
  degenerate-block case in the docstring/USAGE alongside the existing
  zero-block parenthetical); (b) per r5 F2 options, a merged-text or
  windowed comparison that would make degenerate blocks comparable without
  a WARNING contract change.

## Finding 4: h3-dilution residual (mirror of the fixed h3-split)

- Problem: the h1/h2 boundary amendment (h3+ stays body text) closes the
  h3-split evasion but opens a dilution mirror: an h3 subsection present in
  only ONE copy adds enough text to that block to dilute the
  difflib.SequenceMatcher ratio below DUPLICATE_RATIO (0.90), so a real
  duplicate can be missed.
- Evidence: probed 2026-09-13 against the fixed copy: corpus rule + h3
  subsection + unrelated tail vs master rule alone exits 0 (miss); the
  staging doc records the old parser (h3-split) exiting 1 on the same
  shape (old-exit-1 to new-exit-0). Zero real-corpus exposure: all 7
  corpora plus the master are h3-free, and old-vs-new output is
  byte-identical on every pair.
- Exact location: `scripts/check_lesson_scope.py` `find_duplicates`
  (whole-block ratio gate over blocks whose boundary choice comes from
  `parse_blocks` heading detection).
- Why not fixed now: explicit plan tradeoff recorded in the plan's
  Assumption on r5 finding F2 (the `#{1,2}` amendment was chosen over
  merged-text comparison); the closeout scope fixed the split direction
  only. Decision recorded by the executing agent per the r1 staging
  triage disposition.
- Candidate options: (a) keep as documented tradeoff (note the
  one-sided-h3 dilution case in the docstring next to the amendment);
  (b) merged-text or windowed comparison per r5 F2 options, which would
  make the pair comparable regardless of where the h3 subsection sits;
  any change must preserve the pinned
  fence/zero-block contracts.
