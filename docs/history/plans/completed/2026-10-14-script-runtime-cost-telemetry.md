# Plan: per-invocation script wall-time telemetry beside the landing-cost family

Backlog origin: docs/history/backlog/2026-10-13-script-runtime-cost-telemetry.md
Driving force: efficiency + correctness
Plan review record: the staging series {reviews_dir}/2026-10-14-plan-review-script-runtime-cost-telemetry-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1.5h

## Terms

- invocation telemetry: the one-JSONL-line-per-script-invocation record family this plan lands beside the landing-cost family.
- landing-cost family: the landed per-landing telemetry written by the done closeout (registry entry done-skill:landing-cost-record-writer) at the facts-resolved metrics home; one JSONL line per landing, every field nullable, absence reasons carried as named notes, fail-open.
- invocation-costs.jsonl: the new JSONL home this plan adds, `invocation-costs.jsonl` inside the facts-resolved metrics home, sibling of landing-costs.jsonl.
- fail-open writer: a writer whose own failure (unwritable home, missing facts key, import error) never changes the invoking script's exit status, stdout, or stderr contract; telemetry is read-only forever.
- self-timing: the instrumented script measures its own wall time (a start stamp captured at entry, one append at exit) so no caller cooperation is needed.
- invocation kind: the declared integration label a script records for itself: pins-suite, review-validation, readiness-gate, or closeout-battery.
- lane context class: authoring, exec, review-carrier, or unknown; recorded by the invoking site when the site knows the lane, null with a named absence note otherwise.
- worker flag: whether the invocation ran inside a dispatched subagent (true), in-session (false), or unknown (null).
- hot spot: a script ranked by total wall time (invocation count times duration) in the monthly readout.
- machinery registry: scripts/machinery_registry.json, whose entries carry kind/note/witness and whose removals array pre-registers sunsets.
- pre-registered removals row: the registry removals row carrying the invocation-telemetry writer's sunset (a 90-day idle-data review) armed at landing.
- friction-audit: docs/maintenance/recurring-tasks/friction-audit.md, the monthly machinery review's operative input home.
- facts-resolved metrics home: the metrics_dir value from the repo facts TOML block (.ai-playbook/facts.md), default .ai-playbook/metrics, resolved repo-relative by the library through scripts/facts_paths.py (the repo's single TOML-fence parser).
- context telemetry: the existing per-checkpoint token telemetry the execute-plan skill writes under docs/tmp/ (per-run, tmp-resolved); a different family with a different home, named here only to disambiguate.
- start stamp: the entry-side wall-clock record (a python3-derived epoch written to a temp file by the bash integration, or an in-process timestamp for the python integrations) the exit-side append converts into wall_ms.

## Why

The machinery audit priced cost discovery after the fact: its Part 3 root cause 6 names the missing cost feedback into the loop (the 16h/100M-token run was noticed only afterwards) and its Part 1 family 8 prices the per-plan ceremony tax of gate, validator, and probe invocations. The landed landing-cost family records per-landing totals but not which scripts consumed the wall time, so per-script speed decisions are guesses; the operator directed measuring script wall time per session and subagent before optimizing anything.

## Gist & Examples

TLDR: the repo's hot machinery scripts gain one fail-open self-timed JSONL line per invocation beside the landing-cost family, so monthly review can rank scripts by total wall time; driving force efficiency and correctness.

Before: a full landing runs the pins suite, the review validator, the readiness gate, and the closeout battery dozens of times across rounds and workers; nothing records which script consumed the wall seconds, and a runaway session is discovered only when the operator notices the clock.

After: every pins-suite, review-validation, readiness-gate, and closeout-battery invocation appends one line carrying script, invocation_kind, wall_ms, lane_class, worker, recorded_at, and an optional absence note to invocation-costs.jsonl in the facts-resolved metrics home; the write is fail-open and never gates; the monthly friction-audit readout gains the top ten scripts by total wall time, reads only a bounded trailing window, prunes the file to that window in the same pass, and enforces the writer's removals-row sunset.

Edge cases: a script run outside any recognizable lane records lane_class null with the absence note naming why; an unwritable or missing metrics home leaves every instrumented script's exit status and contract output byte-identical; the home is created on first write; a corrupt or partial line never blocks the next append; parallel invocations (parallel review workers) each append one intact line; an invocation whose script file lives outside any checkout (a deployed copy) fails open with no line rather than blocking; the closeout's usage-error and early-refusal arms exit before the exit-side append and record no line.

## Outcome

Script wall-time cost becomes a measured, monthly-reviewed quantity instead of an after-the-fact discovery.

- Each invocation of the four hot machinery scripts leaves one machine-readable cost line where a facts-resolved metrics home is resolvable; unresolvable-home invocations fail open with no line.
- The monthly friction-audit readout ranks the top ten scripts by total wall time from a bounded trailing window, giving any optimization decision its measured target.
- The telemetry is read-only forever: a broken or missing telemetry line never gates a lane.

Gate delta: one new machinery addition (the invocation-telemetry writer family: one shared library plus four script integrations), priced by the origin row's admission record (incident: the audit's Part 3 root cause 6 and Part 1 family 8, docs/maintenance/machinery-blocker-audit-2026-10-09.md; expected catch frequency: every lane, continuous; false-positive cost: one fail-open JSONL line per invocation plus each bash integration's two interpreter spawns, priced in the registry entry's note; sunset: the pre-registered removals row with a 90-day idle-data review); no new refusal class, hard gate, fence, protocol layer, or schema field; no removed refusal, check, or field.

