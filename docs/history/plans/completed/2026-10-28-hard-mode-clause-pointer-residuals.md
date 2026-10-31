# Plan: hard-mode clause pointer residuals - coverage, pinning, fixtures, funnel, and the done-advisory placement pin

Backlog origins (scope of record):
- docs/history/backlog/2026-10-23-hard-mode-pointer-coverage-extensions.md
- docs/history/backlog/2026-10-23-hard-mode-pointer-pinning-and-fixture-residuals.md
- docs/history/backlog/2026-10-20-done-advisory-threshold-sentence-unpinned.md

```toml
date = "2026-10-28"
backlog_origins = [
  "docs/history/backlog/2026-10-23-hard-mode-pointer-coverage-extensions.md",
  "docs/history/backlog/2026-10-23-hard-mode-pointer-pinning-and-fixture-residuals.md",
  "docs/history/backlog/2026-10-20-done-advisory-threshold-sentence-unpinned.md",
]
driving_force = "code-quality"
execution_budget = "2 hours"
review_full_panel_rounds = "2"
```

Driving force: code-quality
Authoring claim: docs/tmp/authoring-claims/hard-mode-clause-pointer-residuals.md (session zcode-auth-188b5264-002140Z)

## Terms

- **Pointer table**: `SKILL_CLAUSE_POINTERS` in `scripts/validate_review_staging.py` - the ordered marker-to-section tuple `_skill_clause_pointer` scans first-match-wins to append `(review-staging SKILL.md, <section>)` to hard-mode ERROR lines.
- **Hard-mode selftest arm**: `_selftest_hard_mode_diagnostics` in the same file (embedded selftest, not a separate test file) - pins emission order, pointer suffixes, and cascade suppression on a multiply-invalid fixture.
- **Drift guard**: the `check_maintenance_pins.sh` block that re-reads the live pointer table and requires every section string to remain a heading or inline mention in `agents/skills/review-staging/SKILL.md`; it currently has two raw `exit 1` sites outside the suite's `emit_outcome` funnel.
- **Outcome funnel**: the pins suite's `fail=1` + `emit_outcome` path that prints the final `OUTCOME:` line; the drift guard's raw exits bypass it, so a drift firing produces no final `OUTCOME:` line.
- **Shared fixture builders**: `_current_finding(**extra)`, the whole-document `_current_findings_markdown` builder, `_version1_payload()`, and the per-arm `_captured()`/`call()` capture copies the malformed-fixture checks and the hard-mode arm each carry privately (they must be hoisted/extracted into shared helpers by this plan, not reused: no shared capture helper or per-finding block builder exists today).
- **Placement-pin family**: the `placement_pin "$PD" "<fragment>"` rows in `scripts/check_maintenance_pins.sh` - warning-only presence greps that never move the suite's exit; the done-advisory task adds one row to this existing family.
- **Finding-id shorthand**: T1, C3, and D2 are findings of the Phase 3 r1 panel recorded in `docs/history/backlog/2026-10-23-hard-mode-pointer-pinning-and-fixture-residuals.md`; R2-1 and R2-4 are that row's Phase 3 r2 residuals; the coverage families are enumerated in `docs/history/backlog/2026-10-23-hard-mode-pointer-coverage-extensions.md` (the coverage row).
- **Precision nit**: the coverage row's observation that `finding conservation: finding {fid} pattern disagrees` maps via the generic conservation marker to the Markdown-hierarchy section while its clause lives in the Version-1 sidecar contract's Canonical Pattern IDs paragraph; the fix is a more specific marker ahead of the generic one.
- **Coverage row**: shorthand for `docs/history/backlog/2026-10-23-hard-mode-pointer-coverage-extensions.md` throughout this plan.
- **Denylisted-surface cost**: the Ad-hoc backlog arm's mechanical denylist bans whole-path edits to `scripts/check_maintenance_pins.sh`, so any change touching it must ride a plan; this plan is that ride for all three origins.

## Why

