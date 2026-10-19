# Plan: restore strict-readiness reachability for legacy review-record series

Backlog origins (scope of record):

- docs/history/backlog/2026-10-17-review-record-legacy-identity-blocks-readiness.md

Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-review-record-legacy-identity-blocks-readiness-pb0c5cfe2-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/review-record-legacy-identity-blocks-readiness.md (session sess_d7b16c2e-0ca5-4449-8d37-07e65ed62f54)

## Terms

- strict readiness consult: the full `scripts/plan_readiness.py` gate over a plan's review-record series (as opposed to the `--pre-round` structural probe, which never consults review records).
- AmbiguousReviewSeries: the fail-closed exception `scripts/plan_readiness.py` raises when one slug's review-round candidates cannot be scoped to a single source plan.
- plan identity: the repo-relative source-plan path a review record carries, read from the sidecar's `extensions.plan_identity` or the record's `URL or Artifact:` line.
- identity-bearing record: a review record whose plan identity resolves to a value.
- identity-unresolvable record: a review record carrying neither identity form; in this home these are the pre-convention records (the convention landed 2026-10-16, commit 5de323de9).
- pure-legacy series: a slug's candidate set in which zero records carry any plan identity.
- mismatch: an identity-bearing record whose plan identity names a different source plan; today's disposition is a silent exclusion from the match, never a raise.
- stats sidecar: the `<record>.stats.json` twin of a review record, carrying the schema fields, `source_digest`, verdict, and counts the readiness shared gate grades.
- stats-skip waiver: the staging-validation escape hatch where a record's Metadata declares `Stats sidecar: skipped` and, with zero staged findings and no digest probe, validation passes without the sidecar file.
- canonical record: a record whose sidecar `record_kind` is `canonical` (a normal plan-review round, as opposed to worker-evidence records).
- re-bind round: a record re-stamped under a corrected filename (for example the tokened form) after a citation or naming correction.
- defective pair: a review record whose stats sidecar is missing (or whose sidecar is unrecoverable) while the record's own Markdown carries its review metadata.
- repair tool: the new transcription script `scripts/regenerate_review_sidecar.py` that rebuilds a missing sidecar from its own record's Markdown fields.
- repair census: the per-run inventory the repair tool prints and writes to a receipt file, naming every repaired pair and every refused record.
- advisory line: a non-blocking warning the readiness consult prints from its pass path (excluded or lexically-resolved record names, and the regeneration notice); it never changes the consult's outcome.
- advisory out-parameter: the optional list parameter the resolver, the selector, and `evaluate_readiness` gain; `main` owns the list, `evaluate_readiness` threads it down to the resolver, and neither the resolver nor `evaluate_readiness` prints or gains module-level state.
- regenerated sidecar: a sidecar the repair tool wrote, marked `extensions.regenerated_from_markdown: true`.
- mint pair: the Metadata lines `review-run-id` and `review-started-at-ms` minted per review round.
- Record kind twin: the Metadata line `Record kind: canonical`, the Markdown-side mirror of the sidecar's `record_kind` and the only kind signal a sidecar-less record carries.
- rank guard: the fail-closed rule that an identity-unresolvable record whose round outranks the resolved identity-bearing latest round refuses with a named reason instead of being excluded.
- repairable class: the defective pairs whose recorded source digest still matches the live plan bytes at the recorded identity path, the only class the campaign repairs.

## Why

