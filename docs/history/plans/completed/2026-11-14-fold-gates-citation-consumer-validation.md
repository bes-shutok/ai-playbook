# Plan: Citation-consumer probe in the pre-round structural gate

Backlog origin: docs/history/backlog/2026-11-14-fold-gates-citation-consumer-validation.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-fold-gates-citation-consumer-validation-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 2h total, largest task 1h
Executed: yes (this landing: branch exec/2026-11-14-fold-gates-citation-consumer-validation squashed into main)
Authoring claim: 2026-11-14-fold-gates-citation-consumer-validation.md (session sess_221cc536-553e-4c50-9b5b-df1025c30192)

## Terms

- citation-series probe: the warning-only check this plan adds to the pre-round structural gate; it expands the series tokens the teardown consumer itself extracts from the plan's header citation label lines through the consumer's own helpers and reports tokens that resolve to zero members.
- series token: a citation token ending in `-r*.md` that names a review-record series, for example `.ai-playbook/reviews/2026-11-13-plan-review-<slug>-r*.md`.
- closeout matcher: `_series_members` in `scripts/worktree_closeout_migrate.py`, the function the worktree-removal gate uses at teardown to verify a cited series is present.
- consumer extraction: `_review_label_rest` and `_extract_citations` in `scripts/worktree_closeout_migrate.py`, the helpers the worktree-removal gate uses to read a plan's owned citations from its header label lines (`Plan review record:` / `Plan review:`); the probe imports them read-only.
- reviews home: the facts-resolved `.ai-playbook/reviews/` directory.
- warning-only arm: a check that prints warning lines on stderr and never changes an exit code, adds no schema field, and refuses nothing.
- pre-round structural gate: `run_pre_round` in `scripts/plan_readiness.py`, invoked with `--pre-round` before review rounds and by the review fold batch.
- machinery inventory: the registry-backed keep-or-delete check `scripts/machinery_inventory.py --check` runs over `scripts/machinery_registry.json`.

## Why

A review fold can reshape a plan's review-record citation into a form the closeout matcher escapes literally, so the token matches zero records; every earlier gate passed it, and the defect surfaced only at teardown, where the one-line fix cost a full re-certification round. The cheapest catch is the matcher's own expansion run over each citation token at authoring time.

## Gist & Examples

TLDR: adds a warning-only citation-series probe to the pre-round structural gate, so a citation token the closeout matcher cannot resolve is named at fold time instead of at teardown; efficiency: a one-line citation fix stops costing a full re-certification round.

Before: an authoring fold widened the plan header's citation to the human-glob form `*plan-review-<slug>*-r*.md`. The fold batch's em-dash fence, pre-round structural gate, and hygiene scan all passed; the certification round staged ready=yes over the defective bytes; teardown's gate-removal then reported zero series members (`missing: .ai-playbook/reviews/*plan-review-machinery-cli-operand-self-description*-r*.md`) and the fix forced a full re-certification round.

After: the same fold batch's pre-round gate prints `readiness PRE-ROUND WARNING:` naming the zero-member header citation token, so the fold author fixes the citation in the same batch. The canonical template form `YYYY-MM-DD-plan-review-<slug>-r*.md` and concrete-date forms verify silently over a live series; a `-r*.md` token quoted in prose never warns.

## Outcome

Plan citation tokens are validated against the consumer matcher at authoring time, so a citation the matcher cannot parse is named before certification instead of at teardown.

- A fold that reshapes a citation into a literally-escaped form is named by a warning line in the same batch that folded it.
- The canonical template and concrete-date citation forms verify silently when the records exist.
- The closeout matcher and its teardown refusal stay unchanged as the blocking backstop.

Gate delta: adds one warning-only checked-set growth (the citation-series warning surface; no refusal class, hard gate, fence, protocol layer, or schema field added, none removed); priced by the origin row's completed-integrity-failure witness (the witnessed re-certification round spent on the teardown catch, docs/history/backlog/2026-11-14-fold-gates-citation-consumer-validation.md).

## Assumptions

- assume warning-only landing (not blocking); basis: at the first pre-round invocation of a plan no review records exist yet, so the cited series legitimately resolves to zero members and a blocking check would false-positive every first round; the origin row's machinery posture and registry precedent entry `script:origins-coverage-undercount-audit` price the same posture.
- assume the probe imports `_series_members` read-only from `scripts/worktree_closeout_migrate.py` instead of copying its grammar; basis: the origin row's fix shape ("re-uses `_series_members` read-only, no new grammar") and the origin row's rejected widen-the-matcher alternative.
- assume the probe is silent when the reviews home is absent or the plan carries no `-r*.md` tokens; basis: the pre-round gate never opens the reviews home today and its tolerated no-review-artifact class stays respected.
- assume the shared warning-surface contract of the precedent arm `plan_files_coverage_warnings` (pre-round stderr after all probes pass, full-gate pass-path stderr, zero lines on every failure path, exit codes unchanged); basis: that arm's docstring pins the contract this plan mirrors.
Decision points requiring a grill: placement (pre-round structural gate vs review-plan fold battery): selected pre-round structural gate (decision receipt: repo evidence 2026-11-14, the witnessed fold batch already invokes the pre-round structural gate so the probe rides an existing call site, while the battery arm would edit the review-loop and review-plan skill files under the byte-budget posture and a frozen peer target set; affected sections: Task 2, Review Scope); posture (warning-only vs blocking): selected warning-only (decision receipt: origin row admission line plus the first-round zero-members legitimacy, 2026-11-14; affected sections: Task 2, Task 3).

