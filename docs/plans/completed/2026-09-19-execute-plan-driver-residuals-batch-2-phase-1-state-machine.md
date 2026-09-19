# Plan: execute-plan driver residuals batch 2 (state machine), phase 1 of 2

Covers six origins of the batch-2 family (state-machine driver code and its
test suites). The sibling plan
`docs/plans/2026-09-19-execute-plan-driver-residuals-batch-2-phase-2-contract-prose.md`
covers the remaining five origins (contract and skill prose, worktree
bootstrap). Execute this phase-1 plan first; the phase-2 plan re-checks these
landed hunks in its own drift gate.

Origin files (scope of record, under `docs/history/backlog/`):

- `2026-09-18-runtime-driver-blocked-claim-recovery-gap.md`
- `2026-09-18-execute-plan-claims-container-shape-refusal.md`
- `2026-09-18-execute-plan-sidecar-read-bounded.md`
- `2026-09-18-execute-plan-terminal-refusal-arms-test-coverage.md`
- `2026-09-18-execute-plan-test-suite-concurrency-safety.md`
- `2026-09-18-execute-plan-archive-test-fixture-scaffolding-dedup.md`

## Terms

- Machine manifest: the driver-owned `runtime_state.json` (schema_version, tasks, claims, checkpoints, history).
- Claim / launch record: a task's durable execution lease; the launch record snapshots baseline revision and generation for drift detection.
- Pre-archive gate: `_pre_archive_gate`, the fixed-order eligibility predicate of the staged terminal operation.
- Clean-round sidecar: the review `.stats.json` sidecar the gate reads as cleanliness evidence.
- Worker-result envelope: the JSON the caller passes to `--operation checkpoint --input`.
- Bounded read: the `read(LIMIT + 1)` byte-capped file policy (`TERMINAL_PLAN_READ_LIMIT`, 1000000 bytes).
- Fixture mixin: `ArchiveGateFixtureBase`, the shared archive-gate test scaffolding base introduced by Task 2.

## Assumptions

