# Plan: Execute-plan runtime r5 residuals + ambient-noise YAGNI trim

Backlog origins (scope of record):
`docs/history/backlog/2026-09-12-execute-plan-runtime-r5-remaining-residuals.md`
(r5 findings F-r5-1 through F-r5-9 plus one recorded out-of-lens observation) and
`docs/history/backlog/2026-09-11-ambient-noise-pattern-trim-yagni.md` (r2
F-r2-12). Review lineage:
`docs/reviews/2026-09-10-execute-plan-runtime-residuals-code-review-r5.md`
(origin of the nine residuals) and
`docs/reviews/2026-09-10-execute-plan-runtime-residuals-code-review-r2.md`
(origin of the trim item). Project guidelines:
`projects/.ai-playbook/agent_workflow_guidelines.md`; runtime language notes:
`scripts/test_execute_plan_runtime.py` is stdlib `unittest` with hermetic
fixture repositories, no external test framework.

## Terms

- **Machine manifest**: the JSON durable-state document the runtime driver owns (`runtime_state.json`); carries `workflow_state`, `tasks`, `claims`, `checkpoints`, `history`, and the terminal receipt.
- **Claim**: the per-task fence record (token, generation, owner, state, launch record) that proves which driver instance may mutate a task.
- **done-pending / commit-pending / checkpointed / complete / aborted**: durable task statuses; `done-pending` means a success checkpoint landed and the done handoff is next; `commit-pending` means the commit boundary is persisted while the commit is being produced or proven; `checkpointed`/`complete` are terminal; `aborted` is the explicit-stop state.
- **Progression guard**: `_claim_progressed_past_receipt`, the shared predicate that refuses late receipts whose claim or task already moved past the receipt boundary.
- **Refinement arm**: the `_checkpoint_retry_or_blocked` distinction (scripts/execute_plan_runtime.py, comment above the `progressed` conjunct): a terminal (`checkpointed`/`complete`) task with a live claim surfaces the raw actionable receipt instead of the stale-claim outcome, because nothing regressed.
- **Ambient-noise allowlist**: `AMBIENT_NOISE_PATTERNS`, consulted only by the pre-launch startup dirty-worktree gate to downgrade purely-ambient untracked dirt to the resumable `cleanup-required` outcome.
- **Launch record**: the per-claim snapshot (`baseline_revision`, generation, timestamp) written at launch; its presence, not file mtime, separates ambient noise from worker-caused changes after launch.
- **Wedge**: the r5-F2 stuck state: a `commit-pending` claim whose commit never landed (crash between `mark_commit_pending` and `git commit`); startup quarantines the claim as ambiguous, `record_done` blocks at the done-boundary checks (the done-evidence gate refuses the commit-pending handoff, and the commit-not-found branch behind it refuses a provable-commit handoff), and the progression guard refuses `abort`, so only manifest surgery exits.
- **Skill-gate marker**: the per-(project, session) consent file at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker` the plans skill refreshes before every plan-file write (recipe: `agents/hooks/skill-gate/README.md`); `project` derives via `facts_paths.resolve_project_key`, `session` via the `session_channel.py` subprocess (empty after strip means literal `no-session`, otherwise `sha1(value)[:16]`).
- **Session key**: the session identifier fed to the marker derivation, read VERBATIM from the shared `session_channel.py` subprocess; when empty, `--session-id` is omitted and the core keys `no-session`.

## Assumptions

- assume all three production call sites of `_claim_progressed_past_receipt` pass `include_terminal=True` (scripts/execute_plan_runtime.py lines 724, 855, 1814 at authoring time); folding the flag into the base set removes no live behavior; basis: grep over the module, 2026-09-13.
- assume only `ExecutePlanRuntimeTest#test_startup_ambient_noise_is_resumable_cleanup_required` builds an editor-swap fixture (`docs/.#notes.md`); every other ambient fixture uses the `.DS_Store` family; basis: grep over scripts/test_execute_plan_runtime.py, 2026-09-13.
- assume the archived runtime-residuals plan (`docs/plans/completed/2026-09-10-execute-plan-runtime-residuals.md`, Task 3 allowlist definition) is frozen history and is not edited by this plan; this plan is the amendment vehicle the trim item's precondition requires; basis: doc-hierarchy archived-state rule (an archived plan's body is never edited).
- assume no quotePath count is pinned in this plan: no task touches a git invocation site; the post-c188b39 baseline is four `core.quotePath=false` flagged sites in the runtime (verified 2026-09-13); basis: the origin item's re-baseline note, checked against the tree.
- assume `agents/skills/execute-plan/runtime-contract.md` is the source of truth for transition, receipt, and seeding prose; basis: contract header plus repo doc-hierarchy.
- assume the three runtime suites (`test_execute_plan_runtime.py` 118 tests, `test_runtime_capabilities.py`, `test_execute_plan_runtime_codex.py`) are the regression net; all three verified green at authoring time, 2026-09-13.