## Assumptions

- assume the metrics home is the facts-resolved metrics home (.ai-playbook/metrics/), not the origin row's literal docs/history/metrics/ path; basis: the audit-artifact consolidation landing re-aimed the telemetry families under .ai-playbook/ with facts keys re-aimed, and the landing-cost writer resolves metrics_dir from facts with that default (the cmd_finalize block in scripts/done_run.sh); the origin row's path predates that landing and this plan supersedes it per the plans skill's SOT placement rule.
- assume the writer placement is the shared self-timing library each instrumented script calls, not a session-side wrapper and not a host hook pair; basis: the origin row delegates the decision to the plan on evidence; a host hook pair knows session identity but has no session-to-lane registry machinery, a wrapper rewrites every documented invocation, and the landed family's nullable-fields-with-absence-notes precedent already covers unknown contexts.
- assume per-session and per-worker attribution is deferred: lane_class and worker land as null plus a named absence note at every site in this plan, including the closeout (cmd_finalize has no lane-discriminating input and authoring-lane closeouts share the same code path), and a later change populates them when a session-to-lane source exists; basis: no current site can derive those values, and the origin row's per-lane and per-subagent aggregations become available once a later mechanism fills the columns.
- assume coverage targets the four hot integration sites named by the origin row's evidence (the pins suite, the review validator, the readiness gate, the closeout battery); ad-hoc interactive invocations of non-instrumented scripts stay unmeasured; basis: the audit's family 8 prices the multiplied ceremony of exactly these loops.
- assume optimization work stays out of scope; basis: the origin row's own rejected alternative (optimize only per measured hot spot, in later separate changes).
- assume Phase 1 confirmation is satisfied by the operator's standing pre-authorization for authoring runs, with the PLAN-PROMPTS entry prompt as the scope of record; basis: the authoring dispatch template's standing pre-authorization; the origin row declares its driving force correctness and this plan re-classifies it as the compound efficiency + correctness at plan level, the measurement serving both.

Decision points requiring a grill: writer placement: resolved by the origin row's delegation to authoring on evidence (docs/history/backlog/2026-10-13-script-runtime-cost-telemetry.md Fix shape, 2026-10-13); affected plan sections: Terms, Gist, Task 1.

## Standing constraints

- The telemetry writer never gates: no instrumented script's exit status, stdout contract, or stderr contract may depend on telemetry success, and no telemetry diagnostics may appear on a script's stdout contract channel (stderr-only diagnostics allowed, never interleaved with a declared stderr-evidence arm).

## Evaluation Criteria

