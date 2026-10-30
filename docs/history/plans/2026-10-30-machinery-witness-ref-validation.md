# Plan: Machinery Witness Reference Validation

Backlog origin: docs/history/backlog/2026-10-30-machinery-witness-ref-validation.md
Driving force: code-quality
Authoring claim: docs/tmp/authoring-claims/2026-10-30-machinery-witness-ref-validation.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)
Plan review record: .ai-playbook/reviews/2026-10-30-plan-review-machinery-witness-ref-validation-r*.md
Execution budget: 1.5h total, largest task 1.5h

## Terms

- Machinery inventory: the registry-backed `--check` validator that reports whether tracked scripts and other machinery have valid witnesses.
- Red-test witness: a registry reference to a tracked test file offered as evidence that machinery is exercised by a test.
- Script stem: the filename without its directory and extension for a resolved script source, such as `hooks_probe`.
- Protocol row: a registry entry whose kind is `protocol` and which has no script path.
- Test-source path: a tracked Python or shell test file with a `.py` or `.sh` extension and a basename beginning with `test_`, matching the tracked test-source formats used in this repository.
- Resolved script source: for a script row, use its non-test file paths; when `paths` is empty, use a `.py` or `.sh` filename in the row id, then explicit non-test `scripts/<file>` paths in its note; if neither resolves, the row has no script stem to check.
- Fence class: the backlog classification for a fix that strengthens an existing guard using an incident already recorded in its origin.

## Why

The existing check accepts any tracked path as a `red-test` witness, so a README can falsely certify machinery and the current `hooks_probe` row points to a test that never references the script. The incident and mutation evidence are recorded in [the backlog origin](docs/history/backlog/2026-10-30-machinery-witness-ref-validation.md).

## Gist & Examples

TLDR: Validate red-test witness paths and script references, improving coverage through code-quality.

Before, changing `script:base_reflog_audit.py` to cite `README.md` leaves `--check` green, and the `hooks_probe` witness names a test with no script reference. After, each red-test ref resolves to a tracked test-source path with a `test_` basename; each script row with a resolved script source also requires its stem in the test. A script row with no resolvable source gets the path check only. False existing witnesses are repaired. A test that reaches a script only through an unrelated helper may be rejected; that is the recorded false-positive cost for this pass.

## Outcome

The existing machinery inventory check reports a row-specific failure when a red-test witness does not meet its required test-path and script-reference evidence.

- False witnesses no longer make the registry appear covered.
- Existing false witnesses are corrected in the registry.
- A mutation-style regression keeps the false-witness case red.

Gate delta: one fence is added within the existing `scripts/machinery_inventory.py --check` gate as a new failure condition for red-test witnesses; no separate gate, protocol layer, or state field is added, and no task condition pauses dispatch; the fence addresses the completed integrity failure recorded in the origin (the false `hooks_probe` witness and the README mutation that passed); the current guard-liveness ledger reports 29 catches to 48 incidents (29:48, `scripts/gate_liveness_ledger.py show`, 2026-10-30); it removes green acceptance of arbitrary tracked paths as test witnesses.

## Assumptions

- Preserve `machinery_inventory.py`'s committed-`HEAD` input boundary for witness paths and source contents; the check must remain independent of the index and worktree edits.
- Require every `red-test` ref to resolve to a tracked test-source path. For `kind: script` rows, require every resolved script stem in the test source. Empty-path rows resolve from a filename-shaped id or explicit non-test script paths in the note; if no source resolves, apply the tracked-test-source check only. The inspected examples are `script:landing_parentage_gate.py` (id), `script:plan-files-coverage-arm` and `script:plan-review-identity-warning` (note path), and `script:origins-coverage-undercount-audit` (no source); the five protocol rows also have no script stem and receive the path check only. Source: `scripts/machinery_registry.json`, 2026-10-30.
- The origin's `Origin class: fence-class` matches its body: this adds one predicate inside the existing validator and no separate gate. The body records a current false witness and a mutation that passes, which justify the extension.
- Machinery admission: incident: the false `hooks_probe` witness and README mutation in the origin; expected catch frequency: each registry edit that introduces a non-exercising red-test witness; false-positive cost: a test that exercises a script indirectly through a helper may not name its stem; review date: the next machinery-inventory maintenance pass. This adds one fence predicate inside the existing validator, not a separate gate, and removes the acceptance of an arbitrary tracked path.
- Scope extensions (grilled): none proposed.
- Sources inspected: not a tracker-linked request.

