# Backlog: doc-registry validator r7 residuals (execute-plan r7 + design exit hybrid)

Origin: execute-plan Phase 3 rounds r7 + design exit hybrid for
`docs/plans/completed/2026-09-08-doc-ownership-lifecycle.md` (review staging:
`docs/reviews/2026-09-10-2026-09-08-doc-ownership-lifecycle-code-review-r{7}.md`).
All items are valid, non-blocking review findings deferred at the round-budget
stop per the backlog-deferral default (no digest mutation before loop exit).
Status values: open / done. Each item names its finding source (r7 = focused
panel F1..F9; hybrid = design exit hybrid H1..H6).

## Items

### 1. Silent facts-module-absent disable (r7 F1, Medium)
`scripts/doc_registry_validator.py` `_import_facts_paths`/`resolve_repo_relative_key`: when `facts_paths.py` is not importable next to the validator, resolution silently returns defaults, so repos with non-default `plans_completed_dir`/`backlog_completed_dir`/`doc_registry_rel` get the default dirs gated and the configured families ungated with no diagnostic. Add a warn mirroring the exception path plus a selftest fixture asserting the warn. Source finding: r7 testing Medium (testing#hermeticity-gap). Status: open

### 2. Cosmetic status whitespace in the HARD message (r7 F2, Low)
The check-writes HARD finding interpolates the raw two-char porcelain status (`change type M ;`), printing a stray space. `change_type.strip()` in the message. Status: open

### 3. Untracked dir-collapse loses the stage-the-move hint (r7 F3, Low)
`?? docs/plans/completed/` (whole untracked dir) fires a directory-level HARD with no remediation hint even when registered lifecycle srcs inside are the freeze move arriving. Expand untracked dir entries against registered srcs or emit the stage-the-move hint naming the dir. Status: open

### 4. Case-variant untracked lifecycle src: inconsistent tier (r7 F4, Low)
`?? docs/plans/completed/A.md` vs registered src `a.md` on a folding platform is a generic HARD, while the byte-equal spelling gets the stage-the-move warn. Extend the near-match handling to the untracked case. Status: open

### 5. Case-only rename of a registered src has no clean passage (r7 F5, Low)
`R  docs/plans/completed/a.md -> docs/plans/completed/A.md` hard-blocks the old side as D; a zero-content case normalization requires the corruption-override note. Route case-only renames (fold-equal sides, no directory change) to the near-match warn tier, or document as override-worthy in doc-hierarchy. Status: open

### 6. Audit-token skew fixtures are midnight-sensitive (r7 F6, Low, theoretical)
`skew_bad` is computed from `date.today()` at fixture-build time while the code re-reads the clock; a run straddling local midnight can flake. Freeze the clock seam (pass a `today` parameter defaulting to `date.today()`). Status: open

### 7. Identity derivation undefined for flat RFC filenames (r7 F7, Low)
The filename scheme assumes a leading `YYYY-MM-DD-` prefix, but migration-complete service repos use flat `*-rfc.md` names. Add the no-date-prefix clause to the doc-hierarchy identity-derivation spec (filename minus `.md` and trailing `-rfc`). Status: open

### 8. Validate-side audit message omits the date rule (r7 F8, Low)
The validate-path HARD message names only the token prefix; the check-writes message states the full real-non-future-date contract. Sync the wording. Status: open

### 9. done hard-findings list omits the ill-dated half (r7 F9, Low)
Step 2.648's enumeration says "malformed audit-note tokens" where the provider spec says "malformed or ill-dated". Sync the wording. Status: open

### 10. Duplicated registry-row audit scan in validate vs check-writes (hybrid H1, Medium)
Two hand-rolled scans enforce the same audit-note contract with divergent message strings; the r6 F4 bug class is their proven failure mode. Extract one shared `audit_defects(rows)` helper with a single message template. Status: open

### 11. done Step 2.648 hand-rolls sed TOML parsing for tmp_dir (hybrid H2, Low)
Inline sed re-implements facts resolution in a fourth style; route through `scripts/facts_paths.py` or have the validator expose the resolved tmp dir. Status: open

### 12. Registry boilerplate rows restate filesystem-derivable data (hybrid H3, Low)
140 backfilled rows carry only derivable content and every completion appends another; consider a derive-by-default tier reserving mandatory rows for non-derivable cells, or record the per-row append as an accepted ADR-0003 cost. Status: open

### 13. Dead duplicate `seen_done.update(walked)` in successor_cycles (hybrid H4, Low)
The while/else update duplicates the unconditional one; delete the `else:` clause. Status: open

### 14. Exemption contract restated in four artifacts (hybrid H5, Low)
The registered-src exemption semantics live in full in the validator docstring, done Step 2.648, doc-hierarchy Document states, and README. Keep doc-hierarchy as the prose SOT and reduce done/README to pointers. Status: open

### 15. Transient review-round tags committed in the validator (hybrid H6, Low)
About 30 comment/docstring annotations reference ephemeral review staging IDs ("r6 F1" etc.) that a public-repo reader cannot resolve. Strip the parenthetical round tags; git history preserves provenance. Status: open