The pointer mechanism is one execution old (landed 2a99f9554 with a clean r2 round and a mutation-proven selftest). Three deferred valid panel findings and two review-fold residuals ride the same surface: high-value marker families still route to the bare fallback although their owning sections exist (coverage row, usability cost: every such ERROR line under-routes); the table's mappings are unpinned against wrong sections (mutation-proven), marker matching is substring-anywhere over author-controlled interpolations, the selftest arm re-implements fixture builders it already owns, and the drift guard's raw exits skip the outcome funnel. The folded done-advisory row adds one warning-only presence row and two comment trims on the pins suite the same change already touches, paying the denylisted-surface cost once. One landing pays the pins-regeneration and digest re-bind cost once for all three rows.

## Gist & Examples

TLDR: extend and pin the hard-mode clause-pointer table (new marker families, exact-section pinning, anchored matching, hoisted shared fixture builders, funnel-routed drift guard), and fold the done-advisory threshold placement pin plus two comment trims into the same pins-suite change, so hard-mode errors route to their owning sections and stay pinned and the done advisory's threshold drift becomes visible again (code-quality: one landing pays the pins-regeneration and digest re-bind cost once for all three rows).
- Title: hard-mode clause pointer residuals - coverage, pinning, fixtures, funnel, done-advisory pin
- Before: eight marker families fall back to the bare skill pointer; 16 of 20 mappings are unpinned against a wrong section (remapping passes selftest and pins); marker matching is substring-anywhere; the selftest arm carries four private fixture copies; the drift guard exits raw; no placement pin quotes the done advisory's threshold sentence; two `# Re-aimed` comments run 278/255 bytes.
- After: every listed family maps to its owning section and each mapping is pinned to its exact `(review-staging SKILL.md, <section>)` suffix in the selftest; matching is quote-position-anchored (occurrences immediately preceded by a quote are skipped except for the `_QUOTED_TEMPLATE_MARKERS` legacy anywhere-match exemptions); the arm composes hoisted shared builders; both drift-guard sites emit through `emit_outcome` while keeping their immediate refusal; one `placement_pin` row quotes a distinctive done-advisory threshold fragment; both re-aim comments are citation-plus-one-clause.
- Edge cases: a planned review-staging section rename records red through the funnel (the R2-1 escape) instead of a bare exit; an author-controlled value equal to an earlier marker's text no longer misroutes (C3's contrived reproduction; interior containment inside a multi-word quoted value remains a known limitation, disclosed in the predicate docstring); a mangled done-advisory threshold trips the new warning-only pin without failing the suite.

## Outcome

Hard-mode ERROR lines route to owning sections for every family named in the coverage row; the table's mappings and matching are pinned against wrong-section and misroute mutations by the selftest; the selftest arm is composed from the hoisted shared fixture builders; the drift guard reports through the outcome funnel while refusing immediately, its provenance comment completed; the done advisory's threshold sentence is covered by a warning-only placement pin and the two re-aim comments match the one-clause convention. All existing verdicts, exits, and readiness routing stay byte-stable.

Gate delta: none net - the placement pin is a warning-only presence row in an existing family (never moves the suite exit) and the drift-guard change re-routes an existing guard's emission channel only; no new gate, validator, lock, ledger, or ceremony.

## Standing constraints

- Print-layer and test-layer only: `ValidationResult.errors` keeps raw messages (errors[0] is the plan_readiness routing input and must stay byte-identical); no verdict, exit contract, or readiness routing change anywhere.
- No new gate, refusal class, schema field, lock, ledger, or ceremony; the drift guard's funnel routing changes only its emission channel, never when or whether it fires (the loop-site refusal stays immediate); the placement pin is one more warning-only presence grep in the existing `placement_pin` family.
- First-match-wins table order stays authoritative: a more specific marker goes ahead of the generic marker it narrows; the generic conservation marker keeps its place for the Markdown F-block reconciliation class (the finding-conservation family that reconciles Markdown `#### F<N>.` blocks against the sidecar).
- The pins drift-guard section list regenerates from the live table (the guard re-reads it), so the change verifies each new section string against the actual review-staging skill headings rather than editing a static list.
- Anti-growth: skill-side growth (none planned) would need its priced deletion in the same change; the done-advisory task nets bytes negative (two comments shrink more than the pin row adds).

