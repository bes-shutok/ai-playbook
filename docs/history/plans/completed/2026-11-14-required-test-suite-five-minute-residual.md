# Plan: Required test suite residual: cancellation evidence, descendant containment, setup cost, decomposition

Backlog origin: docs/history/backlog/2026-11-09-required-test-suite-five-minute-residual.md
Driving force: efficiency + code-quality (ranked primary + secondary)
Plan review record: the staging series .ai-playbook/reviews/2026-11-14-plan-review-required-test-suite-five-minute-residual-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 3.5h total, largest task 1.5h
Executed: yes (95b3d15d936919b5062e31c7c04343371ecae920)
Authoring claim: 2026-11-09-required-test-suite-five-minute-residual.md (session sess_29b133bf-e7d6-4a20-b294-23aa8b15d1a9)

## Terms

- `RequiredTestSuiteRunner`: the coordinator class in `scripts/run_required_test_suite.py` (origin records ~940 lines and 28 methods at authoring time; Task 4 re-derives current counts) that owns discovery, scheduling, worker lifecycle, accounting, and reporting for the required suite.
- Duration map: `docs/history/feature-notes/2026-11-10-test-done-run-wrapper-case-durations.csv`, the 145-row per-test elapsed-time record from the unbounded eight-worker diagnostic (origin-recorded best current evidence).
- Detached descendant: a child process a worker launches in its own process group or session, so it survives outside the worker's own group.
- Reparented descendant: a detached grandchild whose intermediate parent exited before the cleanup snapshot, leaving it parented to the system initializer and invisible to a parent-chain walk.
- Safe-first ordering: the runner's scheduling order that gives queued serial (unknown-safety) scripts priority over safe readers; preserved unchanged by this plan.
- Focused-never-full: this repository's suite policy (`test_suite_policy` in `.ai-playbook/facts.md`); validation uses focused suites, never a whole-inventory acceptance run.
- Mise cancellation probe: a short deliberate run of the `test:required` mise task with appended timeout overrides so cancellation fires in seconds; it is evidence capture, not an acceptance run.

## Why

The operator's 2026-11-11 disposition retired the fixed runtime acceptance gates and closed the 2026-11-08 optimization plan's acceptance work, but four recorded questions stayed open: what actually happens when cancellation arrives through mise, whether cleanup contains a grandchild that reparents before the snapshot, whether the slowest wrapper tests re-pay avoidable setup, and whether the runner coordinator should decompose. Leaving them open without recorded evidence means the next incident re-derives each answer by trial. This plan turns each question into recorded evidence plus an explicit disposition, under the no-new-gates bar the origin pins.

## Gist & Examples

TLDR: each of the four recorded residual questions gets durable evidence and an explicit disposition (close the descendant-attribution gap or document its boundary, reduce slow-case setup where safe, assess the coordinator split), so the retired-gates disposition leaves no silent unknowns, at the efficiency force's direction.

Before (today): an operator interrupts a hanging `mise run test:required` and nobody can say from the repository what signal the runner received, whether captured process groups were reaped, whether the JSON report completed, or what exit code propagated; a worker that launches a grandchild in a new session and exits before cleanup leaves that grandchild unattributed (`_worker_process_groups` walks live parent chains and finds nothing); the slowest wrapper classes (`DoneRunRollingLogRefBoundCommitTest` at 12.4 seconds, `DoneRunDirtCorrectionSetTest` at 11.5 seconds per the duration map) re-pay per-test Git and process setup; and the decomposition question about `RequiredTestSuiteRunner` sits unanswered in the origin row.

After (this plan): the same interruption has a recorded answer in `docs/history/feature-notes/` naming the signal path, cleanup evidence, report state, and exit status, with the supported cancellation boundary stated; the descendant question carries either a closing mechanism with a canary in the focused runner contract suite or a documented supported child-lifecycle boundary with the repro transcript; the named slow classes run with setup cost reduced where a safe reduction was proven, every one of the wrapper test identities preserved (150 after the 2026-11-19 re-pin); and the decomposition question has a recorded assessment with a disposition.