Decision points requiring a grill: r5-F1 fix shape = add the abort fence at the three success sites, not document-claim-scoped-completion-as-intended; source: origin first-listed fix direction, and five sibling receipt paths (`mark_commit_pending`, `_persist_blocked_claim_locked`, `_checkpoint_retry_or_blocked`, `claim_next_task`, `_mark_claim_launched`) already enforce the same global fence; date: 2026-09-13; affected sections: Task 1, Gist & Examples. r5-F2 fix shape = allow abort for commit-pending claims whose commit provably does not exist, not verify-commit-existence-at-`mark_commit_pending` and not an operator-scoped reset operation; source: origin third-listed fix direction, authoring decision under the 2026-09-13 standing pre-authorization (verify-at-write redefines the commit-pending window whose documented purpose is persisting the boundary before the commit is provable; a reset operation adds new CLI surface for a crash-window-only need while `abort` already owns the preserve-and-stop envelope; accepted residual: a transient git failure makes a live commit look wedged and the operator stop proceeds, which keeps the commit recoverable under preserve-and-stop); date: 2026-09-13; affected sections: Task 2, Gist & Examples, contract commit-pending row. r5-F9 = reword the seeding-boundary contract sentence, not enforce non-emptiness at create; source: origin first-listed option, the launch envelope already fails closed on empty scope (`validate_action_envelope` rejects empty `allowed_paths` after envelope construction), so create-time enforcement would duplicate the gate; date: 2026-09-13; affected sections: Task 7. Ambient-noise trim = trim to the `.DS_Store` family in this plan; source: origin suggested fix, whose plan-amendment precondition is satisfied by this plan as the amendment vehicle; date: 2026-09-13; affected sections: Task 8, Gist & Examples.

## Gist & Examples

This plan closes the execute-plan runtime's round-5 residual findings and one
YAGNI trim. Everything stays inside the existing durable-state model: no new
reason codes, no manifest-schema change, no new CLI operations.

**Abort-fence family (F-r5-1).** Trigger (today): the workflow is explicitly
aborted (an operator stops task A), and a success receipt for a different task
B with a still-live claim arrives afterward. Before (today): the three success
writers (`_checkpoint_success_commit`, `_record_done_locked`,
`_reconcile_commit_locked`) never consult `workflow_state`, so the late
success receipt persists a `done-pending` completion, a done handoff, or a
commit reconciliation onto the aborted workflow, contradicting the
"never persist" comments their sibling receipt paths carry. After (this
plan): each of the three sites consults the same global fence the five
sibling paths already enforce and returns the explicit-abort envelope with
nothing written; the manifest is byte-identical before and after the late
receipt.

**Wedge-exit family (F-r5-2).** Trigger (today): `mark_commit_pending`
persists the commit boundary, the process crashes before `git commit` runs,
and the commit never lands. Before (today): startup quarantines the claim as
an ambiguous live worker (`stale-claim`/`owner-mismatch`), `continue_parent`
propagates the block, `record_done` blocks at the done-boundary checks, and
the r4 progression guard refuses `abort` because `commit-pending` is a
progressed status; the only exit is manual manifest surgery. After (this plan): `abort`
with the still-current token proceeds when the task is `commit-pending` AND
its recorded commit provably does not exist (`commit_lookup` returns false),
producing the standard preserve-and-stop aborted envelope (task aborted,
claim aborted, workflow aborted); when the commit provably exists the guard
keeps refusing exactly as today. This is the r4 guard family's one deliberate
exception, documented in the guard comment and the contract's `commit-pending`
recovery cell.

**Witness and consistency family (F-r5-3, F-r5-6, F-r5-8).** The refinement
arm (a non-success receipt for a terminal task with a live claim surfaces the
raw actionable receipt) is intentional and commented, and existing coverage
reaches it only incidentally: no test pins its contract on a checkpointed
task with a live claim, in particular the no-persist dimension. This plan
pins it with a characterization witness plus a mutation probe (Task 3). `_record_activation_receipt`
checks token/generation before the abort fence while `_mark_claim_launched`
orders the same conditions oppositely; Task 6 hoists the abort check so one
interleaving cannot produce two different reason codes (today a mismatched
token on an aborted workflow yields `owner-mismatch` from the activation
fence but `explicit-abort` from the launch fence). The `abort` guard
comment's status list gains `commit-pending` (and names the wedge exception).

