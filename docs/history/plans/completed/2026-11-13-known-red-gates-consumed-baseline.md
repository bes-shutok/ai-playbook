# Plan: Consume the known-red gate baseline at review and preflight triage

Backlog origin: `docs/history/backlog/2026-11-10-known-red-gates-retriage-tax.md`
Authoring claim: 2026-11-10-known-red-gates-retriage-tax.md (session sess_65f4f2f1-d433-47d8-ab81-5a7b64e386a0)
Driving force: efficiency + code-quality
Plan review record: the staging series {reviews_dir}/2026-11-14-plan-review-known-red-gates-consumed-baseline-pb78de609-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1.0h
Executed: yes (79e264fc7)

## Terms

- **Known-red baseline file**: the machine-readable JSON record of each producer surface's current red lines, written by the render mode into the gitignored maintenance state home as `baseline-known-red-gates.json`; the classification input the consumers read at triage time, subject to the pins-escalation carve-out's classification-time ledger re-read.
- **Producer surface**: one of the three guard producers the baseline renders: the machinery inventory check (`scripts/machinery_inventory.py --check`), the maintenance pins suite (`scripts/check_maintenance_pins.sh`), and the skill-text budget scan (`scripts/skill_text_budget.py`).
- **Red line**: a line a producer emits for a failure or advisory warning it reports (the output vocabulary each producer already has; no producer wording changes).
- **Baseline red**: a red line the baseline file lists for its producer; panels and preflights treat exactly these as pre-existing. The pins suite's own recorded-red register (`scripts/gate_liveness_ledger.json`) stays the pins gate-layer record; the baseline is the triage-layer record. Pins-escalation carve-out (the single home; consumer items cite it by reference): a failing-pin line the pins run itself escalates stays actionable regardless of baseline membership; "the pins run itself escalates" is exit-effect keyed, meaning the line moves the exit (a plain `PIN FAIL` or lowercase `pin fail:` line from the check families) or the run fails it as unrecorded, while the warning-only placement family's exit-0 `PIN FAIL: placement pin:` shape and the advisory `PIN WARN` rows keep their baseline classification. The determination re-reads the tracked ledger at classification time against the system date, resolved from the primary checkout (the home authority mechanism), matching the register's stable pin name by exact string equality per the suite's own row-shape contract block in `scripts/check_maintenance_pins.sh` (cited by reference, never re-derived in a consumer clause; a failing line whose remainder extends the register name with a `: <output>` suffix matches that entry, the suite's grep-error row shape; an unreadable or unparseable ledger at classification time escalates recorded-shaped pin lines, the suite's own tool_error shape, and a RECORDED-shaped line whose entry the re-read cannot confirm at the tracked ledger escalates); escalated additionally covers a `PIN RECORDED RED EXPIRED` line, an entry whose review-by has passed, a failing line matching no register entry, and a `PIN RECORDED RED MALFORMED` advisory (a malformed register row is never recorded pre-existing).
- **Unknown red**: a red line absent from the baseline file; it stays fully actionable.
- **Base tip and staleness**: the primary checkout's default-branch tip at render time is recorded as provenance metadata, not the staleness key; a producer section of the baseline is **stale** when its recorded controlling-input digest mismatches the current tracked inputs at classification time (the digest covers that producer's controlling tracked files: the inventory script, `scripts/machinery_registry.json`, and the state-file surface its witness consult reads (`agents/skills/maintenance/state-file.md`); the pins suite's `scripts/check_maintenance_pins.sh` and `scripts/gate_liveness_ledger.json`; the capped-file set the budget scan reads plus the scan script and its caps table `scripts/skill_text_budget.py`, `scripts/skill_text_budget_caps.json`; recorded per section at render, re-derived at each consumer read from the primary checkout's working-tree bytes of those files), and a stale, absent, unreadable, or unavailable section fails open with that producer's reds all actionable (unavailable: the render recorded the producer as failed to run, timed out, or terminated without its expected output; the single definitional home; the Assumptions staleness bullet and the consumer items cite this entry).
- **Capture vocabulary**: the per-producer classes the render records verbatim: the inventory's `FAIL:` lines; the pins suite's `PIN FAIL`, `PIN WARN`, `PIN RECORDED RED`, `PIN RECORDED RED EXPIRED`, `PIN RECORDED RED MALFORMED`, and the exit-0 `PIN FAIL: placement pin:` advisory shape, and the check families' lowercase `pin fail:` failure lines; the budget scan's `CEILING BREACH`, `BREACH`, `PILOT OVER`, and `PILOT PENDING`; excluded as actionable-by-design: the budget scan's `CAPS GAP`, `STALE CAP`, and informational `LOG`/`LOG OVER`, the pins suite's run-summary lines (`PIN RECORDED REDS SUPPRESSED THIS RUN:`, `prune-range pins: first missing clause:`, `placement pins: first missing span:`) and its pre-pin checkpoint's `missing <path>` arm (excluded so a broken checkout's checkpoint failure never baseline-classifies; the lines stay unknown actionable at every consumer); a line matches the section of the producer that emits it as its own report, lines a producer embeds from another producer's report classifying under that other producer's section; accepted behavior: byte-count-bearing advisory entries re-noise when the breaching file's byte count changes.
- **Protocol row**: a `kind: protocol` keep row in `scripts/machinery_registry.json` carrying the machinery admission fields and a pre-registered removals row.
- **Machinery admission fields**: the incident, expected catch frequency, false-positive cost, and review date the Machinery admission protocol requires on the row.
- **Preflight**: the exec-side validation reads this plan classifies: the pre-review text-policy sweep and the execution lane's validation runs (distinct from the rule 29 authoring preflight).
- **Suppression authority**: the render-time determination of which lines may classify as pre-existing; bounded by producer-emission verbatim matching, the carve-out, and the regeneration-time integrity arms.
- **Render mode**: the `machinery_inventory.py` CLI mode that runs the three producers and writes the baseline file; the only regeneration path.
- **Machinery regrowth guard consult**: the maintenance survey's machinery-registry check read (the survey-arms bullet the regeneration duty lands in).
- **Repair entry**: the EXEC-PROMPTS record `machinery-inventory-baseline-red-repair`, which owns repairing the baseline reds themselves.