Edge cases: a probe run whose timeout override does not ride through mise (the probe's own precondition check catches this and reports the deployment gap instead of interpreting results); a containment mechanism that only works on macOS is rejected by the pre-registered portability criterion and routes to the documented-boundary branch; a slow class whose setup cannot be reduced without changing what a test verifies stays unreduced and the record says why.

## Outcome

The required-suite runner's four residual questions are answered with recorded evidence and explicit dispositions, so future cancellations, cleanup gaps, slow-case changes, and refactors start from the record instead of re-derivation.

- Interrupting the suite through mise has a recorded signal, cleanup, report, and exit-status answer, with the supported cancellation boundary stated in `docs/history/feature-notes/`.
- A grandchild that reparents before the cleanup snapshot is either contained by a tested mechanism or covered by a documented supported child-lifecycle boundary with its repro transcript.
- The slowest wrapper classes carry measured setup-cost reduction where proven safe, with the full wrapper ID inventory preserved (150 IDs after the 2026-11-19 re-pin) and verified against the re-pinned expected set (duration map set plus the five post-CSV log_expected IDs).
- The `RequiredTestSuiteRunner` decomposition candidate has a recorded assessment and disposition with coupling evidence.

Gate delta: none (no refusal class, hard gate, fence, protocol layer, or schema field is added or removed; the worker cap and scheduling order are unchanged; all four tasks produce evidence, optional mechanism code, or assessments).

Follow-up disposition rule: a task-2 or task-3 candidate that cannot land inside its task (a containment mechanism needing upstream work, a setup reduction blocked by a behavior-signal conflict) is recorded as a rejected disposition inside that task's feature-notes record with its ruling evidence, or promoted to a durable backlog row with a ready-to-dispatch prompt when the candidate is still viable; task-4's decomposition recommendation, when affirmative, routes as that backlog row rather than expanding this plan.

## Assumptions

- assume investigation evidence lands under `docs/history/feature-notes/`; basis: the origin row and the backlog entry cite feature-notes records as the evidence home.
- assume the mise task's configured 60/270/295-second values remain runner safety bounds, not acceptance criteria; basis: origin operator disposition paragraph (2026-11-11).
- assume the duration map is the profiling input of record for slow-case work; basis: the origin names it the best current evidence.
- assume the 2026-11-08 plan remains in the plans root under its user-authorized partial state and this plan composes beside it without reopening it; basis: entry Stage-1 roster note and origin disposition.
- assume `ps`-based parent-chain attribution is the containment mechanism under evaluation; basis: `_worker_process_groups` and `_cleanup_worker_descendants` in `scripts/run_required_test_suite.py` read at authoring (2026-11-14).

Decision points requiring a grill: close-gap-vs-document-boundary: evidence-decided per the pre-registered criteria in Task 2 (close only when a mechanism verifies portable for macOS and CI-representable environments and keeps the focused runner contract suite green; otherwise document the boundary); source: origin follow-up lifecycle investigation section, receipt recorded 2026-11-14, affects Task 2; setup-reduction-warranted-now: this residual plan is the warranted future change the entry names; source: entry scope arm 2 and origin disposition, receipt recorded 2026-11-14, affects Task 3; assess-only-decomposition: the assessment produces a disposition, no refactor in this plan; source: origin maintainability follow-up (do not refactor merely to satisfy the finding), receipt recorded 2026-11-14, affects Task 4.

## Standing constraints

- Focused suites only: validation never runs a whole-inventory acceptance pass; the operator disposition retired those gates and bars acceptance runs for this residual (the mise cancellation probe is evidence capture with second-scale overrides, not an acceptance run).
- No new machinery: no blocking gate, scheduler lock, persistent tool wrapper, or state-schema byte; any such need routes through the repository's machinery admission protocol as a separate witnessed proposal, never into this plan.
- Eight-worker cap retained: the runner default and the mise task keep `--workers 8` unless new measured evidence plus explicit operator direction support a different cap.
- Evidence records are durable: each record under `docs/history/feature-notes/` names exact commands, observed outputs, and SHA-256 digests of produced artifacts, so the next session can re-derive without re-running.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the focused runner contract suite (`scripts/test_required_test_suite.py`) passes after every task that touches runner or test code, and the wrapper ID set collected by the runner's own collection matches the re-pinned expected set exactly (the duration map's 145-ID set plus the five post-CSV log_expected IDs, 150 total; the CSV itself stays 145 rows, never edited).
- evidence quality: each feature-notes record names its exact commands, observed outcomes, artifact digests, and an explicit disposition; a reader can re-derive each conclusion from the record alone.
- maintainability: the Task 4 assessment cites measured coupling evidence (responsibility inventory, shared state) rather than line counts alone.
- restraint: the landing range carries no machinery, lock, gate, or state-schema bytes; `mise.toml` worker configuration is unchanged.