## Standing constraints

- The closeout matcher's grammar and refusal semantics are frozen input: the probe reads them through an import, never changes them (`scripts/worktree_closeout_migrate.py` is read-only for this plan; changes there are a separate plan).
- Consumer-surface rule: the probe reads only the header citation label lines through the consumer's own extraction helpers, so its scan surface equals the teardown consumer's; a `-r*.md` token outside a header label line (Gist or evaluation prose) never warns.
- Repository admission protocol: the arm lands warning-only; promotion to blocking happens only after a true catch per the criteria pre-registered in Task 3's removals row, in a separate reviewed change; this plan implements no promotion.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the probe reports exactly the distinct tokens the closeout matcher resolves to zero members, naming each token; the fixture pair proves both directions (zero-member wildcard form warns, live-series template form stays silent).
- non-regression: existing `run_pre_round` probes keep their exit semantics and failure-path warning silence; the focused suite passes.
- maintainability: the matcher is imported, not re-implemented; no parallel citation grammar grows.

**Done when:**
- focused suite passes: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_readiness.py -q`
- pre-round self-check exits 0: `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-14-fold-gates-citation-consumer-validation.md` (the plan's own header citation warns until its review series exists; the warning is the arm's designed pre-round-1 behavior)
- machinery inventory reports no failure attributable to this plan's rows: `python3 scripts/machinery_inventory.py --check` exits 0, or its only failure is the pre-existing baseline finding `duty:carrier-liveness-missed-fire` (the unresolved witness ref recorded in the scheduler state notes since 2026-11-13, re-point owned by the sibling entry landing-origin-row-deletion-registry-witness-sweep); a new failure naming `script:plan-readiness-citation-series-arm` or its removals row is a defect

**Ship when:**
- none (repository-only change; no external release condition).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py` (Task 2)
- `scripts/machinery_registry.json` (Task 3)

**Tests:**
- `scripts/test_plan_readiness.py` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/worktree_closeout_migrate.py`; reason: the matcher is frozen input per Standing constraints; a matcher change is a separate plan.
- `agents/skills/review-loop/SKILL.md` and `agents/skills/review-plan/SKILL.md`; reason: the fold-battery placement was priced and not selected; this plan keeps skill text untouched.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_readiness.py -q
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-14-fold-gates-citation-consumer-validation.md
python3 scripts/machinery_inventory.py --check
```

Validation preamble: authoring-time mechanical gates, 2026-11-14: fixer total 0 substitutions; em-dash `touched` exit 0; public hygiene `OUTCOME: pass`; focused suite 205 passed + 58 subtests at the authoring base; `plan_readiness.py --pre-round` first run caught three structural defects (bullet-prefixed trailer line, anchor `*(new)*` suffix, untagged Commit items), fixed and re-run to `OUTCOME: pass` with the advisory FILES-COVERAGE warnings adjudicated (grammar fragments and validation-command paths, not declaration-worthy); `machinery_inventory.py --check` reports the single pre-existing baseline failure `duty:carrier-liveness-missed-fire` (unresolved witness ref on main since 2026-11-13, re-point owned by the sibling entry landing-origin-row-deletion-registry-witness-sweep), no failure attributable to this plan. Rule 19 RED-today execution evidence: none required (no forbidden-sweep or exact-count pin gates in the Validation Commands block). Rule 22 authoring-time mechanical audit: `bash -n` accepted the extracted Validation Commands block; the plan carries no literal pin/text contract spans. Budget gate at the round-1 boundary: probe `pause_decision: continue`, binding primary, 63.0% used, reset 2026-11-14T22:18:48Z, standing resume watcher scheduled (known-binding branch). Round-start state for r1: branch authoring/2026-11-14-fold-gates-citation-consumer-validation, base main ee62f16cf (the Phase 0 freeze commit), plan digest recorded at the round launch in the r1 sidecar.

### Task 1: Fixture-pair tests for the citation-series probe (RED)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_plan_readiness.py`

