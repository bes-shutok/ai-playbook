# Plan: producer exec-record grammar and binding check warning arm

Backlog origin: docs/history/backlog/2026-11-13-producer-exec-record-grammar-arm-promotion.md
Driving force: code-quality
Authoring claim: 2026-11-13-producer-exec-record-grammar-arm-promotion.md (session sess_5069137b-02af-4f4c-bfdd-06cdba47798b)
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-producer-exec-record-grammar-arm-promotion-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Executed: yes (this landing)

## Terms

- archive-ceremony gate: the landing sweep gate (`gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`) that demands execution evidence for every plan archive the derivation surfaces.
- exec-review record (filename-series record): a record under the reviews home whose filename contains `-plan-review-`, the archived plan's slug, and ends `-exec-r<N>.md`; the gate's first acceptance route.
- plan-family record: a producer record named `<date>-plan-review-<slug>-r<N>.md` whose source digest hashes plan bytes; what authoring rounds mint.
- code-family record: a producer record named `<date>-<artifact-slug>-code-review-r<N>.md` whose source digest hashes the reviewed range; what execution Phase 3 rounds mint.
- bound receipt: the gate's second acceptance route: a record whose sidecar binds `extensions.plan_identity`, a matching `source_digest`, and a yes verdict.
- sidecar: the `.stats.json` JSON file written beside each record.
- producer: `scripts/produce_exec_review_record.py`, the mint tool for record pairs.
- repair producer: the producer's plan-family exec-series mint route, the path that produced the witnessed marked-reconstruction repairs.
- marked reconstruction: a hand-installed, verdict-no exec-review pair minted to clear a sweep red without certifying anything.
- artifact slug: the kebab-case slug naming a minted record's subject (`--artifact-slug` in range mode).
- canonical plan slug: a plan filename's stem after stripping the leading `YYYY-MM-DD-` date prefix.
- plans roots: `docs/history/plans/` and `docs/history/plans/completed/` only; the `deferred/` and `rejected/` subdirectories are outside the probe's scan set (the gate exempts rejected-state archives, and deferred plans are human-revival-only, never auto-executed, so a code-family mint naming a deferred plan's slug is not the witnessed class).
- warning-only: output that never changes exit codes, refusals, or the stdout outcome grammar.

## Why

The archive-ceremony gate refuses a landing sweep when an archived executed plan lacks acceptable execution evidence, but the mint that produces execution-round records emits code-family records whose names and sidecars can never satisfy the gate's acceptance routes. Every incident is therefore discovered at sweep time by whichever uninvolved writer sweeps next, and the repair has been another hand-installed marked reconstruction (2026-11-07 twice; 2026-11-12/13 again inside a foreign writer's transaction).

## Gist & Examples

TLDR: the exec-review record producer warns at write time when a minted record cannot stand as the archived plan's execution evidence, closing the sweep-time-discovery gap for code-quality.

Before: an executed plan's Phase 3 rounds mint `<date>-<slug>-code-review-rN.md` records; the archive lands; the next writer's landing sweep refuses on the missing exec-review record; the repair is a hand-installed marked reconstruction that blocks an uninvolved writer's transaction.

After: the same mint prints a stderr warning naming the archive-ceremony gate (`scripts/done_sweep_gates_lib.py`) and the repair producer route (`scripts/produce_exec_review_record.py`, the `-plan-review-<slug>-exec-r<N>` exec-series grammar), so the executor mints acceptable evidence in the same run. Nothing blocks; exit codes and the stdout outcome grammar are unchanged.

## Outcome

Close the evidence-grammar gap at mint time instead of leaving every discovery to the next sweep.

- A code-family mint whose artifact slug matches an executed or active plan warns at write time, naming the consuming gate and the repair producer route.
- The warning is fail-open and non-blocking: an unresolvable probe warns nothing and never fails a mint.
- The machinery registry row carries the arm's admission fields and pre-registered promotion criteria (sunset 2026-12-13; promotion on a third true catch).
- The archive-ceremony gate stays byte-unchanged.

