# Plan: Retain Gate Reports During Worktree Closeout

Backlog origin: docs/history/backlog/2026-10-29-done-gate-report-retention.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/YYYY-MM-DD-plan-review-done-gate-report-retention-r*.md
Execution budget: 3h total, largest task 1.5h

## Terms

- Closeout migration manifest: the existing record consumed by `gate-removal` to bind a source branch and verify migrated artifact destinations.
- Primary checkout: the first registered worktree for the repository; it owns the shared temporary root used by one-plan transfer.
- Run-owner checkout: the primary or linked worktree where `done_run.sh setup` created the current session records.
- Verified report destination: a `destination` entry marked `verified: true` in a manifest's `migrated` or `renamed` section.
- Verified-destination publisher: the closeout path that copies or rechecks a destination and appends its verified manifest entry.
- Live closeout: worktree mode requires the supplied worktree to be registered in the target and bound to the recorded branch; the recorded ref may resolve or return the existing `unknown-ref` state. The consumer does not require that worktree path to equal the manifest's `source` field.
- Unresolved closeout: a verified report reference remains in a supported manifest and a matching registered worktree is bound to the recorded branch, but `gate-removal` returns `unknown-ref` and directs the operator to resolve the ref and retry.
- Session window: the existing mtime boundary used by the done-session sweep to prune old markers and gate reports.
- Supported manifest set: migration-shaped JSON under both the run-owner and resolved primary checkout temporary roots, in their `execute-plan/` and `done-session/` subtrees. This includes canonical and legacy plan-session files, run-ID `worktree-migrate-baseline-<id>-manifest.json` files, and explicit operands under those roots. This plan retains reports only for registered-worktree closeout.

## Why

The done-session sweep can delete an old gate report while a closeout manifest still cites it. `gate-removal` then refuses teardown because its verified artifact is missing, and recovery may depend on finding a backup.

## Gist & Examples

TLDR: retain verified gate-report destinations during registered-worktree closeout while preserving bounded report cleanup.

Before: a report older than the session-window anchor is removed even when a registered-worktree closeout manifest still names it.

After: an aged verified report named by a live manifest stays available to `gate-removal`; an equally old unreferenced report is still pruned.

Edge cases: `migrated` and `renamed` verified entries count, `skipped` does not; both manifest roots contribute; unsupported shapes warn and remain age-prunable; a matching registered-worktree `unknown-ref` retains its report for ref recovery and retry; successful worktree removal makes the report age-prunable; branch-only lifecycle remains in the linked follow-up backlog item; pruning and verified publication share the merge lock, and a publisher records only a present, verified destination.

## Outcome

Old closeout reports remain available for teardown only while the existing closeout consumer can still use them.

- A live closeout keeps its verified migrated and renamed report destinations present.
- Unreferenced reports continue to follow the existing session-window cleanup.
- Retain verified destinations while a supplied worktree registration is bound to the recorded branch, without comparing its path to manifest `source`. A matching registration with an unresolved ref remains pending and retains the report until the ref is resolved and worktree closeout succeeds. Branch-only `unknown-ref` retention and its post-success pruning signal are deferred to `docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md`.

Gate delta: reuse the existing `worktree-closeout-migrate` merge lock for report lookup/unlink. Route baseline-less publication through `cmd_migrate`'s existing lock-owning copy/check/append path, replacing the separate manual copy and manifest-append procedure; add no lock-acquire path or refusal class. Sweep lock failures warn and skip pruning; publisher failures keep the existing migration outcome. Reuse the existing `unknown-ref` result for registered-worktree recovery and retry; add no new refusal class. Leave branch-only retention behavior unchanged pending the separate design item. No new lock file, registry, ledger, schema field, or dispatch pause. Witness: [the report-loss backlog item](../backlog/2026-10-29-done-gate-report-retention.md); expected catch frequency: rare publication overlap; false-positive cost: bounded lock wait or deferred cleanup; current guard-liveness ratio: 29:48 (`scripts/gate_liveness_ledger.py show`, 2026-10-29); review by 2027-01-29. Preserve bounded age pruning and the missing-destination refusal.

## Assumptions

