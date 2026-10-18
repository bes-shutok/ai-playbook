# Plan: review round record lifecycle gaps

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-review-round-copies-stale-supersession-link.md`
- `docs/history/backlog/2026-10-05-review-round-usage-mint-ordering.md`
- `docs/history/backlog/2026-10-05-review-selection-orphan-record-fence.md`

Driving force: reliability (three witnessed 2026-10-05 record-lifecycle failures across one live execution's Phase 3 review rounds: a new round record inherited its predecessor's `Superseded by:` link and the supersession helper then refused to bind the chain, a five-worker panel launched without the usage mint so the round's per-run attribution is permanently lost, and one canonical record left without its sidecar by an interrupted synthesis blocked every later fresh review with no documented recovery; every review round in every lane crosses this record lifecycle, so each gap taxes every review)

Plan review record: the staging series docs/reviews/2026-10-05-plan-review-review-round-record-lifecycle-gaps-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Record pair: the canonical review record Markdown and its `.stats.json` sidecar sharing a stem under the reviews directory; selection allocates pairs, and a canonical Markdown without its sidecar is an orphan.
- Selector: `scripts/review_record_selection.py` (`select`, `mark-superseded`, `backup`); `select` refuses fail-closed on a sidecar digest mismatch without `--explicit-new-round`, and `mark-superseded` appends exactly one `Superseded by:` Metadata line to the prior record, refusing a prior already marked.
- Supersession link: the `Superseded by: <successor>` Metadata line; per the staging skill's Metadata contract it is supersession-rounds-only, lives in the prior record, and is written by the helper, never by hand.
- Round copy: constructing a new round record from a prior record's body; the witnessed defect is the prior's `Superseded by:` line surviving the copy into the successor.
- Usage mint: `scripts/review_usage_capture.py mint`, run at the start of staging a review round before workers launch; it prints `review_run_id` and `minted_at_ms`, carried verbatim into the record's metadata as `review-run-id` and `review-started-at-ms` and merged as the sidecar `usage` field at capture time.
- Bare-capture fallback: the documented `review_usage_capture.py --json` form without identity arguments, used only when a round genuinely lost its mint; its record stays non-attributable and must never be estimated or hand-authored.
- Orphan: a canonical review Markdown with no matching sidecar (a partially written pair from a crashed synthesis); the selector's orphan refusal is correct fail-closed behavior and stays.
- Orphan recovery: the new auditable operation that preserves the orphan under a non-discoverable name, allocates a fresh canonical pair for the same slug, and records an evidence link to the preserved orphan in the new record's Metadata.
- Validator date gates: the validator's existing mechanism for applying new requirements only to records dated on or after a constant (`EXTENDED_SIDECAR_MIN_DATE`, `RECORD_KIND_SIDECAR_MIN_DATE` precedents); this plan adds its gates behind the same mechanism so the historical corpus keeps validating.

## Why

One live execution hit all three failures inside a single Phase 3 chain: round construction copied a stale supersession link, the panel launched before the mint ran, and a crashed synthesis stranded an orphan that fail-closed the selector with no documented way out. Each row's refused path already fails closed (the helper refused the stale chain, the missing mint has a documented non-attributable fallback, the orphan refusal fired before any mutation); what is missing is the successor-side hygiene that prevents the stale link, the mechanical enforcement that makes the mint-first duty impossible to skip silently, and the sanctioned recovery that unblocks the orphan class without letting partial records masquerade as validated reviews. The three rows share one record lifecycle and two scripts, so one plan keeps the refusal vocabulary and the metadata contract coherent instead of drifting across three landings.

## Outcome

- A new round record never carries a `Superseded by:` line: the round-copy workflow strips prior-only links before validation, and the validator refuses a record whose supersession link resolves to itself, so the helper's bind step can never meet a stale self-referential chain again.
- Review usage attribution stops being optional in practice: a canonical record dated on or after the gate date must carry either the minted `review-run-id`/`review-started-at-ms` pair or the named bare-capture-fallback marker, so a skipped mint surfaces at validation as the documented fallback instead of silently losing attribution.
- An orphaned pair has one auditable recovery: `recover-orphan` preserves the orphan byte-identical under a discovery-invisible name, allocates the fresh canonical pair for the same slug, and writes the evidence link into the new record's Metadata; partial records still never validate.

Gate delta: one new validator refusal class (a self-referential supersession link), one new validator presence gate behind a date constant (the mint pair or the fallback marker), one new selector subcommand with its own refusal set (not-an-orphan, missing record, already-preserved `.orphan-` path), and one targeted optional format gate over the new `Orphan recovery:` metadata line (Markdown Metadata keys stay ungated; no allowlist is introduced). Each is priced by its witnessed row; no existing refusal weakens: the selector's digest-mismatch and orphan refusals, `mark-superseded`'s already-marked refusal, and the bare-capture fallback all keep their semantics.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so Step 1.4 confirmation is satisfied by the rows' validated records rather than a live interview; basis: the maintenance loop's authoring blueprint (loop_mode dual, continuous pacing amendment 2026-09-30).
- assume the fallback marker's literal is `usage-attribution: bare-capture-fallback` in the record's Metadata block; basis: the validator's metadata contract is literal-keyed, the fallback is already a named documented mode, and a presence gate needs one exact spelling to be mechanical.
- assume the mint-presence gate rides a new validator date constant so records dated before the plan's landing date keep validating without the pair; basis: the validator's own `EXTENDED_SIDECAR_MIN_DATE` and `RECORD_KIND_SIDECAR_MIN_DATE` precedents and the hundreds of historical records that predate the mint duty.
- assume the validator cannot verify the mint pair's verbatim-ness (it sees only the record), so the gate is presence-and-format; the verbatim-carry duty stays a skill-text obligation enforced by the launch orchestration citation; basis: the mint output exists only in the round's session context and the capture script's own store.
- assume `recover-orphan` allocates the fresh pair by reusing the selector's existing allocation logic rather than inventing a second naming scheme; basis: the orphan row asks for a fresh canonical pair for the same slug, and `select` already owns the `-r<N>` allocation and the kind-prefixed naming.
- assume the preserved orphan's name form is `<original stem>.orphan-<UTCtimestamp>.md` so discovery, selection, and validation glob shapes never match it; basis: the reviews directory's canonical naming (`<date>-<kind>-<slug>-r<N>.md`) is stem-indexed, and the suffix keeps the original bytes findable for the evidence link.
- assume Task 1's validator arm refuses exactly the self-referential link (the record's `Superseded by:` resolving to the record's own path); basis: that is the witnessed shape, the general stale-link class is prevented upstream by the strip duty, and a wider shape-guessing refusal risks false positives on historical records the date gate does not cover.
- assume Task 2 touches agents/skills/review-plan/SKILL.md only to cite the staging skill's mint procedure at the panel-launch step (the integration-point citation duty), not to restate the procedure; basis: the staging skill owns the mint paragraph today (its usage-capture region) and the cross-cutting documentation rule keeps one owner.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the review record lifecycle gains successor-side supersession hygiene, a mechanically enforced mint-first duty with a named fallback marker, and one auditable orphan-recovery operation.

Before (today): a round record cloned from its predecessor carries the predecessor's `Superseded by:` line, and the helper refuses to mark the chain, leaving a self-referential link. A panel launches without `mint`, and the round's usage is permanently non-attributable with nothing surfacing the omission. An interrupted synthesis leaves a canonical Markdown without its sidecar, and every later `select` refuses until a human improvises a repair.

After (this plan): round construction strips the prior-only link (the skill says so; the validator refuses a self-referential link that slips through). A canonical record validates only with the minted identity pair or the named bare-capture-fallback marker, so a skipped mint is a visible, documented fallback decision. `recover-orphan` preserves the partial record under a discovery-invisible name, allocates the fresh pair, and links the evidence, and the whole procedure is documented in the staging skill beside the selection flow it repairs.

Edge cases pinned: a successor record whose `Superseded by:` resolves to itself refuses validation naming the line; a prior record marked by the helper validates unchanged; a record dated before the gate date needs neither the mint pair nor the marker; a record at or after the gate date with neither refuses with both remedy spellings named; a record with the marker but no pair validates as non-attributable; `recover-orphan` on a record whose sidecar exists refuses as not-an-orphan; `recover-orphan` on an absent record refuses; the preserved orphan keeps its bytes byte-identical and its name never matches the canonical discovery glob; the fresh pair's Metadata carries the `Orphan recovery:` link and the pair validates; a second `recover-orphan` on the same preserved orphan refuses.

## Tasks

### Task 1: Supersession-link hygiene on round copies

Files:
- `agents/skills/review-staging/SKILL.md`
- `scripts/validate_review_staging.py`
- `scripts/test_review_record_selection.py`

Evidence:
- `python3 scripts/test_review_record_selection.py`; covers every criterion below at the task boundary (main-shim suite)
- `python3 scripts/validate_review_staging.py --selftest`; covers the validator's own selftest staying green
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks

- [x] `test_self_referential_supersession_link_refuses` (given a record whose Metadata `Superseded by:` value resolves relative to the record's own directory back to the record's own path, expects the named refusal; given the witnessed copy shape (a new round record holding the prior's link), expects the refusal to name the line and the strip duty; given a correctly marked prior record whose link resolves to a real successor, expects validation unchanged) [class: REPOSITORY_TEST]
- [x] Skill text, round-copy strip duty: the staging skill's selection-and-supersession region gains the construction rule: when a new round record is built from a prior record's body, the prior's `Superseded by:` line is stripped from the successor before validation (the line is supersession-rounds-only, lives in the prior record, and only `mark-superseded` writes it); the existing Metadata template line keeps its do-not-hand-write wording and gains the strip-on-copy sentence [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the self-reference refusal in scripts/validate_review_staging.py: resolve the record's `Superseded by:` Metadata value against the record's own directory and refuse (named line, no mutation) when it resolves to the record itself; the refusal text names the strip duty and the helper as the only writer of the line [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full suite, the validator selftest, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: review records strip inherited supersession links and refuse self-references` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Mint-first presence gate with the named fallback marker

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `scripts/validate_review_staging.py`
- `scripts/test_review_record_selection.py`