The source-plan identity convention made strict readiness raise on every slug series that contains pre-convention review records, and most of the reviews home predates it (the plan's 2026-10-17 re-measurement over the live home counted 919 of 3280 records resolving no identity; the origin row's same-day census recorded 854, and 261 sidecar-less records, before the day's landings grew the home). Certified, execution-ready plans are unreachable for strict consults because of record bookkeeping, not because of any review defect.

## Gist & Examples

TLDR: strict readiness stops raising on identity-unresolvable legacy review records and defective pairs gain a repair path, so certified plans in mixed or legacy series become reachable again without weakening any identity-bearing protection.

Before: the rearm-dispatch series (a legacy untokened r1 beside the certified p7ffd23f5 r1-r3) refuses every strict consult with "cannot resolve plan identity"; a re-bind round written without its sidecar (the personal-project r4) refuses with "missing stats sidecar for latest round r4"; a series containing only legacy records refuses exactly like a mixed one (both shapes reproduced 2026-10-17 against `latest_review_round`); the record selector refuses the same series through its own identity loop.

After: identity-unresolvable records at or below the resolved round are excluded from the identity match and named in an advisory line; an unresolvable record outranking the resolved round keeps a fail-closed raise with a named reason; a series with zero identity-bearing records of any plan resolves lexically (highest rN, ties by filename) with the same advisory; the duplicate-round raise and the silent mismatch exclusion stay for identity-bearing records; the selector applies the same rank-guarded disposition (a suppressed highest round refuses before any allocation or reuse decision) and resolves a pure-legacy series lexically, continuing allocation from its highest existing round; a canonical record can no longer declare the stats-skip waiver at staging validation; the witnessed defective-pair shape gains a transcription repair path with refuse-never-overwrite, in-place validation with delete-on-refusal, twin append, dry-run, receipt, and own-marker-retry arms.

## Outcome

Strict readiness consults and record selection reach a verdict for every plan whose series merely contains pre-convention or defective records, while every protection the identity convention added for identity-bearing records keeps its current behavior exactly.

- A mixed series resolves to its identity-bearing latest round and names the excluded legacy records in an advisory line; a pure-legacy series resolves lexically with the advisory line, matching the pre-convention behavior.
- The selector applies the same rank-guarded exclusion to complete pairs, so the next staging round on a certified plan's slug no longer blocks on its legacy records, and a pure-legacy series continues allocation from its highest existing round instead of minting a parallel chain; an identity-unresolvable half keeps the orphan-completeness refusal, and a half carrying a foreign plan identity keeps today's silent skip.
- A canonical record can no longer declare the stats-skip waiver at staging validation, so the writer-side gap surfaces when the record is written instead of at a later readiness consult.
- Defective pairs whose recorded digest still matches their plan's live bytes gain a repair path demonstrated on the witnessed shape; the live-home campaign run delivers the census, repairing the repairable class and naming every refused pair with its reason.

Gate delta: two refusal surfaces narrowed (the blanket "cannot resolve plan identity" raise in `latest_review_round` and its parallel identity raise in the selector's `_record_plan_identity` loop; the paying sibling for the additions below, both over-broad forms whose protection the narrowed rule keeps through the rank guard raise and the duplicate-round raise); one waiver narrowed (the waiver survives only where a readable `Record kind:` twin declares a non-canonical kind; a canonical twin or an unreadable twin refuses fail-closed at staging validation; priced by the witnessed integrity failure the origin row records: a canonical record entered the reviews home without its sidecar twin and blocked a certified lane the same day, the failure shape the waiver currently authorizes at staging time); one new non-gate repair tool (sidecar transcription plus a single Record-kind twin append line, fail-closed with delete-on-refusal cleanup, dry-run, receipt file, never touches a foreign sidecar; a corrected-Markdown retry may rewrite only its own marker-bearing sidecar); one additive optional sidecar extensions member (`regenerated_from_markdown`; paid by the repair census and its receipt file obviating a separate repair-ledger surface; descriptive-only, no gate keys tolerance on it); advisory lines and one report-only consult notice keyed on the regenerated marker are report-only in both consumers (no gate outcome keys on the marker); no new ledger, review round, or gate.

## Assumptions

- assume the identity convention's identity-bearing protections (the duplicate-round raise, the silent mismatch exclusion, the filename token checks) are correct as landed and only the unresolvable-record disposition is defective; basis: the origin row's Expected section and the 5de323de9 landing witness.
- assume the staging Markdown record is the primary review record whose metadata mirrors the sidecar's evidence fields, so transcription regenerates derived data without inventing evidence; basis: the witnessed r4 record carries Source digest, panel counts, findings count, verdict status, the mint pair, and the identity line in its own body.
- assume pre-convention records gain identity only through the repair campaign's explicit transcription scope, never by guessing a plan path from the slug; basis: per-record identity is not mechanically derivable for records whose plan path is unrecorded (the origin row's Problem section prices the census scale).
- assume the transcription field taxonomy splits into transcribed fields, derived fields (named constants and values built only from the record's own lines), and defaulted-empty fields; no evidence-bearing field is ever defaulted; basis: the version-1 sidecar contract's required-field set versus the staging Markdown template's mirrored subset.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the reproduced refusal shapes flip (mixed series returns the identity-bearing latest with an advisory; pure-legacy series returns the lexical latest with an advisory) while the rank-guard, duplicate-round, and foreign-bearing probes keep their fail-closed outcomes and the mismatch exclusion stays silent (no raise, no advisory), each pinned by its own test on an isolated temp home.
- compatibility: the readiness, selection, and staging suites pass with only contract-following test updates, including the must-flip pin that asserts the old blanket raise text.
- docs parity: the verified stale-text inventory (review-plan and plans skill series lines, the staging skill's refusal text, waiver scope, orphan-recovery routing, and trust-anchor sentence) is reconciled in the same landing; the pins suite stays green.

**Done when:**
- a strict readiness consult over a mixed series passes and names the excluded record in an advisory line
- an unresolvable record outranking the resolved round still refuses with a named reason (test)
- a pure-legacy series resolves the highest rN lexically with the advisory line, duplicate rounds included
- a foreign-bearing series with unresolvable strays keeps the no-artifact refusal (test)
- the selector admits a mixed series with the advisory discipline, refuses a mixed series whose highest round is unresolvable above the resolved round before any allocation or reuse decision, resolves a pure-legacy series lexically continuing from its highest existing round, keeps the foreign-half silent skip, and retains its duplicate-round refusal for identity-bearing series (test)
- the readiness consult prints the regeneration notice on its pass path exactly when the resolved sidecar carries the marker (test)
- staging validation refuses a record whose twin declares canonical or whose twin is unreadable when it declares the stats-skip waiver (test) while a record declaring a non-canonical kind keeps the waiver
- the repair tool rebuilds the witnessed r4-class sidecar from the record's own fields under the rule-closed taxonomy, marks it regenerated, refuses incomplete records and foreign sidecars, validates before it promotes, honors dry-run, writes the receipt file, and the repaired series passes the strict consult
- the live-home campaign run delivers the census with its receipt file, repairing the repairable class and naming every refused pair with its reason
- the readiness and selection suites, the staging validator selftest, the pins suite, and the public hygiene scan all exit 0

**Ship when:**
- none; this repository is the release surface for its own scripts and skills.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py` *(modified)*
- `scripts/review_record_selection.py` *(modified)*
- `scripts/validate_review_staging.py` *(modified)*
- `scripts/regenerate_review_sidecar.py` *(new)*

**Tests:**
- `scripts/test_plan_readiness.py` *(modified)*
- `scripts/test_review_record_selection.py` *(modified)*

**Skill and docs surfaces:**
- `agents/skills/review-plan/SKILL.md` *(modified, series-semantics lines only)*
- `agents/skills/plans/SKILL.md` *(modified, review-series metadata line only)*
- `agents/skills/review-staging/SKILL.md` *(modified, refusal text, waiver scope, orphan-recovery routing, and the trust-anchor sentence only)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/review_record_selection.py` selection refusal NAMING for the usage-error path and its review-family scoping; reason: those two defects have their own routed work entry, and this plan touches only the selector's identity disposition
- `scripts/machinery_registry.json` rows; reason: verified none describes the changed refusal semantics, so the reconciliation task verifies absence and edits nothing unless verification says otherwise
- bulk edits to reviews-home records other than the defective pairs the repair census lists; reason: record surgery outside the defective class is unrequested work

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_readiness.py scripts/test_review_record_selection.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/validate_review_staging.py --selftest
bash scripts/check_maintenance_pins.sh
```

The public hygiene scan (the user facts document's `public_hygiene_scan_script`) runs over the changed files and exits 0 before landing.

### Task 1: Narrow the series-identity disposition in the readiness resolver and the record selector

Context surface: the plan's Terms and this task.

Files:
- `scripts/plan_readiness.py` *(modified)*
- `scripts/review_record_selection.py` *(modified)*
- `scripts/test_plan_readiness.py` *(modified)*
- `scripts/test_review_record_selection.py` *(modified)*

Primary class anchors:
- `latest_review_round` in `scripts/plan_readiness.py`
- `AmbiguousReviewSeries` in `scripts/plan_readiness.py`
- `_record_plan_identity` in `scripts/review_record_selection.py`

- [x] `latest_review_round` delivers `legacy-exclusion`: given a mixed series where every identity-unresolvable record's round is at or below the resolved identity-bearing latest round, expects the highest identity-bearing round returned and every excluded record named in the advisory out-parameter, with no raise [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (rank guard): given an identity-unresolvable record whose round outranks the resolved identity-bearing latest round, expects the fail-closed raise with a named reason identifying the outranking record [class: REPOSITORY_TEST]
- [x] `latest_review_round` delivers `pure-legacy lexical fallback`: given a series with zero identity-bearing records of any plan, expects the highest-rN record returned (ties by filename, duplicates included) as the pre-convention selection resolved, with the advisory naming the lexical resolution [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (foreign-bearing series): given identity-bearing records for other plans plus identity-unresolvable strays and a consulting plan owning none, expects the no-artifact refusal, never a lexical fallback [class: REPOSITORY_TEST]
- [x] Safety witness (unchanged protections): given two identity-bearing records claiming the same round for one source plan, expects the duplicate-round raise; given an identity-bearing record naming a different source plan, expects the silent mismatch exclusion without an advisory [class: REPOSITORY_TEST]
- [x] Advisory channel shape: expects the resolver's 2-tuple return unchanged with an optional advisory out-parameter list threaded by `evaluate_readiness` and printed as one non-blocking advisory line on the consult's pass path beside the coverage warnings; no printing or module state in the resolver; identity-less invocations keep today's silent lexical resolution [class: IMPLEMENTATION_REQUIRED]
- [x] Selector parity: expects the selector's pair enumeration to apply the same rank-guarded exclusion and advisory discipline to complete pairs, advisories arriving through an `advisories` array in the select JSON envelope, the duplicate-round refusal retained for identity-bearing series [class: IMPLEMENTATION_REQUIRED]
- [x] Selector orphan boundary: an identity-unresolvable half keeps the orphan-completeness refusal and keeps surfacing for repair, and a half carrying a foreign plan identity keeps today's silent skip [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (orphan retention): given plan-review selection with a source plan over a series whose sidecar-less record resolves no identity, expects the orphan-completeness refusal naming the half on both the reuse and the allocation path, never an advisory exclusion or an allocation [class: REPOSITORY_TEST]
- [x] Safety witness (foreign-half silent skip): given a series containing a sidecar-less record whose Markdown identity names a different plan, expects no refusal and the half never named in any orphan or advisory output on both the reuse and the allocation path [class: REPOSITORY_TEST]
- [x] Safety witness (selector rank guard): given a mixed series whose highest round is an identity-unresolvable record above the resolved identity-bearing round, expects the selector refusing with a named reason identifying the outranking record on both the reuse and the allocation path, before any allocation or reuse decision [class: REPOSITORY_TEST]
- [x] Selector pure-legacy disposition: given a series with zero identity-bearing pairs, expects the selector resolving the highest-rN record lexically (ties by filename, duplicate rounds included, mirroring the resolver) and continuing allocation from the highest existing round, never minting a parallel r1 chain [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: on isolated temp-home fixtures, the mixed-series and pure-legacy probes raise the blanket identity raise today, and the selector refuses them [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN, including the must-flip pin that asserted the old raise text, updated to the narrowed contract [class: REPOSITORY_TEST]
- [x] Commit: `feat: exclude identity-unresolvable review records from the series identity match` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Narrow the stats-skip waiver for canonical records at staging validation

Context surface: the plan's Terms and this task.

Files:
- `scripts/validate_review_staging.py` *(modified)*
- `scripts/test_plan_readiness.py` *(modified)*

Primary class anchors:
- `validate_staging_file` in `scripts/validate_review_staging.py`
- `metadata_allows_stats_skip` in `scripts/validate_review_staging.py`

- [x] Waiver narrowing: given a record whose Metadata `Record kind:` twin declares canonical and whose stats-skip waiver is declared with zero staged findings and no sidecar file, expects staging validation refusing with the reason naming the missing sidecar; the narrowing reads the twin line (the only kind signal a sidecar-less record carries) [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a canonical record with its sidecar present, expects validation unchanged, adding no finding [class: REPOSITORY_TEST]
- [x] Scope guard: given a worker-evidence or other record declaring a non-canonical kind, expects the stats-skip waiver to remain available unchanged [class: REPOSITORY_TEST]
- [x] Boundary witness (undeclared kind): given a canonical-intent record declaring the waiver with no readable `Record kind:` twin on an undated or pre-fence-dated name, expects the waiver refused fail-closed with the missing-sidecar reason, never silently honored [class: REPOSITORY_TEST]
- [x] Readiness parity: given the readiness consult's existing waiver-disabled path, expects its current refusal text unchanged (the readiness gate already passes the expected digest and never honored the waiver) [class: REPOSITORY_TEST]
- [x] Run → expect RED: on a temp-home fixture, a canonical record declaring the waiver passes staging validation today [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: refuse a canonical review record declaring the stats-skip waiver` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Repair the defective pairs

Context surface: the plan's Terms and this task.

Files:
- `scripts/regenerate_review_sidecar.py` *(new)*
- `scripts/test_plan_readiness.py` *(modified)*

Primary class anchors:
- `main` in `scripts/regenerate_review_sidecar.py`

- [x] Transcription taxonomy (rule-closed set): expects the regenerated sidecar to carry the complete version-1 required top-level field set plus the extended freshness set, partitioned into the transcribed, derived, and defaulted classes with no required field unassigned [class: IMPLEMENTATION_REQUIRED]
- [x] Transcription taxonomy (transcribed class): given the witnessed r4-class record, expects the transcribed class reading verbatim from the record's own Metadata lines: source digest, verdict, counts, panel rows, findings, round, date, identity, mint pair, review type, panel mode, selection reason, review mode, changed-risk signals, prior-findings flag, and last fix commit [class: IMPLEMENTATION_REQUIRED]
- [x] Transcription taxonomy (derived fields): given the same record, expects the derived fields (artifact_slug, source_kind plan, schema_version 1, record_kind canonical, coverage object built only from the record's Coverage and panel lines) to follow the named constants [class: IMPLEMENTATION_REQUIRED]
- [x] Transcription taxonomy (defaulted fields): given the same record, expects the defaulted-empty fields (escalation_reason, soften_watchlist, deduplication_groups, discarded, overflow, severity_calibration, triage_outcomes) to carry the empty forms, with no evidence-bearing field ever defaulted [class: IMPLEMENTATION_REQUIRED]
- [x] Transcription taxonomy (self-heal member): expects the regenerated sidecar's self-heal member following the chain rule: a valid post-fence canonical prior round carries the prior chain state verbatim (same run id and status); a repaired round of 1 or unnumbered derives the unused status bound to the record's own run id; other unavailable prior evidence derives the unknown status bound to the record's own run id [class: IMPLEMENTATION_REQUIRED]
- [x] Record-kind twin append: given a post-fence record whose Markdown lacks the `Record kind:` twin, expects the tool appending the twin line `Record kind: canonical` as its only Markdown write, so the repaired pair passes the record-kind gate [class: IMPLEMENTATION_REQUIRED]
- [x] Dry-run and receipt: given the dry-run mode, expects the would-repair and would-refuse sets printed with nothing written; given a real run, expects a receipt file listing every repaired and refused path beside the console repair census [class: IMPLEMENTATION_REQUIRED]
- [x] Validate-in-place: expects the tool to write the sidecar at its real destination (the path derives from the record name, so prior-chain gates see the real home), run the full pair validation in place, and arm the expected-digest check from the transcribed identity's plan bytes (a stale recorded digest refuses at repair time) [class: IMPLEMENTATION_REQUIRED]
- [x] Delete-on-refusal: expects any validation refusal to delete the just-written sidecar in the same invocation before the census names the pair refused, so no non-validating sidecar strands and a corrected-Markdown retry stays bounded [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (incomplete record): given a record missing any transcribed field, expects the repair tool refusing without writing [class: REPOSITORY_TEST]
- [x] Safety witness (never overwrite a foreign sidecar): given a record whose sidecar already exists without the tool's marker, expects a named refusal and no write [class: REPOSITORY_TEST]
- [x] Bounded retry: given a sidecar produced by a prior successful tool run in the same test (carrying its marker), expects a corrected-Markdown retry to be permitted, so the repair path stays bounded [class: REPOSITORY_TEST]
- [x] Safety witness (no identity guess): given a record whose Markdown resolves no identity, expects refusal and census mention, never a slug-derived guess [class: REPOSITORY_TEST]
- [x] Run → expect RED: the witnessed r4-class pair has no sidecar and no repair path today [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: regenerate defective review sidecars from their own records` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Integrate the repair with the validators and run the campaign

Context surface: the plan's Terms and Task 3's taxonomy.

Files:
- `scripts/plan_readiness.py` *(modified, the regeneration notice only)*
- `scripts/validate_review_staging.py` *(modified, the marker-tolerance assertion and its selftest row only)*
- `scripts/test_plan_readiness.py` *(modified)*

Primary class anchors:
- `evaluate_readiness` in `scripts/plan_readiness.py`

- [x] Taxonomy completeness: expects the three classes jointly covering every required field of the version-1 contract including the extended freshness and fenced members, with the partition pinned by test so no required field is unassigned [class: REPOSITORY_TEST]
- [x] Safety witness (write bounds): on a temp home, expects the repaired Markdown to differ from the original by exactly the appended twin line, a record already carrying the twin to receive no second line, the dry-run to write nothing anywhere, a real run's total writes to be exactly the sidecar, the twin line, and the receipt file, and the written sidecar to carry `extensions.regenerated_from_markdown: true` [class: REPOSITORY_TEST]
- [x] Hermeticity: every test witness builds an isolated temp home; the live-home run is the campaign operation whose verification is its printed census and receipt file [class: REPOSITORY_TEST]
- [x] Repaired series passes: given the regenerated sidecar, expects the shared staging validator passing on the pair and the strict readiness consult passing on the series [class: REPOSITORY_TEST]
- [x] Self-heal chain-rule witnesses: given a prior round with a valid post-fence canonical sidecar, expects the prior chain state carried verbatim; given a repaired round of 1 or unnumbered, expects the unused status bound to the record's own run id; given missing, malformed, pre-fence, or non-canonical prior evidence, expects the unknown status bound to the record's own run id [class: REPOSITORY_TEST]
- [x] Tolerance asserted, not extended: expects the validator's existing open-extensions handling to accept the marker, with the negative direction pinned (a marker-bearing sidecar with a stale digest or failing gate still refuses, proving no gate keys tolerance on the marker) [class: REPOSITORY_TEST]
- [x] Regeneration notice: given the readiness consult resolving a sidecar carrying the marker, expects one report-only notice line on the pass path through the advisory channel, and no notice when it does not; pinned by its own test beside the advisory-line witness [class: IMPLEMENTATION_REQUIRED]
- [x] Campaign run: after the witnessed-shape witness passes, expects the repair tool run over the live reviews home in receipt mode, iterating each series in ascending round order so a higher round's verbatim carry always sees its lower neighbor's final sidecar [class: IMPLEMENTATION_REQUIRED]
- [x] Campaign repairable class: the repairable class is pairs whose recorded source digest still matches the live plan bytes at the recorded identity path; every other pair (a stale digest, a moved or completed plan, incomplete Markdown metadata) receives a named refusal recorded in the receipt file, which is the census of record [class: IMPLEMENTATION_REQUIRED]
- [x] Composed-chain witness: on a temp home with defective r2 and r3 beside a valid r1, expects repairing r3 then r2 to leave r3's in-place validation refusing with the run-id continuity reason, and a bounded-retry re-run of the tool on r3 (its own marker-bearing sidecar permits the rewrite) to end with the full staging validation of r3 passing [class: REPOSITORY_TEST]
- [x] Refusal-path witness (stale digest): on a temp home, a record whose transcribed fields are complete but whose recorded Source digest mismatches the live plan bytes at the recorded identity path expects the tool to write the sidecar, fail the in-place validation with the digest reason, delete the just-written sidecar in the same invocation, name the pair refused in census and receipt, and leave no sidecar file [class: REPOSITORY_TEST]
- [x] Refusal-path witness (moved plan): a fixture whose recorded identity path does not exist expects the same refusal path, pinning the moved-plan refusal class [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the readiness and selection suites, the staging validator selftest, the pins suite, and the public hygiene scan all exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: integrate the regenerated sidecar marker with the validators and run the repair campaign` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Reconcile the documented contract

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/review-plan/SKILL.md` *(modified)*
- `agents/skills/plans/SKILL.md` *(modified)*
- `agents/skills/review-staging/SKILL.md` *(modified)*

- [x] Verified stale-text inventory: the review-plan skill's blanket-raise sentence, its review-record template line, and its readiness-gate integration paragraph's exact-path selection sentence, the plans skill's review-series metadata line, and the staging skill's refusal text are updated to the narrowed contract (advisory exclusion, rank guard, lexical fallback, narrowed waiver scope) [class: IMPLEMENTATION_REQUIRED]
- [x] Orphan-recovery routing: the staging skill names the routing predicate in one boundary clause, routed by record property rather than discovery lane: a sidecar-less record whose Markdown carries the repairable metadata set routes to the repair tool from whichever lane discovered it, while halves beyond transcription repair (missing or incomplete metadata) continue through the existing recover-orphan path unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Trust-anchor sentence: the staging skill states that transcription shifts the repaired pair's trust anchor to the Markdown record [class: IMPLEMENTATION_REQUIRED]
- [x] Registry and pin verification: no registry row or pin literal describes the changed refusal semantics (verified absence; edit nothing unless verification says otherwise); the pins suite exits 0 [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the readiness and selection suites, the staging validator selftest, the pins suite, and the public hygiene scan all exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: reconcile the review-series contract with the narrowed identity disposition` [class: IMPLEMENTATION_REQUIRED]