**Simplification family (F-r5-4, F-r5-5).** The `include_terminal` flag has
no `False` caller; it folds into the base predicate and the test matrix
shrinks to the post-fold truth table. The F-r4-9 pre-loop startup gate
duplicates the claim loop's two filters; one `examined` list is built and
iterated, with behavior pinned identical by the existing startup suite.

**Docs family (F-r5-7, F-r5-9).** The contract's receipt-rejection taxonomy
names three approval-receipt cross-check classes while the receipt-loading
path emits four explicit cross-check messages (a
config file that is not valid TOML is unlisted); the sentence is amended to
name the four explicit classes and to record that a config file holding
non-UTF-8 bytes surfaces the raw decode error, caught fail-closed at the CLI
boundary, without being a named cross-check class (Task 7). The seeding-boundary
sentence claims the non-empty `allowed_paths` requirement "is established at
seeding time", but `create` validates only each entry's shape and an empty
list seeds fine (the empty-scope gate fires later, at envelope authorization);
the sentence is reworded to match.

**YAGNI trim (F-r2-12).** Trigger (today): an untracked `docs/.#notes.md`
editor-swap file appears before any launch. Before (today): startup downgrades
it to the resumable `cleanup-required` outcome because
`AMBIENT_NOISE_PATTERNS` carries editor swap/lock patterns (`.#*`, `#*#`,
`*.swp`, `*.swo`, `*.swpx`, `*~`) that no run in this workflow has ever
produced; only the `.DS_Store` family has observed evidence. After (this
plan): the allowlist is the `.DS_Store` family (`.DS_Store`, `.DS_Store?`,
`._.DS_Store`); the same editor-swap file now keeps the hard non-resumable
`dirty-worktree` block, and the contract's ambient-noise paragraph drops the
editor-swap enumeration in the same pass. The archived runtime-residuals
plan's Task 3 allowlist definition is superseded by this amendment and stays
frozen as history.