Evidence:
- `python3 scripts/test_review_record_selection.py`; covers every criterion below at the task boundary
- `python3 scripts/review_usage_capture.py --selftest`; covers the mint producer's selftest staying green
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks

- [x] `test_mint_pair_presence_gate` (a record_kind-canonical record dated on or after the new gate constant validates with the `review-run-id`/`review-started-at-ms` pair present in well-formed shape (worker-evidence and reconciliation records stay outside the gate, mirroring the coverage fence); the same-date record with neither the pair nor the marker refuses naming both remedy spellings; the same-date record with the `usage-attribution: bare-capture-fallback` marker validates as non-attributable; a record dated before the gate constant validates with neither, unchanged) [class: REPOSITORY_TEST]
- [x] `test_mint_pair_format_gate` (a record carrying a pair with an empty or non-32-hex `review-run-id`, or a non-positive-integer `review-started-at-ms`, refuses with the malformed field named, matching the capture producer's own grammar; a well-formed pair validates) [class: REPOSITORY_TEST]
- [x] Implement the presence gate in scripts/validate_review_staging.py behind a new date constant set to the landing date plus one day (the precedent convention, so same-day records stay exempt as the existing constants' fence notes do): for record_kind-canonical records dated on or after it, require the well-formed mint pair or the exact `usage-attribution: bare-capture-fallback` Metadata marker; refusals name both remedy spellings (run the mint before workers launch per the staging skill, or record the fallback marker only when the mint is genuinely lost) [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, enforcement sentence: the staging skill's usage-capture region (which already mandates the mint at round start and the verbatim carry) gains the consequence sentence: a canonical record at or after the gate date validates only with the minted pair or the fallback marker, so a skipped mint must be recorded as the marker, never left silent [class: IMPLEMENTATION_REQUIRED]
- [x] Review-plan launch citation: the panel-launch step of agents/skills/review-plan/SKILL.md cites the staging skill's mint procedure as a launch precondition (one sentence pointing at the owning paragraph; the procedure itself is not restated, and the cross-reference names the launch-blocking consequence from this plan's gate) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full suite, the mint selftest, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: review records gate the usage mint pair or the named fallback marker` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Auditable orphan recovery operation

Files:
- `scripts/review_record_selection.py`
- `scripts/test_review_record_selection.py`
- `agents/skills/review-staging/SKILL.md`
- `scripts/validate_review_staging.py`

Evidence:
- `python3 scripts/test_review_record_selection.py`; covers every criterion below at the task boundary
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks

- [x] `test_recover_orphan_happy_path` (given a canonical Markdown with no matching sidecar, expects `recover-orphan` to preserve the orphan byte-identical at `<original stem>.orphan-<UTCtimestamp>.md`, emit the fresh canonical pair paths for the same slug and kind, print a receipt naming the preserved path and the allocated pair, and exit 0; the preserved name never matches the canonical discovery glob, and the canonical orphan path is vacated by the recovery (renamed, not copied), proven by a follow-up `select --explicit-new-round` for the same slug succeeding post-recovery) [class: REPOSITORY_TEST]
- [x] `test_recover_orphan_refusals` (arms: a record whose sidecar exists refuses as not-an-orphan; an absent record refuses; a second `recover-orphan` naming an already-preserved `.orphan-` path refuses; every refusal is a named one-line error leaving the reviews directory byte-identical) [class: REPOSITORY_TEST]
- [x] `test_orphan_recovery_link_validates` (given the fresh record created per the recovery procedure with `Orphan recovery: <preserved orphan path>` in its Metadata, expects the recovery pair to validate end-to-end; given a malformed link value (an absolute path or a path escaping the reviews directory), expects the named format refusal; given the preserved orphan itself offered for validation, expects the canonical discovery and validation shapes to never select it) [class: REPOSITORY_TEST]
- [x] Implement the `recover-orphan` subcommand in scripts/review_record_selection.py taking `--record` plus `--slug` and the optional `--kind` (forwarded to the existing allocation exactly as `select` takes them; the slug and kind are never inverse-parsed from the preserved stem, whose alias analysis is documented ambiguous for infixed slugs): refuse when the named record has a matching sidecar (not an orphan), does not exist, or already carries the `.orphan-` infix (already preserved, so a second recovery cannot double-suffix); preserve the orphan byte-identical under the discovery-invisible name; allocate the fresh canonical pair for the same slug and kind through the existing allocation logic; print the receipt naming the preserved path, the allocated pair, and the evidence-link Metadata line to add (the preserved path spelled repo-relative so the printed line passes the Task 3 format gate verbatim) [class: IMPLEMENTATION_REQUIRED]
- [x] Validator format gate: Markdown Metadata keys are ungated in scripts/validate_review_staging.py (only targeted per-label gates exist; no Markdown allowlist is built, so the historical corpus keeps validating unchanged), and this task adds one targeted optional gate: when an `Orphan recovery:` line is present, its value must be a repo-relative path under the reviews directory, refusing a malformed link [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, recovery procedure: the staging skill's selection region gains the documented recovery procedure per the origin row (preserve the orphan, allocate the fresh pair, record the evidence link, never let a partial record validate), placed beside the selection flow it repairs, with one sentence naming the real retention classification: the preserved orphan stays in the retention scan as an unpaired-retained unit that is reported every run and never auto-pruned, requiring explicit handling at prune review, unlike backup copies which prune as pairs [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full suite, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: recover-orphan preserves stranded review pairs and links the evidence` [class: IMPLEMENTATION_REQUIRED]

## Review Scope

Files in scope (the union of the task Files lists): `agents/skills/review-staging/SKILL.md`, `agents/skills/review-plan/SKILL.md`, `scripts/validate_review_staging.py`, `scripts/review_record_selection.py`, `scripts/test_review_record_selection.py`.

Reviewers judge: fail-closed preservation (the selector's digest-mismatch and orphan refusals, `mark-superseded`'s already-marked refusal, and the bare-capture fallback keep their semantics), the date-gate mechanism's correctness (historical corpus keeps validating; the gate binds exactly the new requirements), the recovery operation's auditability (byte-identical preservation, discovery-invisible naming, evidence link), the metadata contract's coherence (one exact fallback marker spelling, one new accepted key), scope discipline (no task reaches beyond its Files list), and test reality (every criterion has a named test runnable in this repository).

## Validation Commands

```bash
python3 scripts/test_review_record_selection.py
python3 scripts/validate_review_staging.py --selftest
python3 scripts/review_usage_capture.py --selftest
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-review-round-record-lifecycle-gaps.md
```

## Disposition

- Outcome: executed; the landing squash commit is the landing witness on main.
- Tasks 1-3 complete; all checkboxes ticked; implementation commits 9b1146d1 (Task 1), b4d24eca (Task 2), a0a93cad (Task 3), plus the r1 fold 4b77317d (staging-path predicate excludes preserved orphans across all kind shapes with the newest_staging_for_branch None probe; the mint kind exemption pinned at the gate date).
- Exec review: r4 fresh adversarial (one blocking: the preserved-orphan name was staging-visible for plan-review/branch-review shapes because STAGING_NAME_RE's rN tail is optional; folded in 4b77317d) then r5 verification ready=yes (one residual Low recorded: _validate_slug_and_kind refuses the backup infix but not the orphan infix, so an operator slug embedding .orphan- could mint a discovery-invisible canonical record; no witnessed case, corpus clean; one-arm remedy shape noted for a future fence); records + sidecars at docs/reviews/2026-10-05-plan-review-review-round-record-lifecycle-gaps-r{4,5}.md; the readiness digest-stale reading on the ticked bytes is the designed mid-loop state resolved by the r5 binding.
- Gates on the exec bytes: selection suite 54 tests OK; validator selftest ok (581 checks); mint selftest ALL PASS; retention suite 10 passed; pins OUTCOME: pass; em-dash added-lines exit 0; hygiene PASS.
- Deferred residuals: the r5 slug-infix asymmetry Low (non-blocking, remedy shape one added refusal arm in _validate_slug_and_kind).
