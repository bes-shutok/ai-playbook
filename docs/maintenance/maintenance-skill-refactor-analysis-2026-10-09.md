# Maintenance skill refactor analysis (2026-10-09)

Companion to `machinery-blocker-audit-2026-10-09.md`. That audit rated blockers in what the pipeline does; this one analyzes what the pipeline reads: the `maintenance` skill corpus itself, its unbounded growth, its duplication, and the missing signal that should be triggering refactoring. The operator's framing that motivated it: the skill's context was incrementally expanded by backlog processing without a single attempt to refactor, and nothing in the machinery creates a counter-pressure.

## TL;DR

1. **The corpus is 627KB (~157K tokens at the 4-chars-per-token proxy) across three files.** `SKILL.md` alone is 357KB (~89K tokens): a scheduler turn that loads the skill end to end spends a large fraction of a context window on doctrine before doing any work.
2. **Growth is a pure ratchet.** 35 commits since 2026-09-15: 18KB then, 357KB now (20x in 24 days). Thirty-four of 35 commits grew the file; the single shrink event recovered 64 bytes (0.02%). Median commit adds 3.9KB, mean 10KB.
3. **Nothing measures it.** The survey counts backlog rows, plans, and queue depth; `scripts/machinery_inventory.py` tracks scripts; the pins suite freezes spans; no surface anywhere records skill-file bytes, per-section growth, or duplication. There is no consumer in the loop whose job is consolidation.
4. **About 24% of the corpus is changelog, not rules.** The `Revisions` section inside `SKILL.md` is 75.7KB (21% of the file); the deviation-list preamble inside `prompt-templates.md` is 78KB (44% of that file). Both duplicate git history and plan receipts that already exist, and both are loaded by every turn that loads the operative files.
5. **Duplication is quantified and localized.** `prompt-templates.md` carries 30% of its words inside repeated 10-word spans (57 duplicated sentences over 60 chars): the re-arm duty set and verification contracts restated across the authoring, execution, and unblock templates. `SKILL.md` is only 6% verbatim-duplicated; its bloat shape is instead per-site restatement of one contract (39x "targeted state edit", 17x sanctioned-writer, 17x carry-forward, 16x completion evidence, 62x `turn_error`) and inline incident dossiers (64 witness clauses, 81 dated parentheticals, a median sentence of 49 words with a p99 of 459 words and a 1,122-word maximum).
6. **Fix in three moves:** (a) extract the changelogs (154KB out, near-zero semantic risk); (b) split the monolith into a loadable router plus per-concern module files, with the 515-pin suite re-pointed in the same landings; (c) install the standing anti-growth mechanism: byte budgets enforced by a pins-companion check, growth telemetry in the loop's weekly rider, an append-tax rule, and a consolidation pass in the harvest duty. All three are plan work (pinned spans, machinery, cross-skill navigation); the mechanism piece is the priority because it is what prevents re-growth after the split.

## Part 1: anatomy and load cost

| File | Bytes | Lines | Median sentence | Role |
|---|---|---|---|---|
| `agents/skills/maintenance/SKILL.md` | 357,313 | 426 | 49 words | The scheduler turn: steps, guards, decisions, state schema |
| `agents/skills/maintenance/prompt-templates.md` | 176,925 | 509 | 56 words | Child blueprints (authoring, execution, unblock) + deviation list |
| `agents/skills/maintenance/zcode.md` | 92,566 | 127 | 40 words | ZCode runtime overlay: recipes, dispatch ladder, quota leg |
| Total | 626,804 | | | ~157K tokens |

Section sizes in `SKILL.md` (bytes):

| Section | Bytes | Share |
|---|---|---|
| `## Revisions` | 75,700 | 21% |
| `### Step 3: decision` | 71,979 | 20% |
| `### Step 1: survey` | 68,188 | 19% |
| `## State file` | 48,258 | 13% |
| `### Step 2: guards` | 20,910 | 6% |
| `## Failure detection and the failure cap` | 19,754 | 6% |
| `## Loop modes` | 7,530 | 2% |
| `### Step 5: scheduling` | 7,741 | 2% |
| `### Step 0: context load` | 12,513 | 4% |
| `### Step 4: quota leg` | 8,023 | 2% |
| everything else (config, cycle gate, invariants, integration points, step 6-7) | ~16,700 | 5% |

Three observations:

- **The entry file is not loadable.** No agent context budget accommodates a 89K-token skill read on top of the work itself. Whatever partial-loading behavior runtimes apply today is undefined in the text; the file's own architecture (runtime overlay loaded only when the runtime is ZCode) proves the authoring convention supports load-on-demand, but the concern split was never applied to SKILL.md itself.
- **History is load-bearing in the wrong place.** `Revisions` (75.7KB) and the template deviation preamble (78KB) are change ledgers, not rules. Every landed plan appends to both. They are the single largest structural growth channel: roughly 154KB, 24% of the corpus, that no turn ever needs at run time.
- **The loop reads it repeatedly.** The scheduler prompt template instructs each child to run the skill end to end; a dispatching turn reads SKILL.md, the matching blueprint in prompt-templates.md, and (on ZCode) the overlay: up to ~157K tokens of doctrine per dispatch cycle.

Coupling: `scripts/check_maintenance_pins.sh` (2,852 lines) carries **515 `pin()` fingerprints**, the dominant share over the three maintenance files (section anchors other skills navigate by, guard structure, dispatch-slice integrity, the recognition span, the schema-4 contract, and so on). Sixteen non-history files reference the skill by path: `agents/skills/plans/SKILL.md`, `agents/skills/execute-plan/SKILL.md` (+ its runtime-contract), `agents/skills/investigate/SKILL.md`, `agents/skills/done/SKILL.md`, `agents/skills/doing-code-review/SKILL.md`, `docs/maintenance/operator-directives.md`, five scripts, `README.md`, and `scripts/machinery_registry.json`. The directives home and the D-series records cite homes like "SKILL.md Step 1 reader" by section name. Any split must keep section names stable or leave redirect stubs, and must re-point pins in the same landing.

Context: maintenance is the largest but not the only bloated skill. The pipeline family reads: execute-plan 309KB, plans 193KB, done 152KB, doing-code-review 88KB, review-staging 81KB. The mechanism proposed in Part 6 should be family-wide from day one, with maintenance as the pilot because its growth rate is the extreme (compare: `investigate/SKILL.md`, a recently authored skill, is ~17KB and holds to the shape the guidelines prescribe).

## Part 2: duplication findings (quantified)

Method: normalized 10-word shingles over each file (words in spans repeated at least twice), sentence-level exact duplication at 60+ chars, cross-file shingle intersection. Scripts run ad hoc on 2026-10-09; a pinned-down version is proposed in Part 6.

| File | Words in repeated spans | Duplicated sentences (60+ chars) | Reading |
|---|---|---|---|
| `prompt-templates.md` | **30%** | 57 | Heavy verbatim duplication across the three blueprints |
| `SKILL.md` | 6% | 6 | Not a verbatim-duplication problem; a restatement problem |
| `zcode.md` | 2% | 0 | Healthiest of the three |

Cross-file shared 10-grams: SKILL-zcode 266, SKILL-templates 219, templates-zcode 178. The load-bearing duplications:

1. **The re-arm and carrier contract has four homes.** SKILL.md Step 0 rearm-on-touch, the overlay's "Re-arm hygiene" and "Turn-start carrier re-arm duty", the dispatch ladder's delete-plus-create discipline, and both child blueprints' re-arm duties each restate overlapping pieces (the live-bound condition, consume-after-survival, the recognition match verification, delete-before-create ordering). 'delete-plus-create' appears 42 times across the corpus (23 in zcode, 16 in templates).
2. **The blueprints deliberately self-contain their duties**, which is why templates duplicate 30%: each payload must carry its re-arm, claim, worktree, and landing duties without references the child cannot resolve. The dedup shape here is **shared duty blocks included by reference from both blueprints** (one `duties-core.md` whose spans the templates name), not deletion of payload self-containment; the pins suite already pins some cross-blueprint spans byte-identical, which keeps them from drifting while both copies still load.
3. **Per-site restatement inside SKILL.md.** "targeted state edit" 16x and "targeted field edit" 17x in templates: every writer site restates the write discipline instead of naming one write-discipline home. "sanctioned-writer" and "carry-forward" at 17x each are the same scar: the Step 6 carry-forward list must re-enumerate every field written outside Step 6, so each new field taxes the enumeration, and every guard re-restates its completion-evidence class (16x).
4. **Quota rules have two homes** (SKILL.md Step 4 and the overlay's Quota leg) joined by explicit keep-in-sync wording, with the constants (240/120 minute bounds) restated on both sides and again in the `--fire-at` contract.
5. **What is NOT duplicated:** the "one home by name" convention (each rule names its owning section and consumers reference by name) mostly works and is the pattern to keep; the duplication above is what to fold.

Sentence-shape findings for SKILL.md: median sentence 49 words, p90 156, p99 459, max 1,122 (single sentences longer than most complete rules elsewhere in the repo). 64 "witness" clauses and 81 dated parentheticals are embedded in operative text; each is an incident dossier living where a pointer would do.

## Part 3: why growth is unlimited (root causes)

1. **Rent is paid in appended text.** Every landed plan's receipt ritual appends a Revisions bullet, pins, and deviation entries. No ritual ever appends a deletion. With one 64-byte shrink in 35 commits, the ratchet is structural, not accidental.
2. **Changelogs live inside operative files.** Because Revisions and the deviation list are in the loaded files, growth in history is indistinguishable from growth in rules to any consumer that does not parse sections.
3. **No size signal exists anywhere.** The survey's queue-depth token counts work items; `machinery_inventory.py` registers scripts; the pins suite freezes spans but carries no budget; the friction-audit/audit lane audits other surfaces; the weekly rider measures throughput. No surface records skill bytes, section growth, or duplication, so the loop cannot notice the one thing that steadily worsened.
4. **Removal is structurally expensive.** The machinery audit's root cause applies to prose too: the ad-hoc denylist blocks machinery edits, pins make edits risky, and review panels flag deletions as possible regressions more often than appends. Appends are free; edits to pinned spans cost a pin re-aim. Rational actors append.
5. **Incident fixes land as new clauses with dossiers inline.** A backlog row's fix must be provable in the same commit, so the clause carries its witness, its date, and its rejection of the alternative. Nothing is later tasked with folding the clause into the existing rule it specialized, so the corpus accretes special cases instead of deepening general ones.
6. **The loop has no consolidation consumer.** The harvest duty invokes learn and investigate per cycle; the monitor invokes investigate when logs are empty. No duty, registry task, or rider ever runs a dedup/consolidation pass, and no eligibility test would admit one today (a pure simplification of the maintenance skill itself would fail the ad-hoc denylist's "no machinery removal" arm and has no plan entry).

## Part 4: the refactor (one-time structural moves)

Target architecture. Entry file first, modules by concern, changelog extracted:

| File | Target size | Content |
|---|---|---|
| `SKILL.md` | ~25-40KB operative | Frontmatter; loop modes and cycle-gate summaries; configuration; the Step 0-7 skeleton as dispatch tables with one-paragraph rules plus pointers; invariants; integration points; the router contract (which module a step must load) |
| `survey-arms.md` | ~45KB (Step 1's ~25 arms, restructured) | |
| `guards.md` | ~20KB (Step 2, fleet cap, tripwires, override) | |
| `decisions.md` | ~70KB initially (Step 3's D1-D4, carrier ordering, contention, rolling-log duties; consolidation target after the split) | |
| `quota-policy.md` | ~15KB (Step 4) | |
| `scheduling.md` | ~10KB (Step 5) | |
| `failure-cap.md` | ~20KB | |
| `state-file.md` | ~45KB (schema, field paragraphs, writer classes, carry-forward) | |
| `CHANGELOG.md` | 75KB+, unloaded | The Revisions ledger, verbatim |
| `template-authoring.md`, `template-execution.md`, `template-unblock.md` + `duties-core.md` | current blueprint sizes minus shared blocks | Deviation preamble moves to `templates-CHANGELOG.md` |
| `zcode.md` | keep, budget it | Runtime overlay stays one file unless it breaches budget |

Execution order (cheapest, highest-yield first):

1. **Changelog extraction** (both files): pure moves, no semantics, kills 24% of the corpus. Verify: no pin targets Revisions or the deviation list (spot-check; the suite's green-before-green-after discipline decides), cross-references to "the Revisions ledger" re-pointed.
2. **Section-module split** with the router contract: each module keeps its section headings verbatim so the "one home by name" convention, the directives-home citations, and other skills' anchor navigation survive; SKILL.md leaves one-line summaries plus module pointers. Pins re-pointed in the same commits, suite green before and after each move. `machinery_registry.json` entries naming the files updated in the same landing.
3. **Blueprint split with `duties-core.md`**: extract the byte-identical shared duty sets the pins already hold identical, have both blueprints reference them, and move the deviation list to its changelog.
4. **Restatement folding** (the Part 2 items): one write-discipline home, one completion-evidence table, one carry-forward table generated from the writer-class list rather than hand-enumerated. This is the part that needs a plan's review, because each fold touches pinned spans.

Explicit non-goal: changing any rule's semantics. This refactor is packaging. The semantic slimming (demotions, arm removals) is the machinery audit's program and stays routed there.

## Part 5: the standing anti-growth mechanism (the missing signal)

This is the piece the operator's message points at: a split without a counter-pressure reproduces the monolith within a month (the current file grew 92KB in its second week of life). Mechanism, all cheap and mechanical:

1. **Byte budgets with enforcement.** `scripts/skill_text_budget.py` (outcome-contract style, wired into the pins suite so every landing lane runs it): per-file and per-section byte caps from Part 4's table; exit 1 (`OUTCOME: fail`) on breach; a `--ratchet` mode that lowers a cap when a landing shrinks the file, so budgets only tighten. Caps are set generously at first (current minus the changelog extraction) so the gate bites at growth, not at day one.
2. **Growth telemetry in the loop.** The weekly measurement rider (already a registry rider) gains a text-liveness block: per-file bytes and net delta since last run, recorded in the state file or the tool-runtime stats log. A file with N consecutive growing windows and no shrink earns a line in the rider report; past a threshold the audit lane files a consolidation backlog row automatically, which routes the row into the loop's existing investigate machinery. This converts "unlimited growth" into "a triaged row per growth episode."
3. **Append-tax.** A standing rule (guidelines addition or a directives-home row, D-11): a change that grows a skill file past budget must, in the same change, delete equivalent bytes elsewhere in the file, or land a growth-debt note naming the scheduled consolidation. Paired with the audit's machinery admission gate: a new top-level arm must name the existing section it extends and why that section's predicate cannot absorb the case.
4. **Witness budget.** A fix lands the rule; the dossier (witness narrative, rejected alternatives, dates) lives in the backlog row or the changelog. Operative text cites the row in at most one line. This single rule would have kept today's 64 witness clauses and 81 dated parentheticals out of ~40KB of operative text.
5. **A consolidation consumer.** The per-cycle harvest duty gains a third leg: one consolidation pass per cycle under a live standing directive, taking the highest-value dedup candidate from the duplication report (below), ad-hoc-eligible when it is pure dedup with byte parity on non-pinned spans, plan-routed when pinned spans move.
6. **A duplication report as a script.** Land the Part 2 analysis as `scripts/skill_text_duplication.py` (repeated-span percentage per file, top duplicated sentences, cross-file intersections). The rider reads it; the consolidation pass consumes it; the budget gate and the report together give the loop both the alarm and the work list.
7. **Review alignment.** The plan-review panel lenses gain one line: operative text that grew without a deletion is a finding class, so authoring-time bloat gets caught before landing instead of after.

## Part 6: routing recommendation

- **Plan-worthy:** the changelog extraction, the split, the budget gate, and any pinned-span fold. The maintenance skill is machinery by the ad-hoc eligibility test's own arms (pins suite and cross-skill navigation both break under a careless edit), so this routes through a plan, not an ad-hoc run. Suggested carrier: a new backlog row (the ceremony-friction carrier row is scoped to gate demotions and should not absorb a second program), investigated into a PLAN-PROMPTS entry per the standing verb routing.
- **Do first, cheapest:** the changelog extraction as the plan's Task 1 (it alone removes ~154KB and makes every later task's diff readable), the budget gate as Task 2 (so the mechanism exists before the split, closing the re-growth window), the split as Tasks 3+.
- **Ad-hoc-able now, if wanted:** landing `scripts/skill_text_duplication.py` (a new read-only script, no skill edits) and filing the backlog row. Nothing else in this program is ad-hoc-eligible.
- **Relationship to the machinery audit:** this is that audit's Part 5 admission-gate item supplied with its evidence base. The two programs share the append-tax and admission-gate machinery; landing this document's Part 5 first gives the audit's Part 5 its enforcement surface.

## Appendix: measurement notes

- Byte sizes from `wc -c` at HEAD (2026-10-09, both copies identical between `~/.agents/skills/maintenance/` and the vendored `agents/skills/maintenance/`); token estimates at the corpus's own 4-chars-per-token proxy (zcode.md "Context measurement primitive").
- Growth series: 35 commits touching SKILL.md, 2026-09-15 through 2026-10-09; sizes at sampled commits 18KB (09-15), 92KB (09-21), 242KB (09-27), 314KB (10-04), 326KB (10-06), 357KB (10-09); one shrink event (10-06, minus 64 bytes); median per-commit delta +3.9KB, mean +10.0KB.
- Duplication: 10-word word-shingles, normalized lowercase; repeated-span share counts words inside any shingle occurring twice or more; sentence dedup at 60+ normalized chars; cross-file intersection counts unique shared shingles.
- Pin count: 515 `pin()` invocations in `scripts/check_maintenance_pins.sh` (2,852 lines).
- Peer-skill sizes for context: execute-plan 309KB, plans 193KB, done 152KB, doing-code-review 88KB, review-staging 81KB, investigate ~17KB.