**Done when:**
- `docs/history/feature-notes/2026-11-14-required-suite-mise-cancellation-evidence.md` exists with the probe evidence, the supported cancellation boundary or a defect finding, and its disposition.
- `docs/history/feature-notes/2026-11-14-descendant-containment-evidence.md` exists with the repro transcripts, the comparison of containment options, and the close-or-document disposition per Task 2's criteria.
- `docs/history/feature-notes/2026-11-14-wrapper-setup-cost-reduction.md` exists with the per-class setup profile, the reductions landed (or the recorded reason none were safe), and before/after per-class measurements.
- `docs/history/feature-notes/2026-11-14-runner-coordination-decomposition-assessment.md` exists with the responsibility inventory, coupling evidence, and the disposition.
- the Validation Commands block passes per its own fail-closed recipe at the final boundary.

**Ship when:** none (repository-internal evidence, code, and docs; no deploy surface).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/run_required_test_suite.py` (Task 2) *(partially in scope: the close-gap branch may change only the descendant snapshot/attribution and cleanup path; all other methods are frozen; reject any review finding that touches them; Task 4 reads this file as its assessment target and changes nothing)*
- `mise.toml` (review-only; Task 1's probe precondition reads it, no edits)

**Tests:**
- `scripts/test_required_test_suite.py` (Task 2; close-gap branch adds the canary)
- `scripts/test_done_run_wrapper.py` (Task 3) *(partially in scope: setup reduction in the six named classes only; all other classes and the module's collection surface are frozen; reject any review finding that touches them)*

**Docs:**
- `docs/history/feature-notes/2026-11-14-required-suite-mise-cancellation-evidence.md` (Task 1) *(new)*
- `docs/history/feature-notes/2026-11-14-descendant-containment-evidence.md` (Task 2) *(new)*
- `docs/history/feature-notes/2026-11-14-wrapper-setup-cost-reduction.md` (Task 3) *(new)*
- `docs/history/feature-notes/2026-11-14-runner-coordination-decomposition-assessment.md` (Task 4) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/machinery_registry.json`; reason: the standing constraints bar machinery bytes and the gate delta is none.
- Any other suite under `scripts/` (for example `test_done_sweep_gates_lib.py`, `test_release_skill_selftest.py`); reason: Task 3 scopes setup reduction to the six named wrapper classes; other slow suites are named in the origin as future evidence, not this plan's scope.
- `docs/maintenance/` skill and directive text; reason: this plan changes runner code, wrapper tests, and evidence records only.

## Validation Commands

Validation preamble (authoring-time record): the wrapper ID-set derivation was executed at authoring (2026-11-14, primary checkout, wrapper source SHA-256 prefix ea90816c8883a209): the runner's own collection (`_load_unittest_tests` plus `_flatten`) yields exactly 145 IDs and `cmp` against the duration map's ID column passes byte-for-byte. The ID count 145 is pinned to that derivation; if a future run mismatches, re-derive through this same command and treat the difference as source drift to re-pin through a plan correction, never by editing the CSV. Correction (2026-11-19, execution session re-derivation in the run worktree, same command, wrapper source SHA-256 2a25931951fdbb6d4d2e12559bee9003faecebddf7053fcbdb6f5fbc3329d7d3): the live collection yields exactly 150 IDs; the delta is exactly the five post-CSV `log_expected` DoneRunRollingLogRefBoundCommitTest entries landed after the duration map was recorded (evidence: docs/history/feature-notes/2026-11-14-wrapper-setup-cost-reduction.md, ID-set section); the pinned count is re-pinned to 150 and the check below updated to match. Evidence-record checks below are vacuous at authoring (the records do not exist yet); the first failing gate at authoring execution is expected to be the Task 1 record check, and every earlier pass is vacuous by construction.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
mkdir -p docs/tmp
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

