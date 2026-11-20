# Plan: Handoff reconciler scope-drift recovery and dead-drift mapping prune

Authoring claim: 2026-10-31-handoff-reconciler-dead-drift-mappings.md (session sess_939f5b42-9671-4d9b-8535-93b6ae8366f1)

Backlog origin: docs/history/backlog/2026-10-31-handoff-reconciler-dead-drift-mappings.md
Driving force: code-quality (primary), efficiency (secondary)
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-handoff-reconciler-dead-drift-mappings-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3h total, largest task 1.5h
Executed: yes (0f19aee5feda647db428d9efd0910cf9a5832913)

## Terms

- Reconcile helper: `scripts/reconcile_execute_plan_handoff.py`, the receipt validator that applies one atomic per-task `runtime_state.json` replacement; after this plan it hosts two receipt-backed transitions and one read-only effect-evidence capture command.
- done-pending: a task record status meaning an accepted worker completion is recorded terminal while the task boundary is not yet committed.
- terminal receipt: `tasks[task_id].terminal_receipt`, the accepted-worker completion evidence the parent records at acceptance time.
- effect evidence: the terminal receipt's `effect_evidence` map, per changed path the post-acceptance raw-byte digest or lowercase `absent`; the read-only capture command resolves under the repository root before reading and accepts only regular readable files. Only a genuine missing path maps to `absent`; escaping or dangling symlinks, directories, unreadable paths, and non-regular targets refuse before a state write. Use the helper's shared digest and path resolver.
- effect: the accepted worker's source change for one changed path, decidable from the effect evidence plus the current worktree bytes.
- task-scope digest: sha256 of the complete task section with every `[ ]`/`[x]` marker normalized to `- [#]`, derived with the helper's `task_scope_digest`.
- task-scope-changed: the helper refusal when the launched scope digest differs from the current normalized section digest.
- projection-complete: the recovery-specific refusal when the reviewed bytes leave the task projection fully checked, the mirror of the reconcile path's `projection-incomplete`.
- launch-scope-unrecorded: the recovery-specific refusal for a legacy record without `tasks[task_id].task_scope_digest`, the mirror of the reconcile path's `launch-scope-unverified`.
- scope-drift recovery: the new `recover-scope-drift` operation that requeues a done-pending task against current reviewed scope when every changed path classifies absent or neutral; named with the scope-drift qualifier everywhere because the execution contracts already call the reconcile operation the receipt-backed recovery.
- effect_baseline: the new additive task-record field recorded at the pre-prompt write beside the task-scope digest, per declared path the path's launch-baseline content digest (or the literal `absent`), the declared set being the task's `Files:` entries as of the pre-prompt write; the sole baseline source the recovery's absent-cell comparison consumes, the acceptance producer records no baseline half at all (the post-only map needs none), so no acceptance-time baseline transcription exists to mis-capture.
- effect probe: the per-path comparison of current worktree content against `effect_baseline`'s recorded baseline digest and the effect evidence's recorded post digest, evaluated as one total ordered procedure with verdict strings pinned to the bare forms `absent`, `present`, `evolved`, `neutral`: a missing current path compares as the literal `absent`; when the recorded baseline equals the recorded post (one digest, whatever its form), current equal to that one digest means neutral and anything else means evolved; when baseline differs from post, current equal to post means present, current equal to baseline means absent, anything else means evolved. The procedure decides every corner cell deterministically: a deleted-then-rebase-lost file (baseline digest, post `absent`, current missing) means present, the deletion survived; a declared-but-never-created path (both halves `absent`, current missing) means neutral; a net-zero reverted edit (baseline equals post, current matches) means neutral.
- park: the fail-closed outcome that preserves the state and terminal-receipt bytes unchanged and hands the decision to the operator through the named refusal.
- origin row: docs/history/backlog/2026-10-31-handoff-reconciler-dead-drift-mappings.md.
- scope_recovery receipt: the new additive task-record field storing the recovery's identity receipt (run and plan identity, task identity, generation binding, the prior launched scope digest, the recovered current scope digest, the worker-receipt digest, the effect verdicts, the review evidence, and the projection, nine field groups; this entry is the single enumeration of the receipt's field set that the re-read's reason map and its static key-coverage regression pin).
- generation: the `runtime_state.json` integer every parent-owned write advances by one; the compare-and-swap anchor.
- execution claim: `docs/tmp/execution-claims/<slug>.md`, binding the plan to its owning session.
- drift mappings: `DRIFT_REASON_BY_FIELD`, naming the refusal class for each between-reads receipt-field change.