Edge cases covered: a late success receipt for a foreign (not live) claim on
an aborted workflow keeps the `owner-mismatch` reason code (the fence sits
after the identity checks, mirroring `mark_commit_pending`); a
`commit-pending` task with a missing `commit_identity` field in a
hand-corrupted manifest still exits through the wedge path (empty identity
fails `commit_lookup`); a duplicate success receipt on an aborted workflow
returns the abort outcome rather than a `duplicate: true` success envelope
(the fence sits before the duplicate short-circuit, matching the retry path's
fence ordering); purely-ambient `.DS_Store` dirt keeps its resumable
`cleanup-required` outcome after the trim.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every late-receipt family has its own canary (three fence tests, wedge exit, wedge-guard hold, refinement arm) and each fence fix survives its per-site mutation probe; the r4 progression guard keeps refusing every progressed shape except the one unlocked wedge.
- consistency: one abort reason vocabulary; the activation fence orders conditions exactly as `_mark_claim_launched`; the contract's taxonomy sentence names exactly the classes `approval_policy_fingerprint` emits.
- simplicity: `include_terminal` is gone from code and tests; the startup gate and loop share one `examined` list; the allowlist carries exactly three entries.
- docs-contract: every contract sentence this plan edits matches observable code behavior; the taxonomy sentence names exactly the cross-check classes the approval-receipt loading path emits (`approval_policy_fingerprint` plus `load_approval_receipt`'s fingerprint comparison), and no contract sentence names a pattern class the code does not emit.
- test hygiene: every new test is given/expects self-contained, pins a gate-unique assertion, and runs hermetically (fixture repos, injected `commit_lookup`).

**Done when:**
- `python3 scripts/test_execute_plan_runtime.py`, `python3 scripts/test_runtime_capabilities.py`, and `python3 scripts/test_execute_plan_runtime_codex.py` all exit 0 with the new tests included.
- The `## Validation Commands` block runs green end to end on the final tree.
- The two origin backlog items are moved to `docs/history/backlog/completed/` with `Status: done` in the completion pass (registry rows appended), per the plans lifecycle.

**Ship when:**
- The next execute-plan run on any host picks up the fenced, trimmable runtime with no manifest migration; hosts need no re-activation because no inventory, profile, or adapter surface changed.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (named methods only: `_claim_progressed_past_receipt`, `_checkpoint_success_commit`, `_record_done_locked`, `_reconcile_commit_locked`, `abort`, `_record_activation_receipt`, `_reconcile_startup_locked`, `_persist_blocked_claim_locked` and `_checkpoint_retry_or_blocked` (Task 4 edits their `include_terminal=True` call sites), the `AMBIENT_NOISE_PATTERNS` constant, and the guard comment inside `abort`; all other methods in this file are frozen; reject any review finding that touches them)
- `agents/skills/execute-plan/runtime-contract.md` (named spans only: the approval-receipt cross-check sentence, the seeding-boundary sentence in the `create` paragraph, the ambient-noise paragraph, the `commit-pending` transition-table recovery cell; all other sections are frozen)

**Tests:**
- `scripts/test_execute_plan_runtime.py` *(edited: new witnesses plus the two reworked tests named in the tasks; all other tests are frozen except where a task explicitly rewrites them)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. The contract edits are listed above; a doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/2026-09-10-execute-plan-runtime-residuals.md`; frozen history (archived plan body is never edited); this plan's Gist records the supersession instead.
- `scripts/runtime_capabilities.py` and `scripts/execute_plan_runtime_codex.py`; the r5-F7 fix amends the contract sentence only; the code's four-class emission is the correct side and is read-only evidence here.
- `docs/history/backlog/` items other than the completion-pass move; history is immutable.
- The recorded out-of-lens observation (a stale `mark_commit_pending` write onto an already-`done-pending` task): the origin item records it as a behavior question for a future pass, not a finding; do not fix it here.

## Design Invariants (CR Guard)

- The r4 progression-guard family must not be weakened: `abort` stays refused for every progressed status and closed claim, with the single new exception from Task 2 (commit-pending plus provably missing commit). Rationale: r4 review round family sweep (origin r5 doc, mutator matrix section).
- The post-launch ambient-versus-worker discriminator stays launch-record presence, never mtime or path shape alone; the trim changes only which untracked names are pre-launch-tolerated. Rationale: archived plan Task 3 as qualified by r9 (origin trim item).
- No new reason codes: every outcome reuses the existing vocabulary (`explicit-abort`, `stale-claim`, `owner-mismatch`, `cleanup-required`, `dirty-worktree`). Rationale: runtime-contract reason-code section.
- The porcelain `-z` parsing and the four `core.quotePath=false` git invocation sites stay untouched. Rationale: post-c188b39 re-baseline note in the origin item; development_lessons rule on `-z` parsing.
- Identity checks precede the abort fence at the three success sites and `mark_commit_pending` (foreign claims keep `owner-mismatch`), while `_mark_claim_launched` and `_record_activation_receipt` (after Task 6) order abort first by their documented launch-window rationale. Rationale: r5-F6 and the existing `_mark_claim_launched` comment.

## Validation Commands

```bash
python3 scripts/test_execute_plan_runtime.py
python3 scripts/test_runtime_capabilities.py
python3 scripts/test_execute_plan_runtime_codex.py
bash scripts/check-no-em-dash.sh file docs/plans/2026-09-13-execute-plan-runtime-r5-residuals-yagni-trim.md agents/skills/execute-plan/runtime-contract.md
```

Structural gates (run from the repo root; each gate is fail-closed and
names its obligation; forbidden sweeps use fixed strings so the plan's own
text cannot satisfy them, and every swept path is a repo file, never this
plan):

```bash
must_match() { pat="$1"; shift; for f in "$@"; do
  test -f "$f" || { echo "missing target: $f" >&2; exit 1; }
  grep -qF -- "$pat" "$f" || { echo "required pattern missing: $pat in $f" >&2; exit 1; }
done; }
no_match() { pat="$1"; shift; for f in "$@"; do
  test -f "$f" || { echo "missing sweep target: $f" >&2; exit 1; }
  grep -qF -- "$pat" "$f"; rc=$?
  if test "$rc" -eq 0; then echo "forbidden pattern present: $pat in $f" >&2; exit 1
  elif test "$rc" -ge 2; then echo "grep error rc=$rc on $f" >&2; exit 1; fi
done; }
RT=scripts/execute_plan_runtime.py
RC=agents/skills/execute-plan/runtime-contract.md
TT=scripts/test_execute_plan_runtime.py
# Task 1: one abort fence per success site (three distinct evidence strings)
must_match "explicitly aborted before the success checkpoint" "$RT"
must_match "explicitly aborted before the done handoff" "$RT"
must_match "explicitly aborted before the commit reconciliation" "$RT"
# Task 2: the wedge exception and its contract cell
must_match "provably missing commit" "$RT"
must_match "provably does not exist" "$RC"
# Task 3: the refinement-arm witness exists by name
must_match "test_terminal_task_live_claim_surfaces_actionable_receipt" "$TT"
# Task 4: the dead flag is gone from production code
no_match "include_terminal" "$RT"
# Task 5: one examined list, loop no longer re-filters
must_match "examined = [" "$RT"
# Task 6: the activation-fence hoist witness exists by name
must_match "test_activation_receipt_aborted_workflow_beats_token_mismatch" "$TT"
# Task 7: the invalid-TOML class is named in the taxonomy sentence
must_match "not valid TOML" "$RC"
# Task 7: the seeding overclaim is gone (whole-contract sweep; the only hit today is the rewritten sentence)
no_match "established at seeding" "$RC"
# Task 8: the allowlist is the .DS_Store family, exactly three entries, no editor patterns
must_match '".DS_Store",' "$RT"
no_match "*.swp" "$RT"
count="$(sed -n '/^AMBIENT_NOISE_PATTERNS = (/,/^)/p' "$RT" | grep -c '"')"
test "$count" -eq 3 || { echo "AMBIENT_NOISE_PATTERNS must carry exactly 3 entries, found $count" >&2; exit 1; }
# Task 8: the contract ambient paragraph no longer enumerates editor swaps (both today-hits live in the rewritten paragraph)
no_match "editor swap files" "$RC"
no_match ".#*" "$RC"
# Task 8: the reworked startup test pins the post-trim hard block
must_match "test_startup_ambient_noise_is_resumable_cleanup_required" "$TT"
must_match "dirty-worktree" "$TT"
echo "structural gates: all green"
```

Authoring-time baselines recorded 2026-09-13 (the gates are RED-today and
flip GREEN exactly when their task lands): each of the three fence evidence
strings has 0 hits in the runtime today; `provably missing commit` has 0 hits
today; `include_terminal` has 6 hits today (signature, docstring, guard line,
three call sites); `examined = [` has 1 hit today and stays 1 after the
unification (the pin proves the list construction survives the refactor);
`not valid TOML` has 0 hits in the contract today; `established at seeding`
has 1 hit today; the allowlist block has 9 quoted entries today; `*.swp`
matches 2 runtime lines today (its own constant entry and the `*.swpx` entry,
which carries it as a fixed-string prefix; both inside the constant);
`editor swap files` has 1
contract hit today; `.#*` has 1 contract hit today; and the Task 6 witness
name `test_activation_receipt_aborted_workflow_beats_token_mismatch` has 0
hits in the test file today. The `.DS_Store?` entry
needs no separate pin: the three-entry count plus the `"`.DS_Store`",`
presence pin and the editor-pattern bans leave no room for a wrong family.

### Task 1: Abort-fence the three success-path writers (r5-F1)

Files:
- `scripts/test_execute_plan_runtime.py`
- `scripts/execute_plan_runtime.py`

- [ ] `ExecutePlanRuntimeTest#test_success_checkpoint_refuses_aborted_workflow`; given task-4 with a live launched claim (`seed_claim(task="task-4", token="seed-task-4")`) and `workflow_state` set directly to `aborted` in the manifest (simulating an abort that landed elsewhere while this claim stayed live), when `record_worker_checkpoint(worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))` runs, expects status `aborted`, reason_code `explicit-abort`, resume_allowed false, and no persist: task stays `pending` (the `seed_claim` fixture sets only the claim, not the task status), claim stays `launched`, `workflow_state` stays `aborted`, and no `task-4:worker-1` checkpoint record is written
- [ ] `ExecutePlanRuntimeTest#test_done_handoff_refuses_aborted_workflow`; given task-4's success checkpoint landed `done-pending` and `workflow_state` then set to `aborted`, when `record_done(done(task="task-4"))` runs, expects `aborted`/`explicit-abort` with no completion write: task stays `done-pending`, claim stays `launched`, and the task carries no `commit_identity` or `checkbox: True`
- [ ] `ExecutePlanRuntimeTest#test_commit_reconciliation_refuses_aborted_workflow`; given task-4 at `commit-pending` via `mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)` and `workflow_state` then set to `aborted`, when `reconcile_commit_before_checkpoint("task-4", "aa11bb22cc33", lambda _c: True, claim_token="seed-task-4", generation=0)` runs, expects `aborted`/`explicit-abort` with no reconciliation write: task stays `commit-pending`, claim stays `launched`, and no `task-4:commit` checkpoint exists
- [ ] Run → expect RED: `python3 scripts/test_execute_plan_runtime.py` fails exactly the three new tests (each late success write persists today), all pre-existing tests pass
- [ ] Add the fence at the top of `_checkpoint_success_commit` (before the prior-duplicate short-circuit; the caller `_record_checkpoint_locked` has already run the identity check, mirroring `mark_commit_pending`'s identity-then-abort order): `if manifest.get("workflow_state") == "aborted": return _abort_outcome(result["checkpoint_identity"], result["generation"], ["workflow was explicitly aborted before the success checkpoint"])` with the comment noting the same global fence the sibling receipt paths enforce
- [ ] Add the fence in `_record_done_locked` immediately after the `valid` gate and before the commit lookup: `if manifest.get("workflow_state") == "aborted": return _abort_outcome(checkpoint_identity, manifest.get("generation", 0), ["workflow was explicitly aborted before the done handoff"], action_scope="done-handoff")`
- [ ] Add the fence in `_reconcile_commit_locked` immediately after the owner-match check and before the evidence requirement: `if manifest.get("workflow_state") == "aborted": return _abort_outcome(f"{task_id}:commit", manifest.get("generation", 0), ["workflow was explicitly aborted before the commit reconciliation"], action_scope="done-handoff")`
- [ ] Run → expect GREEN: full suite passes including the three new tests
- [ ] Mutation probes (record in the task log, revert after each): delete the fence from `_checkpoint_success_commit` only and expect `test_success_checkpoint_refuses_aborted_workflow` to fail while the other two new tests still pass; repeat per site for the done-handoff and reconciliation fences
- [ ] Commit: `runtime: abort-fence the three success-path writers (r5-F1)`

### Task 2: Abort kill switch for the wedged commit-pending claim (r5-F2, r5-F8)

Files:
- `scripts/test_execute_plan_runtime.py`
- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] `ExecutePlanRuntimeTest#test_abort_exits_wedged_commit_pending_claim`; given task-4 at `commit-pending` (via `mark_commit_pending` exactly as in Task 1's reconciliation fixture) with commit identity `aa11bb22cc33` that provably does not exist (driver built with `commit_lookup=lambda _commit: False`), when `driver.abort("task-4", "seed-task-4")` runs with the still-current token, expects the abort to proceed: status `aborted`, reason_code `explicit-abort`, task status `aborted`, claim state `aborted`, `workflow_state` `aborted`
- [ ] `ExecutePlanRuntimeTest#test_abort_still_refuses_commit_pending_with_provable_commit`; given the same fixture shape but the driver's `commit_lookup` returning True, when `abort` runs with the current token, expects the r4 progression refusal (`blocked`/`stale-claim`, resume_allowed true) and state untouched: task stays `commit-pending`, claim stays `launched`, `workflow_state` stays `active`
- [ ] Run → expect mixed RED/GREEN: the wedged-exit test fails (today abort refuses the wedge too, because `commit-pending` is a progressed status), while the provable-commit hold test passes today (characterization: it pins the refusal the fix must keep); all pre-existing tests pass
- [ ] In `abort`, compute the wedge exception before the progression guard: `wedged = task is not None and task.get("status") == "commit-pending" and not self.commit_lookup(str(task.get("commit_identity") or ""))`, and gate the guard on it (`if not wedged and _claim_progressed_past_receipt(...)`); a missing/empty `commit_identity` on a hand-corrupted `commit-pending` task routes through the wedge path because an empty identity fails `commit_lookup` and the task is unreconcilable anyway
- [ ] Amend the progression-guard comment inside `abort` in the same commit (r5-F8): the status list gains `commit-pending` (matching the predicate and the sibling docstring) and the sentence names the wedge exception, for example: "the durable state stays untouched unless the claim is wedged (a commit-pending task with a provably missing commit), where the explicit stop is the only runtime exit"
- [ ] Amend the contract's `commit-pending` transition-table recovery cell (the row whose recovery action reads "Inspect the exact commit before deciding whether work is complete.") by appending one sentence: `Abort with the current token is permitted when the recorded commit provably does not exist (the wedged-claim runtime exit; preserve-and-stop).`
- [ ] Run → expect GREEN: full suite passes including both new tests (the hold test was green before and stays green after)
- [ ] Mutation probes (record in the task log, revert after each): probe A flips the wedge conjunct to `and self.commit_lookup(...)` and expects BOTH new tests to fail (lookup-True becomes wedged so the hold test's refusal is replaced by an abort; lookup-False stays guarded so the wedged test never exits); probe B drops the wedge term so the guard is unconditional and expects exactly one failure, the wedged test (the hold test still sees the refusal it pins)
- [ ] Commit: `runtime: abort kill switch for wedged commit-pending claims (r5-F2)`

### Task 3: Pin the terminal-task refinement arm (r5-F3)

Files:
- `scripts/test_execute_plan_runtime.py`

- [ ] `ExecutePlanRuntimeTest#test_terminal_task_live_claim_surfaces_actionable_receipt`; given task-4 seeded as a live launched claim (`seed_claim(task="task-4", token="seed-task-4")`) whose task is then set to `checkpointed` with `complete: True` in the manifest, when `record_worker_checkpoint(worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1", status="approval-required", reason_code="approval-required", action_scope="external-write:publish", evidence=["approval-request:publish"]))` runs, expects the raw actionable receipt surfaced: returned status `blocked`, reason_code `approval-required` (not `stale-claim`, not an abort), and no persist: task stays `checkpointed`, claim stays `launched`, no `worker-retry` or blocked-history event, no attempt checkpoint record
- [ ] Run → expect GREEN (characterization: pins existing behavior; the refinement arm at the end of `_checkpoint_retry_or_blocked` already returns the receipt for a terminal task)
- [ ] Mutation probe (record in the task log, revert after): collapse the refinement distinction by changing the stale-claim guard to `if progressed:` unconditionally, expect this test to fail (the receipt is swallowed by `stale-claim`), restore
- [ ] Commit: `runtime: pin the terminal-refinement-arm receipt witness (r5-F3)`

### Task 4: Fold include_terminal into the progression predicate (r5-F4)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [ ] Rewrite `ExecutePlanRuntimeTest#test_claim_progressed_past_receipt_include_terminal_matrix` as `test_claim_progressed_past_receipt_matrix` (drop every `include_terminal=` argument): given a live launched claim, expects statuses `done-pending`, `commit-pending`, `aborted`, `checkpointed`, `complete` all to progress (True), statuses `pending`, `claimed`, `launched`, `blocked` and a None task not to progress (False), and a closed claim to progress even with a None task; run → expect RED against the current signature
- [ ] Simplify `_claim_progressed_past_receipt`: remove the `include_terminal` keyword and the conditional union so the base set is exactly `{done-pending, commit-pending, aborted, checkpointed, complete}`; update the docstring to drop the flag sentence and keep the closed-claim rule
- [ ] Drop the `include_terminal=True` argument at all three call sites (the blocked-claim persistence guard, the retry-path `progressed` conjunct, and `abort`)
- [ ] Run → expect GREEN: full suite passes with the rewritten matrix test; `grep -c include_terminal scripts/execute_plan_runtime.py` prints 0
- [ ] Commit: `runtime: fold include_terminal into the progression predicate (r5-F4)`

### Task 5: One examined list in startup reconciliation (r5-F5)

Files:
- `scripts/execute_plan_runtime.py`

- [ ] Unify `_reconcile_startup_locked`: build the list with the construction `examined = [` (the launch-evidence claims whose task status is not in `{"done-pending", "checkpointed", "complete"}`) once, directly after the dirty-worktree gate, flatten the examined-empty block (the one whose comment begins "Every launch-evidence claim sits on a task the per-claim loop below skips") to fire on `if dirty_worktree and launch_evidence_claims and not examined:`, and iterate `for claim in examined:` in the per-claim loop with both `continue` filters removed; the earlier ambient return for a worktree with zero launch-evidence claims (the block commented "Hoisted no-live-claim case") stays in place unchanged; `launch_evidence_claims` stays the gate discriminator exactly as documented (a legacy manifest whose every launch-evidence claim sits on a completed task must still fire the gate)
- [ ] Characterization gate: the existing startup witnesses stay green unchanged, including `test_startup_ambient_noise_is_resumable_cleanup_required`, `test_startup_ambient_noise_without_live_claim_is_resumable_cleanup`, `test_blocked_claim_with_launch_record_and_ambient_noise_blocks_hard`, and every dirty-worktree quarantine test; run → expect GREEN (behavior-identical refactor; run the full suite, not just these names)
- [ ] Mutation probe (record in the task log, revert after): re-add the task-status `continue` inside the loop (double filter) and confirm the suite stays green (proving the refactor is behavior-preserving), then revert the probe
- [ ] Commit: `runtime: one examined list in startup reconciliation (r5-F5)`

### Task 6: Hoist the abort check in the activation-receipt fence (r5-F6)

Files:
- `scripts/test_execute_plan_runtime.py`
- `scripts/execute_plan_runtime.py`

- [ ] `ExecutePlanRuntimeTest#test_activation_receipt_aborted_workflow_beats_token_mismatch`; given task-4's live claim (`seed_claim(task="task-4", token="seed-task-4")`) and an explicit abort (`driver.abort("task-4", "seed-task-4")`), when the activation-receipt fence re-verifies a claim dict whose token does NOT match the live claim (`{"token": "stale-token", "generation": 0, "task_id": "task-4"}`) via `driver._record_activation_receipt(claim, "task-4", {"status": "success"})`, expects the abort outcome (`aborted`/`explicit-abort`, not `owner-mismatch`) and no `activation_receipt` persisted on the claim; today's identity-first ordering returns `owner-mismatch`, so this is the discriminating RED witness (the existing `test_activation_receipt_fence_refuses_aborted_workflow` arms use matching identities and stay green under either ordering)
- [ ] Run → expect RED: the new test fails (today the token/generation check precedes the abort check), all pre-existing tests pass
- [ ] Hoist the abort check in `_record_activation_receipt` above the token/generation check (mirroring `_mark_claim_launched`'s ordering and its launch-window rationale comment, "an explicit abort racing the launch window is an abort outcome, not an owner mismatch"); the claim-state check (`claimed`/`launched`) stays after both, so the stale-claim family still surfaces on an active workflow
- [ ] Run → expect GREEN: full suite passes including the new test and both arms of `test_activation_receipt_fence_refuses_aborted_workflow`
- [ ] Mutation probe (record in the task log, revert after): restore today's identity-first order and expect the new test to fail while both arms of the existing activation-fence test still pass; revert
- [ ] Commit: `runtime: abort first in the activation-receipt fence (r5-F6)`

### Task 7: Contract sentences match the code (r5-F7, r5-F9)

Files:
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] Amend the approval-receipt taxonomy sentence (the paragraph recording the two mandatory cross-check fields, sentence beginning "Loading the receipt re-reads...") to name the four explicit cross-check classes the code emits: `a missing or unreadable config file, a config file that is not valid TOML, an absent non-interactive approval policy, or a recomputed fingerprint that differs from the recorded policy_fingerprint` (keep the existing parenthetical that only the mismatch case names the fingerprint mismatch), and append one clause recording the decode shape without widening scope: `a config file holding non-UTF-8 bytes surfaces the raw decode error (UnicodeDecodeError, caught fail-closed at the CLI boundary) and is not a named cross-check class`
- [ ] Reword the seeding-boundary overclaim in the `create` paragraph: replace the clause "so the non-empty `allowed_paths` requirement that feeds the empty-scope fail-closed gate is established at seeding time" with: `entry validation at create covers each listed path's shape, while an empty allowed_paths list seeds successfully and fails closed later, at envelope authorization, where the empty-scope gate rejects it`
- [ ] Run → expect GREEN: the contract grep gates flip (`not valid TOML` present, `established at seeding` absent); run `python3 scripts/test_runtime_capabilities.py` as the doc-adjacent regression check
- [ ] Commit: `contract: name the invalid-TOML cross-check class and reword the seeding boundary (r5-F7, r5-F9)`

### Task 8: Trim the ambient-noise allowlist to the .DS_Store family (r2 F-r2-12 YAGNI)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] Rework `ExecutePlanRuntimeTest#test_startup_ambient_noise_is_resumable_cleanup_required`: the resumable arm places `.DS_Store` at the repo root plus `._.DS_Store` under `docs/` (both allowlisted) and still expects `cleanup-required` from `reconcile_startup` and `continue_parent`; the negative arm then writes `docs/.#notes.md` (an editor swap, no longer allowlisted) and expects the hard non-resumable `dirty-worktree` block; keep the existing tracked-modification arm unchanged; run → expect RED (today the editor swap is ambient and the negative arm's first step returns `cleanup-required`)
- [ ] Trim `AMBIENT_NOISE_PATTERNS` to exactly `(".DS_Store", ".DS_Store?", "._.DS_Store")` and drop the editor-swap comment line; run → expect GREEN on the reworked test
- [ ] Amend the contract's ambient-noise paragraph (the "Before launch only" paragraph) to define the allowlist as the `.DS_Store` family (` .DS_Store`, `.DS_Store?`, `._.DS_Store`), removing the editor-swap enumeration ("and editor swap files such as ... `*~`") and keeping every other sentence of the paragraph intact (the mtime-forgeability rule and the post-launch hard block are untouched)
- [ ] Audit the contract's `cleanup-required` transition-table row for editor-swap enumeration (expected outcome: the row names no patterns and needs no edit); record the audit outcome in the task log
- [ ] Record the supersession note in this plan's Gist (already written; no further edit): the archived runtime-residuals plan's Task 3 allowlist definition stays frozen as history
- [ ] Run → expect GREEN: full runtime suite plus the contract grep gates (`*.swp` absent from the runtime, `editor swap files` and `.#*` absent from the contract, allowlist count exactly 3)
- [ ] Mutation probe (record in the task log, revert after): re-add `".#*"` to the constant and expect the reworked test's negative arm to fail; revert
- [ ] Commit: `runtime: trim ambient-noise allowlist to the .DS_Store family (YAGNI)`

### Task 9: Final validation

Files:
- (none; validation only)

- [ ] Run the complete `## Validation Commands` block (three suites, em-dash scan, all structural gates) → expect every command green
- [ ] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py` (125 tests total: the suite carries 118 today, the plan adds seven new witnesses from Tasks 1, 2, 3, and 6, while Task 4's rename and Task 8's in-place rework are both net zero), `python3 scripts/test_runtime_capabilities.py`, `python3 scripts/test_execute_plan_runtime_codex.py`
- [ ] No commit; the tree is final for review