# 1. Focused runner contract suite stays green (includes the Task 2 canary when present).
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_required_test_suite.py -q > docs/tmp/rts-contract-validation.txt 2>&1 || { tail -5 docs/tmp/rts-contract-validation.txt >&2; fail "runner contract suite"; }
tail -1 docs/tmp/rts-contract-validation.txt | grep -q "passed" || fail "runner contract summary line"

# 2. Wrapper ID-set preservation: the runner's own collection still matches the re-pinned expected set (150 = CSV set + the five post-CSV log_expected IDs; see preamble correction) exactly.
python3 -c "import sys; sys.path.insert(0,'scripts'); import run_required_test_suite as r; from pathlib import Path; ids = sorted(t.id() for t in r._flatten(r._load_unittest_tests(Path('scripts/test_done_run_wrapper.py')))); open('docs/tmp/rts-live-wrapper-ids.txt','w').write(chr(10).join(ids)+chr(10)); print(len(ids))" > docs/tmp/rts-live-wrapper-count.txt || fail "wrapper collection run"
grep -qx "150" docs/tmp/rts-live-wrapper-count.txt || fail "wrapper live ID count is not 150"
sort docs/tmp/rts-live-wrapper-ids.txt > docs/tmp/rts-live-wrapper-ids-sorted.txt
# 2026-11-19 re-pin correction: the live set must equal the CSV set plus exactly the five post-CSV log_expected additions recorded in the preamble (the CSV is never edited).
tail -n +2 docs/history/feature-notes/2026-11-10-test-done-run-wrapper-case-durations.csv | cut -d, -f1 | sort > docs/tmp/rts-csv-wrapper-ids.txt
cat docs/tmp/rts-csv-wrapper-ids.txt > docs/tmp/rts-expected-wrapper-ids.txt
printf '%s\n' test_done_run_wrapper.DoneRunRollingLogRefBoundCommitTest.test_log_expected_advisory_binds_to_staged_blob_not_commit_time_worktree_bytes test_done_run_wrapper.DoneRunRollingLogRefBoundCommitTest.test_log_expected_deletion_shape_advises_and_lands test_done_run_wrapper.DoneRunRollingLogRefBoundCommitTest.test_log_expected_malformed_blob_id_refuses_usage test_done_run_wrapper.DoneRunRollingLogRefBoundCommitTest.test_log_expected_match_passes_silently test_done_run_wrapper.DoneRunRollingLogRefBoundCommitTest.test_log_expected_mismatch_advises_once_and_lands >> docs/tmp/rts-expected-wrapper-ids.txt
sort docs/tmp/rts-expected-wrapper-ids.txt -o docs/tmp/rts-expected-wrapper-ids.txt
cmp -s docs/tmp/rts-live-wrapper-ids-sorted.txt docs/tmp/rts-expected-wrapper-ids.txt || fail "wrapper ID set differs from the re-pinned expected set"

# 3. Worker cap and task shape preserved in the mise task.
grep -q "run = \"python3 scripts/run_required_test_suite.py --workers 8" mise.toml || fail "mise task worker cap line"
grep -q "timeout = \"295s\"" mise.toml || fail "mise task outer timeout line"
if grep -E "workers (9|1[0-9]|[2-9][0-9])" mise.toml; then fail "a worker count above 8 appears in mise.toml"; fi

