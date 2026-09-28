# Execute-plan preflight must recover legacy run identity and tolerate prompt text in process snapshots

- **Filed:** 2026-09-29
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** consumer-feedback
- **Driving force:** reliability; secondary usability
- **Source:** PROJ-607 execute-plan continuation, 2026-09-29. The seeded manifest had no `runtime` or `repo_root`, so current preflight correctly emitted no continuation command. The documented claim-boundary remedy let the driver create a fresh claim and persist `runtime: codex`, but that intermediate claim had no activation receipt or prepared handoff, so preflight then refused it as unprovable. Continuing the existing claim reached the recognized Codex adapter, whose process inventory returned `unavailable` because `ps` included another active worker prompt with unmatched shell quotes; the adapter's `shlex.split` rejected the entire snapshot and capacity was quarantined.

## Problem

Two gaps combine to strand an older active run at the launch boundary. First, the preflight contract rejects a legacy manifest without a runtime id, but its suggested claim-boundary repair does not describe a complete transition from that manifest to an admissible continuation. A plain `claim` persists the runtime id but leaves a claimed task that readiness cannot prove claimable, while manually assembled `continue` is prohibited by the canonical-command rule. The recovery path needs to bind runtime identity and enter a state that the next read-only preflight can admit, or it needs a dedicated locked migration operation that does both atomically.

Second, Codex inventory parsing treats `ps` command text as valid shell syntax. Process arguments can contain arbitrary worker prompts, including unmatched quotes. A malformed unrelated prompt currently converts the entire host inventory to unavailable and quarantines capacity, even when the relevant process identity and command prefix are readable. This prevents the recognized adapter from starting work for reasons unrelated to the target run.

## Established mechanism facts

- `agents/skills/execute-plan/runtime-contract.md` requires the canonical continuation command to pin the recorded runtime id and repository root, and says a manifest without a runtime id fails preflight emission with re-create or claim-boundary remedies.
- `scripts/execute_plan_runtime.py` stamps approval/runtime evidence at successful claim, continue, resume, and worker-start transitions. Its current preflight admits a fresh done-successor claim only when the prepared handoff identity agrees; the observed direct claim did not qualify.
- `scripts/execute_plan_runtime_codex.py` obtains process rows with `/bin/ps -ww -axo pid=,lstart=,command=` and applies `shlex.split` to the complete rendered command text before filtering for `codex exec`. One active worker prompt containing an unmatched quote made inventory unavailable.
- The process table showed two related process rows for one active Codex worker in a separate repository. The single-slot adapter therefore had a real capacity occupant after parser recovery as well; the parser defect must not be “fixed” by ignoring unrelated live workers.

## Suggested fix

Add one bounded implementation plan over the two admission complements. For legacy manifests, provide a driver-owned migration/recovery transition that validates the target repo, registered runtime, approval receipt, next task, claim/handoff state, and generation under the manifest lock, then persists the runtime binding in a state the normal preflight can prove. Refusals must leave bytes unchanged, and preflight must still emit no command when identity or activation evidence is incomplete. Keep ordinary `claim` and continuation fencing intact.

For Codex process inventory, parse only the identity-bearing command prefix needed to identify `codex exec` and accepted `resume` forms, or use a structured process interface that preserves argv boundaries. Unrelated prompt payload text must not invalidate the whole snapshot. Continue to fail closed on malformed PID/start-time identity, unreadable process inventory, or ambiguous target-process identity. Add tests for unmatched quotes in prompt arguments, malformed identity fields, unrelated live exec processes, accepted resume IDs, and unavailable snapshots. Preserve the capacity lock and single-slot exclusion.

## Possibility space and simplifications

- **Recommended: one atomic legacy-run binding operation plus narrow process-prefix parsing.** It completes the missing continuation state and removes prompt text from the inventory parser's trust boundary while preserving exact runtime, repo, approval, claim, and capacity checks.
- **Acceptable simplification: make runtime/repo identity mandatory at manifest creation and expose a dedicated recovery-only binding command for older manifests.** Do not make preflight infer a runtime from ambient machine state.
- **Reject: hand-edit `runtime_state.json` or hand-assemble a continuation command.** These bypass the driver-owned evidence and canonical invocation fence.
- **Reject: ignore every malformed process row or report an empty inventory.** This can misclassify a live worker as absent and admit a second launch.
- **Reject: wait for every host process to exit.** Capacity should remain scoped to recognized active Codex executions, not unrelated processes.

## Acceptance

- A legacy manifest can bind a verified runtime and repository identity through one audited, locked transition, after which read-only preflight emits a self-sufficient command; invalid, stale, replayed, or mismatched evidence leaves the manifest unchanged.
- A plain direct claim cannot leave the task in a claimed-but-unprovable state when preflight cannot emit a command.
- A Codex process row with unmatched quote characters in prompt text no longer makes an otherwise parseable inventory unavailable.
- A real unrelated live `codex exec` process still consumes the single-slot capacity and prevents a second launch.
- Malformed process identity, command ambiguity, and failed `ps` remain fail-closed and covered by focused tests.