- The current gate consumer treats the latest branch record as authoritative and checks verified destinations from `migrated` and `renamed`; `skipped` entries are not presence checks. Basis: `scripts/worktree_closeout_migrate.py` `_gate_branch_closeout`.
- `_gate_branch_closeout` binds a supplied worktree registration's branch to the record but not its path to manifest `source`. An `unknown-ref` result refuses and instructs resolution followed by retry, so the registered worktree remains available for the sweep to recognize. Branch-only completion has no durable signal and is explicitly deferred to the linked backlog item. Basis: `scripts/worktree_closeout_migrate.py` and the r11 reconciliation.
- Sanctioned plan-session manifests may be under the primary checkout temporary root, while zero/multi-plan run-ID manifests are under the run-owner temporary root; in a linked worktree these can differ. Explicit operands under either root are discoverable from those existing subtrees; external low-level CLI overrides are outside the sanctioned retention producer path. Basis: `scripts/done_run.sh`, `scripts/worktree_closeout_migrate.py` `_candidate_migration_manifest`, and `scripts/done_sweep_gates_lib.py` `_resolve_primary_checkout`.
- For every unreadable or unsupported shape, the resolver returns no references and the sweep age-prunes with a warning. Existing consumer behavior is shape-specific: unreadable JSON refuses; absent or non-list `branch` and a non-dictionary latest branch record skip; non-dictionary destination rows are ignored; a non-object root or non-iterable `migrated`/`renamed` section can reach the caught `OUTCOME: tool_error`. Preserve these outcomes; add no normalization or refusal class. Basis: `_gate_branch_closeout` and its CLI exception boundary in `scripts/worktree_closeout_migrate.py`.
- The plan's `code-quality` force maps the origin's reliability motive to the available plan taxonomy; the operator impact and recovery objective remain reliability-focused. Basis: the plan format's closed driving-force taxonomy and the backlog origin.
Decision points requiring a grill: branch-only lifecycle scope: maintenance-selected receipt (defer branch-only terminal-state behavior to `docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md`; the current plan explicitly excludes a new schema field and the branch-only gate does not persist success); source: r11 review and reconciliation, 2026-10-29; affected sections: Gist & Examples, Outcome, Evaluation Criteria, Task 2, Out of scope.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: retain verified destinations while a registered worktree bound to the recorded branch remains in `unknown-ref`; prune after successful worktree removal, while branch-only lifecycle remains explicitly deferred.
- Bounded storage: unreferenced, completed, unsupported, and unreadable-manifest reports remain eligible for existing age pruning; a verified reference in unresolved closeout outlasts the window only until ref resolution and successful closeout.
- Safety: missing verified destinations continue to refuse teardown.

**Done when:**
- Implementation behavior covers worktree-mode closeout with a resolving ref, recovery after an `unknown-ref` refusal, unreferenced aged reports, and pruning after successful worktree removal.
- Unsupported records create no retention references; preserve existing shape-specific consumer behavior and bounded age pruning without a second registry or weakened `gate-removal` guard. Branch-only report retention and its terminal-state contract stay outside this plan.
- The repository's focused closeout and done-sweep regression coverage passes.

**Ship when:**
- None; this is shared local cleanup behavior.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/worktree_closeout_migrate.py` (Task 1)
- `scripts/worktree_closeout_migrate.py` (Task 3)
- `scripts/done_sweep_gates_lib.py` (Task 2)
- `agents/skills/execute-plan/worktree-first.md` (Task 3)

**Tests:**
- Regression coverage selected from repository evidence for worktree closeout (Task 1) and done-session pruning (Task 2)

**Plan-related extension:** implementation and review may change files not listed above when they implement this retention behavior or fix a regression it introduces.

**Out of scope; reject unless plan-related:**
- Branch-only closeout report retention and its terminal-state transition; reason: the current manifest has no durable success signal, and a new retention schema is outside this plan. Track the design in `docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md`.
- New report registries, ledgers, or retention schema; reason: the existing closeout manifest and worktree state are the source of truth.
- Any change that allows `gate-removal` to proceed when a verified destination is missing; reason: the presence refusal is the safety condition this retention change protects.
- Removing age pruning for all gate reports; reason: it violates the bounded report contract in `docs/history/plans/completed/2026-10-10-done-closeout-lock-span-and-output-cost.md`.
- Explicit override manifests outside the facts-resolved temporary directory; reason: they are not produced by the sanctioned workflow and cannot be discovered from the report directory without a separate registry.

## Validation Commands

At execution, select the repository-owned regression suites covering the done-session sweep and worktree closeout; record the exact commands and selected tests in the task log. Then run:

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-10-29-done-gate-report-retention.md --pre-round
```

### Task 1: Resolve consumer-usable closeout references

Context surface: the plan's Terms and this task.

Files:
- `scripts/worktree_closeout_migrate.py`