# 4. Evidence records exist and carry their required sections (one dedicated check per record and obligation).
test -f docs/history/feature-notes/2026-11-14-required-suite-mise-cancellation-evidence.md || fail "Task 1 evidence record"
grep -q "^## Disposition" docs/history/feature-notes/2026-11-14-required-suite-mise-cancellation-evidence.md || fail "Task 1 disposition section"
test -f docs/history/feature-notes/2026-11-14-descendant-containment-evidence.md || fail "Task 2 evidence record"
grep -q "^## Disposition" docs/history/feature-notes/2026-11-14-descendant-containment-evidence.md || fail "Task 2 disposition section"
test -f docs/history/feature-notes/2026-11-14-wrapper-setup-cost-reduction.md || fail "Task 3 evidence record"
grep -q "^## Disposition" docs/history/feature-notes/2026-11-14-wrapper-setup-cost-reduction.md || fail "Task 3 disposition section"
test -f docs/history/feature-notes/2026-11-14-runner-coordination-decomposition-assessment.md || fail "Task 4 evidence record"
grep -q "^## Disposition" docs/history/feature-notes/2026-11-14-runner-coordination-decomposition-assessment.md || fail "Task 4 disposition section"

# 5. The new evidence records carry no em dash (scoped to files this plan creates; intentional escape: the bracketed class keeps this document's own text from matching).
if grep -q "$(printf '\\342\\200\\224')" docs/history/feature-notes/2026-11-14-required-suite-mise-cancellation-evidence.md docs/history/feature-notes/2026-11-14-descendant-containment-evidence.md docs/history/feature-notes/2026-11-14-wrapper-setup-cost-reduction.md docs/history/feature-notes/2026-11-14-runner-coordination-decomposition-assessment.md 2>/dev/null; then fail "em dash in an evidence record"; fi

# 6. Machinery absence over the run's landing range: BASE_SHA is assigned here from the recorded merge base, never pinned.
# 2026-11-19 correction (second execution-time correction): merge-base against origin/main pinned a stale base (the loop never pushes; origin/main was 619 commits behind main at execution), so the range polluted with peer landings. The default branch is the base of record: merge-base HEAD against main resolves the run branch's own branch point.
BASE_SHA="$(git merge-base HEAD main)"
git log --name-only --format= "$BASE_SHA..HEAD" | sort -u > docs/tmp/rts-landing-paths.txt
if grep -E "^(scripts/machinery_registry.json|.github/)" docs/tmp/rts-landing-paths.txt; then fail "machinery or workflow bytes in the landing range"; fi
```

### Task 1: Mise cancellation evidence and boundary

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/feature-notes/2026-11-14-required-suite-mise-cancellation-evidence.md` *(new)*

Primary class anchors:
- `RequiredTestSuiteRunner` in `scripts/run_required_test_suite.py`, probe target, no edits in this task