Gate delta: one warning-only producer write-time check added (a checked surface at mint time; warning emission only, no refusal semantics), priced by the completed-integrity-failure witness docs/history/backlog/2026-11-13-producer-exec-record-grammar-arm-promotion.md (the 2026-11-07 checkout-wide red and the 2026-11-12/13 recurrence inside a foreign writer's span); no refusal class, hard gate, fence, protocol layer, or schema field is added or removed; the archive-ceremony gate's acceptance routes stay unchanged; promotion criteria pre-registered in the machinery registry row this plan adds.

## Assumptions

- assume the warning fires only on range-mode (code-family) mints whose `--artifact-slug` equals an executed or active plan's canonical slug under the plans roots; the active-plan root (`docs/history/plans/`) is the arm's primary firing window because a Phase 3 mint names a plan still living at mint time (the archive happens only at closeout), and the completed root (`docs/history/plans/completed/`) is the post-archive window; basis: the origin row's ship-when line ("Minting a code-review-kind record whose slug matches an executed plan prints the warning"), the witnessed incident class, and the origin row's observed narrative.
- assume "matches" is canonical-slug equality: the probe compares `--artifact-slug` to each plan slug for exact equality, and the containment subclass (an artifact slug merely containing a plan slug, for example `<plan-slug>-impl`) stays unwarned; the subclass is priced as the accepted boundary and the 2026-12-13 promotion review owns its revisit; basis: the ship-when pin read at its tight form, and the panel r1 finding F5 pricing.
- assume the slug-match probe is fail-open: an unresolvable repository root or plans roots emit no warning and never fail the mint; basis: the origin row's machinery admission (false-positive cost: one warning line, nothing blocks).
- assume the warning emits on the mint success path only: a validator-refused pair self-deletes and leaves no record to warn about; basis: the producer's delete-on-refusal contract.
- assume the warning rides stderr and never mutates the stdout outcome grammar or exit codes; basis: the producer's success contract (the validator's final OUTCOME line is the gate) plus the ship-when line "no blocking behavior is added".
- assume the warning text names the archive-ceremony gate with its file path (`scripts/done_sweep_gates_lib.py`), the repair producer path (`scripts/produce_exec_review_record.py`), and the exec-series grammar token `-plan-review-<slug>-exec-r<N>`; basis: the origin row's expected line ("naming the consuming gate and the repair producer").
- assume plan-family non-exec (`-rN`) mints stay warning-free; basis: the ship-when pin fixes the code-review-kind class only; the gate's filename route demands the `-exec-r<N>` series token a `-rN` name lacks, and the producer's sidecar omits `extensions.plan_identity`, so a producer-minted `-rN` record satisfies neither acceptance route as minted, while a plan-family record with a bound sidecar (identity, digest, yes verdict) remains the gate's own named bound-receipt remedy; the witnessed incidents are all code-family records, and a plan-family matching-slug silence witness is pinned in Task 1.
- assume the registry row follows the sibling duty-row precedent (`duty:archive-ceremony-post-landing-report`): paths and tests empty per the claim-if-concurrent precedent (both surfaces owned by existing rows), admission fields and promotion criteria in the note; basis: the sibling row's landed shape in `scripts/machinery_registry.json`; the row's structure and note fields are verified by the pinned registry-row check in Validation Commands (Task 3), the panel r1 finding F3 remedy.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: suite cells pin the warning on the matching class and pin its absence on the non-matching class
- non-blocking: exit code and stdout outcome grammar byte-identical with and without the warning
- fail-open: probe resolution failure emits no warning and never fails the mint
- maintainability: the registry row carries incident links, expected catch frequency, false-positive cost, promotion criteria, and the sunset date

