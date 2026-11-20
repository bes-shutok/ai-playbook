# Plan: Measure the skill-gate consult path under load and land the measured disposition

Backlog origin: docs/history/backlog/2026-11-05-hook-timeout-recurrence-diagnostic.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-09-plan-review-hook-timeout-recurrence-diagnostic-p7daeac52-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3.0h total, largest task 1.5h
Executed: yes (090834f6ffc41f3584c2a87a463b0f00d370278b)
Authoring claim: 2026-11-05-hook-timeout-recurrence-diagnostic.md (session sess_be1eb068-ead4-400b-9040-ea660e097814)

## Terms

- harness: `scripts/profile_skill_gate_consult.py`, the tracked profiling script whose `ConsultProfiler` drives and times the consult path and whose analyze mode writes the analysis record.
- analysis record: the JSON file the harness's analyze mode writes beside the sample sets: per-class stage shares, the worse run, the regime verdict, the resolver-failed and resolver-timeout counts, the all-sample and clean-only loaded maxes, each stage's provenance (timing record or replicated probe), the emission-off p95, the dominance verdict or the no-dominant fields, and the stage-to-candidate mapping; Task 2 summarizes it into the task log, and Task 3 reads it.
- consult path: the work one gated Write/Edit consult performs: the adapter's subprocess chain plus the core's internal stages.
- adapter chain: the subprocesses one host hook invocation spawns: payload extraction, session-channel derivation, the core invocation, and the decision parsing.
- session-channel derivation: the `scripts/session_channel.py` subprocess that derives the session id for the core's marker keying.
- core: the agent-agnostic guard script `scripts/skill_gate.py`; it classifies the write target, consults the marker, and emits one allow/block decision.
- guard: the skill-gate as a whole (adapters, core, marker store, host pins) whose decision the consult produces.
- gated target: a write target inside the gated plans directory (the plans-dir suffix registry); only gated targets reach the git resolver and the marker check, so every measured consult targets a gated fixture file.
- fixture repo: the temporary git repository the harness constructs inside the sandbox (mirroring the core selftest's temp-repo recipe), holding the gated target file the measured consults classify.
- git resolver: the `git -C <start_dir> rev-parse --show-toplevel` subprocess inside `resolve_project_key` (scripts/facts_paths.py), bounded by `RESOLVER_GIT_TIMEOUT_S`.
- marker freshness window: the age bound `check_marker` applies to a skill-invoked marker.
- pin: a frozen configuration value or bound the plan must not change: the resolver bound (`RESOLVER_GIT_TIMEOUT_S = 5`) and the per-hook host timeout (at least 10 seconds per the README recipe, hand-synced at install time).
- pinned idiom: a frozen code-shape rule the doctor enforces: adapters parse stdin with python3 (never jq) and derive the session id via the literal session-channel subprocess invocation; a narrowing that crosses a pinned idiom is not a candidate.
- doctor: the core's `--doctor` live-install check (shape, path-liveness, idiom, and bound checks; it never byte-compares installed files).
- refusal class: one distinct deny/fail-open outcome family of the guard (block decisions, fail-open allows, unreadable-decision fallbacks).
- fail-open aperture: the catch arms that allow a write when the marker store or decision is unreadable, loudly logged.
- pins suites: the two selftest suites of record, run as `python3 scripts/skill_gate.py --selftest` and `python3 scripts/session_channel.py --selftest` (name filters via `--selftest#<name>`).
- timing emission: the measurement-only, environment-variable-gated timing record the core writes when the variable is set: one buffered JSON record per consult carrying the per-stage durations, the core pid, and the per-consult nonce the harness passes in a second variable for the core to echo, written once after the decision is emitted to the per-consult file path the variable names inside the worker's sandbox (never stdout, which carries the decision, nor stderr, which the adapter discards), touching no decision byte.
- isolated HOME: a temporary HOME directory passed to every spawned consult subprocess (the core selftest's isolated_home recipe), pre-populated with `.ai-playbook/scripts` symlinks resolving to the worktree's own scripts, so the real adapter chain runs against the measured bytes while its hooks log and marker store stay inside the sandbox; each concurrent worker gets its own isolated HOME.
- degraded-path sample: a sample lacking positive core-execution witness: no timing record with the expected nonce (emission-on runs only), no keying line in its sandbox hooks log, a keying value other than env-var or project-only (fail-open, error, or no-anchor; a no-anchor sample is labeled resolver-failed, or resolver-timeout when its resolver stage sits at the 5-second bound), an unreadable or empty decision (including adapter-level fail-opens where the core never ran), or a consult that exceeded the per-consult timeout (the 10-second host timeout; classified timed-out); recorded separately, never aggregated into the clean-path statistics. Consults within one worker run sequentially, and a log line belongs to the consult whose start and end bracket its append to that worker's own sandbox log.
- decision-path class: the allow-versus-block shape of one consult (block consults spawn one more interpreter than allow consults), forced per worker by seeding the worker sandbox's marker through the sandbox core's `--write-marker` (allow) or leaving it absent (block); per-stage shares compare only samples within one class, and dominance is evaluated per class.
- clean-sample floor: at least 20 clean samples per decision-path class per loaded repeat; a repeat under the floor fails loudly and is re-run at most twice; a repeat still under the floor records its degraded-label breakdown: when timed-out or resolver-timeout labels dominate the degraded share, it records the incident regime reached, no stage verdict is drawn, and the note arm lands that measurement; otherwise it is a harness incident, fixed and re-run. The emission-off spot-check is an end-to-end-only statistic exempt from the floor.
- keying branch: the session-id derivation branch one consult took (environment-derived, flag-supplied, or empty), recorded per sample; with the session variables cleared the harness expects the empty branch throughout.
- dominant stage: the stage that is dominant in both measured decision-path classes, where a stage is dominant in a class when its share (the stage's loaded p95 over the class's end-to-end loaded p95) is at least 40% and at least twice the runner-up's share (the next-largest stage share), measured on two loaded matched-control repeats each meeting the clean-sample floor, with the worse run governing; when no stage meets both bounds in both classes, no stage dominates.
- emission-off: a run with the timing variable unset (emission-on: set).
- incident regime: reached when the worse run's all-sample loaded end-to-end max (degraded samples included at their measured duration) reaches at least half the 10-second per-hook host timeout; when not reached, no stage verdict is drawn and the note arm lands in its regime-not-reached form.
- improvement margin: the narrowing keeps only when the post-narrowing worse-run loaded end-to-end p95 is at least 20% below the baseline worse run's; otherwise it is reverted and the note arm lands with both measurements.
- worse run: among the repeats counted for a class (re-runs replacing the repeats they redo), the one with the highest loaded end-to-end p95; it governs that class's shares and verdict.
- stage vocabulary: the closed list of stage names the harness emits (the core-internal stages from the timing record, the replicated adapter subprocess stages, and the residual), each mapped to at most one candidate: payload extraction, decision parse, and the residual to (a); session-channel derivation to (b) only when its share minus the interpreter probe's share still dominates, otherwise no-candidate (the invocation is a pinned idiom); the git resolver and every other stage implemented in `scripts/facts_paths.py` (keying log append, plans-dir resolution, project-key resolution) to no-candidate; every stage implemented in `scripts/skill_gate.py` itself to (c).
- interpreter probe: a timed bare `python3 -c pass` run inside the worker sandbox alongside each consult, emitted as its own stage.
- worker ceiling: the loaded run's worker count, at or under the host's physical core count minus one, its derivation recorded in the run context.
- verbatim argv replication: timing each adapter subprocess stage by re-running its exact argv as a separate timed probe, the argv re-derived from the adapter source at harness start with a loud failure on a mismatch against the harness's pinned replica.
- run context: repeat index, worker count and its ceiling rationale, iteration count, host summary, ambient load indicator before and after the run, and keying-branch uniformity.
- durable record line: the one disposition line appended to the README outcomes section, self-sufficient: per-class loaded p95 and max, the dominant stage and share (or, with no dominant stage, per-class top stage, its share, the runner-up's share, and the failing bound), the emission-off p95, the run context, and the harness command that regenerates the samples (its output flag shown as a placeholder); it cites no docs/tmp path.
- digest comparison: each installed symlink's resolved target path checked live and inside the primary checkout, and its sha256 checked against the execution branch's final bytes.
- candidate narrowing: a pre-registered, bounded, semantics-preserving per-stage fix on a stage's own surface (see Task 3's list); the narrow arm fires only when the dominant stage appears on this list.
- narrowed path: a per-stage latency reduction that leaves the guard's decision semantics, refusal classes, and pins unchanged.
- accepted-cost note: the note arm's form of the durable record line in the hook README's "Build-time verifications (outcomes)" section, adding the witnessed frequency taken from the origin row's incident count; the regime-not-reached form carries that frequency as historical context and claims no accepted cost.
- retained raw samples: the per-invocation latency records the harness writes for every measured run, kept on disk for re-analysis; disposable run evidence, unlike the durable record line.
- matched control: a measurement repeat whose load configuration, keying branch, and target class are held identical so runs compare; each loaded repeat covers both decision-path classes with per-class attribution.
- ambient load indicator: a host load reading (for example load average) recorded alongside each sample set.

## Why

Under parallel-session load the skill-gate hook exceeds its host timeout budget and the degraded consult costs blocked edits, failed tool calls, and retry turns (six witnessed timeouts in one afternoon, all without a record of what the core was doing when the budget expired). One measurement pass identifies where the budget goes and lands the measured disposition, so the cost is either narrowed or priced instead of recurring unexplained.

## Gist & Examples

TLDR: a profiling harness times the consult path per stage, idle and under matched parallel load in a populated sandbox HOME against a gated fixture target, and the measured evidence decides between a bounded narrowing and the accepted-cost record, for efficiency.

Before: the host hooks time out under load with no per-stage record; the pins are correct, so nothing is misconfigured, and the residual question is where the host timeout budget goes.

After: `scripts/profile_skill_gate_consult.py` drives the real adapter chain end to end against a gated fixture target, with the core emitting opt-in per-stage timing records, each adapter subprocess stage timed by verbatim argv replication, both decision-path classes forced by marker seeding, degraded paths classified by positive core-execution witness, and raw samples retained under idle and loaded matched controls (the loaded control run twice, the incident regime checked); the disposition record lands in the README outcomes section on either arm, and a dominant stage fires its pre-registered narrowing. Decision semantics, refusal classes, and pins are unchanged either way.

## Outcome

The recurring hook timeout is either measurably narrowed or recorded as accepted cost, and every disposition cites retained samples and a durable record rather than anecdote.

- The consult path has a re-runnable per-stage measurement harness, so future timeout recurrences compare against a baseline instead of starting from silence.
- The landed disposition (narrowing or record) names the measured dominant stage and its loaded p95 share (or the no-dominant fields, or the regime-not-reached measurement), witnessed by the retained samples and the durable record line with its run context.
- The narrowing reaches live sessions only through the normal landing (the installed chain symlinks to the primary checkout); the completion pass names the digest comparison that verifies deployed bytes after that landing.
- The guard's decision semantics, refusal classes, marker freshness window, and pins are unchanged; both pins suites stay green.

Gate delta: none. The harness and the core's timing emission are measurement tooling, not a gate, validator, lock, ledger, or required ceremony; the narrowing arm changes no decision semantics, refusal class, or pin; the record arm is prose. No refusal, check, or field is removed.

## Assumptions

- assume the harness measures the real chain (the real adapter driving real subprocesses against the real git resolver) rather than stage mocks, supplemented by the core's opt-in timing emission for the core-internal stages and by verbatim argv replication for the adapter's outer stages; basis: the defect is load-contingent, so mocks cannot witness it, and the internal stages emit no timings today (verified).
- assume the measured chain runs under isolated, populated sandbox HOMEs (one per worker) so the shared hooks log, live markers, and guard state stay untouched; basis: the core's own selftest isolates HOME for exactly this reason, the adapter hardcodes HOME-pinned script paths (so the sandbox must be populated for the chain to run at all), and the subprocess CLI exposes no runtime-dir flag.
- assume load injection is bounded synthetic concurrency (N workers running matched gated consults concurrently for M iterations, N at or under a declared ceiling), run on a verified-quiet host, not a real-session swarm; basis: controllable, repeatable, safe on the shared machine, and the measurement must not induce the incident in production sessions.
- assume raw samples land under docs/tmp via the harness output flag (gitignored run evidence), while the durable record line is the retained artifact landing in the README outcomes section on either arm; basis: samples are re-analysis input, the record is what future recurrence investigations read.
- assume the pins suites of record are the core selftest and the session-channel selftest; basis: the core never imports session_channel, so the core suite cannot exercise it, and both scripts carry selftest modes (verified).
- assume the narrowing arm's fix lives in the measured stage's own surface, never across a pinned idiom: the session-channel subprocess invocation is a pinned idiom, so a dominant session-channel stage narrows only inside `scripts/session_channel.py` internals; the unpinned adapter surfaces are the payload-extraction and decision-parse subprocesses.

- assume the regime-not-reached form deliberately extends the origin row's two dispositions with a third; basis: a synthetic run that never approaches the host timeout cannot price or narrow the incident, and its follow-up row carries the origin acceptance bar forward.

Decision points requiring a grill: none remain.

## Standing constraints

- Decision semantics unchanged: the allow/block contract, the deny message, the fail-open aperture, the marker freshness window, and the pins (the resolver bound and the per-hook host timeout of at least 10 seconds per the README recipe) are frozen for every task.
- The narrowing arm edits only the measured stage's own surface and never widens or narrows what the gate consults; a narrowing that crosses a pinned idiom is not a candidate.

## Evaluation Criteria

**Quality dimensions:**
- measurement validity: the harness reports per-stage and end-to-end latencies with retained raw samples, over a gated target, under one idle and two loaded matched-control repeats each covering both decision-path classes at the clean-sample floor, with degraded-path samples classified by positive core-execution witness, keying-branch uniformity and the run context recorded, the incident regime checked, and a block-class emission-off spot-check beside the emission-on p95.
- disposition evidence: the landed arm cites the loaded p95 and the dominant stage's share (or the no-dominant fields, or the regime-not-reached measurement) against the pinned per-class rule (the narrow arm also against the improvement margin); the durable record line lands in the README outcomes section on either arm; the narrowing arm's diff is confined to the measured stage's surface and respects the pinned idioms.
- guard preservation: decision semantics, refusal classes, and pins unchanged; all three Validation Commands green.

**Done when:**
- the harness and timing emission exist with their retained-sample output, the measurement run has produced the idle and loaded sample sets under the populated sandbox, and exactly one disposition arm has landed with its evidence recorded in the task log and the durable record line in the README outcomes section.

**Ship when:**
- the narrowing has landed to the primary checkout (the installed symlinks point there, so live behavior changes only at that landing), the recorded post-landing digest comparison has verified the deployed bytes, and the next parallel-session window produces no unexplained hook timeouts; or the record's accepted frequency is what recurs. (Operations condition; no checklist item.)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/profile_skill_gate_consult.py` (Task 1) *(new)*
- `scripts/skill_gate.py` (Task 1)
- `scripts/session_channel.py` (Task 3)
- `agents/hooks/skill-gate/claude.sh` (Task 3)

**Tests:**
- `scripts/test_profile_skill_gate_consult.py` (Task 1) *(new)*

**Documentation:**
- `agents/hooks/skill-gate/README.md` (Task 3)
- `docs/history/backlog/2026-11-09-hook-timeout-higher-load-remeasure.md` (Task 3) *(new, regime-not-reached form only)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. Task 3 executes exactly one arm; findings on the not-taken arm's files are out of scope unless causally related to the taken arm.

**Out of scope; reject unless plan-related:**
- `agents/hooks/skill-gate/README.md` decision-semantics sections ("Host hook timeout", wiring recipes); reason: the pins are correct today and frozen by the entry's scope line; only the outcomes section is an edit target, on either arm's record line.
- `scripts/facts_paths.py` `RESOLVER_GIT_TIMEOUT_S`; reason: the resolver bound is a frozen pin; the harness measures around it, never changes it.
- The scheduler-state, clocked-order, and done-run families; reason: unrelated guard families.

## Validation Commands

```bash
python3 scripts/skill_gate.py --selftest
python3 scripts/session_channel.py --selftest
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_profile_skill_gate_consult.py -q
```

### Task 1: The timing emission and the per-stage measurement harness

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/skill_gate.py`
- `scripts/profile_skill_gate_consult.py` *(new)*
- `scripts/test_profile_skill_gate_consult.py` *(new)*

Primary class anchors:
- `ConsultProfiler` in `scripts/profile_skill_gate_consult.py`

- [x] The core emits opt-in timing records: given a core invocation over the gated target with the timing variable naming a sandbox path, expects the timing record written there once after the decision, nothing of the record on stdout or stderr. [class: IMPLEMENTATION_REQUIRED]
- [x] Through-adapter witness: given the real adapter driving the sandbox core with the timing variable set, expects the record present at its path echoing the nonce the harness passed. [class: REPOSITORY_TEST]
- [x] Decision-byte identity witness: given the suite's fixed fixtures, expects the core's decision stdout and exit code captured with the timing variable unset and set to be byte-identical for allow and block shapes, with the timing record present only in the timed run. [class: REPOSITORY_TEST]
- [x] `ConsultProfiler` measures one gated consult end to end and per stage: given the populated sandbox, expects one retained sample carrying the stage vocabulary's latencies, the end-to-end latency, decision outcome, keying branch, project key, and decision-path class. [class: IMPLEMENTATION_REQUIRED]
- [x] Sandbox startup self-check: given the harness start, expects a loud failure when the sandbox core path is not a symlink into the worktree, the fixture repo lacks the gated target or fails `git rev-parse`, or the adapter's stage argv no longer matches the pinned replica. [class: IMPLEMENTATION_REQUIRED]
- [x] Self-check abort arms: given one fixture per arm (plain-file sandbox core, no gated target, non-git fixture, doctored adapter copy), expects each loud abort. [class: REPOSITORY_TEST]
- [x] Matched-control load mode: given a worker count at or under its declared ceiling and an iteration count, expects each worker running the matched consult chain under its own isolated HOME, each consult spawned in its own session and bounded by the per-consult timeout (killing its own process group), and per-worker samples and failure counts retained. [class: IMPLEMENTATION_REQUIRED]
- [x] Class forcing: given the run start, expects allow-class worker sandboxes seeded through the sandbox core's `--write-marker` and block-class ones left unseeded, and a loud abort when a pre-run consult per class contradicts its class or a repeat misses the floor. [class: IMPLEMENTATION_REQUIRED]
- [x] Degraded-path classification: given a sample, expects it classified clean only with positive core-execution witness per the Terms rule, every other sample classified degraded with its label, reported separately, and excluded from clean-path statistics. [class: IMPLEMENTATION_REQUIRED]
- [x] Classifier negative arms: given one fixture per Terms degraded disjunct (including fail-open and no-anchor lines), expects each classified degraded. [class: REPOSITORY_TEST]
- [x] Harness aggregation witnesses: given a mixed clean and degraded fixture, expects count, p50, p95, max, and per-class stage shares over clean samples only, with degraded counts including the rest. [class: REPOSITORY_TEST]
- [x] Dominance helper witnesses: given fixed share fixtures, expects the suite-pinned helper to apply the Terms rule (share, runner-up, floor, worse run) and to return no-dominant for 40%-but-not-twice, twice-but-under-40%, and dominant-in-one-class-only cases. [class: REPOSITORY_TEST]
- [x] Suite and run hermeticity: given the suite and the harness, expects HOME pinned per subprocess (in-process calls patch HOME per the isolated_home recipe), session and GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR variables cleared, PYTHONDONTWRITEBYTECODE set, explicit target and cwd, and project keys equal to the fixture repo's. [class: REPOSITORY_TEST]
- [x] Run → expect RED: the behavior's failing check (tests, fixtures, and commands are selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: consult-path timing emission and per-stage profiling harness` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The measurement run

Context surface: the plan's Terms, Task 1's harness, and `## Standing constraints`.

Files:
- `scripts/profile_skill_gate_consult.py`

Primary class anchors:
- `ConsultProfiler` in `scripts/profile_skill_gate_consult.py`

- [x] Quiet-host gate: given the loaded run, expects the real hooks log and process table checked before it, the worker ceiling enforced, an abort-and-report on a failed check, and a live line inside the run window stopping the load, invalidating the repeat, and re-running the gate before any re-run (the residual check-to-act window recorded as accepted). [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (sandbox hygiene): given the loaded run, expects no writes outside the declared output roots and sandbox HOMEs: no live marker keyed to the fixture repo's project key, and each sandbox log holding one keying line per consult. [class: REPOSITORY_TEST]
- [x] Idle and loaded matched controls are run and retained: given one idle control run and two loaded control repeats at the declared worker count, expects three or more sample sets on disk under docs/tmp, each loaded repeat covering both classes at the clean-sample floor and carrying its run context, with the summary lines recorded in the task log. [class: REPOSITORY_TEST]
- [x] Analysis record produced: given the retained sample sets, expects the harness's analyze mode to write the analysis record with its Terms fields and its summary in the task log. [class: REPOSITORY_TEST]
- [x] Incident-regime check: given the worse loaded run, expects the analysis record to state whether the incident regime was reached, and, when not, no stage verdict drawn. [class: REPOSITORY_TEST]
- [x] The dominant stage is decided by the pinned per-class rule: given the loaded summaries in the incident regime, expects the analysis record to apply the dominance helper per class, name a stage dominant only when it dominates in both classes, record the no-dominant fields otherwise, and map every stage through the stage vocabulary. [class: REPOSITORY_TEST]
- [x] Emission-off spot-check: given the loaded control, expects one block-class emission-off run whose end-to-end p95 is recorded beside the block-class emission-on p95 in the analysis record. [class: REPOSITORY_TEST]
- [x] Pre-run check: the sample-set paths are absent or stale before the run and present with the declared summary lines after it. [class: REPOSITORY_TEST]
- [x] Commit: `feat: consult-path measurement run with retained samples` (carries any harness run-mode adjustments; skipped when none exist) [class: IMPLEMENTATION_REQUIRED]

### Task 3: The measured disposition

Context surface: the plan's Terms, Task 2's analysis record, and `## Standing constraints`. This task's pre-registered candidate narrowing list, which the narrow arm requires the dominant stage to appear on: (a) collapsing the adapter's payload-extraction and decision-parse subprocesses in `agents/hooks/skill-gate/claude.sh` into one interpreter that spawns the core subprocess, keeping the literal session-channel line, the core stderr discard, and the nonzero-exit fail-open; (b) a bounded per-stage optimization inside `scripts/session_channel.py` internals; (c) a bounded optimization of a core stage implemented in `scripts/skill_gate.py` itself, outside every decision byte. The stage vocabulary's mapping decides which candidate a stage owns.

Files:
- `scripts/skill_gate.py`
- `scripts/session_channel.py`
- `agents/hooks/skill-gate/claude.sh`
- `agents/hooks/skill-gate/README.md`
- `scripts/profile_skill_gate_consult.py`
- `scripts/test_profile_skill_gate_consult.py`
- `docs/history/backlog/2026-11-09-hook-timeout-higher-load-remeasure.md` *(new, regime-not-reached form only)*

Primary class anchors:
- `ConsultProfiler` in `scripts/profile_skill_gate_consult.py`

- [x] Narrow arm (executes only when the dominant stage appears in this task's candidate list): given the dominant stage on that list, expects the narrowing implemented on that stage's own surface, decision semantics, refusal classes, and pins byte-unchanged, and both pins suites green. [class: IMPLEMENTATION_REQUIRED]
- [x] Narrow-arm contract witness (only when `agents/hooks/skill-gate/claude.sh` carries a diff): given the modified adapter, expects a contract smoke (stub core swapped in) to pass: allow exits 0; block exits 2 with the exact deny text; empty-SID alarm on stderr; an absolute target with the cwd absent reaches the core with its parent as cwd; a core exiting nonzero with garbage stdout yields exit 0 allow, core stderr suppressed. [class: REPOSITORY_TEST]
- [x] Narrow-arm wiring witness (same condition): given the modified adapter, expects the stub core's captured argv to carry `--session-id <value>` when the session variable is set and to omit it when unset, and the doctor's idiom check to pass over the adapter. [class: REPOSITORY_TEST]
- [x] Narrow-arm efficacy witness: given the narrowing, expects the matched controls re-run on the narrowed bytes under the same sandbox, the post-narrowing numbers recorded beside the baseline, any other stage's share regression flagged, and the narrowing reverted for the note arm when the improvement margin is missed. [class: REPOSITORY_TEST]
- [x] Note arm (executes when no stage dominates, the dominant stage maps to no-candidate, the regime was not reached, the floor fallback fired, or the margin was missed): given Task 2's analysis, expects the accepted-cost record in the README outcomes section (the regime-not-reached form claiming no accepted cost), with no production bytes changed. [class: IMPLEMENTATION_REQUIRED]
- [x] Regime follow-up: given the regime-not-reached form, expects the row `docs/history/backlog/2026-11-09-hook-timeout-higher-load-remeasure.md` filed for a higher-load re-measurement, citing the record line. [class: IMPLEMENTATION_REQUIRED]
- [x] Exactly one arm lands: given Task 2's evidence, expects the task log to record which arm fired and the rule comparison (per-class threshold bounds and candidate-list membership) that decided it, and the other arm's production files to carry no diff. [class: REPOSITORY_TEST]
- [x] Durable record line: given either arm, expects the self-sufficient durable record line (post-narrowing numbers beside the baseline on the narrow arm) present in the README outcomes section, citing no docs/tmp path. [class: REPOSITORY_TEST]
- [x] Deployment coupling recorded: given the taken arm, expects the task log to record that the installed chain (the installed runtime-scripts symlinks and the host hook script) resolves to the primary checkout, so live behavior changes only after the execution branch lands there, and the replacement-window fail-open transient is noted as accepted. [class: REPOSITORY_TEST]
- [x] Deployed-bytes follow-up named: given the landing, expects the completion pass to name the post-landing digest comparison (each installed symlink target's checksum against the landed file's, the doctor remaining the shape and idiom witness) with its owner recorded. [class: REPOSITORY_TEST]
- [x] Arm verification: on either arm all three Validation Commands are green on the final bytes (plus the contract smoke when the adapter carries a diff); on the note arm the record is present and a worktree diff shows no production bytes changed. [class: REPOSITORY_TEST]
- [x] Commit: `feat: land the measured consult-path disposition` [class: IMPLEMENTATION_REQUIRED]