Primary class anchors:
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`

Evidence:
- `_gate_branch_closeout` checks only verified `destination` values in `migrated` and `renamed`; `skipped` rows are excluded. It binds the latest branch record and supports worktree and branch-only closeout.
- `docs/history/plans/completed/2026-10-10-done-closeout-lock-span-and-output-cost.md` bounds report retention to the session window. The `closeout-proof-record-retention` receipt at `docs/history/backlog/EXEC-PROMPTS.md` retains a different execute-plan proof family.

- [ ] Given repeated branch records and a resolvable recorded branch ref, expect the latest record to govern liveness while every verified migrated and renamed destination remains represented. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given absent or legacy no-branch records, expect the existing consumer skip behavior. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given unreadable JSON, expect unresolved/no destinations from the resolver and the existing consumer refusal. For malformed parsed JSON, expect unresolved/no destinations while preserving these examples: an array root and integer `migrated` section reach `OUTCOME: tool_error`; a non-list `branch` field or string latest branch record skips; a string row in `migrated` is ignored. Do not normalize these shapes or add a refusal class. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a missing verified destination at `gate-removal`, expect its existing refusal; given a `skipped` entry, expect no new presence requirement. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given branch-only closeout, expect this plan to leave existing consumer and sweep behavior unchanged; branch-only retention is deferred to the linked follow-up item. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add focused regression coverage for reference resolution, record ordering, and malformed input shapes selected from repository evidence. [class: REPOSITORY_TEST]
- [ ] Commit: `refactor: expose closeout reference state` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Retain referenced reports during cleanup

Context surface: the plan's Terms and this task.

Files:
- `scripts/done_sweep_gates_lib.py`

Primary class anchors:
- `_prune_done_session_markers` in `scripts/done_sweep_gates_lib.py`

Evidence:
- The sweep prunes old gate reports by mtime without checking closeout references.
- The one-plan producer writes under the primary checkout temporary root; zero/multi-plan setup writes a run-ID migration-shape file under the run-owner `done-session/`. In a linked worktree these roots differ, and both are available through existing checkout and facts resolution.
- Existing subprocess fixtures `runner_env` and `sweep_env` pin facts, runtime helper resolution, and lock homes while clearing ambient Git selectors.

- [ ] Given a live verified `migrated` or `renamed` destination in a plan-session manifest under the primary root, expect report retention. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a live verified destination in the run-ID manifest under the run-owner `done-session`, expect report retention. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a sweep running in a linked worktree, expect discovery of plan-session manifests under the resolved primary temporary root. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an explicit migration-shaped JSON under either supported temporary root, expect its verified destinations to be considered. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a resolvable recorded branch ref and a registered worktree operand on that branch, expect retention for worktree-mode closeout even when its path differs from manifest `source`, matching the existing consumer checks. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a matching worktree registration whose recorded ref no longer resolves, expect the verified report to remain while `gate-removal` returns `unknown-ref`; after resolving the ref, expect retry to consume the report and a later sweep to prune it only after worktree removal succeeds. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an aged unreferenced report with mtimes before, at, and after the anchor, expect pruning only strictly before the anchor. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given unreadable or unsupported manifests, expect a warning and normal age pruning, not indefinite retention. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given merge-lock acquisition fails, launches unsuccessfully, returns refusal, or omits ownership exports, expect a warning and no aged report pruning; the sweep must not continue without a verified hold. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add worktree-mode sweep/consumer subprocess coverage for `unknown-ref`, ref restoration and retry, and pruning after successful worktree removal using fixture-owned `sweep_env`: pin facts/runtime/lock roots and helper resolution, clear inherited Git selectors, and control report/marker mtimes; select the focused suite from repository evidence. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: retain gate reports during worktree closeout` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Route scoped publication through existing migration

Context surface: the plan's Terms and this task.

Files:
- `scripts/worktree_closeout_migrate.py`
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors:
- `cmd_migrate` in `scripts/worktree_closeout_migrate.py`
- `_append_manifest` in `scripts/worktree_closeout_migrate.py`

Evidence:
- `done_run.sh setup` writes an empty zero/multi-plan manifest skeleton; it names no destinations until scoped copy appends verified transfers.
- `cmd_migrate` already owns the shared merge-lock transaction across copy, verification, and append; the baseline-less flow currently uses a separate manual copy and manifest-append procedure.

- [ ] Supply the baseline-less arm's explicitly captured scoped inventory to `cmd_migrate` without fabricating a baseline or requiring non-empty `dirs`; replace manual copy and skeleton-append instructions in `agents/skills/execute-plan/worktree-first.md`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Validate every expected inventory item one-for-one: a missing source or digest mismatch fails the existing publisher transaction and appends no `verified: true` row; no expected source is silently omitted. [class: IMPLEMENTATION_REQUIRED]
- [ ] Copy, verify, and append only successful items inside `cmd_migrate`'s existing merge-lock transaction; the empty skeleton alone creates no protected destination, and a report not selected into the captured inventory remains age-prunable. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given sweep and scoped-migration subprocesses race in either order, expect no manifest to cite a missing report; sweep lookup/unlink and the existing copy/check/append transaction share the merge lock. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add baseline-less migration subprocess regressions using fixture-owned `runner_env`/`sweep_env`: pin facts/runtime/lock roots, helper resolution, and `PATH`; clear inherited Git selectors, control report mtimes, and cover both race orders plus missing-source/no-verified-row and digest-mismatch/no-verified-row behavior. Run focused closeout suites selected from repository evidence. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: route scoped closeout through migration` [class: IMPLEMENTATION_REQUIRED]