**Quality dimensions:**
- correctness: each instrumented script appends exactly one schema-valid line per invocation with wall_ms at least 0 and the script basename as script; the file stays line-delimited valid JSON per line even under parallel appends.
- fail-openness: with the metrics home unwritable or missing, every instrumented script still exits with its pre-plan status and byte-identical contract output; proven by unit test for the library and by fixed-literal contract probes for the integrations.
- contract neutrality: no telemetry prose on any instrumented script's stdout contract channel; stderr-only diagnostics allowed and never interleaved with a declared stderr-evidence arm.
- observability: the friction-audit body names the monthly hot-spot readout (top ten scripts by total wall time) reading invocation-costs.jsonl from a bounded trailing window.

**Done when:**
- scripts/invocation_telemetry.py exists with a unit suite covering schema fields, fail-open behavior on an unwritable home, the absence-note case, the torn-line case, concurrent-append parseability, and the start-stamp precision witness, and the suite passes.
- the four integrations each append exactly one line per invocation without changing the script's observable contract; a scratch invocation of each script is probed and the file gains exactly one line per run, with the success, refusal, and usage-error exit paths each probed for the two python scripts.
- the friction-audit body carries the hot-spot readout sentence; scripts/machinery_registry.json carries the invocation-telemetry entry and the pre-registered removals row, and stays valid JSON.
- bash -n passes over the touched shell scripts.