## Evaluation Criteria

- Quality: the selftest arm asserts, per marker-family line, the exact expected `(review-staging SKILL.md, <section>)` suffix (mutation check: remapping any pinned marker to a wrong section fails the selftest); anchored matching kills the C3 reproduction (a value equal to an earlier marker's text no longer misroutes); the arm contains no private `finding()`/Markdown-block/payload/capture copies.
- Done when: all eight families from the coverage row map to owning sections with the precision nit's specific marker ahead of the generic conservation marker; both drift-guard sites emit `OUTCOME: fail` through the funnel and still refuse immediately; the provenance comment carries the r1 admission link and review date; the done-advisory pin row is present and green; both re-aim comments are one clause + citation; the origin rows flip covered in the landing.
- Ship when: the validator selftest, the pins suite, the plan-readiness regression, the public hygiene scan, and the em-dash gate all pass, and the suite still exits 0 with a final `OUTCOME: pass` line in the primary checkout.

## Review Scope

**Explicit must-fix:**
- `scripts/validate_review_staging.py`: pointer-table coverage rows and precision-nit marker, `_skill_clause_pointer` anchoring, selftest-arm suffix pinning and hoisted shared builders (Tasks 1-2).
- `scripts/check_maintenance_pins.sh` (Task 2, Task 3): drift-guard funnel routing with immediate refusal, provenance comment completion, done-advisory placement pin, re-aim comment trims.
- `docs/history/plans/2026-10-28-hard-mode-clause-pointer-residuals.md` (Task 0): this plan's own em-dash fix rides the same branch delta, so the em-dash ship gate passes over the full delta.

**Plan-related extension:** none.

### Task 0: Plan-bytes em-dash fence

- [x] Run `python3 scripts/fix_plan_em_dashes.py` over this plan file and verify `bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-28-hard-mode-clause-pointer-residuals.md` exits 0. [class: REPOSITORY_TEST]

Files: `docs/history/plans/2026-10-28-hard-mode-clause-pointer-residuals.md` (this plan, em-dash substitution only)

### Task 1: Pointer coverage extensions and selftest mapping checks

- [x] Derive, from the validator's live emit sites, the exact diagnostic-marker text for each family in the coverage row: version-1 sidecar field family, extensions.cap_closure family, extensions.corrections / corrections-verification family, the coverage families other than `coverage attempt record`, mint pair field family, the Metadata Review mode and clean-verdict/Last-fix-commit cross-field family, Superseded by link family, and the source_digest shape/stale family. [class: IMPLEMENTATION_REQUIRED]
- [x] Add each as a `(marker, section)` row with the section string taken byte-exact from the review-staging skill's heading or inline mention for that family's owner, keeping the counts-conservation and enum-before-generic ordering rules; add the precision nit's more specific marker ahead of the generic conservation marker. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the hard-mode selftest arm's pointer checks so every table entry (new and existing) is asserted against its exact expected suffix per Task 2's pinning shape, and retire/reshape the bare-marker recomputed check into those hardcoded per-family-line assertions (the bare markers no longer match once anchoring lands). [class: REPOSITORY_TEST]
- [x] Verify the pins suite's drift guard accepts every new section string against the skill, and add the extractor completeness assertion (extracted distinct-section count must equal the live table's distinct-section count, so extraction drift fails closed). [class: REPOSITORY_TEST]

Files: `scripts/validate_review_staging.py`, `scripts/check_maintenance_pins.sh`
Primary class anchors: `SKILL_CLAUSE_POINTERS` (coverage rows), `_skill_clause_pointer` (anchoring predicate), `_selftest_hard_mode_diagnostics` (suffix assertions).

### Task 2: Suffix pinning, anchored matching, hoisted fixtures, funnel routing