**Done when:**
- the focused producer suite passes green with the new cells
- the pinned registry-row check passes over the landed row (the registry's verification witness; the pins suite does not read the registry) and the pins suite itself stays green
- the em-dash and public hygiene scans pass over the changed set
- the warning text names the gate file, the repair producer file, and the exec-series grammar token

**Ship when:**
- promotion review 2026-12-13 or on a third true catch: the registry row owns the criteria; warning-only stays the posture until that review promotes or sunsets it (prose only)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/produce_exec_review_record.py` (Task 2)

**Tests:**
- `scripts/test_produce_exec_review_record.py` (Task 1)
- `scripts/test_produce_exec_review_record.py` (Task 2)

**Registry:**
- `scripts/machinery_registry.json` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py`; the archive-ceremony gate stays byte-unchanged per the origin row and the dispatch entry ("The archive-ceremony gate itself stays unchanged")

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_produce_exec_review_record.py -q
bash scripts/check_maintenance_pins.sh
python3 scripts/fix_plan_em_dashes.py docs/history/plans/2026-11-13-producer-exec-record-grammar-arm-promotion.md
python3 -c "import json, os; row=[r for r in json.load(open('scripts/machinery_registry.json'))['entries'] if r.get('id')=='duty:producer-exec-record-grammar-warning']; assert row and row[0]['kind']=='protocol' and row[0]['disposition']=='keep' and row[0]['paths']==[] and row[0]['tests']==[], 'missing or malformed duty row'; w=row[0].get('witness') or {}; assert w.get('class')=='incident' and w.get('ref','').startswith('docs/history/plans/') and os.path.exists(w['ref']), 'missing or unresolvable witness'; note=row[0]['note']; assert all(s in note for s in ['2026-11-07','2026-11-12/13','2026-12-13','code-review-kind','warning line','third witnessed sweep-time discovery']), 'thinned admission note'; print('registry row ok')"
```

### Task 1: RED suite cells for the mint-time warning

Context surface: the plan's Terms and this task.

Files:
- `scripts/test_produce_exec_review_record.py`

- [x] given a range-mode mint whose `--artifact-slug` equals an archived fixture plan's canonical slug under `docs/history/plans/completed/`, expects the run prints a stderr warning naming the archive-ceremony gate file (`scripts/done_sweep_gates_lib.py`), the repair producer file (`scripts/produce_exec_review_record.py`), and the exec-series token `-exec-r` [class: REPOSITORY_TEST]
- [x] given a range-mode mint whose `--artifact-slug` equals a living fixture plan's canonical slug under `docs/history/plans/`, expects the same stderr warning (the active-plan firing window: Phase 3 mints name a plan still living at mint time) [class: REPOSITORY_TEST]
- [x] given a range-mode mint whose `--artifact-slug` matches no plan under the plans roots, expects the run prints no warning line [class: REPOSITORY_TEST]
- [x] given a plan-family mint whose derived slug (the producer's plan-mode slug is the kebab of the full filename stem, date prefix included, so the fixture must pass `--artifact-slug` naming a plan slug deliberately) equals a plan slug under the plans roots, expects no warning line on either channel (the slug-conditioned-probe regression catcher) [class: REPOSITORY_TEST]
- [x] given a slug-match probe that cannot resolve (no plans roots reachable), expects the mint succeeds with no warning and an unchanged final OUTCOME line [class: REPOSITORY_TEST]
- [x] given the pinned warning scenario, expects exit code 0 and the final `OUTCOME: pass` line unchanged, and the produced record and sidecar bytes unaffected by the warning [class: REPOSITORY_TEST]
- [x] Run → expect RED: the cells above fail against today's producer [class: REPOSITORY_TEST]
- [x] Commit: `test: red cells for the producer mint-time exec-record warning` [class: IMPLEMENTATION_REQUIRED]

### Task 2: implement the warning arm (GREEN)

Context surface: the plan's Terms and this task.

Files:
- `scripts/produce_exec_review_record.py`

Primary class anchors:
- `build_context` in `scripts/produce_exec_review_record.py`
- `produce` in `scripts/produce_exec_review_record.py`

- [x] `build_context` resolves the fail-open slug match: given a range-mode mint, expects the warning decision computed from whether the artifact slug equals any canonical plan slug under the plans roots, with any resolution failure deciding "no match" [class: IMPLEMENTATION_REQUIRED]
- [x] `produce` emits the warning on the success path only: given a validator-passed range-mode mint with a matching slug, expects one stderr warning naming `scripts/done_sweep_gates_lib.py` (the archive-ceremony gate), `scripts/produce_exec_review_record.py` (the repair producer), and the `-plan-review-<slug>-exec-r<N>` exec-series grammar; expects stdout OUTCOME grammar and exit code unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (non-blocking posture): given any probe or emission failure at mint time, expects the mint outcome identical to the no-warning path (no new refusal, no exit-code change) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: Task 1's cells pass [class: REPOSITORY_TEST]
- [x] Commit: `feat: warn at mint time when a code-family record cannot serve as plan execution evidence` [class: IMPLEMENTATION_REQUIRED]

### Task 3: machinery registry admission row

Context surface: the plan's Terms and this task.

Files:
- `scripts/machinery_registry.json`

- [x] add the `duty:producer-exec-record-grammar-warning` registry row (kind `protocol`, disposition `keep`, empty paths and tests per the claim-if-concurrent precedent) carrying a `witness` field (class `incident`, ref this plan's plans-root path at execution, re-pointed to this plan's `completed/` archive twin at this plan's own landing per the sibling row's re-point convention, the vocabulary `machinery_inventory.py` validates) [class: IMPLEMENTATION_REQUIRED]
- [x] the row note carries the two incident links: the 2026-11-07 two-catch red per the covered sibling row and the 2026-11-12/13 foreign-span recurrence per the origin row [class: IMPLEMENTATION_REQUIRED]
- [x] the row note carries the admission fields: expected catch frequency (every executed plan whose exec rounds are code-review-kind) and false-positive cost (one warning line per mint, nothing blocks) [class: IMPLEMENTATION_REQUIRED]
- [x] the row note carries the promotion criteria (a third witnessed sweep-time discovery whose mint transcript shows this warning promotes the arm to a mint-time refusal for the pinned class) and the sunset review date 2026-12-13 [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the pinned registry-row check in Validation Commands passes over the landed row (structure fields, the incident-class witness with a resolving ref, and all six note needles: both incident links, catch frequency, false-positive cost, the promotion-criteria phrase, the sunset date) [class: REPOSITORY_TEST]
- [x] given the touched registry, expects the pins suite green [class: REPOSITORY_TEST]
- [x] Commit: `feat: pre-register promotion criteria for the producer exec-record warning arm` [class: IMPLEMENTATION_REQUIRED]