## Why

Guards that are red at baseline (the pins prune-range placement warnings standing today, the pins staleness warnings the origin window witnessed, advisory budget breaches, the inventory's standing witness failure) reach every review worker and exec preflight as if actionable, so each panel re-derives the same pre-existing classification by hand; the origin's window saw five such instances with zero catches while genuinely new reds got the same weight. One machine-readable record of the pre-existing set lets triage treat exactly those as pre-existing. Repairing the reds themselves stays owned by the repair entry; this plan adds only the consumer side.

## Gist & Examples

TLDR: render the three guard producers' current red lines into one regenerable baseline file and consume it at review triage and the pre-review sweep, so baseline reds render as pre-existing and unknown reds stay actionable, driven by efficiency.

**Before:** a review worker or exec session running the pins suite sees `PIN WARN: prune-range pin ...` lines, the budget scan's advisory `BREACH`/`PILOT OVER` lines, and the inventory check's standing `FAIL: duty:carrier-liveness-missed-fire ...` line, and re-adjudicates each by hand every round.

**After:** the same surfaces read the baseline file first; a line the baseline records is reported as pre-existing with a pointer to the baseline, and a line it does not record is flagged as actionable exactly as today. When a repair lands and an inventory run re-renders, the baseline red set shrinks with it.

## Outcome

Give guard-baseline triage one regenerable record so pre-existing reds stop consuming review and preflight attention.

- A review worker's startup context names each baseline red as pre-existing; unknown reds keep full weight.
- The pre-review text-policy sweep classifies its red lines against the baseline without changing any exit code.
- The baseline regenerates from the producers at machinery inventory runs; no hand-maintained ignore list exists.
- Coordination stays clean: the repair entry repairs the reds, this plan consumes them, and neither absorbs the other.

Gate delta: no refusal class, hard gate, fence, protocol layer, or schema field is added or removed; the change adds one render mode on `scripts/machinery_inventory.py` (repository-state read-only; it writes only the gitignored baseline artifact), one gitignored baseline artifact, and report-only consumption duties on three skill surfaces plus a regeneration duty on the maintenance survey's machinery regrowth guard consult, admission-registered as a protocol row carrying the origin row's machinery admission fields; every producer's exit semantics and output vocabulary stay unchanged. Follow-up disposition: a future producer surface (a fourth guard producer) is an anticipated candidate; it routes to a durable backlog origin with a ready-to-dispatch prompt, never silently into this plan.

## Assumptions

- assume the baseline covers exactly the three origin-named producer surfaces; basis: the origin row's Expected names "each baseline-red guard" and names the machinery inventory as the known-red record home for the inventory surface, while its source reference witnesses the pins instances (five staleness classifications plus the seven-probe pins pass) and the budget instances (two BREACH re-reads).
- assume the baseline artifact is gitignored runtime state under the maintenance state home resolved as the `maintenance_state_dir` facts key with the verified `.ai-playbook/maintenance/` fallback (the resolution `scripts/execute_plan_runtime.py` and the survey's maintenance-state clause implement), never a tracked file, and the authoritative home is the PRIMARY checkout's (a worktree render writes worktree-local state invisible to primary consumers, so renders and consumption resolve the home explicit-rooted in the primary checkout by the mechanism the home authority item names); basis: that home is the loop's existing runtime-record home, the fallback is verified in code, and a tracked baseline would churn with per-checkout state and peer landings.
- assume consumption is report-shape only (a startup preamble and a sweep classification), never a gate, refusal, or exit-code change; basis: the origin's machinery admission prices the artifact as a consumed baseline, and the repository's Machinery admission protocol lands new machinery read-only.
- assume an absent, unreadable, unavailable, or stale baseline fails open to today's behavior (all reds actionable; stale per the Terms Base tip and staleness entry); the quieting benefit is scoped per producer to render-to-next-controlling-input-change windows, and a landing unrelated to a producer's inputs does not stale that producer's section; basis: the origin's false-positive-cost field prices a stale baseline masking new reds after repair-without-regeneration, the re-render absorption cost is this plan's re-pricing under the digest-scoped staleness window, and the gitignored artifact carries no per-read integrity gate, so no-baseline must equal the status quo and the catch window must be honest about the measured landing cadence.

Decision points requiring a grill: baseline set scoped to the three origin-named producer surfaces (maintenance-selected receipt: best-supported in-scope option; source: origin Expected, `docs/history/backlog/2026-11-10-known-red-gates-retriage-tax.md`; 2026-11-13; Assumptions); baseline home is the gitignored maintenance state home resolved as the `maintenance_state_dir` facts key with the `.ai-playbook/maintenance/` code fallback, authoritative in the primary checkout (maintenance-selected receipt; source: the fallback resolution verified in `scripts/execute_plan_runtime.py` and the survey-arms maintenance-state clause; 2026-11-13; Assumptions); consumption is report-only on the worker-preamble and sweep surfaces (maintenance-selected receipt; source: origin machinery admission fields; 2026-11-13; Review Scope); fail-open on an absent or stale baseline (maintenance-selected receipt; source: origin false-positive-cost field; 2026-11-13; Evaluation Criteria); the staleness criterion is per-producer controlling-input digests rather than a whole-tree tip, timestamp, or commit count (maintenance-selected receipt; source: the measured landing cadence and the r5 reconciliation's design-reflection adoption; 2026-11-14; Terms).

## Standing constraints

- Byte budget: every touched skill file pays its growth in the same change per the repo-wide byte-budget gate (`scripts/skill_text_budget.py`); additions past a cap delete equivalent bytes in the same commit.
- Producer integrity: no producer's exit codes, refusal paths, or output wording change; the baseline classifies lines only at the consumption surfaces.
- Coordination: the repair entry repairs the reds; this plan neither repairs them nor absorbs that entry; a repair landing regenerates the baseline through the same render mode.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the render mode reproduces each producer's current red lines verbatim in the baseline; a consumer following the classification wording treats a baseline red as pre-existing except a pins line the pins run itself escalates (the carve-out), and a near-miss line as actionable.
- safety: with the baseline file absent, every surface behaves exactly as today; on the line-matching classification surfaces (the sweep clause and the validation reads), a fabricated line no producer emits never classifies as pre-existing, the startup preamble consumes render-time snapshots under the subordination line (live producer output and the carve-out win), and suppression authority joins producer-unavailability and staleness as regeneration-time integrity arms, not per-read gates.
- maintainability: one command regenerates the baseline; no manual editing path exists.

**Done when:**
- `python3 scripts/machinery_inventory.py --render-baseline <path>` writes the baseline JSON listing each producer's red lines and exits per the outcome contract.
- An initial render has run into the resolved authoritative home: `baseline-known-red-gates.json` exists at the primary checkout's maintenance state home (the home authority mechanism) and the worker-preamble classification path reads it (witnessed by the Task 3 preamble-surface needle, not by a command); the render lands pre-landing bytes, so the inventory and budget sections are expected stale-at-landing and fail open until the next survey-consult re-render.
- The pytest run of `scripts/test_machinery_inventory.py` passes with exactly the recorded pre-existing failure (`RealTreeCheck::test_real_tree_checks_green`) and no new failure.
- `bash scripts/check_maintenance_pins.sh` and `python3 scripts/skill_text_budget.py --check` return their current baseline verdicts unchanged, and the budget scan reports no new blocking breach after the skill-text edits.
- The four skill surfaces carry their clauses (three consumption, one regeneration, with the exec-lane pointer among them), and the registry carries the protocol row.
- The pinned skill surfaces carry the explicit-rooted primary-checkout resolution, the matching-baseline pre-existing classification wording, the absent, unreadable, unavailable, and stale fail-open wording, and the pins-escalation carve-out wording, witnessed red-before-landing by the Task 3 content witness needles via the focused pytest run, with the resolution arm executing the primary-checkout mechanism from a worktree-like cwd.
- The content witness needles pin each claim in the worktree bullet above, including the pins-escalation carve-out span on the preamble and sweep surfaces and the snapshot-subordination span on the preamble surface: matching-baseline classification from a worktree cwd (its negative arm transitively covering the unknown-reds-actionable and baseline-pointer wordings), the absent, unreadable, unavailable, and stale fail-open arms, the explicit-rooted resolution, and the carve-out's escalation predicate.

**Ship when:**
- none; the work is repository-verifiable, and no external release condition exists.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/machinery_inventory.py` (Task 1)
- `scripts/machinery_registry.json` (Task 3)
- `scripts/OUTCOME_CONTRACT.md` (Task 1)

**Tests:**
- `scripts/test_machinery_inventory.py` (Task 1)

**Skill text:**
- `agents/skills/execute-plan/implementation-loop.md` (Task 2)
- `agents/skills/review-agents/SKILL.md` (Task 2)
- `agents/skills/plans/plan-quality-gate.md` (Task 2)
- `agents/skills/maintenance/survey-arms.md` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above when causally related to this plan: it implements or completes a task, fixes a regression plan work introduced, or closes wiring a named change implies. A weak or speculative link drops as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/check_maintenance_pins.sh` and `scripts/skill_text_budget.py`; reason: producer surfaces stay byte-unchanged by standing constraint; their red repairs belong to the repair entry.
- `docs/history/backlog/EXEC-PROMPTS.md`; reason: the repair entry's home; this plan adds no EXEC record.
- Any repair of a baseline red (witness re-point, staleness fix); reason: owned by the repair entry per the coordination constraint.

## Validation Commands

Validation preamble (rule 29 authoring preflight, recorded 2026-11-14 at the worktree placement root):

- Round-start state for r1: draft checkpoint 736b4b547 (sha256 e5e413e9c66a12fb, superseded pre-round by the preflight fixes); preflight checkpoint c9a424cdc carries the bytes r1 reviewed (sha256 1fb998740dccb0735b59bfd67a2a68ebdd5cd94f7554c69fc4c268126b2f44e7); this line is historical provenance and the certification wall of record is the seal file.
- `bash scripts/check-no-em-dash.sh touched`: OUTCOME: pass (rc 0).
- `bash scripts/check-no-em-dash.sh added-lines --base a8742e9ecc4d34357bdd7b412e6d676d3971a0a6`: OUTCOME: pass (rc 0).
- `bash scripts/scan-public-hygiene.sh`: OUTCOME: pass (rc 0).
- pytest `scripts/test_machinery_inventory.py`: 28 passed, 1 failed; the failure (`RealTreeCheck::test_real_tree_checks_green`) reproduced identically on the primary checkout's main before any plan work, a pre-existing baseline red of exactly the class this plan documents; its repair belongs to the repair entry, not this plan.
- `python3 scripts/machinery_inventory.py --render-baseline /tmp/known-red-baseline-demo.json`: rc 2 today (argparse usage error, the mode does not exist yet); this is the rule 19 RED-today execution evidence for Task 1.
- `python3 scripts/machinery_inventory.py --check`: rc 1 today (1 known failure: the `duty:carrier-liveness-missed-fire` witness ref unresolved); pre-existing baseline red.
- `python3 scripts/skill_text_budget.py --check`: OUTCOME: pass (0 ceiling breaches; 3 advisory ratchet lines, 9 caps gaps, baseline posture).
- `bash scripts/check_maintenance_pins.sh`: OUTCOME: pass (baseline posture preserved; 4 advisory PIN WARN prune-range lines on EXEC-PROMPTS.md).
- `python3 scripts/plan_readiness.py --pre-round <plan>`: first run failed on missing classification tags in Task 1; tags added in the same edit; re-run pending at the next boundary record.
- `python3 scripts/check_review_agent_portability.py` and `python3 scripts/test_review_agent_doors.py`: both OUTCOME green on today's tree (recorded for the F10 fold; Task 2 runs them at execution).

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_machinery_inventory.py -q
python3 scripts/check_review_agent_portability.py
python3 scripts/test_review_agent_doors.py
python3 scripts/machinery_inventory.py --render-baseline /tmp/known-red-baseline-demo.json
python3 scripts/machinery_inventory.py --check
bash scripts/check_maintenance_pins.sh
python3 scripts/skill_text_budget.py --check
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base a8742e9ecc4d34357bdd7b412e6d676d3971a0a6
```

### Task 1: Render the known-red baseline from the three producer surfaces

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/machinery_inventory.py`
- `scripts/test_machinery_inventory.py`
- `scripts/OUTCOME_CONTRACT.md`

Primary class anchors:
- `render_baseline` in `scripts/machinery_inventory.py`

- [x] `render_baseline` delivers baseline rendering: expects the requested output path to hold JSON listing, per producer, the captured classes verbatim per the Terms capture vocabulary entry, plus generation timestamp, base tip, each section's controlling-input digest, and the resolved write home [class: IMPLEMENTATION_REQUIRED]
- [x] `render_baseline` delivers outcome-contract reporting: given a producer that fails to run, times out, or terminates without its expected output, expects the render to record that producer unavailable and still render the others, exiting per `scripts/OUTCOME_CONTRACT.md`, never a silent partial baseline; a modeled fail exit carrying expected output is a capture-success, never an unavailable trigger [class: IMPLEMENTATION_REQUIRED]
- [x] `render_baseline` legacy-exit status: the machinery inventory's legacy exit shape (no `OUTCOME:` line) is normal output, never an unavailable trigger [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a baseline output path that is unwritable, expects the render to refuse with the observed error and write nothing, leaving any existing baseline byte-untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture seam controls in the render tests: expects the fixture tree to carry a minimal valid register or the test to set PINS_RECORDED_RED_REGISTER, escalation-line assertions to pin PINS_RECORDED_RED_AS_OF to a fixed date, and the unavailable-producer injection to resolve producer paths repo-relative within the target checkout [class: REPOSITORY_TEST]
- [x] Hermetic env pins in the render tests: expects every ambient env input the pins producer reads pinned by the fixture, PINS_DUPLICATE_ROOT set to the scratch checkout root (or empty) [class: REPOSITORY_TEST]
- [x] Render-test determinism: comparisons assert the captured-line set modulo the documented variable fields (generation timestamp, absolute paths in captured lines, base-tip hash); the fixture pins commit dates, identity, and init.defaultBranch (precedent: identity only) [class: REPOSITORY_TEST]
- [x] Digest discrimination: given one producer's controlling tracked input edited in the fixture, expects that section's recorded digest to change while the other two stay byte-equal, one mutation per producer [class: REPOSITORY_TEST]
- [x] Fixture reach floor: the scratch carries the five core-file checkpoint targets, one commit on HEAD, and an `agents/skills` file so all three producer arms execute and recorded-red routing runs; the pins producer runs with cwd inside the target checkout; recorded line samples exercise the advisory classes beside live emissions [class: REPOSITORY_TEST]
- [x] Suite selection: new render-test classes join load_tests's discovery arm, so the required inventory collects them [class: REPOSITORY_TEST]
- [x] Primary-checkout resolution arm in the render tests: given the render invoked with cwd in a linked worktree diverging from the primary's tree (one pinned skill file byte-edited and committed, moving a captured line or digest), expects the producers, base-tip provenance, and a relative output path to resolve against the primary checkout per the Task 2 home authority mechanism, the fixture asserting the recorded home and captured lines match the primary tree, not the worktree's [class: REPOSITORY_TEST]
- [x] `render_baseline` env posture: the render mode runs the pins producer with PINS_RECORDED_RED_REGISTER at the primary checkout's tracked ledger and PINS_RECORDED_RED_AS_OF, PINS_DUPLICATE_ROOT unset (ambient environment only; the render-test fixture seam supplies its own pins) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the new render-mode tests fail against the unextended script [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Land the render mode's `scripts/OUTCOME_CONTRACT.md` register row (declaring the producer-subprocess operating-context assumptions and the legacy-exit status of `--check`/`--scaffold`) [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: render the known-red gate baseline from the three producer surfaces` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Consume the baseline at triage surfaces

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-agents/SKILL.md`
- `agents/skills/plans/plan-quality-gate.md`
- `agents/skills/execute-plan/implementation-loop.md`
- `agents/skills/maintenance/survey-arms.md`

- [x] Worker-startup preamble at the severity-calibration prepend point in `agents/skills/review-agents/SKILL.md`: given the baseline file present, expects a known-red preamble naming each baseline red pre-existing under the snapshot subordination (live output and the carve-out win), unknown reds actionable, and failing-pin lines actionable per the carve-out [class: IMPLEMENTATION_REQUIRED]
- [x] Preamble fail-open arm: the preamble is omitted, that producer's reds actionable, when the file is absent, unreadable, or the producer section is stale or unavailable (Terms staleness home) [class: IMPLEMENTATION_REQUIRED]
- [x] Preamble placement marker: the landed preamble lines carry the `portability: abstract` placement marker whose owning-layer note self-declares the lines as operative instructions (not illustrations) per the file's Consumer contract, and both portability checkers stay exit 0 [class: IMPLEMENTATION_REQUIRED]
- [x] Baseline home authority: the baseline resolves explicit-rooted in the primary checkout's maintenance state home (the `maintenance_state_dir` key, `.ai-playbook/maintenance/` fallback) for every consumer read; the primary checkout resolves as the first `git worktree list --porcelain` worktree entry (the OUTCOME_CONTRACT precedent), rooting the home, the producer reads, and the ledger re-reads [class: IMPLEMENTATION_REQUIRED]
- [x] Render resolution scope: renders run the three producers against the primary checkout's tree, and a relative output path resolves against the primary checkout's resolved home; this item is the home authority mechanism's landing home (Task 1's resolution arm tests it) [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep classification clause in the pre-review text-policy sweep in `agents/skills/plans/plan-quality-gate.md`: expects the clause to bind every producer-reading surface (the sweep and the execution lane's validation reads); this clause is the operative classification home (the sweep semantics and the carve-out predicate), cited by reference from the preamble and the exec pointer, the preamble needle asserting the citation resolves to this clause's current wording [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep classification semantics: each baseline-listed line except a failing-pin line escalated per the pins-escalation carve-out classified pre-existing with the baseline pointer, every unmatched line actionable, exit codes unchanged, failing open (that section's reds all actionable) when the file is absent or unreadable, or the producer section is unavailable or stale per the Terms staleness home [class: IMPLEMENTATION_REQUIRED]
- [x] Pins-escalation carve-out enforcement: given a failing-pin line the pins run itself escalates, expects the live-run surfaces to keep it actionable per the Terms carve-out, never from baseline membership alone [class: IMPLEMENTATION_REQUIRED]
- [x] Regeneration duty in the machinery regrowth guard consult in `agents/skills/maintenance/survey-arms.md`: given the consult's inventory run, expects the render-mode invocation refreshing the baseline at the authoritative home (the home authority resolution) [class: IMPLEMENTATION_REQUIRED]
- [x] Exec-lane classification pointer in `agents/skills/execute-plan/implementation-loop.md`: expects a pointer at the Step 1.4 verification gate's scope-intersecting validation accounting and beside the Phase 2 fresh validation run, binding those producer red-line reads to the plan-quality-gate classification clause; the implement worker's task-local validation reads inherit the clause through the Implement Task template's validation commands, no second pointer [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: consume the known-red baseline at triage surfaces` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Register the artifact, witness the landing, render the initial baseline

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/machinery_registry.json`
- `scripts/test_machinery_inventory.py`

Primary class anchors:
- `RegistryContentWitness` in `scripts/test_machinery_inventory.py`

- [x] Content witness in `scripts/test_machinery_inventory.py` for the protocol row (the `RegistryContentWitness` shape): given the row dropped, its admission fields thinned, or any of the four pinned skill surfaces stripped, expects the suite to red; it opens each pinned file (per Task 2 Files) for a per-surface clause-content needle plus the row-note needles, covering the Done-when worktree claims and the carve-out span on preamble and sweep surfaces; a row-only landing reds the run [class: REPOSITORY_TEST]
- [x] Registry protocol row in `scripts/machinery_registry.json` for the baseline artifact with the origin row's machinery admission fields (incident: five 2026-11-09/10 re-triage instances; expected catch frequency: every multi-worker round while pins red; false-positive cost: a re-render without review absorbs newly introduced reds as pre-existing until the next review (re-priced under the digest design; the origin's field prices stale-masking); review date 2026-12-10) [class: REPOSITORY_TEST]
- [x] Registry row witness and removals: the row's witness ref at this plan's living path, the row note carrying the Witness re-point duty (plan-family completion fold re-points it; `duty:carrier-liveness-zero-turn` precedent), the pre-registered removals row naming 2026-12-10 [class: REPOSITORY_TEST]
- [x] Red-before-landing observation: run the focused suite against the pre-Task-2 surface state (the four pinned files checked out at Task 2's parent commit inside the scratch checkout) with the registry row present; the red names the per-surface strip needles (a red from the row-missing assertion does not discharge this item); the witness enumeration adds the snapshot-subordination span on the preamble surface, and the witness class joins load_tests's discovery arm [class: REPOSITORY_TEST]
- [x] Initial render: run `python3 scripts/machinery_inventory.py --render-baseline` with the resolved authoritative home path (the home authority mechanism; file `baseline-known-red-gates.json`), expects the baseline present at the primary checkout's home and the worker-preamble classification path reading it; the render lands pre-landing bytes, so the inventory and budget sections are expected stale-at-landing and fail open until the next survey-consult re-render [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 scripts/machinery_inventory.py --check` → expect rc 1 unchanged, no new failure line naming the new row; run `python3 scripts/skill_text_budget.py --check` and `bash scripts/check_maintenance_pins.sh` → expect no new blocking breach, verdict preserved; run `python3 scripts/check_review_agent_portability.py` and `python3 scripts/test_review_agent_doors.py` → expect exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: register the known-red baseline artifact and witness its consumption` [class: IMPLEMENTATION_REQUIRED]