- [x] Probe precondition: run `mise run test:required --suite-timeout 10 --json-report docs/tmp/rts-mise-cancel-probe-report.json` (mise `raw_args` appends; argparse last-wins governs) and first verify the report landed at the probe path, proving the overrides rode through; if it lands at the task's default path, record the deployment gap and stop this task's evidence capture without interpreting partial results [class: IMPLEMENTATION_REQUIRED]
- [x] Given the probe run, expects at least one worker spawn observed before cancellation (a process listing sample or the report's per-script attempts), so the cleanup expectation is non-vacuous; a cancellation before any worker spawn proves nothing about cleanup and is recorded as a vacuous probe [class: IMPLEMENTATION_REQUIRED]
- [x] Given the probe run above, expects cancellation inside the 10-second suite timeout with the runner's captured descendant groups reaped before process exit, a complete JSON report at the probe path (inventory, outcomes, cancel reason), and a nonzero `mise` exit status; record the observed signal the runner received, the cleanup evidence, the report completeness, and the exit status verbatim in the evidence record [class: IMPLEMENTATION_REQUIRED]
- [x] Second probe mode: send SIGTERM to the running `mise run test:required` process tree from outside (a second probe run of the same shape, interrupted externally once child workers are observably active in the process listing, before the suite timeout fires; the JSON report is written once at exit, so mid-run it cannot be the trigger) [class: IMPLEMENTATION_REQUIRED]
- [x] Given the second probe, expects the record to state which process received the signal, what the runner did, the cleanup evidence, report state (a mid-run kill may leave no report; record whether one was written and how complete), and the exit status verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given either probe leaving any descendant process group live after the runner exited, expects the record to name the leaked groups with their pgids and the repro command, never a bare "cleanup worked" claim [class: IMPLEMENTATION_REQUIRED]
- [x] The record states the supported cancellation boundary (what is verified to work end to end and what is unverified or broken) plus the disposition: supported-as-recorded, or a defect finding with the evidence and the follow-up route named per the Outcome's follow-up disposition rule [class: IMPLEMENTATION_REQUIRED]
- [x] Probe scratch (probe JSON, transcripts) is second-scale and stays in the run's gitignored temporary scratch; the durable copy of every load-bearing observation rides the feature-notes record with digests [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: record required-suite mise cancellation evidence and boundary` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Descendant containment evidence, close or document

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/feature-notes/2026-11-14-descendant-containment-evidence.md` *(new)*
- `scripts/run_required_test_suite.py` (close-gap branch only)
- `scripts/test_required_test_suite.py` (close-gap branch only)

Primary class anchors:
- `RequiredTestSuiteRunner` in `scripts/run_required_test_suite.py`

- [x] Bounded reproduction inside `mktemp -d` with explicit teardown: a worker spawns an intermediate child, the intermediate child launches a grandchild in a new session and exits before the worker's cleanup snapshot (reparenting the grandchild to the system initializer); record today's observed outcome (no group returned, grandchild live in the probe window) as the baseline transcript in the evidence record [class: IMPLEMENTATION_REQUIRED]
- [x] Same fixture under cancellation: the worker is cancelled mid-run while owning the detached grandchild; record whether the grandchild's group is attributed and terminated, verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] Same fixture with external SIGKILL of the worker while it owns the detached grandchild; record containment or attribution outcomes verbatim (the origin's externally-killed-worker section) [class: IMPLEMENTATION_REQUIRED]
- [x] Compare portable containment options against the transcripts (for example snapshot-time session bookkeeping, PGID inheritance mapping, or a different attribution walk), scoring each for macOS compatibility and CI-representable primitives; the comparison table lands in the record [class: IMPLEMENTATION_REQUIRED]
- [x] Decision per the pre-registered criteria: choose the close-gap branch only when a mechanism attributes and terminates the reparented grandchild, keeps the focused runner contract suite green, uses CI-representable primitives, adds no gate, lock, or persistent wrapper, and keeps termination scope bounded to descendant groups it attributed (no kill-set growth over unrelated groups); otherwise take the document-boundary branch [class: IMPLEMENTATION_REQUIRED]
- [x] The decision states which attribution path or paths the mechanism fixes, naming the blind spot as shared by the worker-side snapshot (`_worker_process_groups` under `_cleanup_worker_descendants`) and the coordinator-side mirror (`_descendant_groups`), both walking live parent chains [class: IMPLEMENTATION_REQUIRED]
- [x] Close-gap branch, RED: add a canary to `scripts/test_required_test_suite.py` in given/expects form: given a worker that spawns an intermediate child, the intermediate child launches a grandchild in a new session and exits before the worker's cleanup snapshot (reparenting the grandchild to the system initializer) [class: IMPLEMENTATION_REQUIRED]
- [x] The canary expects the fixed path to attribute the grandchild's group and terminate it (a deterministic-report arm only when the record's boundary documents why termination is not achievable for that shape); run it, expect RED against today's tree, and record the observed failure [class: IMPLEMENTATION_REQUIRED]
- [x] Close-gap branch, GREEN: implement the minimal mechanism in the descendant snapshot/attribution and cleanup path the criteria pinned, preferring to extend or share the existing parent-chain walk over adding a duplicated second implementation; run the canary, expect GREEN; run the full focused runner contract suite, expect GREEN with no other test changed [class: IMPLEMENTATION_REQUIRED]
- [x] Document-boundary branch: the record states the supported child-lifecycle boundary exactly (cleanup covers detached children visible in the snapshot-time parent chain; pre-reparented grandchildren are out of the supported boundary), with the repro transcripts as the evidence [class: IMPLEMENTATION_REQUIRED]
- [x] The record closes with `## Disposition` naming the branch taken and the criteria result; an unlanded viable candidate routes per the Outcome's follow-up disposition rule [class: IMPLEMENTATION_REQUIRED]
- [x] Commit (close-gap branch): `fix: attribute and contain reparented worker descendants in required-suite cleanup`; Commit (document-boundary branch): `docs: record required-suite descendant containment boundary` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Slow-case setup-cost reduction

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_done_run_wrapper.py` (the six named classes only)
- `docs/history/feature-notes/2026-11-14-wrapper-setup-cost-reduction.md` *(new)*

Primary class anchors:
- `DoneRunRollingLogRefBoundCommitTest` in `scripts/test_done_run_wrapper.py`
- `DoneRunDirtCorrectionSetTest` in `scripts/test_done_run_wrapper.py`
- `DoneRunDescriptionLengthCatchTest` in `scripts/test_done_run_wrapper.py`
- `DoneRunDirtCachedDiffAuthorizationSeparationTest` in `scripts/test_done_run_wrapper.py`
- `DoneRunDeclaredStageChannelTest` in `scripts/test_done_run_wrapper.py`
- `DoneRunDeclaredStageRecoveryReplayTest` in `scripts/test_done_run_wrapper.py`

- [x] Characterization baseline: run the six named classes through the execution-selected focused path and record per-class pass counts and wall time as the before-measurement in the evidence record; expect GREEN before any edit [class: REPOSITORY_TEST]
- [x] Profile each named class's setup share (per-test Git init/checkout/process spawns) using the duration map rows for its IDs plus a targeted per-test timing of the class; the profile table lands in the record [class: IMPLEMENTATION_REQUIRED]
- [x] Given the profile, expects a reduction design that removes repeated setup (shared class fixture or setup reuse chosen at execution) while every test's observable assertions stay byte-identical; a class where no safe reduction exists is recorded as unreduced with the conflict named, never forced [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the reduction to the classes where it is proven safe; run the touched classes, expect GREEN with the same per-class pass counts as the baseline [class: IMPLEMENTATION_REQUIRED]
- [x] Discriminating check for assertion preservation: the branch diff over `scripts/test_done_run_wrapper.py` carries no changed line inside any test method body, the body range running from each `def test_` line through the last non-blank line before the next `def test_`, `class `, or zero-indentation statement (blank lines inside a body never terminate the range) [class: REPOSITORY_TEST]
- [x] Given the reduction diff, expects zero hunks intersecting a test-body line range, so the byte-identical-assertions invariant is enforced by a check, not assumed from green pass counts [class: REPOSITORY_TEST]
- [x] Run the wrapper ID-set preservation command from `## Validation Commands` (check 2), expect the count 150 (re-pinned by the 2026-11-19 plan correction) and a byte-identical match against the re-pinned expected set (the CSV set plus the five post-CSV log_expected IDs) [class: REPOSITORY_TEST]
- [x] Record after-measurement per class (pass counts and wall time) and the per-class delta; no runtime target gates the result, the delta is recorded informationally [class: IMPLEMENTATION_REQUIRED]
- [x] The record closes with `## Disposition` naming reductions landed and classes left unreduced with reasons [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `test: reduce repeated setup in slow required-suite wrapper classes` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Coordinator decomposition assessment

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/feature-notes/2026-11-14-runner-coordination-decomposition-assessment.md` *(new)*

Primary class anchors:
- `RequiredTestSuiteRunner` in `scripts/run_required_test_suite.py`, assessment target, no edits in this task

- [x] Re-derive the current shape with provenance (class line count, method count, date, source digest) and record it beside the origin's 940-line/28-method figures [class: IMPLEMENTATION_REQUIRED]
- [x] Inventory the class's responsibilities (discovery, scheduling gate, worker lifecycle and cleanup, accounting, reporting) and map the shared state each responsibility reads or mutates; the inventory table lands in the record [class: IMPLEMENTATION_REQUIRED]
- [x] Given the inventory, expects a decomposition verdict with coupling evidence: name the cohesive components that would extract cleanly and the shared state that would split poorly; do not recommend a refactor solely to satisfy the origin's structure finding [class: IMPLEMENTATION_REQUIRED]
- [x] The record closes with `## Disposition`: decompose (routing per the Outcome's follow-up disposition rule as a backlog row with a ready-to-dispatch prompt) or keep with the recorded rationale [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: assess required-suite runner decomposition candidate` [class: IMPLEMENTATION_REQUIRED]
