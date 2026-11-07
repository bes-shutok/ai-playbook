# Plan: operative file read-budget gate and load-on-dispatch splits

Backlog origins (scope of record):
- docs/history/backlog/2026-11-07-operative-files-exceed-read-tool-single-read-cap.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-operative-file-read-budget-gate-p<identity-token>-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3h total, largest task 1h
Authoring claim: 2026-11-07-operative-files-exceed-read-tool-single-read-cap.md (session sess_2ef2f7d4-cfc2-4dac-8d4b-fde95273bf35)
Executed: no

Design input (prose only, never a Backlog origin): the PLAN-PROMPTS entry `operative-file-read-budget-gate` in docs/history/backlog/PLAN-PROMPTS.md, which routes this item; its admission fields, scope arms, and rejected alternatives are adopted here.

## Terms

- Operative file: a tracked file a skill instruction directs a session to read whole (the maintenance skill's files under `agents/skills/maintenance/`, the plans and execute-plan skills' SKILL.md files, and their siblings under `agents/skills/`), plus the two rolling prompt logs.
- Single-read budget: the harness Read tool's per-call token ceiling (25000 tokens as witnessed) and its hard per-file size cap (256KB as witnessed); a file above either cannot load whole regardless of the caller's window.
- Byte-budget gate: the EXISTING warning-only gate `scripts/skill_text_budget.py` with its per-file ratchet caps table `scripts/skill_text_budget_caps.json` and its machinery registry row `script:skill_text_budget.py` (landed by docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md Task 2, wired advisory into the pins suite); this plan promotes and calibrates it, never a second gate.
- First true catch: the promotion criterion the gate's own docstring reserves (blocking "ONLY after its first true catch (a breach line that identified real growth worth stopping)"); the origin row's fourteen-refusal inventory is that catch on record.
- Load-on-dispatch split: the learn skill's router-plus-modules shape (agents/skills/learn/SKILL.md routing each step to its module file): the file's top section keeps the dispatch entries and the moved sections become module files read per dispatch, never the full pre-split body.

## Why