- [x] Fixture pair, zero-member direction: given plan text whose `Plan review record:` header line carries the witnessed wildcard form `*plan-review-<slug>*-r*.md`, over a reviews home holding no matching records, expects the probe returns exactly one warning naming that token [class: REPOSITORY_TEST]
- [x] Fixture pair, live-series direction: given a header line carrying the canonical template form `YYYY-MM-DD-plan-review-<slug>-r*.md` and a concrete-date variant over a reviews home holding a planted live series, expects zero warnings for both forms [class: REPOSITORY_TEST]
- [x] Prose-silence fixture: given a plan whose only `-r*.md` tokens sit outside header label lines (Gist or evaluation prose), expects zero warnings, proving the scan surface equals the consumer's [class: REPOSITORY_TEST]
- [x] Tolerated-class fixtures: given an absent reviews home, and given plan text with no `-r*.md` tokens, expects zero warnings in both cases [class: REPOSITORY_TEST]
- [x] Run → expect RED: the probe helper does not exist yet, so the new tests fail before Task 2 [class: REPOSITORY_TEST]
- [x] Commit: `test: RED fixture pair for the citation-series probe` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Warning-only citation-series arm in the readiness gates (GREEN)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/plan_readiness.py`

Primary class anchors:
- `plan_citation_series_warnings` in `scripts/plan_readiness.py`

- [x] `plan_citation_series_warnings` delivers zero-member detection: given plan bytes and the reviews home, expects the series tokens extracted exactly as the teardown consumer extracts them (`_review_label_rest` then `_extract_citations`, imported read-only from `scripts/worktree_closeout_migrate.py`) and expanded through `_series_members` to yield one warning per distinct zero-member series token, each naming the token [class: IMPLEMENTATION_REQUIRED]
- [x] Silence cases: given a plan whose header tokens all resolve, a plan with no tokens, and a plan whose tokens sit outside header label lines, expects zero warnings in all three cases [class: IMPLEMENTATION_REQUIRED]
- [x] Wiring delivers the shared warning-surface contract: the pre-round gate prints the lines on stderr after all probes pass and the full gate's main pass path prints them the same way, mirroring the precedent arm's channel and ordering [class: IMPLEMENTATION_REQUIRED]
- [x] Identity contract: the arm calls `_series_members` without `plan_identity` and without a sink, so the arm performs zero-member detection only and emits no `series-identity:` diagnostics; identity diagnostics stay the closeout's job [class: IMPLEMENTATION_REQUIRED]
- [x] The `run_pre_round` docstring's no-review-home invariant sentence is updated to name the arm's read-only header-citation home opening, so the docstring stays truthful at landing [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a plan whose probes fail, expects zero citation warnings on every failure path and unchanged exit codes [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: Task 1's fixture pair passes [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the full focused suite `scripts/test_plan_readiness.py` passes [class: REPOSITORY_TEST]
- [x] Commit: `feat: citation-series warning arm in the readiness gates` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Registry rows for the warning arm

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/machinery_registry.json`

- [x] Entries row `script:plan-readiness-citation-series-arm` lands warning-only with the row shape mirrored from entry `script:origins-coverage-undercount-audit`: `paths` empty, `tests` `["scripts/test_plan_readiness.py"]`, `witness` class `red-test` ref `scripts/test_plan_readiness.py` [class: IMPLEMENTATION_REQUIRED]
- [x] The entries row's note carries the concrete incident (the origin row's teardown catch and the re-certification round it cost), expected catch frequency (every fold that reshapes a header citation token), the false-positive cost (one warning line per header citation whose series is legitimately absent before the first round; prose tokens never warn), review date 2027-05-14, and the promotion pointer to the pre-registered removals row [class: IMPLEMENTATION_REQUIRED]
- [x] Pre-registered removals row with the same id, empty `paths` and `tests` lists, `witness` class `red-test` ref `scripts/test_plan_readiness.py`, naming the no-catch sunset (at the review date, if no true catch, remove the arm and its call sites and keep this row as the removal record) and the promotion criteria (blocking only after a witnessed fold-time true catch, with a priced first-round false-positive-free shape, in a separate reviewed change) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/machinery_inventory.py --check` reports no failure attributable to this plan's rows (exit 0, or the only failure is the pre-existing baseline finding `duty:carrier-liveness-missed-fire` whose witness ref is unresolved on the authoring base and whose re-point is owned by the sibling entry landing-origin-row-deletion-registry-witness-sweep) [class: REPOSITORY_TEST]
- [x] Commit: `chore: registry rows for the citation-series warning arm` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- Origin row `docs/history/backlog/2026-11-14-fold-gates-citation-consumer-validation.md` (fold and pre-round gates do not validate plan citations through their consumer matchers): covered and deleted by this landing. The planned arm landed warning-only (the row's machinery posture), wired into the pre-round structural gate and the full gate's pass path, with the closeout matcher's grammar and refusal left untouched as the blocking backstop, and the pre-registered registry-removal row `script:plan-readiness-citation-series-arm` naming the 2027-05-14 no-catch sunset and the witnessed-catch promotion criteria. The row's blocking-check alternative was rejected in the plan's Assumptions (a blocking shape false-positives every first pre-round, where a cited series legitimately resolves to zero members).