- The six origin files listed above are the scope of record; where this plan quantifies a pin, the quantity was re-derived against the tree on 2026-09-19 (drift notes below) and is re-derived again at execution by Task 1; basis: task constraint plus the three-executions caution.
- Behavioral probes recorded at authoring time (2026-09-19, python3 against the current tree) are evidence for current behavior, not predictions: malformed-checkpoint latch reproduced; corrected same-token receipt recovers in place when the launch record exists; stale-claim refusal reproduced when it does not; claims-null AttributeError reproduced; parallel suite pair-run reproduced 1 error plus a leftover `$TMPDIR/runtime_state.json`.
- Origin 1 is resolved as its documentation arm plus a recovery pin; the drift guard's record-absence refusal stays by design; basis: probes above, the drift docstring at `_claim_drift_outcome`, and the origin's own (a)-or-(b) disjunction.
- Origin 2 is fixed at the `load_manifest` validation boundary so the whole `.get("claims", {})` call-site family closes at once; basis: `load_manifest` already validates `tasks` the same way, and the sibling call sites (:1048, :1313, :2236, :2608, :4125 area, line spans re-derived by Task 1) share the exposure.
- Origin 9, origin 11, origin 3, origin 5, origin 8 belong to the phase-2 sibling plan; basis: the batch split rule in the authoring task.
- This plan edits `agents/skills/execute-plan/runtime-contract.md` at exactly two places (clause (4) bound sentence, checkpoint caller envelope subsection); all other prose origins stay in phase 2 (scope annotation: a third sentence recording the legacy hesitation-alias translation landed in the Normalized result schema section at execution r2 to keep the envelope row's cross-reference truthful; plan_correction non-semantic); basis: scope-of-record split.
- Execution sequences after any in-flight driver work on the same surfaces; Task 1 stands down when a peer holds the driver or test files dirty; basis: task constraint and the repo's parallel-session practice.

Decision points requiring a grill: plan split: resolved by the authoring task split rule (roughly 600-line threshold, measured single-file estimate about 700 lines), 2026-09-19, plan header; origin 1 direction: resolved by authoring-time behavioral probes plus the origin disjunction, 2026-09-19, Task 6; origin 2 fix level: resolved by family-closure rationale (tasks-idiom parity), 2026-09-19, Task 3.

## Gist & Examples

Three driver defects and three test-suite debts, all witnessed by review
rounds deferred at the round cap or by learn captures, get closed in one
pass over `scripts/execute_plan_runtime.py` and
`scripts/test_execute_plan_runtime.py`:

1. A malformed claims container (`"claims": null`, a list, or a string)
   passes `load_manifest` (which validates only `schema_version` and
   `tasks`) and crashes `_pre_archive_gate` with `AttributeError` at the
   container iteration; the CLI except tuple lacks `AttributeError`, so the
   operator sees a traceback instead of a failure line. Fix: validate
   the claims container at load time the same way `tasks` is validated, so
   every consumer site is safe and the CLI's top-level handler catches the
   `ValueError`, prints the claims-naming failure line, and exits nonzero
   (a stderr failure line, not a JSON refusal envelope; gate refusals keep
   printing envelopes with exit 0).
2. The gate reads the clean-round sidecar with an unbounded
   `read_text(encoding="utf-8")`, while every other read in the same gate
   uses the bounded byte-capped policy. Fix:
   read the sidecar through the same `LIMIT + 1` pattern and refuse an
   over-limit sidecar as clean-round evidence failure.
3. A first checkpoint with an incomplete worker-result envelope (missing
   `reason_code`) latches the claim blocked with `resume_allowed: false`,
   and the caller has no documented way to know the exact envelope the CLI
   expects (`generation` must be the claim generation, `claim_token` the
   live token). Probed behavior on the current tree: a corrected
   re-submission under the same token recovers in place when the claim
   carries its launch record. Fix: document the caller envelope in the
   runtime contract with a copy-paste example that a validation command
   executes end-to-end, and pin the in-place recovery with a regression
   test. The drift guard's refusal for a post-launch claim without a launch
   record stays by design (anti-tamper; the plan does not weaken it).
4. Seven fail-closed refusal arms of the pre-archive gate and the terminal
   dispatcher have no test witness: missing `plans_completed_dir` facts
   key, resolved destination directory absent on disk, destination escaping
   the repository root, sidecar failing the safe-path policy, sidecar
   invalid JSON, unknown terminal stage, and the input shape guard. One
   refusal fixture per arm pins them.
5. The suite writes a fixture manifest to the fixed name
   `runtime_state.json` in the shared `$TMPDIR` (outside the per-test temp
   dir, because the manifest must sit outside the fixture git repo), so two
   concurrent suite instances clobber it; a pair-run at authoring time
   reproduced one error and a leftover file. Fix: uuid-suffix the fixture
   manifest name (pattern already used elsewhere in the file) and gate the
   fix with a parallel pair-run validation. The unconfirmed
   success-instead-of-blocked observation gets a bounded controlled-
   concurrency investigation, backlogged only if reproduced.
6. Four archive/terminal test classes duplicate overlapping scaffolding:
   the facts writer, the completed-directory mkdir, the manifest seed, and
   driver construction appear in every class, while the sidecar and
   gate-seeding helpers are shared in pairs. A shared
   `ArchiveGateFixtureBase` owns exactly the members the inventory proves
   shared; each class keeps only its differing constants and expectations,
   and the hermetic git setup stays only in the class that proves real
   ancestry.

Example of the documented envelope (Task 6 pins this exact shape in the
contract and gate G9 executes it end-to-end; `generation` is the live claim
generation from the claim record, 1 for the first claim of a fresh manifest,
and a workflow-generation value refuses as `owner-mismatch`):

```json
{
  "status": "success",
  "reason_code": "completed",
  "evidence": ["worker-log: task complete"],
  "action_scope": "repository-task",
  "checkpoint_identity": "task-1:worker-1",
  "generation": 1,
  "claim_token": "REPLACE_WITH_LIVE_CLAIM_TOKEN"
}
```

## Evaluation Criteria

**Quality dimensions:**

- Correctness: every refusal arm this plan pins keeps its fail-closed semantics; no pinned refusal weakens to make a test pass.
- Test determinism: the suite passes serially and as two concurrent instances; no test writes a fixed name into the shared `$TMPDIR`.
- Simplicity: the claims-container fix is one validation line mirroring the existing `tasks` check; the mixin extraction deletes duplicated scaffolding rather than adding a parallel layer.
- Documentation truth: the contract's checkpoint envelope section matches `runtime_capabilities.normalize_result` field-for-field; every documented claim traces to code probed or read in this plan.

**Done when:**

- Full suite green: `cd scripts && python3 -m unittest test_execute_plan_runtime` exits 0 (259 tests at authoring baseline; count re-derived by Task 1).
- Two concurrent suite instances both exit 0 and leave no `$TMPDIR/runtime_state.json` behind.
- All seven previously unwitnessed refusal arms have named fixtures asserting blocked status, evidence fragment, and byte-identical manifest.
- The claims-container canaries refuse with a claims-naming message at load time for null, list, and string shapes.
- The gate refuses an over-limit sidecar and accepts a at-limit sidecar through the same bounded policy as the plan read.
- The contract carries the caller envelope with a copy-paste example that the validation executes end-to-end to a successful checkpoint.

**Ship when:** nothing external; all work is repository-verifiable.

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**

- `scripts/execute_plan_runtime.py` (tasks own: `load_manifest` claims validation, `_pre_archive_gate` sidecar read, contract-facing docstring spans; all other methods are frozen; reject findings that touch them)

**Tests:**

- `scripts/test_execute_plan_runtime.py` (tasks own: `ArchiveGateFixtureBase` extraction, the four archive/terminal classes' scaffolding, `ClaimsContainerShapeTest` *(new)*, `CheckpointRecoveryTest` *(new)*, the bounded-sidecar and refusal-arm fixtures, the shared-`$TMPDIR` fixture write site; the remaining main-class tests are frozen except the one fixture write site Task 7 owns)

**Documentation:**

- `agents/skills/execute-plan/runtime-contract.md` (tasks own: the clause (4) sidecar bound sentence, the new checkpoint caller envelope subsection; all other sections frozen)

**Plan-related extension;** implementation and review may change files not
listed above when causally related (a moved helper's import site, a
launch-record fixture field a new test needs). Findings without a causal
link to these origins drop with a one-line reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/execute-plan/SKILL.md` and `agents/skills/execute-plan/subagent-prompts.md`; owned by the phase-2 sibling plan.
- `scripts/runtime_capabilities.py`; `normalize_result` is the envelope's source of truth and stays unchanged; the contract documents it, never the reverse.
- `scripts/execute_plan_runtime_codex.py`, `scripts/test_execute_plan_runtime_codex.py`, `scripts/test_runtime_capabilities.py`; no origin touches the codex adapter surface.
- The archived plan `docs/plans/completed/2026-09-16-execute-plan-integrity-quad.md`; immutable history (phase-2 origin records the disposition).

## Design Invariants (CR Guard)

- Fail-closed refusals stay fail-closed: no task may weaken an existing refusal arm, widen an except tuple to swallow `AttributeError` silently, or convert a refusal into a default-and-continue.
- The drift guard's record-absence refusal (`claim is in a post-launch state but has no launch record`) is deliberate anti-tamper; origin 1's recovery work must not bypass, weaken, or special-case it.
- Lock discipline: the sidecar read becomes bounded; no task adds an unbounded read, and no task changes the terminal path's locking semantics (the terminal path runs under the manifest lock via the `_locked_mutation` fence on `mark_terminal`; the lock is deliberately non-reentrant, so no nested acquisition may be added inside `_pre_archive_gate`, and adding or removing locking there is out of scope).
- Hermeticity: the hermetic git setup (pinned `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM`) stays attached to exactly the class that proves real ancestry; the mixin must not silently grant git init to classes that never prove ancestry.
- The suite stays the validation GREEN gate: serially stable first, then concurrency-safe; a concurrency fix must not trade away hermetic env pinning.

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repository root. Each gate fails loud; a subprocess error is
# not a pass.
set -u
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

# G1: full suite green (serial).
( cd scripts && python3 -m unittest test_execute_plan_runtime ) || fail "G1 suite"

# G2: two concurrent suite instances both green, no shared fixed-name leftover.
EV=$(mktemp -d "${TMPDIR:-/tmp}/b2-par.XXXXXX")
LEFT="${TMPDIR:-/tmp}/runtime_state.json"
rm -f "$LEFT" "$LEFT.lock"
( cd scripts && python3 -m unittest test_execute_plan_runtime >"$EV/a.log" 2>&1; echo $? >"$EV/a.rc" ) &
( cd scripts && python3 -m unittest test_execute_plan_runtime >"$EV/b.log" 2>&1; echo $? >"$EV/b.rc" ) &
wait
[ "$(cat "$EV/a.rc")" = "0" ] || { tail -5 "$EV/a.log"; fail "G2 parallel instance A"; }
[ "$(cat "$EV/b.rc")" = "0" ] || { tail -5 "$EV/b.log"; fail "G2 parallel instance B"; }
[ ! -e "$LEFT" ] || fail "G2 leftover shared fixture manifest"
if ls "${TMPDIR:-/tmp}"/runtime_state-*.json* >/dev/null 2>&1; then fail "G2 uuid fixture litter in shared TMPDIR"; fi
rm -rf "$EV"

# G3: claims-container canaries exist and the loader validation lands.
expect_contains() { grep -qF -- "$2" "$1" || fail "G3 missing in $1: $2"; }
expect_contains scripts/execute_plan_runtime.py "runtime manifest claims must be a mapping"
expect_contains scripts/test_execute_plan_runtime.py "class ClaimsContainerShapeTest"
expect_contains scripts/test_execute_plan_runtime.py "class CheckpointRecoveryTest"
test "$(grep -cF 'claims must be a mapping' scripts/execute_plan_runtime.py)" -eq 1 || fail "G3 claims validation count"

# G4: bounded sidecar read replaces the unbounded one in the gate.
expect_contains scripts/execute_plan_runtime.py "TERMINAL_PLAN_READ_LIMIT + 1"
test "$(grep -c 'sidecar_path.read_text' scripts/execute_plan_runtime.py)" -eq 0 || fail "G4 unbounded gate sidecar read remains"
expect_contains scripts/execute_plan_runtime.py "clean-round review sidecar exceeds the bounded read limit"

# G5: refusal-arm witnesses exist (one test method per arm family).
for witness in test_pre_archive_refuses_environment_and_shape_arms test_refuses_unknown_terminal_stage; do
  grep -qF "$witness" scripts/test_execute_plan_runtime.py || fail "G5 missing witness $witness"
done

# G6: fixture scaffolding dedup landed; facts literal owned once.
expect_contains scripts/test_execute_plan_runtime.py "class ArchiveGateFixtureBase"
test "$(grep -c 'plans_completed_dir = ..*docs/plans/completed/' scripts/test_execute_plan_runtime.py)" -eq 1 || fail "G6 facts literal not owned once"
! grep -qF 'root.parent / "runtime_state.json"' scripts/test_execute_plan_runtime.py || fail "G6 shared fixed-name fixture write remains"

# G7: contract carries the caller envelope and the clause (4) bound sentence.
expect_contains agents/skills/execute-plan/runtime-contract.md "### Checkpoint caller envelope"
expect_contains agents/skills/execute-plan/runtime-contract.md "the terminal gate reads the clean-round review sidecar through the same bounded policy"
grep -q "checkpoint_identity" agents/skills/execute-plan/runtime-contract.md || fail "G7 envelope fields"

# G8: hygiene over the files this plan touches (authored content only).
for f in docs/plans/2026-09-19-execute-plan-driver-residuals-batch-2-phase-1-state-machine.md; do
  if grep -q $'\xe2\x80\x94' "$f"; then fail "G8 em-dash in $f"; fi
done

# G9: the documented envelope executes end-to-end to a successful checkpoint
# (fresh temp repo, seeded launched claim with its launch record, then the
# Gist envelope with the live claim token and the claim generation).
EV9=$(mktemp -d "${TMPDIR:-/tmp}/b2-env.XXXXXX")
python3 - "$EV9" <<'PYEOF' || { echo "G9 envelope end-to-end failed" >&2; rm -rf "$EV9"; exit 1; }
import subprocess, sys
from pathlib import Path
sys.path.insert(0, "scripts")
import execute_plan_runtime as runtime
ev = Path(sys.argv[1])
root = ev / "repo"; root.mkdir()
def git(*a): subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)
git("init", "-q"); git("config", "user.email", "t@e.invalid"); git("config", "user.name", "T")
(root / ".gitignore").write_text("runtime_state.json\nruntime_state.json.lock\n")
git("add", ".gitignore"); git("commit", "-qm", "fixture")
sp = ev / "runtime_state.json"
runtime.create_manifest(sp, "b2-envelope", [{"id": "task-1", "number": 1, "status": "pending"}])
state = runtime.load_manifest(sp)
state["claims"]["task-1"] = {"token": "b2-tok", "generation": 1, "owner": "b2-owner", "state": "launched", "task_id": "task-1", "launched_at": 111.0, "launch_record": {"baseline_revision": "", "generation": 1, "launched_at": 111.0}}
runtime._safe_write_json(sp, state)
driver = runtime.RuntimeDriver(sp, plan_slug="b2-envelope", owner="b2-owner", repo_root=root)
good = {
    "status": "success",
    "reason_code": "completed",
    "evidence": ["worker-log: task complete"],
    "action_scope": "repository-task",
    "checkpoint_identity": "task-1:worker-1",
    "generation": 1,
    "claim_token": "b2-tok",
}
r = driver.record_worker_checkpoint(good)
assert r.get("status") == "success", r
m2 = runtime.load_manifest(sp)
assert m2["tasks"]["task-1"]["status"] == "done-pending", m2["tasks"]["task-1"]
PYEOF
rm -rf "$EV9"
```

Authoring-time execution record (2026-09-19, post r2 folds): bash -n clean.
G1 green (259 tests). G2 red today (pair-run reproduced one instance error
and the leftover file; flips green at Task 7). G3, G5, G7 red today over
not-yet-created symbols (flip per their owning tasks). G4 red today (the
gate site's unbounded read count is 1; flips to 0 at Task 4). G6 red today
(the facts literal count is 3 under the quote-style-agnostic pattern;
flips to 1 at Task 2; the pattern was proven in both directions at authoring:
3 today, and 1 against a simulated post-fold tree with a single-quoted
python literal; the shared-name site count is 1 and flips to 0 at Task 7).
G8 green today. G9 green today (executed at authoring: the envelope passes
end-to-end on the current tree; it is the end-to-end owner of the
Done-when envelope criterion and stays green). Every red gate maps to
exactly one owning task. Review r1 verdict: ready=yes zero blocking (7
non-blocking folded). Review r2 verdict: ready=no with one blocking
finding (the G6 facts gate pinned python quoting style instead of literal
ownership; replaced with a quote-style-agnostic pattern proven in both
directions) plus four non-blocking findings folded (the recovery test's
seed pinned to claim generation equal to the manifest generation, the
stale under-the-lock premise dropped from the Gist and the CR Guard lock
line rewritten to preserve terminal-path locking semantics, the mixin
member list qualified by the inventory, the G4 refusal fragment pinned in
Task 4's step text). Review r3 verdict: ready=yes zero blocking (1 Medium
plus 2 Low folded: the CR Guard lock parenthetical corrected to the
verified under-the-lock-via-`_locked_mutation` shape with the lock fence
added to Task 1's re-derivation list, the uuid fixture and its `.lock`
pinned with addCleanup unlinks plus a G2 litter gate, and the Gist's
claims-container operator surface corrected to the stderr failure line
the CLI handler actually prints). Review r4 verdict: ready=yes zero
blocking (1 Low folded: the Task 7 uuid name shape pinned to the literal
`f"runtime_state-{uuid.uuid4().hex[:8]}.json"` so the G2 litter glob
cannot be blinded by a conforming deviation); this digest is the r5
input, the final round at the cap.

### Task 1: Phase 0 drift gate (re-derive every pin before any edit)

Files:
- none (read-only gate)

- [x] Re-read the six origin files and this plan's pinned spans against the current tree: `load_manifest` body, the `_pre_archive_gate` sidecar read and claims iteration, the `mark_terminal` stage dispatch and its `_locked_mutation` lock fence, the four archive/terminal test classes' helper inventories, the shared-name fixture write site, `TERMINAL_PLAN_READ_LIMIT` and `_read_plan_bounded`; where a pin drifted, update this plan's task text in the same edit and record the drift; classification [class: REPOSITORY_TEST]
- [x] Probe current behavior once more and record outcomes in the session notes: malformed-checkpoint latch, corrected same-token receipt with and without a launch record, claims-null container, parallel pair-run; a probe that now contradicts a task's premise stops the plan for re-authoring, not a silent edit; classification [class: REPOSITORY_TEST]
- [x] Stand down and report when any peer session holds `scripts/execute_plan_runtime.py` or `scripts/test_execute_plan_runtime.py` dirty or mid-flight driver work exists in recent commits; sequence after it instead of interleaving; classification [class: REPOSITORY_TEST]
- [x] Run the full suite and record the test count as the execution baseline (authoring baseline: 259, OK); classification [class: REPOSITORY_TEST]

### Task 2: Extract ArchiveGateFixtureBase (origin: fixture scaffolding dedup)

Files:
- `scripts/test_execute_plan_runtime.py`

- [x] Inventory the four classes' helpers first (setUp bodies, write_facts, write_sidecar, clean_sidecar, complete_all_tasks, driver, pre_archive, seed_gate, PLAN_TEXT and path constants) and record which class uses which; the extraction moves exactly the shared members; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Introduce `class ArchiveGateFixtureBase(unittest.TestCase)` owning exactly the members the inventory proves shared: `PLAN_TEXT`, the TOML-fence facts writer, the completed-directory mkdir, the manifest seed from a class-level task-row list, the active-plan writer, and the `driver()` constructor helper, plus whichever of the sidecar writer, `clean_sidecar`, `complete_all_tasks`, `pre_archive()`, and `seed_gate()` the inventory shows shared (single-class helpers stay local); a `requires_git = False` class attribute gates the hermetic git setup; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Rebase the four classes onto the mixin keeping only their differing constants and expectations; `ArchiveGatePreArchiveTest` alone sets `requires_git = True` (it proves real ancestor-or-self ancestry); classification [class: IMPLEMENTATION_REQUIRED]
- [x] `TestArchiveGateFixtureBase#test_mixin_membership`; given the four rebased classes, expects each class defines no local copy of a mixin-owned helper and the facts TOML literal occurs exactly once in the file; classification [class: REPOSITORY_TEST]
- [x] Run the four classes then the full suite → expect GREEN (Task 1 baseline count, zero regressions); classification [class: REPOSITORY_TEST]
- [x] Commit: `test: extract ArchiveGateFixtureBase shared scaffolding` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Claims container validation (origin: claims-container shape refusal)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] RED canary `ClaimsContainerShapeTest#test_load_manifest_refuses_non_mapping_claims`; given manifests whose claims container is `null`, a list, and a string (one subTest each), expects `load_manifest` raises `ValueError` naming the claims mapping requirement for every shape; expect RED: the suite fails this class with `AttributeError` or a missing-message assert while all previously green tests stay green; classification [class: REPOSITORY_TEST]
- [x] RED canary `ClaimsContainerShapeTest#test_cli_refuses_claims_container_before_driver_work`; given a claims-null manifest driven through the CLI terminal pre-archive operation as a subprocess, expects a nonzero exit, output naming the claims shape, and a byte-identical manifest; expect RED: today the subprocess dies on a traceback without the claims-naming message; classification [class: REPOSITORY_TEST]
- [x] Implement in `load_manifest` beside the existing tasks check: when the claims key is present and not a mapping, raise `ValueError("runtime manifest claims must be a mapping")`; absent key stays legal; scope boundary: the origin-recorded row-level non-Mapping task-value exposure via `_task_complete` is pre-existing and stays out of scope (this task fixes the container level only); classification [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the new class passes and the full suite holds the Task 1 baseline plus the new tests; classification [class: REPOSITORY_TEST]
- [x] Commit: `fix: refuse non-mapping claims containers at manifest load` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Bounded clean-round sidecar read (origin: sidecar read bounded)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] RED canary `ArchiveGatePreArchiveTest#test_sidecar_read_bounded_refuses_oversize`; given a valid-shape sidecar padded to `TERMINAL_PLAN_READ_LIMIT + 1` bytes, expects blocked `done-pending` with evidence naming the bounded-read limit and a byte-identical manifest; expect RED: today the oversize sidecar parses and the gate proceeds; classification [class: REPOSITORY_TEST]
- [x] RED canary `ArchiveGatePreArchiveTest#test_sidecar_read_bounded_accepts_at_limit`; given a valid sidecar sized to exactly `TERMINAL_PLAN_READ_LIMIT` bytes, expects the gate records and the run stays active; expect RED or GREEN-as-written today (record which; the at-limit arm pins the boundary either way); classification [class: REPOSITORY_TEST]
- [x] Implement: replace the gate's `read_text(encoding="utf-8")` with a binary `read(TERMINAL_PLAN_READ_LIMIT + 1)`, refuse `len(data) > TERMINAL_PLAN_READ_LIMIT` as clean-round evidence failure, then decode and parse; decode failures keep the existing unreadable-or-invalid-JSON refusal (a decode error is a `ValueError` subclass, no except-tuple change); the oversize refusal evidence names the bound with exactly this fragment: clean-round review sidecar exceeds the bounded read limit; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the staged-terminal contract passage (clause (4)) with one sentence: the terminal gate reads the clean-round review sidecar through the same bounded policy as the plan read, and an over-limit sidecar refuses with evidence naming `clean-round review sidecar exceeds the bounded read limit` (reworded at execution r2 to quote the observable evidence line; plan_correction non-semantic); classification [class: IMPLEMENTATION_REQUIRED]
- [x] Twin the same fact in the `_pre_archive_gate` docstring's sidecar clause so the docstring and the contract sentence state the same bounded-read behavior in the same edit; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the class passes and the full suite holds; classification [class: REPOSITORY_TEST]
- [x] Commit: `fix: bound the clean-round sidecar read in the pre-archive gate` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Refusal-arm witnesses (origin: terminal refusal arms test coverage)

Files:
- `scripts/test_execute_plan_runtime.py`

- [x] `ArchiveGatePreArchiveTest#test_pre_archive_refuses_environment_and_shape_arms`; six subTests, each asserting blocked `done-pending`, the arm-naming evidence fragment, and the byte-identical manifest, following the existing case-tuple pattern: (a) facts without `plans_completed_dir` expects the missing-facts-key evidence; (b) resolved destination directory removed from disk expects the does-not-exist evidence; (c) facts resolving the completed directory outside the repository root expects the escapes-the-root evidence; (d) `review_sidecar` escaping the repository root expects the unsafe-path evidence; (e) a sidecar file of raw non-JSON text expects the unreadable-or-invalid evidence; (f) the shape guard with a non-string plan path, a non-sha commit identity, and an empty Phase 5 checklist expects the required-inputs evidence; expect RED: each arm's evidence fragment is absent from today's suite (zero grep hits at authoring), so every subTest fails on the missing fragment or an unexpected outcome; classification [class: REPOSITORY_TEST]
- [x] `TerminalFinalStageTest#test_refuses_unknown_terminal_stage`; given `mark_terminal` with `stage` neither `pre-archive` nor `final`, expects blocked `done-pending` naming the unsupported stage and a byte-identical manifest; expect RED: the unsupported-stage evidence appears in no test today; classification [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the two methods pass; the suite holds the baseline plus all new tests; classification [class: REPOSITORY_TEST]
- [x] Commit: `test: witness the unwitnessed pre-archive and terminal refusal arms` [class: REPOSITORY_TEST]

### Task 6: Checkpoint caller envelope documentation and recovery pin (origin: blocked-claim recovery gap)

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

- [x] Add a `### Checkpoint caller envelope` subsection under the driver entrypoint section: required keys (`status`, `reason_code` from the closed reason set, non-empty string-list `evidence`, non-blank `action_scope`, non-blank `checkpoint_identity` (tightened from non-empty at execution r2 to match the strip-based checks; plan_correction non-semantic) whose task prefix selects the claim, `generation` defined as the CLAIM generation from the claim record, `claim_token` matching the live claim), the malformed-receipt fail-closed behavior, and the recovery statement grounded in the authoring probes: a corrected re-submission under the same live token recovers in place without lease expiry when the claim carries its launch record; a post-launch claim without a launch record refuses as stale-claim by design; include the copy-paste JSON example from this plan's Gist with the token placeholder; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Open the subsection with a one-line canonical-home pointer: the Normalized result schema section owns the post-normalization field list; this subsection documents the caller-facing checkpoint input only; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the section consistent with the code: every field except `claim_token` must appear in `runtime_capabilities.normalize_result`'s checks (do not edit `runtime_capabilities.py`, frozen); `claim_token` is the driver's claim-fencing input consumed at `_record_checkpoint_locked`, and the example's generation value matches the Gist (1, the first claim's generation); classification [class: IMPLEMENTATION_REQUIRED]
- [x] `CheckpointRecoveryTest#test_corrected_checkpoint_after_malformed_receipt_recovers`; given a launched claim whose generation equals the manifest generation (seed 0, the suite seed's default; a differing claim generation refuses the malformed receipt at fencing as `owner-mismatch` before any latch) and a launch record, and a first checkpoint missing `reason_code`, expects the malformed receipt blocked with `resume_allowed` false and the task latched, then a corrected envelope under the same token and generation expects success, task `done-pending`, and no lease or manifest-recreation steps; this is a GREEN-on-arrival characterization pin of probed current behavior, not a RED-then-fix item; classification [class: REPOSITORY_TEST]
- [x] `CheckpointRecoveryTest#test_drift_guard_refuses_post_launch_claim_without_launch_record`; given a blocked latched claim whose launch record is absent, expects the corrected receipt refused as stale-claim naming the missing record; pins the by-design boundary the documentation states; classification [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: both tests pass on arrival (behavior exists); if either fails, stop and re-author the documentation claim against the probe; classification [class: REPOSITORY_TEST]
- [x] Commit: `docs: document the checkpoint caller envelope and pin in-place recovery` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Concurrency-safe fixture manifest (origin: suite concurrency safety)

Files:
- `scripts/test_execute_plan_runtime.py`

- [x] Replace the shared fixed-name fixture write (`root.parent / "runtime_state.json"`) with the pinned literal name shape `f"runtime_state-{uuid.uuid4().hex[:8]}.json"` in the same location (the sibling fixtures' pattern), and pair the new name with `addCleanup` unlinks (missing-ok) for both the manifest and its `.lock` sibling so no per-run litter accumulates in the shared `$TMPDIR`; the manifest must stay outside the fixture git repo so the clean-worktree witnesses stay inert; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full suite serially → expect GREEN with the Task 1 baseline plus all tests added by earlier tasks; classification [class: REPOSITORY_TEST]
- [x] Controlled-concurrency investigation: run the pre-archive refusal class as four concurrent instances three times and record every outcome; if a refusal test ever returns success-instead-of-blocked, stop, capture the manifest and logs, and record a new backlog item for the mechanism; if unreproduced, record the attempts as the evidence and close the investigation; classification [class: REPOSITORY_TEST]
- [x] Commit: `test: uuid-suffix the shared fixture manifest name` [class: IMPLEMENTATION_REQUIRED]

### Task 8: Final validation sweep

Files:
- none (verification only)

- [x] Run the full Validation Commands block from the repository root → expect every gate green; classification [class: REPOSITORY_TEST]
- [x] Run the pin-versus-prescribed-text audit: every pinned span in this plan occurs verbatim in the prescribed task snippet or target file, all counts re-derived; classification [class: REPOSITORY_TEST]
- [x] Run the public hygiene scan from the repository root; expect exit 0; classification [class: REPOSITORY_TEST]
- [x] Commit (if anything moved): `chore: batch 2 phase 1 final sweep` [class: REPOSITORY_TEST]