## Why

The 2026-11-10 witnessed run stopped at the helper's `task-scope-changed` refusal: an accepted worker's source effect was lost in a rebase while reviewed corrections changed the task section, and no supported continuation existed. Manual state edits and completed-worker relaunches stay prohibited, so the run consumed a separately recorded operator-authorized recovery. This plan adds the smallest receipt-backed route for exactly that case and prunes the drift mappings control flow proves unreachable.

## Gist & Examples

TLDR: Adds the receipt-backed `recover-scope-drift` operation to the done-pending handoff helper and prunes the two drift mappings no control flow can reach, so the witnessed rebase-lost accepted completion requeues against the current reviewed scope without operator hand-spawns; requeue requires every changed path to classify absent or neutral (a neutral path's current bytes match its baseline-equals-post digest); driving force code-quality.

Today the helper refuses `task-scope-changed` and stops. After this plan, when the reviewed bytes leave the task incomplete for the loop to reselect and every changed path classifies absent or neutral under the probe's ordered procedure, one invocation requeues the task: status back to `pending`, the current scope digest recorded, the recovery receipt stored under a new additive field, the original terminal receipt preserved verbatim, generation advanced once. Any present or evolved effect, a fully-checked or checklist-less reviewed section, an empty evidence map, an unrecorded baseline, or an escaping receipt path parks without mutation (the Task 3 vocabulary is the authoritative refusal set). The two mappings for fields that derive from immutable constructor arguments (`task_id`, `plan_task`) are removed with the proof recorded beside them; `plan_path` keeps its mapping because its derivation consults the filesystem.

## Outcome

An accepted done-pending completion whose reviewed task scope changed, whose reviewed bytes leave the task reselectable, and whose every changed path classifies absent or neutral requeues safely through one atomic state transition.

- `task-scope-changed` stays the fail-closed default of the ordinary reconcile path: its reason code, mutation behavior, and refusal/no-mutation outcomes stay identical, the evidence line's remedy sentence being the one amended surface.
- Effect present or evolved, a fully-checked or checklist-less reviewed section, an empty evidence map, an unrecorded baseline, or an escaping receipt path parks without mutation, never requeues; every park input names its decided cell (present, evolved, projection-complete, empty-map refusal, baseline-unrecorded refusal, escape refusal), so no undecidable input reaches the operation.
- Two proven-unreachable drift mappings are removed and the reachable set keeps every named refusal class.
- The loop and contract docs route the witnessed refusal to the scope-drift recovery once, with park-on-refusal semantics.
- Follow-up disposition: none anticipated; the eight sibling concerns keep their existing origin rows and this plan creates no new follow-up surface, it extends one existing sibling row's watchlist line (cas-reread-window) in place.

Gate delta: adds one receipt-backed recovery operation and two task-record fields, priced by the origin-cited no-exit reason in `docs/history/backlog/2026-10-31-handoff-reconciler-dead-drift-mappings.md`; adds one read-only path-safe effect-capture command in the existing helper so baseline and post-evidence producers share a checked digest map; removes two unreachable refusal mappings and extends one existing CAS watchlist row; adds no gate or state-writer.

## Assumptions

- assume the pre-launch record shape is `status` `pending` with `checkbox` false; basis: the run fixture's status vocabulary and non-done-pending status matrix in `scripts/test_reconcile_execute_plan_handoff.py` (fixture lines 209 and 432).
- assume the effect evidence composes with the parent's two existing writes once this plan amends them: today the pre-prompt write records only `tasks[task_id].task_scope_digest` (implementation-loop Step 1.2 duty), so Task 3 amends that duty to record the declared-path launch-baseline digest map in the new additive field `effect_baseline` beside it, and the acceptance write records the changed paths' post-acceptance digests in the terminal receipt's `effect_evidence` map, post-only with no baseline half recorded (runtime-contract Done-pending producer side); without the amended pre-prompt duty the recovery's baseline half has no producer and every real recovery would park, so the amendment is load-bearing; the recovery reads only recorded bytes and runs no git subprocess beyond the existing claim gate.
- assume the effect probe's four-cell partition is conservative by construction: any present or evolved path parks, so dirty residue, later edits, and partially lost effects all park; basis: the origin row prices a false source-absence judgment as duplicated or overwritten landed work.
- assume requeue deliverability requires the reviewed bytes to leave the task incomplete (at least one unchecked checklist line), because the loop reselects tasks only from plan checkboxes; a fully-checked reviewed section refuses `projection-complete` and parks; basis: implementation-loop Step 1.1 selection rule and Phase 2 entry; the origin's no-plan-edit constraint blocks an uncheck remedy inside the route.
- assume legacy records without `tasks[task_id].task_scope_digest` refuse the recovery fail closed (`launch-scope-unrecorded`); basis: the origin row requires an explicit current-scope digest and forbids relaunching the same completed worker identity.
- Shared-surface sibling dispositions, all separate origins, each keeping its own row (the decision grounded in the origin row's Cluster line for the per-residual scope note and the dispatch entry's scope-arm item, docs/history/backlog/PLAN-PROMPTS.md entry handoff-scope-refusal-source-effect-recovery, scope arm 5, for the explicit separation): cas-reread-window (watchlist row extended by this plan, Task 4 amending the row's Watchlist line in place: the recovery's worktree-byte probe surface is a new between-reads input class the reconcile path never reads, keyed to any claim-unfenced writer rather than only a second caller of the same operation, the re-read-to-replace residual window joining the same row), env-hermeticity (test-harness env pinning for the existing harness; the new operation runs no git subprocess beyond the existing claim gate), reread-contract-shape (contract-shape robustness of the existing reconcile paths; this plan's prune stays safe by the static-field proof recorded in Task 1), span-rule-docstring (docstring claim fix on existing text; Task 3 refreshes the module docstring for the second operation only), uppercase-checkbox (projection regex defect outside this plan's surfaces), launch-digest-pinning (writer-side legacy `plan_digest` pinning), outcome-contract-row (contract row declaration for the tool), reviews-dir-facts-resolution (reviews dir resolution through facts).

Decision points requiring a grill: effect-evidence mechanism: receipt digest-pair partition chosen over boundary-commit and receipt-shape-guessing designs, the done-pending task having no boundary commit of its own while the receipt is the only acceptance-time evidence surface the contract defines (r1 finding F2, five-worker convergence; 2026-11-13; Tasks 2-3); requeue deliverability: projection-complete refusal admitting only loop-reselectable reviewed bytes over post-recovery uncheck or explicit re-selection wiring, both blocked by the origin's no-plan-edit constraint or new machinery (r1 finding F1; 2026-11-13; Task 2); sibling dispositions: all eight separate with per-sibling reasons (origin row Cluster line and dispatch entry scope arm; 2026-11-13; Assumptions); drift-prune scope: exactly the two argument-derived static mappings, both derivations reading the same immutable constructor args so the fields cannot differ, `plan_path` retained for its filesystem-consulting derivation (r1 finding F10; 2026-11-13; Task 1).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the focused reconciliation suite passes with no existing test-definition lines removed (enforced by the removed-existing-test-definitions validation command; the command proves the narrower definition-removal invariant, not byte-identity of test bodies) and the new prune and recovery regressions green.
- preservation: a successful recovery leaves the original terminal receipt and every unrelated task record byte-identical.
- fail-closed posture: every modeled refusal and tool error leaves the state bytes unchanged; present or evolved evidence never requeues, and the new write-failure cell enforces the posture for the recovery's own replace path, not just the sibling reconcile path.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_reconcile_execute_plan_handoff.py -q` exits 0.
- `python3 scripts/reconcile_execute_plan_handoff.py --help` exits 0 (metadata exit).
- The pruning proof regression, the recovery refusal matrix, and the four-cell partition regressions exist and pass under the focused suite.
- The recovery end-to-end cell shows the requeued task re-entering the loop's selection contract (unchecked plan lines) with the documented done-pending-status detection no longer reporting it.
- Task 3's orchestrator-run acceptance evidence records both ordinary-path acceptances and their state transitions, leaving the preserved run state untouched.

**Ship when:**
- none; this plan has no external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reconcile_execute_plan_handoff.py` (Task 1)
- `scripts/reconcile_execute_plan_handoff.py` (Task 2)
- `scripts/reconcile_execute_plan_handoff.py` (Task 3)
- `scripts/reconcile_execute_plan_handoff.py` (Task 5)

**Tests:**
- `scripts/test_reconcile_execute_plan_handoff.py` (Task 1)
- `scripts/test_reconcile_execute_plan_handoff.py` (Task 2)
- `scripts/test_reconcile_execute_plan_handoff.py` (Task 3)
- `scripts/test_reconcile_execute_plan_handoff.py` (Task 5)

**Documentation:**
- `agents/skills/execute-plan/runtime-contract.md` (Task 4)
- `agents/skills/execute-plan/implementation-loop.md` (Task 4)
- `docs/history/backlog/2026-10-31-handoff-reconciler-cas-reread-window.md` (Task 4) watchlist line extension in place

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py`; retained driver-owned runtime, untouched by this plan.
- `scripts/OUTCOME_CONTRACT.md`; the tool's contract row is the outcome-contract sibling's own scope.
- The eight shared-surface sibling concerns: cas-reread-window, env-hermeticity, reread-contract-shape, span-rule-docstring, uppercase-checkbox, launch-digest-pinning, outcome-contract-row, reviews-dir-facts-resolution; each keeps its own origin row per the recorded dispositions.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_reconcile_execute_plan_handoff.py -q
python3 scripts/reconcile_execute_plan_handoff.py --help
bash scripts/scan-public-hygiene.sh
python3 -c 'import pathlib,re; roots=[pathlib.Path("scripts/reconcile_execute_plan_handoff.py"),pathlib.Path("agents/skills/execute-plan")]; files=[p for root in roots for p in ([root] if root.is_file() else root.rglob("*")) if p.is_file()]; assert not any(re.search(r"(?<!scope-recovery-)task-identity-drift",p.read_text()) for p in files)'
git diff <base-branch> -- scripts/test_reconcile_execute_plan_handoff.py | grep -c "^-.*def test_" || true
```

The first command is the plan's primary gate: the full reconciliation suite, existing regressions unchanged. The Python assertion is the contract-removal check: after Task 1 the unqualified `task-identity-drift` class appears nowhere in the helper or execution docs; the qualified `scope-recovery-task-identity-drift` remains intentional. The focused suite also checks both parent evidence producers against `capture-effect-evidence` and its refusal-before-state-write contract. The `grep -c` command (with `|| true` so its zero-match exit status does not trip a `set -e` runner) is the existing-test-definition-removal enforcement: it must print 0 (no existing test-definition lines removed); `<base-branch>` resolves to the plan-freeze base (main at freeze commit 9344a5ff8), and the executor verifies that resolution before trusting the printed 0, since an empty diff from a mis-resolved base would print 0 vacuously. The hygiene scan runs over the changed set before each commit.

### Task 1: Prune the proven-unreachable drift mappings

Context surface: the plan's Terms, this task, and the prune proof recorded beside the mapping.

Files:
- `scripts/reconcile_execute_plan_handoff.py`
- `scripts/test_reconcile_execute_plan_handoff.py`

Primary class anchors:
- `HandoffReconciler` in `scripts/reconcile_execute_plan_handoff.py`

- [x] `DRIFT_REASON_BY_FIELD` keeps exactly the mutable-field mappings: given a between-reads change in any of `expected_generation`, `run_session_id`, `plan_path`, `plan_digest`, `worker_receipt_digest`, `review`, expects the same named refusal class as before [class: IMPLEMENTATION_REQUIRED]
- [x] Precedence-witnessed kept mappings: `plan_slug`, `task_scope_digest`, and `checkbox_projection` keep their mappings, witnessed by the refusal precedence instead of a direct per-field injection, a plan-section or plan-identity change fires the plan-digest refusal earlier in the identity order (the canonical-slug plan-identity check for `plan_slug`), with that precedence reason recorded in the same proof text [class: IMPLEMENTATION_REQUIRED]
- [x] `task_id` and `plan_task` mappings removed: given the post-prune mapping set, expects every remaining `DRIFT_REASON_BY_FIELD` key to be mutable-field-derived and the two removed keys to be absent from the table, both fields deriving from immutable constructor args so no drift lookup can ever index them [class: IMPLEMENTATION_REQUIRED]
- [x] `plan_path` mapping retained: given its stable-identity derivation consulting the filesystem per derivation, expects the mapping kept with that reason recorded beside the mapping [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given every existing drift regression rerun unchanged, expects identical refusal reason codes and evidence lines [class: REPOSITORY_TEST]
- [x] Run → expect RED: the static-field equality proof regression fails against the pre-prune mapping set [class: REPOSITORY_TEST]
- [x] Write the prune with the recorded proof [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: prune handoff reconciler drift mappings control flow proves unreachable` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Receipt-backed scope-drift recovery admission and refusal gates

Context surface: the plan's Terms, this task, and `## Standing constraints` when present.

Files:
- `scripts/reconcile_execute_plan_handoff.py`
- `scripts/test_reconcile_execute_plan_handoff.py`

Primary class anchors:
- `HandoffReconciler` in `scripts/reconcile_execute_plan_handoff.py`

- [x] `recover-scope-drift` refuses scope-unchanged: given a done-pending task whose launched digest equals the current section digest, expects refusal `scope-unchanged` naming the ordinary reconcile operation, no mutation [class: IMPLEMENTATION_REQUIRED]
- [x] Requeue deliverability admission: given reviewed bytes whose task projection is fully checked, expects refusal `projection-complete` (the loop cannot reselect the task) parking without mutation; a reviewed section with no recognizable checklist lines also refuses `projection-complete` (the loop can never reselect it, the degenerate cell is fail-closed); given reviewed bytes leaving at least one unchecked line, expects the admission to pass [class: IMPLEMENTATION_REQUIRED]
- [x] Gates precedence pin: the effect gates evaluate in the pinned order, scope-unchanged, then projection-complete, then effect-evidence-unavailable, then effect-baseline-unrecorded, then effect-path-escapes-root, then the effect verdicts [class: IMPLEMENTATION_REQUIRED]
- [x] Evidence-unavailable gate: given a terminal receipt without a usable `effect_evidence` map, expects refusal `effect-evidence-unavailable` parking without mutation, usable means the map carries at least one recorded changed path, so an empty map or a map with no changed paths refuses (a zero-verification requeue is the false source-absence the origin row prices) [class: IMPLEMENTATION_REQUIRED]
- [x] Baseline-unrecorded gate: given a task record without a usable `effect_baseline` field, or a changed path with no baseline cell in `effect_baseline`, expects refusal `effect-baseline-unrecorded` before any probe [class: IMPLEMENTATION_REQUIRED]
- [x] Path-escape gate: given a receipt path escaping the repository root, expects refusal `effect-path-escapes-root` before any read, changed-path keys are repo-relative POSIX paths, an absolute or non-repo-relative key refuses, and containment resolves keys against the repository root (never the process CWD) then relative_to it [class: IMPLEMENTATION_REQUIRED]
- [x] Symlink containment witness: given an in-repo symlink whose target lies outside the repository root, expects refusal `effect-path-escapes-root`, witnessed by a symlink fixture cell [class: REPOSITORY_TEST]
- [x] Unreadable-path gate: given an existing-but-unreadable changed path (unreadable file, directory), expects a named tool_error through the helper's outcome contract, state unchanged [class: REPOSITORY_TEST]
- [x] Derivation forks explicit: given a legacy record without the scope digest, expects `launch-scope-unrecorded`; the recovery's derivation admits the recorded scope mismatch, inverts the projection gate, and names every fork beside the operation [class: IMPLEMENTATION_REQUIRED]
- [x] Inherited gates: given a missing or foreign claim, stale review evidence, verdict no, missing terminal receipt, or wrong task state, expects the same named refusals as the reconcile path; every modeled path, refusals, tool errors, and the success exit, asserts the exit codes and `OUTCOME:` lines matching the module's outcome contract [class: IMPLEMENTATION_REQUIRED]
- [x] Write-failure cell: given a failing replace injected into the recovery's own write sequence (the same injection seam the atomic-write regression uses), expects a tool_error outcome with the runtime record bytes unchanged, enforcing the fail-closed posture for the new transition, not just the sibling reconcile path [class: REPOSITORY_TEST]

### Task 3: Recovery write path and witness regressions

Context surface: the plan's Terms, this task, and `## Standing constraints` when present.

Files:
- `scripts/reconcile_execute_plan_handoff.py`
- `scripts/test_reconcile_execute_plan_handoff.py`

Primary class anchors:
- `HandoffReconciler` in `scripts/reconcile_execute_plan_handoff.py`

- [x] Partition procedure: classify every path per the Terms effect probe, treating missing current as `absent` and applying the baseline/post equality cases in their stated order [class: IMPLEMENTATION_REQUIRED]
- [x] Partition corner cells: expects each named corner's decided verdict, created-then-rebase-lost (absent baseline, post digest, current missing: absent), deletion-survived (baseline digest, post `absent`, current missing: present), both-absent-missing: neutral, net-zero reverted edit: neutral [class: REPOSITORY_TEST]
- [x] Set aggregation: any present or evolved path parks without mutation (`effect-present` for mixed sets); only all-absent-or-neutral sets proceed, with mixed and all-clear multi-path witnesses [class: IMPLEMENTATION_REQUIRED]
- [x] Recovery success state: given the witnessed shape, expects success reason code `scope-drift-recovered` with one atomic replacement setting status `pending`, checkbox false, the current scope digest, and generation advanced one [class: IMPLEMENTATION_REQUIRED]
- [x] Recovery preservation: given the same recovery, expects the original terminal receipt and the requeued record's `effect_baseline` retained byte-identical, unrelated task records byte-identical, and the run's `plan_digest` unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Recovery receipt fields: given the stored `scope_recovery` receipt, expects field-level assertions against the Terms entry's nine field groups [class: REPOSITORY_TEST]
- [x] Re-read drift refusal: mutation between reads of any recovery receipt field refuses with unchanged state; a recovery-specific map covers the Terms' nine groups and re-derives effect verdicts, distinct from Task 1's map [class: REPOSITORY_TEST]
- [x] Re-read class strings: given the reason map, expects its class strings recorded beside the map, one named class per field group, the set the Task 4 vocabulary references [class: IMPLEMENTATION_REQUIRED]
- [x] Re-read key coverage: given the reason map, expects a static key-coverage regression asserting its key set equals the Terms entry's field set, with the verdict re-derivation recorded as the last read before replace [class: REPOSITORY_TEST]
- [x] Safety witness: given a recovered task re-invoked, expects the `task-state-not-done-pending` refusal, no already-recovered retry arm, the task re-entering the ordinary loop instead [class: REPOSITORY_TEST]
- [x] Recovery CLI transition: given an isolated done-pending runtime state with a valid terminal receipt and effect evidence, invoke `recover-scope-drift` through the production CLI; expect status `pending`, checkbox false, generation advanced once, and the task scope digest updated, while the original receipt, effect baseline, unrelated task records, and run plan digest remain unchanged [class: REPOSITORY_TEST]
- [x] Preserved-run acceptance: restore recorded launch bytes; actual parent preflight selects pending and a distinct worker accepts; the task log records transitions and verifies original state restoration [class: IMPLEMENTATION_REQUIRED]
- [x] Isolated CLI-to-parent acceptance: invoke recovery CLI on a valid fixture, then run the actual parent preflight and distinct worker; the task log records reselection, acceptance, and every state transition [class: IMPLEMENTATION_REQUIRED]
- [x] Preflight emulation supersession witness: a new test-local case documents the file's receipt-presence emulation as superseded for done-pending detection by the contract's status-keyed rule, without mutating existing bytes [class: REPOSITORY_TEST]
- [x] Module docstring refreshed for two receipt-backed transitions with routing staying parent-owned [class: IMPLEMENTATION_REQUIRED]
- [x] Task-scope-changed evidence names `recover-scope-drift` as the post-acceptance remedy; prelaunch referral stays unchanged, and existing plus new remedy-text regressions pass [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED then GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: add receipt-backed scope-drift recovery for done-pending handoffs` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Contract and loop wiring for the scope-drift recovery route

Context surface: the plan's Terms, this task, and implementation-loop Step 1.2 (the pre-prompt digest-record duty this task amends).

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/implementation-loop.md`
- `docs/history/backlog/2026-10-31-handoff-reconciler-cas-reread-window.md` (watchlist line extension in place)

- [x] Contract route: given the Done-pending handoff reconciliation section, expects the `recover-scope-drift` invocation, the `scope_recovery` receipt binding, and the acceptance-time `effect_evidence` producer duty composing with the existing writes, its wording pins the digest recipe (sha256 over raw bytes, lowercase `absent` literal, the no-ad-hoc-reimplementation mandate), and records the post-only shape (no baseline half recorded) [class: IMPLEMENTATION_REQUIRED]
- [x] Contract vocabulary: expects the refusal vocabulary (`scope-unchanged`, `projection-complete`, `launch-scope-unrecorded`, `effect-evidence-unavailable`, `effect-baseline-unrecorded`, `effect-path-escapes-root`, `effect-present`, `effect-evolved`), the success code `scope-drift-recovered`, the reason map's recorded per-field drift class strings, and the pinned precedence order recorded once beside the reconcile contract, every mention using the qualified scope-drift name [class: IMPLEMENTATION_REQUIRED]
- [x] Contract semantics: expects the park semantics, the no-relaunch rule, the audit-trail boundary (the post-requeue re-acceptance replaces `terminal_receipt`; the `scope_recovery` receipt carries the original receipt's digest as the surviving evidence anchor, the accepted completion's evidence trail remaining in the plan's review staging series), and the status-keyed done-pending detection recorded as the authority for done-pending reporting [class: IMPLEMENTATION_REQUIRED]
- [x] Contract limitation: expects the limitation recorded, receipts without the `effect_evidence` map park with `effect-evidence-unavailable`, and records with a usable map but no usable `effect_baseline` field (pre-amendment launches, or runs whose changed paths leave the declared set) park with `effect-baseline-unrecorded`, both requiring operator disposition (fresh capture or manual reconciliation) [class: IMPLEMENTATION_REQUIRED]
- [x] Loop arm routes the refusal: given the done-pending reconciliation arm in the implementation loop, expects the `task-scope-changed` outcome to name the `recover-scope-drift` invocation once, park for operator disposition on its refusal, rerun ordinary preflight on success before the loop continues, and note that Step 1.1 reselects the unchecked task against the current scope [class: IMPLEMENTATION_REQUIRED]
- [x] Pre-prompt duty amended: Step 1.2 records `effect_baseline` beside `task_scope_digest` for each declared `Files:` path at the pre-prompt write: SHA-256 of raw bytes or lowercase `absent`; no acceptance-time baseline is captured. Before reading, resolve paths under the repository root; only a genuinely missing file maps to `absent`; an escaping symlink, directory, or unreadable/non-regular file refuses before dispatch with runtime state unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Watchlist row extended in place: given the cas-reread-window sibling row's Watchlist line, expects it to name the recovery's worktree-byte probe input class (keyed to any claim-unfenced writer) and the re-read-to-replace residual window joining the same row, no new row created [class: IMPLEMENTATION_REQUIRED]
- [x] Contract-removal check: the obsolete `task-identity-drift` reason is absent from the helper and execution-contract docs after Tasks 1 and 4 [class: REPOSITORY_TEST]
- [x] Commit: `docs: wire the scope-drift recovery route into the execution contract and loop` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Make effect evidence capture path-safe and executable

Context surface: Terms `effect evidence`, the existing recovery probe, and implementation-loop Step 1.2 acceptance writes.

Primary class anchors:
- `HandoffReconciler` in `scripts/reconcile_execute_plan_handoff.py`

Files:
- `scripts/reconcile_execute_plan_handoff.py`
- `scripts/test_reconcile_execute_plan_handoff.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/implementation-loop.md`

- [x] Read-only capture command: anchor traversal at the repository-root directory descriptor, walk components relative to held descriptors with no-follow flags, and open the final file nonblocking; reject symlink components and non-regular descriptors before reading; only a genuinely missing path maps to lowercase `absent`, and emit a complete map only after all paths are safely read [class: IMPLEMENTATION_REQUIRED]
- [x] Recovery reuses the safe resolver: given an escaping symlink or dangling in-root symlink for a recorded effect path, expects refusal/tool error without classifying the path as `absent` and without changing runtime state [class: IMPLEMENTATION_REQUIRED]
- [x] Producer wiring: the parent uses the read-only command for pre-prompt `effect_baseline` and acceptance-time post-only `effect_evidence`; runtime state is written only after a complete successful map, and acceptance records no baseline half [class: IMPLEMENTATION_REQUIRED]
- [x] Capture regressions: CLI tests cover raw-byte digest, genuine absence, symlinks, directory, unreadable files, and a no-writer FIFO that refuses within a short timeout; a deterministic parent-directory symlink swap cannot read outside bytes or emit a partial map; recovery refusal leaves runtime state unchanged [class: REPOSITORY_TEST]
- [x] Parent wiring witness: a focused contract assertion checks both pre-prompt baseline and acceptance-time post-only producers invoke `capture-effect-evidence` and defer state writes until capture succeeds [class: REPOSITORY_TEST]
- [x] Commit: `fix: make execute-plan effect evidence capture path-safe` [class: IMPLEMENTATION_REQUIRED]


## Residual findings (cap closure)

Declared at the full-panel budget breach (plans Plan Quality Gate rule 17) with operator authorization, 2026-11-14; the terminal round is r4, whose blocking finding is fixed in commit 1b71d53bb alongside every staged finding below.

- F1 (consistency#receipt-field-set-contradiction, High): folded.
- F2 (testing#recovered-preflight-contradiction, Medium): folded.
- F3 (architecture#partition-corner-precedence, Medium): folded.
- F4 (simplification#copy-duty-dead-machinery, Medium): folded.
- F5 (security#declared-set-undershoot, Medium): folded.
- F6 (implementation#refusal-precedence-and-success-code, Medium): folded.
- F7 (consistency#watchlist-extension-unowned, Medium): folded.
- F8 (testing#symlink-cell-missing, Medium): folded.
- F9 (testing#multipath-aggregation-unwitnessed, Medium): folded.
- F10 (testing#effect-baseline-survival, Low): folded.
- F11 (documentation#delivery-record-undefined, Low): folded.
- F12 (consistency#task1-proof-false-ground, Low): folded.
- F14 (consistency#park-enumerations-incomplete, Low): folded.
- F15 (security#degenerate-projection-cell, Low): folded.
- F16 (documentation#drift-class-strings-unpinned, Low): folded.
- F13 (consistency#env-hermeticity-qualifier, Low, overflow): folded.

## Disposition of migrated backlog items

| Former backlog origin | Disposition |
| --- | --- |
| `docs/history/backlog/2026-10-31-handoff-reconciler-dead-drift-mappings.md` | Implemented by this plan and removed in this archive pass. |