Decision points requiring a grill: script-stem matching applies to script rows with a resolved source from `paths`, a filename-shaped id, or an explicit non-test script path in the note; script rows with no resolvable source and protocol rows receive tracked-test-source validation only (source: `scripts/machinery_registry.json`; inspected 2026-10-30; affected section: Task 1).

## Evaluation Criteria

**Quality dimensions:**
- Correctness: `--check` rejects an invalid red-test ref and names its registry row id.
- Coverage: a mutation-style regression demonstrates that a test path without the script stem fails, while a valid witness passes.
- Maintainability: validator inputs remain committed-`HEAD` based and the existing `--check` entry point remains the only gate.

**Done when:**
- Every red-test witness ref resolves to a tracked test-source path whose basename begins `test_`.
- Script rows with a resolved source require the referenced test source to contain each resolved script stem; script rows with no resolvable source and protocol rows receive the tracked-test-source check only.
- Every false existing red-test witness is repaired, including `script:hooks_probe.py`.
- The false-path and no-stem mutations fail; a valid positive-control fixture and the existing machinery inventory check pass.

**Ship when:** none.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/machinery_inventory.py` (Task 1)

**Registry:**
- `scripts/machinery_registry.json` (Task 1)

**Tests:**
- `scripts/test_machinery_inventory.py` (Task 1 mutation regressions and positive controls)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Other witness classes or new gates; they are outside the selected origin scope.

## Validation Commands

```bash
python3 scripts/machinery_inventory.py --check
```

### Task 1: Validate red-test witnesses

Context surface: Terms and this task.

Files:
- `scripts/machinery_inventory.py`
- `scripts/machinery_registry.json`
- `scripts/test_machinery_inventory.py`

Primary class anchors:
- `check_failures` in `scripts/machinery_inventory.py`

Admission record: the origin documents the false `hooks_probe` witness and the README mutation that `--check` accepts. Expected catches are registry edits that cite non-exercising red-test witnesses. The known false-positive cost is indirect helper coverage that does not leave the script stem in the referenced test. Review on the next machinery-inventory maintenance pass.

- [ ] Every `red-test` ref that is not a tracked Python or shell test-source path with a basename beginning `test_` makes `--check` fail with its row id. [class: IMPLEMENTATION_REQUIRED]
- [ ] A script row with a resolved script source fails when its tracked test-source ref omits any resolved stem; valid refs pass. [class: IMPLEMENTATION_REQUIRED]
- [ ] With empty `paths`, a filename-shaped id or explicit non-test script path in the note supplies a stem; if neither resolves, only the tracked-test-source check applies. [class: IMPLEMENTATION_REQUIRED]
- [ ] Existing false witnesses are repaired: given the current registry, expects every `red-test` ref to satisfy its applicable predicate, including repair of the known false script witness by ensuring its cited test directly references and exercises the script stem. [class: IMPLEMENTATION_REQUIRED]
- [ ] Mutation regression: a tracked Markdown file with a basename beginning `test_` fails with its registry row id. [class: REPOSITORY_TEST]
- [ ] Mutation regression: a path-bearing script row whose test source omits a resolved stem fails with its registry row id. [class: REPOSITORY_TEST]
- [ ] Mutation regression: an ID-resolved pathless script row fails when its test source omits the ID-derived stem. [class: REPOSITORY_TEST]
- [ ] Mutation regression: a pathless row whose note names a concrete script path (such as `script:plan-files-coverage-arm`) fails when its test source omits that note-derived stem. [class: REPOSITORY_TEST]
- [ ] Positive control: a pathless row with no resolvable script source (such as `script:origins-coverage-undercount-audit`) passes with a valid test-source ref and receives no inferred stem check. [class: REPOSITORY_TEST]
- [ ] Positive control: a clean-registry fixture with every resolved stem and a valid shell test source stays green; its `test_` basename and script-stem content are accepted. [class: REPOSITORY_TEST]
- [ ] Preserve committed-tree inputs: given staged or unstaged changes to a witness test, expects `--check` to read the committed `HEAD` version, not the index or worktree copy. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect RED: the mutation witness must fail before the implementation is added. [class: REPOSITORY_TEST]
- [ ] Write minimal implementation and registry repairs. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect GREEN: valid registry witnesses and the mutation regression produce their expected outcomes. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: validate machinery red-test witnesses` [class: IMPLEMENTATION_REQUIRED]