The fleet's operative files grew past the Read tool's single-read budget and the tool refuses the whole file even when the caller supplies offset and limit, contradicting the refusal's own remedy advice: fourteen refused reads across the 2026-11-06 10:00 through 2026-11-07 02:00 sessions, every one with a window supplied, on exactly the files every unattended session must load (the maintenance runtime overlay at 119033 bytes, the plans skill at 205074 bytes, the decisions file at 111845 bytes when witnessed, and one 354240-byte rolling log at the 256KB hard size cap). Each session recovered only by falling back to shell text tools, so instructions that direct a whole-file read silently degrade to partial or skipped context. The corpus owns both remedy halves and has landed only half of one: the learn skill's load-on-dispatch module split is the in-repo precedent for an over-cap file, and the byte-budget gate EXISTS but stands warning-only with per-file ratchet caps seeded from landing-time sizes (zcode.md's cap 116647 sits above the single-read budget), its own promotion path reserved for exactly the true catch this row records. The witnessed cost is the price of that pending promotion, now measured.

## Gist & Examples

TLDR: the existing warning-only byte-budget gate is promoted to blocking with its caps calibrated to the harness single-read budget and every file the promoted gate names as over-cap splits load-on-dispatch after the learn router precedent, so operative files load whole through the Read tool again, naming efficiency as the driving force.

Before (today): a session loading the runtime overlay, the plans skill, or the decisions file hits a hard mid-walk refusal, re-issues the same windowed read, then falls back to grep and sed; the walk continues with degraded context and wasted turns; the existing gate prints advisory lines nobody promoted, and its ratchet caps seeded above the single-read budget cannot see the refusal class.

After (this plan): the gate's caps are calibrated to the single-read budget, its promotion criteria fire on the recorded true catch, and its blocking breach report names the over-cap files; the named files split into router-plus-modules; a fresh unattended session loads each through the Read tool without a fallback.

Example: the runtime overlay's 119033 bytes (about 27.6K tokens) breach its calibrated cap; its sections move byte-verbatim into module files beside it, the router keeps the runtime identity and the module dispatch table, and the sessions that directed a whole-file read now read the router plus the in-flight module.

Edge cases: a file at or under its calibrated cap never splits (the promoted gate's blocking breach report is the split set of record; decisions.md measured 91086 bytes at authoring time and is inside the calibrated cap, so it splits only if execution-time measurement names it); the breach set at authoring-time sizes holds four skill files (the runtime overlay 119033, the plans skill 205074, the execute-plan skill 187745, and the vendored agterm reference 129763 bytes), and the conditional split task owns whichever of them remain at execution time; the rolling logs carry the tool's own 256KB hard cap as an informational class in the gate's output and the witnessed breach is recorded, while their size governance stays with the logs' existing prune and freeze duties (no new log machinery); a split moves bytes verbatim and changes no wording, so every consumer instruction that names a moved section keeps resolving through the router's dispatch entry.

## Outcome

Every file a skill instruction directs a session to read loads whole through the Read tool, or the owning skill's router names its own module read path so the load never depends on a whole-file single read; the gate keeps the corpus inside the calibrated caps from then on.

- Gate delta: the existing warning-only byte-budget gate (`scripts/skill_text_budget.py`) promotes to blocking through its own reserved criteria and its pins-suite wiring moves to the suite mode; no gate is added or removed (the registry row update is the admission record; nothing enters the removals list).
- The gate's breach report is the split set of record at execution time and the growth record thereafter.
- The witnessed fallback-to-shell-text degradation ends for the named surfaces.

## Assumptions

- assume the promotion runs through the gate's own reserved criteria: the origin row's fourteen-refusal inventory is the first true catch, so `scripts/skill_text_budget.py` promotes to blocking (exit 1 on skill-file breaches) in this plan's Task 1 with the machinery registry row `script:skill_text_budget.py` updated in the same change (the witness ref-pointed at the origin row, the promotion date and criteria satisfaction recorded in its note); basis: the gate's docstring reserves exactly this path, and the guidelines' Machinery admission protocol's same-change rule is satisfied because the promotion updates the existing row rather than adding one.
- assume the caps calibration is a one-time lowering in the caps table (the ratchet's never-raise rule untouched: lowering is its sanctioned direction): each per-file cap above the single-read ceiling drops to that ceiling; basis: the ratchet seeded caps from landing-time bytes plus margin (zcode.md at 116647), which is above the 25000-token budget the tool enforces, so the seeded figures cannot see the refusal class by construction.
- assume the single-read ceiling is 100000 bytes, keyed to the binding witnessed pairing (111845 bytes refused at 27432 tokens, 4.08 bytes per token) so the ceiling sits inside the 25000-token budget by about 490 tokens at the worst pairing; the calibration's safety rides the breach row naming any file the tool still refuses, not on a wide numeric margin; the rolling-log figure is 262144 bytes, the tool's own hard cap, not a corpus choice.
- assume the splits move bytes verbatim with no wording changes; basis: the maintenance-skill-size-refactor precedent (docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md Task 3, archived durable home) moved module bodies byte-verbatim with headings intact, and wording changes inside a split would invalidate the pins and cross-references that resolve through the moved text.

Decision points requiring a grill: none remain (the promotion path, the cap calibration, and the split method are resolved by the gate's own reserved criteria, the origin row's scope arms, the guidelines' anti-growth rules, and the recorded precedents, under the maintenance-selected standing authorization).

## Standing constraints

- The gate is the only machinery: the EXISTING `scripts/skill_text_budget.py` is promoted and calibrated; no second gate, validator, ledger, or fence is added, no new script file is created, and the registry row update is the same-change admission record (nothing is removed; the removals list gains no entry).
- Splits move bytes verbatim: headings, wording, and internal cross-references intact; the router text declares the read set and names the moved sections; no consumer instruction is rewritten to chase a moved section (the router's dispatch entry is the only new resolution path).
- The rolling logs' size governance stays with their existing prune and freeze duties; this plan adds the log class to the gate's output and the witnessed breach to the record, never a log-specific enforcement arm.
- Anti-growth balance: the promotion activates the guidelines' pending clause (a change growing a file past its cap deletes equivalent bytes in the same change); the split commits' own byte delta is the verbatim move itself, priced by the router text's addition being the only new bytes.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the promoted gate's breach report matches the Read tool's observed refusal class (the runtime overlay, the plans skill, the execute-plan skill, and the agterm reference breach at authoring-time sizes; decisions.md and the maintenance router do not)
- portability: caps live in the gate's own calibrated table, never inline in skill text; the split shape follows the learn precedent, not a runtime-specific mechanism
- simplicity: one script, one registry row, one test file; the splits add no logic, only verbatim moves plus router dispatch entries

**Done when:**
- the promoted gate's caps table carries the calibrated 100000-byte ceiling on the skill class and the gate's output carries the log class against the 262144-byte tool hard cap as informational rows, with its registry row updated in the same change
- every file the promoted gate names in its blocking ceiling class at execution time is split load-on-dispatch with the router text declaring the read set (sub-ceiling ratchet breaches stay the advisory growth watch)
- the pins suite, the hygiene scan, and the amended gate test file all exit 0

**Ship when:**
- a fresh unattended session loads the runtime overlay, the plans skill, and the decisions file through the Read tool without a shell-text fallback (the origin row's own ship-when; post-landing observation, not a plan task)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Scripts and registry:**
- `scripts/skill_text_budget.py` (Task 1)
- `scripts/skill_text_budget_caps.json` (Task 1)
- `scripts/test_skill_text_budget.py` (Task 1)
- `scripts/machinery_registry.json` (Task 1)
- `scripts/check_maintenance_pins.sh` (Task 1)

**Docs:**
- `agents/skills/maintenance/zcode.md` plus its split modules (Task 2)
- `agents/skills/plans/SKILL.md` plus its split modules (Task 3)
- `agents/skills/execute-plan/SKILL.md`, `agents/skills/agterm/reference.md`, and `agents/skills/maintenance/decisions.md` plus their split modules if the promoted gate names them (Task 4)
- `agents/skills/maintenance/SKILL.md` router text for the overlay's dispatch entries (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- any second gate, validator, or ledger beyond the promoted `scripts/skill_text_budget.py`; reason: the anti-growth rules sanction exactly one gate and landing a sibling would violate the Machinery admission protocol's same-change rule this plan's own standing constraint records
- entry-content edits in the rolling logs (their roster, entries, receipts); reason: the logs' size governance is their existing prune and freeze duties' job; this plan touches only the gate's log-class output and the witnessed-breach record
- wording changes inside split-out module bodies; reason: verbatim moves keep pins and cross-references resolving
- `agents/skills/learn/` files; reason: the learn split is the cited precedent, not a target

## Validation Commands

```bash
# Run every command from the target repository root.
bash scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
python3 scripts/machinery_inventory.py --check
python3 scripts/skill_text_budget.py --check
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_skill_text_budget.py -q
```

Authoring preflight on 2026-11-07: the pre-round gate ran over the drafted bytes before the first review round (python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-07-operative-file-read-budget-gate.md), failed twice at the create boundary (one over-cap task item in Task 1, then a missing (new) Files annotation, a malformed Primary class anchors entry, and two further over-cap task items), and passed after those structural fixes; the re-run before the first review round exited 0, and its outcome records beside the review evidence before certification. The pre-review sweep ran the hygiene scan, the pins suite, and the machinery inventory check from the placement root; their outcomes ride the r1 record. Rule 22 audit: this plan promotes an existing script and splits tracked docs; no literal-insertion or negative-grep simulation applies to its prose; the em-dash changed-line scan covers the draft and fold commits. This validation preamble owns command purpose; measured execution results live in the run's execution evidence, not in plan review-state prose. The machinery inventory check reports the pre-existing unregistered scripts/maintenance_fire_outcomes.py finding (commit 833e4c7d3 predates this plan) as report-only when it fires during this plan's execution.

## Tasks

### Task 1: promote and calibrate the existing byte-budget gate

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/skill_text_budget.py`
- `scripts/skill_text_budget_caps.json`
- `scripts/test_skill_text_budget.py`
- `scripts/check_maintenance_pins.sh`
- `scripts/machinery_registry.json`

- [ ] The caps table is calibrated in one lowering pass: every per-file cap above 100000 bytes drops to 100000 (the single-read ceiling), the ratchet's never-raise rule untouched, and the calibration date and derivation recorded in the caps file's own metadata field or the registry note [class: IMPLEMENTATION_REQUIRED]
- [ ] The derivation names the binding witnessed pairing (111845 bytes refused at 27432 tokens, 4.08 bytes per token) so the ceiling sits inside the 25000-token budget by about 490 tokens at the worst pairing, and the calibration's safety rides the breach row naming any file the tool still refuses, not on a wide numeric margin [class: IMPLEMENTATION_REQUIRED]
- [ ] The gate promotes to blocking per its docstring's reserved criteria with a two-surface exit contract and a two-class breach taxonomy: the blocking class is the single-read ceiling class (a skill file whose byte size exceeds 100000), standalone `--check` exits 1 with `OUTCOME: fail` when any blocking-class file exists, 0 when the ceiling class is clean, 3 on usage errors [class: IMPLEMENTATION_REQUIRED]
- [ ] Sub-ceiling ratchet-cap breaches stay advisory rows exactly as the warning-only gate printed them, the ratchet's growth-watch doctrine unchanged; a suite mode (a `--suite` flag the pins suite passes) prints both classes' rows but exits 0 [class: IMPLEMENTATION_REQUIRED]
- [ ] The docstring's warning-only mode descriptions are updated to the promoted semantics in the same change [class: IMPLEMENTATION_REQUIRED]
- [ ] The pins suite's gate-invocation arm (the capture treating a non-zero gate exit as did-not-run-reliably) is rewired to call the suite mode, so the suite keeps exit 0 while printing the breach lines; every true catch surfaces as a visible report line instead of a suite failure [class: IMPLEMENTATION_REQUIRED]
- [ ] The gate's `--check` output gains the rolling-log class measured as informational rows (the two rolling prompt logs at their backlog-dir paths against the 262144-byte tool hard cap, never moving the exit code; the logs' size governance stays with their existing prune and freeze duties), and the execution record carries the witnessed breach figure (EXEC-PROMPTS.md at 364091 bytes against 262144 at authoring time) [class: IMPLEMENTATION_REQUIRED]
- [ ] The machinery registry row `script:skill_text_budget.py` is updated in the same change: the witness ref-pointed at docs/history/backlog/2026-11-07-operative-files-exceed-read-tool-single-read-cap.md (the first true catch), the promotion date and the criteria satisfaction recorded in the note, and a review date of 2027-02-07 added; no new row is created [class: IMPLEMENTATION_REQUIRED]
- [ ] The existing test file is amended to the promoted contract: the advisory pin asserting rc 0 with `OUTCOME: pass` on breach is updated to the two-surface semantics (standalone exit 1 on a ceiling-class breach, suite mode exit 0 with both classes' rows printed), and a tree at the caps passes clean [class: REPOSITORY_TEST]
- [ ] The amended test file pins the exit-3 usage arm in both surfaces (the suite mode's usage error also exits 3, the class the capture arm's wiring-failure detection depends on) and the calibration lowering (a cap above the ceiling drops to it; a cap below stays) [class: REPOSITORY_TEST]
- [ ] Run the Validation Commands block, expects the hygiene scan exit 0, the pins suite exit 0 with the promoted gate's breach lines visible in its report (the pre-split tree carries breaches by design), the amended test file exit 0, and the machinery inventory reporting the pre-existing unregistered-script finding as report-only [class: REPOSITORY_TEST]
- [ ] Run the standalone gate, expects exit 1 naming the ceiling class exactly (the four Why-named files; whatever the tree carries at execution time) with the sub-ceiling ratchet breaches (template-authoring.md and template-execution.md at authoring-time sizes) printed as advisory rows that do not move the exit [class: REPOSITORY_TEST]
- [ ] Commit: `scripts: promote skill-text byte-budget gate to blocking with single-read calibrated caps` [class: IMPLEMENTATION_REQUIRED]

### Task 2: split the maintenance runtime overlay load-on-dispatch

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode.md`
- new module files beside it (the split task names them)
- `agents/skills/maintenance/SKILL.md` (router text only)

Primary class anchors:
- `## Scheduling primitives` in `agents/skills/maintenance/zcode.md`

- [ ] The overlay's top section keeps the runtime identity line and gains a module dispatch table in the learn router's shape declaring the read set: this router plus the in-flight module named by the consuming step, never the full pre-split body [class: IMPLEMENTATION_REQUIRED]
- [ ] The section-to-module mapping moves the overlay's sections byte-verbatim (headings, wording, and cross-references intact) into module files beside the router, the boundaries following the file's own `##` section headings as they exist at execution time, each heading mapped to exactly one module [class: IMPLEMENTATION_REQUIRED]
- [ ] The boundary families this task splits into: scheduling primitives and child markers; recurring automation recipe and re-arm duties; dispatch ladder and discipline; primitive verification and witnesses; quota, pricing, and effort policy; context and audit [class: IMPLEMENTATION_REQUIRED]
- [ ] Each module's name is recorded in the dispatch table, and the router's own byte total stays inside the calibrated cap after the split [class: IMPLEMENTATION_REQUIRED]
- [ ] The maintenance skill's router text (agents/skills/maintenance/SKILL.md Step 0 runtime-load line and any other whole-file overlay references) resolves the overlay through the dispatch-table form; no other consumer instruction is rewritten [class: IMPLEMENTATION_REQUIRED]
- [ ] Pay for growth: the split is a verbatim move priced by the dispatch table's added bytes; the router's own byte total stays inside the calibrated cap after the split [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the pins suite and the gate, expects pins exit 0 and the gate to stop naming the overlay [class: REPOSITORY_TEST]
- [ ] Commit: `docs: split maintenance runtime overlay load-on-dispatch` [class: IMPLEMENTATION_REQUIRED]

### Task 3: split the plans skill load-on-dispatch

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`
- new module files beside it (the split task names them)

- [ ] Read the plans skill whole once through shell text tools (the witnessed fallback the split removes) and map its sections to modules; the top section keeps the skill identity and gains the module dispatch table declaring the read set [class: IMPLEMENTATION_REQUIRED]
- [ ] Sections move byte-verbatim into module files beside the router with the boundaries following the skill's own phase and concern headings, each module named in the dispatch table; the vendored-copy discipline applies to the runtime-side catalog per the repository guidelines (a tracked landing path when the runtime twin diverges) [class: IMPLEMENTATION_REQUIRED]
- [ ] Consumers that direct a whole-file plans-skill read (the maintenance authoring payload's skill references, the review skills' read lists) resolve through the dispatch-table form by the router's own declaration; a consumer instruction naming a specific section keeps resolving through the module that now holds it [class: IMPLEMENTATION_REQUIRED]
- [ ] Pay for growth: verbatim move priced by the dispatch table's added bytes; the router stays inside the calibrated cap [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the pins suite and the gate, expects pins exit 0 and the gate to stop naming the plans skill [class: REPOSITORY_TEST]
- [ ] Commit: `docs: split plans skill load-on-dispatch` [class: IMPLEMENTATION_REQUIRED]

### Task 4: split the promoted gate's remaining breach set

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md` plus its split modules (187745 bytes at authoring time; the fleet's most-loaded execution surface)
- `agents/skills/agterm/reference.md` plus its split modules (129763 bytes at authoring time; a vendored skill's reference, so the split carries the local-fork notice per the repository guidelines' vendored sync rules and the upstream sync must re-apply or consciously drop it)
- `agents/skills/maintenance/decisions.md` (91086 bytes at authoring time, inside the calibrated cap; splits only if the promoted gate names it at execution time)

- [ ] For each over-cap file the promoted gate names beyond Tasks 2 and 3's files: the same verbatim move plus router dispatch-table shape as Tasks 2 and 3, with the split task recording the module boundaries it chose and the simpler-design comparison when a boundary choice was contested; a file the gate stops naming needs no split and the task records none-found [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the pins suite and the gate after each split, expects pins exit 0 and the gate's ceiling-class breach set empty at the task's end (sub-ceiling advisory rows may remain; they are the ratchet's growth watch, not this plan's split set) [class: REPOSITORY_TEST]
- [ ] Commit per split: `docs: split <file> load-on-dispatch` [class: IMPLEMENTATION_REQUIRED]