- [x] In the selftest arm: hardcode the expected `(review-staging SKILL.md, <section>)` suffix per origin-family line (T1), replacing the recomputed-mapping-only check's coverage gap. [class: REPOSITORY_TEST]
- [x] Hoist one shared capture helper from the arm-private `_captured()`/`call()` copies, extract a shared per-finding Markdown block builder out of `_current_findings_markdown` adding both Pattern and Severity bullets, and compose the arm from the shared builders (`_current_finding`, the new block builder, `_version1_payload`), segment-building the malformed variant and deleting the private copies (D2). [class: IMPLEMENTATION_REQUIRED]
- [x] In `_skill_clause_pointer`: anchor matching by quote position (occurrences immediately preceded by a quote are skipped except for the `_QUOTED_TEMPLATE_MARKERS` exemptions) so the C3 reproduction misroutes no more; keep `SKILL_CLAUSE_POINTERS` rows 2-tuples with the anchoring predicate derived inside the function so the drift guard's extractor regex keeps parsing. [class: IMPLEMENTATION_REQUIRED]
- [x] In `check_maintenance_pins.sh`: keep the drift guard's refusal immediate at each site (`{ echo ... >&2; emit_outcome fail; exit 1; }`, safe in the pipeline subshell because `emit_outcome` guards on `BASH_SUBSHELL`, `done || exit 1` retained) or move the loop to the main shell via a herestring (R2-1). [class: IMPLEMENTATION_REQUIRED]
- [x] Route the drift guard's PIN FAIL lines through `recorded_red_check` with stable names so a planned section rename can be recorded red, and add `--` before the section-string grep operand. [class: IMPLEMENTATION_REQUIRED]
- [x] Complete the drift-guard provenance comment with the r1 review-record admission link and review date (R2-4). [class: IMPLEMENTATION_REQUIRED]
- [x] Demonstrate in the run record: the C3 reproduction refused, one wrong-section remap failing the selftest, and one demonstrated-red guard firing (a temporarily renamed section string) emitting `OUTCOME: fail`. [class: REPOSITORY_TEST]

Files: `scripts/validate_review_staging.py`, `scripts/check_maintenance_pins.sh`
Primary class anchors: `_skill_clause_pointer` (anchoring), `check_maintenance_pins.sh` drift-guard block (funnel routing).

### Task 3: Done-advisory placement pin and re-aim comment trims

- [x] Add one `placement_pin "$PD"` row quoting a distinctive fragment of the done advisory's threshold sentence (re-derive the sentence's current location in `agents/skills/done/SKILL.md` at execution; verify exactly one occurrence of the quoted fragment before pinning; use the `grep -qF --` safe form the sibling rows model). [class: IMPLEMENTATION_REQUIRED]
- [x] Trim the two `# Re-aimed 2026-10-20` comments at the `$PD` rows to the plan citation plus one relocation clause, matching the adjacent one-clause convention. [class: IMPLEMENTATION_REQUIRED]
- [x] Pins suite green with the new warning-only row present; net byte delta negative for this task. [class: REPOSITORY_TEST]

Files: `scripts/check_maintenance_pins.sh`
Primary class anchors: `placement_pin` `$PD` rows (new pin row, trimmed comments).

### Origin-row resolution

All three origin rows resolve per the covered-row rule with this plan's landing as witness (`check_plan_origins_closed.py --mark-covered` rides the landing commit); the PLAN-PROMPTS entries `hard-mode-clause-pointer-residuals` and `done-advisory-threshold-pin-and-re-aim-comment-trim` prune at the landing per the log's rules.

## Validation Commands

```bash
python3 scripts/fix_plan_em_dashes.py docs/history/plans/2026-10-28-hard-mode-clause-pointer-residuals.md
python3 scripts/validate_review_staging.py --selftest   # embedded arm green
bash scripts/check_maintenance_pins.sh                  # exit 0, final OUTCOME: pass line
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_readiness.py -q
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh touched
```

## Assumptions