**Ship when:** none; the change is repository-verifiable only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/invocation_telemetry.py` *(new)*
- `scripts/check_maintenance_pins.sh`
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py`
- `scripts/done_run.sh` (only inside `cmd_finalize`: exactly one start-stamp line at the function's entry and one unconditional telemetry block immediately before its final exit; all other regions are frozen; reject any review finding that touches them)
- `scripts/machinery_registry.json`

**Tests:**
- `scripts/test_invocation_telemetry.py` *(new)*

**Documentation:**
- `docs/maintenance/recurring-tasks/friction-audit.md` (only the cost-question rule paragraph gains the readout and retention sentences; the rest is frozen)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/hooks/`; reason: the hook-pair writer placement is rejected by this plan's Assumptions and no hook surface changes.
- `.ai-playbook/metrics/` and `docs/tmp/` data files; reason: untracked telemetry data homes, never committed.
- any optimization change to the measured scripts' logic; reason: optimization is decided per measured hot spot in later separate changes (origin row's rejected alternative).

## Validation Commands

Authoring-time rule 29 record: the no-em-dash scan, the public-hygiene scan, the readiness pre-round invocation, the rule 19 RED-today probes, and the rule 22 mechanical audit (each pinned span exactly once in its owning snippet, plus `bash -n` over this block) run over these bytes before round 1, and their outcomes append below as Recorded lines.

Recorded 2026-10-14 (authoring session sess_9f5841ba, over the v1 bytes on branch authoring/script-runtime-cost-telemetry): fix_plan_em_dashes.py 0 substitutions; em-dash touched scan exit 0; public-hygiene scan final line OUTCOME: pass; python3 scripts/plan_readiness.py --pre-round exit 0 OUTCOME: pass (the first run FAILed on three untagged Write-minimal-implementation items and three untagged Commit items, tagged in the same pass; the second run FAILed on the Primary class anchors grammar refusing the *(new)* suffix and descriptive-phrase anchors, normalized in the same pass with Task 3's block dropped per the doc/data-task precedent; the third run passed); rule 19 RED-today evidence, run before round 1 over the current tree: the content greps in the Validation Commands block all exit 1 today (the friction-audit body and scripts/machinery_registry.json lack every pinned span), python3 -m pytest -q scripts/test_invocation_telemetry.py exits 4 today under the validator PATH (file or directory not found), the readiness selftest is green, and bash -n over both touched shell scripts is green; rule 22 mechanical audit PASS over the v1 pin geometry with bash -n PASS.

Recorded 2026-10-14, r1 fold re-run (sess_9f5841ba, over the post-fold bytes): the r1 panel's 19 staged findings folded (the guard-coupling, timing-span, clock-mechanism, exit-path, atomicity, retention, lane-deferral, hermeticity, baseline-literal, persistent-coverage, tool-error-arm, stderr-neutrality, sunset-predicate, structural-registry-probe, sanity-band, citation-scoping, terms-alignment, outcome-scoping, and facts-parser folds; the five overflow one-liners folded beside them). Battery over the amended bytes: fix_plan_em_dashes.py 0 substitutions; em-dash touched exit 0; hygiene OUTCOME: pass; python3 scripts/plan_readiness.py --pre-round reached OUTCOME: pass after five same-pass envelope splits (the 698, 533, 535, and 577-byte over-cap criteria split in place, then the 4975-byte Task 1 aggregate resolved structurally by splitting the pins-suite bash items into their own Task 2 with tasks renumbered, then the renumbered Task 3's 948-byte closeout item and Task 4's 641-byte registry item split); rule 22 mechanical audit PASS over the new pin geometry with bash -n PASS; the registry structural probe (AssertionError: no entry) and the two friction-audit greps (exit 1) remain RED-today over the current tree. Round-start state for r2: the bytes at the fold commit carrying this preamble.

```bash
python3 -m pytest -q scripts/test_invocation_telemetry.py

python3 scripts/plan_readiness.py --selftest > /dev/null && echo "readiness selftest green"

grep -q "top ten scripts by total wall time" docs/maintenance/recurring-tasks/friction-audit.md || { echo "friction-audit body omits the invocation hot-spot readout"; exit 1; }

grep -q "invocation-costs.jsonl" docs/maintenance/recurring-tasks/friction-audit.md || { echo "friction-audit body omits the invocation telemetry home"; exit 1; }

python3 -c "
import json
r = json.load(open('scripts/machinery_registry.json'))
entries = [e for e in r['entries'] if 'invocation-telemetry' in e.get('id', '')]
removals = [x for x in r['removals'] if 'invocation-telemetry' in str(x.get('id', ''))]
assert entries, 'machinery registry omits the invocation telemetry entry'
assert removals, 'machinery registry omits the pre-registered removals row'
print('registry structural probe green')
"

python3 -c "import json; json.load(open('scripts/machinery_registry.json'))" && echo "registry JSON valid"

bash -n scripts/check_maintenance_pins.sh && bash -n scripts/done_run.sh && echo "shell syntax green"
```

### Task 1: the telemetry library and the two python self-timing integrations

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/invocation_telemetry.py` *(new)*
- `scripts/test_invocation_telemetry.py` *(new)*
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py`

Primary class anchors:
- `record_invocation` in `scripts/invocation_telemetry.py`
- `main` in `scripts/validate_review_staging.py`
- `main` in `scripts/plan_readiness.py`

- [x] `record_invocation(script, invocation_kind, wall_ms, lane_class=None, worker=None, home=None)` appends one line to invocation-costs.jsonl in the facts-resolved metrics home, creating the home on first write; the home parameter overrides resolution for tests; given a normal writable home, expects exit status 0/True [class: IMPLEMENTATION_REQUIRED]
- [x] the facts-resolved metrics home resolves through scripts/facts_paths.py (the repo's single TOML-fence parser, start_dir-injected, anchored at the repo root) with the .ai-playbook/metrics default applied by the library; given a normal writable home, expects the appended line's parsed JSON to carry script (basename), invocation_kind, wall_ms (number, at least 0), lane_class, worker, recorded_at (UTC ISO-8601) [class: IMPLEMENTATION_REQUIRED]
- [x] the append opens the target with O_APPEND and emits the complete line in one write() call (no read-modify-write, no temp-file rename), so parallel invocations leave every line parseable; given N concurrent record_invocation callers against one home, expects every appended line to parse as JSON [class: IMPLEMENTATION_REQUIRED]
- [x] given lane_class or worker unknown, expects the line to carry null for that field plus a note field naming the absence reason, mirroring the landing-cost family's absence-note precedent [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (fail-openness): given an unwritable metrics home (a target path under a regular file, immune to uid-0 permission-bit bypass), expects record_invocation to return False without raising [class: REPOSITORY_TEST]
- [x] contract baseline: the unit suite pins each probed invocation's fixed pre-integration contract literals (exact expected stdout line, stderr line, and exit code), and the instrumented scripts' exit status and stdout/stderr contract channels match those pinned literals with telemetry active [class: REPOSITORY_TEST]
- [x] given a metrics home whose invocation-costs.jsonl ends in a truncated or corrupt partial line lacking the trailing newline, expects the writer to prefix the separating newline into the same single write payload (last-byte check, no read-modify-write of the line bytes) and the file to gain exactly one new schema-valid line after the corrupt bytes; parseability witnesses skip empty lines [class: REPOSITORY_TEST]
- [x] the start stamp records sub-second-resolution values (fractional epoch) and two consecutive stamps differ, landed as a unit test [class: REPOSITORY_TEST]
- [x] `main` in `scripts/validate_review_staging.py` wraps its body in try/finally so the self-timed append fires on SystemExit paths too, spans one wall_ms across the full run, and appends the invocation_kind review-validation line on the success, refusal (nonzero exit), and usage-error exit paths with no stdout or stderr contract change against the pinned contract literals [class: IMPLEMENTATION_REQUIRED]
- [x] `main` in `scripts/plan_readiness.py` gets the same try/finally self-timing with invocation_kind readiness-gate across the success, refusal, and usage-error exit paths [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the suite and integration probes fail before implementation (no library file; no telemetry calls in the instrumented scripts) [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the unit suite passes; per python script the success, refusal (nonzero exit), and usage-error invocations each append exactly one line with the script's own contract channels unchanged against the pinned literals; every probed line's wall_ms is plausible (0 < wall_ms < 60000) [class: REPOSITORY_TEST]
- [x] the unit suite gains one subprocess-level integration test per python script this task instruments, in a tmp fixture (the test_done_sweep_gates_lib.py pattern: run each script in a cheap mode and assert exactly one appended line plus the unchanged contract literal, the success, refusal, and usage-error exit paths each covered), the one-line-per-invocation invariant keeps a persistent regression witness; Tasks 2 and 3 land their scripts' tests in the same suite [class: REPOSITORY_TEST]
- [x] Commit: `feat: add fail-open wall-time telemetry library and two python self-timing integrations` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the pins-suite bash integration and its repo-resolution arms

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `emit_outcome` in `scripts/check_maintenance_pins.sh`

- [x] `emit_outcome` in `scripts/check_maintenance_pins.sh` appends the invocation_kind pins-suite line on the script's exit path: the entry side writes a python3-derived start stamp (an epoch float to a temp stamp file created at script entry), the exit side runs one python3 call that reads the stamp, computes wall_ms, appends the line, and removes the stamp file; bash -n clean [class: IMPLEMENTATION_REQUIRED]
- [x] each bash integration's two interpreter spawns add roughly 20-60ms per invocation; the registry entry's admission note prices this measurement overhead beside the JSONL line cost [class: IMPLEMENTATION_REQUIRED]
- [x] the library resolves the repo top by walking up from the instrumented script's own installed location when the working directory has no repo, so the pins suite's not-inside-a-git-repo arm (which exits through emit_outcome before any cwd-resolvable home exists) still records one line when the script file lives inside a checkout [class: IMPLEMENTATION_REQUIRED]
- [x] a non-repo scratch probe (the pins script run from a tmp directory) asserts the prescribed outcome: a line when the script location resolves, or the named zero-line exception carrying its absence note [class: REPOSITORY_TEST]
- [x] Run → expect RED: a pins-suite probe shows no pins-suite line in the telemetry home before the change [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: two pins-suite runs produce differing sub-second wall values with the pins line's wall_ms at least 100 and under 60000, and the script's own OUTCOME: pass stdout stays byte-identical against the pinned literal [class: REPOSITORY_TEST]
- [x] shared-file note: scripts/invocation_telemetry.py and scripts/test_invocation_telemetry.py are declared at their creating Task 1 per the readiness gate's single creating-task annotation rule; this task's edits to them are recorded in the execution manifest's expanded task scope [class: REPOSITORY_TEST]
- [x] the unit suite gains the pins suite's subprocess-level integration test (a tmp fixture copy resolving through the location-based arm) asserting exactly one appended line plus the unchanged OUTCOME: pass literal [class: REPOSITORY_TEST]
- [x] Commit: `feat: self-time the pins suite into invocation telemetry with location-based repo resolution` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the closeout-battery line spanning the whole finalize

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/done_run.sh`

Primary class anchors:
- `cmd_finalize` in `scripts/done_run.sh`

- [x] `cmd_finalize` captures its start stamp at the function's entry (exactly one added line, in scope per the Review Scope carve-out); bash -n clean [class: IMPLEMENTATION_REQUIRED]
- [x] an unconditional telemetry block immediately before `cmd_finalize`'s final exit, outside the landing-cost guard (`no_landing_cost`/`landing_commit`/`RUN_MANIFEST`, skipped by real finalize arms including --no-landing-cost, no-ledger, and no-manifest runs), appends one invocation_kind closeout-battery line with the same facts-resolved metrics home resolution shape and fail-open semantics, silent on stdout (diagnostics stderr-only) [class: IMPLEMENTATION_REQUIRED]
- [x] placement witnesses: a no-ledger closeout and a --no-landing-cost closeout each record exactly one closeout-battery line; a landing-bearing closeout keeps the landing-cost line intact beside it [class: REPOSITORY_TEST]
- [x] named zero-line exception: the closeout's usage-error and early-refusal arms exit before the exit-side append and record no line, and the placement and safety witnesses land as subprocess-level tests in scripts/test_invocation_telemetry.py [class: REPOSITORY_TEST]
- [x] Safety witness: given a telemetry failure at the closeout site, expects the closeout flow to complete with the pinned pre-integration contract literals (exit status, export lines, stderr text) and the landing-cost record unaffected [class: REPOSITORY_TEST]
- [x] magnitude witness: the probed closeout's wall_ms spans the whole finalize (at least 100 for a real closeout invocation), not just the writer block [class: REPOSITORY_TEST]
- [x] Run → expect RED: a closeout flow probe shows no closeout-battery line before the change, including on the no-ledger arm [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the no-ledger and --no-landing-cost probes each append exactly one closeout-battery line, the landing-bearing probe keeps the landing-cost line intact, the appended line's wall_ms is at least 100, and the closeout's stdout carries no new telemetry prose [class: REPOSITORY_TEST]
- [x] Commit: `feat: record the closeout battery in invocation telemetry spanning the whole finalize` [class: IMPLEMENTATION_REQUIRED]

### Task 4: the monthly readout, the retention rule, and the machinery registry registration

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `docs/maintenance/recurring-tasks/friction-audit.md`
- `scripts/machinery_registry.json`

- [x] the friction-audit cost-question rule paragraph gains the invocation-telemetry readout: the monthly review reads invocation-costs.jsonl as a measured input from a bounded trailing window, names the top ten scripts by total wall time (invocation count times duration), and prunes invocation-costs.jsonl to that window in the same review pass, riding the same review cadence and the same writer-duty sunset enforcement shape the landing-cost rule already carries [class: IMPLEMENTATION_REQUIRED]
- [x] `machinery registry entries` in `scripts/machinery_registry.json` gains the invocation-telemetry writer entry (kind protocol, mirroring done-skill:landing-cost-record-writer's shape) carrying the origin row's admission fields: incident (the audit's Part 3 root cause 6 and Part 1 family 8) and expected catch frequency (every lane, continuous) [class: IMPLEMENTATION_REQUIRED]
- [x] the same entry prices the false-positive cost (one fail-open JSONL line per invocation plus each bash integration's two interpreter spawns as measurement overhead), names the retention rule owner (the monthly review's bounded-window read and prune), and points its sunset at the removals row [class: IMPLEMENTATION_REQUIRED]
- [x] `machinery registry entries` in `scripts/machinery_registry.json` removals array gains the pre-registered removals row for the writer: a 90-day idle-data review sunset (three consecutive monthly reviews with no review decision, optimization or removal or demotion, citing the invocation-costs.jsonl readout remove the writer duty), mirroring the budget gate's two-phase sunset discipline [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the friction-audit greps and the registry structural probe in the Validation Commands block fail before this task lands (both artifacts lack the pinned spans and rows) [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the friction-audit greps and the registry structural probe in the Validation Commands block pass and the registry parses as valid JSON [class: REPOSITORY_TEST]
- [x] Commit: `docs: register invocation telemetry with its monthly readout and pre-registered removals sunset` [class: IMPLEMENTATION_REQUIRED]
