# Plan: execute-plan driver residuals: re-cert survivors and quotePath dedupe

Backlog origins (scope of record; they move to `docs/history/backlog/completed/` only at this plan's execution completion):
- `docs/history/backlog/2026-09-11-execute-plan-runtime-residuals-recert-nonconvergence.md`
- `docs/history/backlog/2026-09-11-vrs-quotePath-pin-vs-worktree-entries-reuse.md`

Disposition authority for origin 1: `docs/reviews/2026-09-11-review-reconciliation-execute-plan-runtime-residuals.md` (r14 findings folded, dissolved, or superseded under the 2026-09-11 threat-model decision; the rider execution r15-r18 landed the folded ones).

## Terms

- Driver: `RuntimeDriver` in `scripts/execute_plan_runtime.py`, the durable task-transition owner.
- Manifest: the machine state JSON file a driver instance fences with the manifest lock.
- quotePath pin: the Validation Commands assertion counting `"-c", "core.quotePath=false"` git invocation sites in `scripts/execute_plan_runtime.py`.
- Disposition ledger: Task 1's fail-closed probe set verifying each origin-1 finding's recorded disposition is present in the execution-time tree.
- Threat-model boundary: the 2026-09-11 user decision deferring malicious same-user worker defenses (`docs/history/backlog/deferred/2026-09-11-deferred-malicious-worker-hardening.md`; guidelines section 64).

## Assumptions

- assume origin 1's r14 blocking findings F1-F5 and its non-blocking pendings are already dispositioned and landed (folded via the rider execution r15-r18, dissolved with the deferred mechanism, or superseded); this plan verifies those dispositions and does not re-implement them; basis: `docs/reviews/2026-09-11-review-reconciliation-execute-plan-runtime-residuals.md` plus direct probes of the tree on 2026-09-12.
- assume the quotePath count is 5 on the execution-time tree before Task 2 and drops to exactly 4 after the dedupe; basis: probe executed 2026-09-12 (count 5 on both the committed HEAD and the working tree) and origin 2's arithmetic.
- assume the count-5 pin in `docs/plans/2026-09-10-execute-plan-runtime-residuals.md` is that plan's history and is never edited (archived and completed plan bodies are immutable); this plan's Validation block carries the only live pin; basis: a repo-wide grep on 2026-09-12 found no live enforcement of the count-5 assertion outside that plan's Validation block (remaining matches are inert history copies in the origin backlog item, review staging, and execution task logs), and the plans lifecycle freezes archived bodies.
- assume `_git_changed_paths` preserves its documented contract "Returns `None` when either git witness fails" by catching the `RuntimeError` the delegated `_git_worktree_entries` raises when the status witness fails; basis: the method's docstring and its only caller's handling (the scope check maps `None` to `unavailable`).
- assume tests follow the repo's unittest discovery conventions; basis: the existing suites and the active runtime plan's Validation block.

Decision points requiring a grill: threat-model boundary: narrowed by user decision 2026-09-11, source `docs/history/backlog/deferred/2026-09-11-deferred-malicious-worker-hardening.md`, affects Design Invariants and Task 1 probes, recorded 2026-09-12; execution sequencing: this plan executes only after the runtime-residuals and guardrails executions have landed and archived, source the origin notes and `docs/tmp/future-plan-prompts-2026-09-12.md` Prompt 1, affects the Task 1 sequencing gate, recorded 2026-09-12; r14 pendings routing: folded pendings are verified as landed and mechanism-served pendings are dropped, source `docs/reviews/2026-09-11-review-reconciliation-execute-plan-runtime-residuals.md`, affects the Task 1 ledger, recorded 2026-09-12.

## Gist & Examples

Origin 2 contributes the one code change. Origin 1 contributes a verification ledger, not code.

**Before (today):** the done-boundary scope check calls `_git_changed_paths(baseline)` after each adapter window. That method runs two git witnesses of its own: `git diff --name-only <baseline>` for tracked changes, plus its own re-inlined `git status --porcelain -z --untracked-files=all` for untracked files, parsed by the shared `_parse_porcelain_z` helper. The re-inline exists only because the authoring plan of the already-landed runtime-residuals work pinned exactly 5 quotePath invocation sites, and reusing `_git_worktree_entries` would have broken that pin mid-review. Backlog item `2026-09-11-vrs-quotePath-pin-vs-worktree-entries-reuse.md` records the duplication as the cheaper evil at the time and prescribes exactly this dedupe once the pin could be re-derived.

**After (this plan):** `_git_changed_paths` delegates its untracked witness to `_git_worktree_entries` (identical argv, identical shared parser), wraps the delegated call so a status-witness failure still returns `None`, and the invocation count drops to 4. This plan's Validation block pins 4 and is the only live pin. Origin 1 adds no code: the 2026-09-11 reconciliation dispositioned every r14 finding, and the rider execution (r15-r18, squash on main) landed the folded ones. Task 1 verifies each recorded disposition on the execution-time tree and aborts with a drift report on any mismatch; it never re-implements dissolved machinery, because doing so would reintroduce the deferred anti-adversarial apparatus against the recorded threat-model decision.

**Happy path example:** a worker commits a baseline, then adds tracked edit `t.txt` and untracked `notes.txt`. Before: `_git_changed_paths(baseline)` returns `["notes.txt", "t.txt"]` via two subprocess calls it owns. After: the same list, with the status witness delegated (exactly one `_git_worktree_entries` call).

**Edge case example:** the status witness fails (non-zero git exit). Before: `_git_changed_paths` returns `None` and the scope check reports `unavailable`. After: `_git_worktree_entries` raises `RuntimeError`, the wrapper catches it and returns `None`; the observable contract is unchanged.

**Why verify-only for origin 1:** the driving principles are efficiency, token usage, simplicity, then code quality, with no net machinery growth without a demonstrated cost in the origins. The reconciliation record plus the HEAD probes on 2026-09-12 show no surviving code cost: F1's fixture wording is gone (no `codex-only` anywhere; approval fixtures present in both suites), F2's sweep is deferred with its mechanism and the adjacent `{path}.lock` lockfile is landed, F3's non-reentrant lock with fresh post-window re-read and `stale-claim` conflict outcome is landed with suite coverage, F4's token file does not exist, and F8's receipt contract line is documented in `load_approval_receipt`. Pendings that only served the deferred mechanism (seed-token modes, crash-window digest staging) stay dropped; the selftest HOME pin is admitted as a Validation-block pin in this plan; the receipt classification and selftest-case folds are verified as landed.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the two new tests pass and both suites stay green; the union result and the `None` contract are behaviorally identical before and after (the delegation spy and the raise-patch witness discriminate exactly the delegation and failure-contract changes)
- simplicity: net-zero machinery growth; one re-inlined invocation deleted, one delegated call and one except path added, two tests added; no new functions, fields, or gates
- drift-safety: Task 1's ledger is fail-closed; any span or count mismatch aborts execution with a drift report instead of an improvised mid-run adaptation
- maintainability: the porcelain status invocation has exactly one owner (`_git_worktree_entries`); the live count pin exists only in this plan's Validation block

**Done when:**
- every checklist item is checked
- the full Validation Commands block exits 0 on the execution-time tree
- Task 1's ledger completed all-green and its result is recorded in the task log

**Ship when:**
- the runtime-residuals execution (`docs/plans/2026-09-10-execute-plan-runtime-residuals.md`) and the guardrails execution (`docs/plans/2026-09-11-execute-plan-runtime-guardrails.md`) have landed and archived before this plan's execution starts; Task 1's sequencing gate proves this at run time
- at execution completion, the plan-completion archive pass (plans lifecycle) moves both origin backlog items to `docs/history/backlog/completed/` marked `Status: done` and appends one registry row per item; no plan task performs the move

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (method `_git_changed_paths` only; all other methods and module-level code are frozen; reject any finding that touches them)

**Tests:**
- `scripts/test_execute_plan_runtime.py` (new content only; the two new tests appended to `ExecutePlanRuntimeTest`; all existing tests are frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/2026-09-10-execute-plan-runtime-residuals.md`; in-flight peer execution plan, archived history after landing; its count-5 Validation pin is superseded by this plan's pin and is never edited
- `scripts/test_execute_plan_runtime_codex.py`; regression-only surface, no edits planned (findings there predate this plan; track separately)
- `scripts/runtime_capabilities.py`; probe target only, no changes planned

## Design Invariants (CR Guard)

- Threat-model boundary (user decision 2026-09-11): the anti-adversarial apparatus stays deferred. The out-of-tree anchor, seed tokens, sibling sweeps, TOFU migration, and their reason codes, fixtures, and witnesses must not be reintroduced by implementation or review; they live in `docs/history/backlog/deferred/2026-09-11-deferred-malicious-worker-hardening.md`. Rationale: the r9-r14 non-convergence was manufactured by inventing mechanism inside plan prose; the deferral is the recorded decision (reconciliation root cause; guidelines section 64).
- The non-reentrant manifest lock with fresh post-window re-read stays exactly as landed by the rider execution (r15-r18); the dedupe must not alter locking or any locked method.
- `_git_changed_paths` keeps its documented `None` contract; its only caller fails closed to `unavailable`.
- Archived and completed plans are immutable: the superseded count-5 pin is never edited anywhere; this plan's Validation block is the single live pin.
- Gate coverage (the r14 F5 rule, re-admitted for this plan): any task whose edit touches a suite runs that suite in its own gates.

## Validation Commands

Run from the repository root. The block exits 1 on the first failed check.

```bash
run_check() { "$@" || { echo "VALIDATION FAILED: $*"; exit 1; }; }
expect_absent() {
  pattern="$1"; file="$2"
  test -f "$file" || { echo "missing file: $file"; exit 1; }
  rc=0; grep -qE "$pattern" "$file" || rc=$?
  if [ "$rc" -eq 0 ]; then echo "forbidden pattern present in $file: $pattern"; exit 1
  elif [ "$rc" -ge 2 ]; then echo "grep error rc=$rc on $file"; exit 1; fi
}
# Both suites: the driver suite carries the plan's edits; the codex suite is
# the shared-fixture regression the canonical scope surface names.
run_check python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'
# Selftest under the HOME pin (r14 pending F6, admitted as a validation-block pin).
run_check env HOME="$(mktemp -d)" python3 scripts/execute_plan_runtime.py --selftest
# quotePath pin at the post-dedupe count. The [.] escape is intentional
# (self-match immunity for the embedded pattern); do not normalize it.
run_check python3 -c 'import pathlib,re; t=pathlib.Path("scripts/execute_plan_runtime.py").read_text(); n=len(re.findall(r"\"-c\",\s+\"core[.]quotePath=false\"", t)); assert n == 4, n'
# Dissolved-machinery guard: the deferred apparatus stays absent from the driver.
expect_absent "seed[_ ]token|sibling sweep|TOFU" scripts/execute_plan_runtime.py
expect_absent "codex-only" scripts/test_execute_plan_runtime.py
expect_absent "codex-only" scripts/test_execute_plan_runtime_codex.py
```

### Task 1: Phase 0 drift re-verification and disposition ledger (read-only)

This task is read-only: probes only, no file edits, no commit; nothing to add to the Review Scope inventory.

Run each probe from the repository root; any failure aborts execution with a drift report (do not adapt the plan mid-run; a drifted tree needs a fresh authoring pass).

- [ ] Sequencing gate: for each of `2026-09-10-execute-plan-runtime-residuals` and `2026-09-11-execute-plan-runtime-guardrails`, `docs/plans/<name>.md` does not exist and `docs/plans/completed/<name>.md` does; on failure report `SEQUENCING: prior execution not landed` and stop
- [ ] Pre-dedupe count baseline: `python3 -c 'import pathlib,re; t=pathlib.Path("scripts/execute_plan_runtime.py").read_text(); n=len(re.findall(r"\"-c\",\s+\"core[.]quotePath=false\"", t)); assert n == 5, n'`; a mismatch is count drift; stop and report
- [ ] Non-reentrant lock landed: `grep -q "deliberately non-reentrant" scripts/execute_plan_runtime.py` (span verified unique on 2026-09-12)
- [ ] Locked-conflict stale-claim landed: `grep -A10 "def _locked_mutation" scripts/execute_plan_runtime.py | grep -q "manifest mutation is held by another owner"`
- [ ] Fresh post-window re-read landed: `grep -A2 "def _record_done_locked" scripts/execute_plan_runtime.py | grep -q "load_manifest(self.manifest_path)"`
- [ ] Receipt contract line landed: `grep -q "anything else fails closed" scripts/runtime_capabilities.py` (span verified unique on 2026-09-12)
- [ ] Approval fixtures in both suites: `grep -q "approval" scripts/test_execute_plan_runtime.py` and `grep -q "approval" scripts/test_execute_plan_runtime_codex.py`
- [ ] Dissolved-machinery guard (all clean today, rc 1 on 2026-09-12): with the `expect_absent` helper from the Validation Commands block, `expect_absent "seed[_ ]token|sibling sweep|TOFU" scripts/execute_plan_runtime.py`, `expect_absent "codex-only" scripts/test_execute_plan_runtime.py`, `expect_absent "codex-only" scripts/test_execute_plan_runtime_codex.py`
- [ ] Record the ledger result (all-green probe list) in the task log

### Task 2: RED then GREEN: dedupe `_git_changed_paths` onto `_git_worktree_entries`

Files:
- `scripts/test_execute_plan_runtime.py` (two new tests in `ExecutePlanRuntimeTest`)
- `scripts/execute_plan_runtime.py` (`_git_changed_paths` only)

- [ ] `ExecutePlanRuntimeTest#test_changed_paths_delegates_to_worktree_entries`; given a committed baseline from `self.commit_file()`, an untracked file `notes.txt`, and a call-counting wrapper patched over the driver instance's `_git_worktree_entries` (the wrapper records one count per call and delegates to the original), expects `_git_changed_paths(baseline)` returns `["notes.txt"]` and the wrapper recorded exactly 1 call
- [ ] `ExecutePlanRuntimeTest#test_changed_paths_returns_none_when_status_witness_raises`; given `_git_worktree_entries` patched with `side_effect=RuntimeError("git status witness failed")` and a valid committed baseline from `self.commit_file()`, expects `_git_changed_paths(baseline)` returns `None` and does not raise
- [ ] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime.py'`; exactly the two new tests fail (the spy records 0 calls today because `_git_changed_paths` runs its own status invocation, and the patched-raise method is never invoked so the `None` assertion fails); every pre-existing test passes. RED-today basis: the 2026-09-12 source performs no delegation on either the committed HEAD or the working tree
- [ ] Implement: in `_git_changed_paths`, delete the re-inlined status invocation and its parse loop; obtain the status entries via `self._git_worktree_entries()` inside `try` / `except RuntimeError` and `return None` on the except path; keep the sorted-union return and the docstring contract unchanged
- [ ] Run → expect GREEN: the same discovery command passes with the two new tests green and no pre-existing regressions
- [ ] Commit: `refactor: dedupe the porcelain status invocation through _git_worktree_entries (quotePath pin 5 to 4)` with both files in one commit

### Task 3: final validation sweep

This task is read-only: it runs the Validation Commands block; no file edits, no commit.

- [ ] Run the entire Validation Commands block → expect exit 0: both suites green, the HOME-pinned selftest green, the quotePath pin green at 4, and all three dissolved-machinery sweeps clean