- The eight families' owning sections exist in `agents/skills/review-staging/SKILL.md` today (basis: the coverage row's parenthetical owner names, verified against the live skill at execution; a missing section would surface at the drift-guard check and narrow the task to the skill-side naming reality).
- The embedded selftest runs via a validator CLI flag (re-derive the exact invocation at execution from the validator's argparse; the arm is invoked in the file's selftest registry).
- The done advisory's threshold sentence survives verbatim at execution (basis: pinned indirectly by the owner file's pins; the pin task re-derives and fails loud on drift).
- Decision: which arm of the folded done-advisory row to take (add the placement pin vs record that the owner file's pins suffice). Receipt: add the warning-only row - the row's problem section demonstrates a mangled threshold passing all four done-file pins on a scratch copy, so the restatement gap is witnessed, and the pin family is warning-only by design; the recorded-sufficiency alternative stays the row's sanctioned fallback only if the advisory fragment cannot be pinned to exactly one occurrence. Source: backlog row 2026-10-20-done-advisory-threshold-sentence-unpinned.md; 2026-10-28.
- Decision: marker-anchoring mechanism (C3). Receipt: per-marker anchoring keyed to each marker's shape - prefix markers anchor at message start, mid-message enum markers anchor at their template position - rather than blanket `startswith`; evidence: the row's reproduction (a `risk_signals` value equal to `coverage attempt record`) misroutes only because matching is substring-anywhere, and several legitimate markers sit mid-message; the rows stay 2-tuples so the guard extractor keeps parsing, and the bare-marker recomputed check retires into the hardcoded suffix assertions. Source: row 2026-10-23-hard-mode-pointer-pinning-and-fixture-residuals.md C3; 2026-10-28.
- Decision: exact section strings for the new families. Receipt: use the review-staging skill's actual heading text per family, re-derived at execution from `agents/skills/review-staging/SKILL.md` - the coverage row's parenthetical names are pointers to owners, not byte-exact pins, and the drift guard holds the byte-exactness. Source: coverage row family list; 2026-10-28.
- Decision: R2-1 funnel-routing shape and scope. Receipt: keep the refusal immediate at each site with `emit_outcome fail` in the site braces (or a herestring loop), never a deferred `fail=1` inside the pipeline subshell; funnel routing delivers the final `OUTCOME:` line and, via the tasked `recorded_red_check` routing, the recorded-red escape for a planned rename; no other recorded-red surface changes. Source: same row R2-1 and the r1 review's F7/F8 findings; 2026-10-28.

Decision points requiring a grill: none remain.

Scope extensions (grilled): none proposed.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-23-hard-mode-pointer-coverage-extensions.md` covered: all coverage families landed and pinned (Tasks 1-2); status: covered (docs/history/plans/completed/2026-10-28-hard-mode-clause-pointer-residuals.md).
- `docs/history/backlog/2026-10-23-hard-mode-pointer-pinning-and-fixture-residuals.md` covered: exact-section pinning, anchored matching, shared fixture builders, funnel-routed drift guard, and the precision-nit marker split landed (Tasks 1-2 plus review r1 fixes); status: covered (docs/history/plans/completed/2026-10-28-hard-mode-clause-pointer-residuals.md).
- `docs/history/backlog/2026-10-20-done-advisory-threshold-sentence-unpinned.md` covered: the done-advisory threshold placement pin and the two comment trims landed with the same pins-suite change (Task 3); status: covered (docs/history/plans/completed/2026-10-28-hard-mode-clause-pointer-residuals.md).

## Completion pass (2026-10-31)

Executed by session zcode-exec-20261031-hardmode (resume carrier of the interactive exec mandate). Landing shape: worktree-first run on branch `2026-10-31-hard-mode-pointer-residuals` (base main@4f3639943), squash-landed via `land_squash.sh land-worktree`. Review rounds: r1 full panel (1 blocking: zero durable regression coverage for the anchoring predicate; fix commit ce8bf7c96) then r2 fresh full panel hard-validated with verdict ready=yes and zero blocking findings (`.ai-playbook/reviews/2026-10-31-hard-mode-clause-pointer-residuals-code-review-r2.md`; seven non-blocking residuals deferred with durable capture in `docs/history/backlog/2026-10-31-clause-pointer-r2-residual-improvements.md`).

Task 2's demonstration record (the bullet's run-record requirement): the C3 reproduction refusal, one wrong-section remap failing the selftest, and one demonstrated-red guard firing with final `OUTCOME: fail` were each performed against the run tree and logged in the session's task-2 implement log and r2 panel verification notes; the r2 testing lens independently reproduced all three mutations against the committed state (probe-verified, restored clean), which is the durable witness this completion pass cites.
