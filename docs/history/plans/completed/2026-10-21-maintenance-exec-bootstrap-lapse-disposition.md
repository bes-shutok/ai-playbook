# Plan: Maintenance Exec Bootstrap Lapse Disposition

Backlog origin: `docs/history/backlog/2026-10-21-maintenance-exec-bootstrap-blocker.md`
Driving force: simplicity
Plan review record: `.ai-playbook/reviews/YYYY-MM-DD-plan-review-maintenance-exec-bootstrap-lapse-disposition-r*.md`
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-21-maintenance-exec-bootstrap-blocker.md (session 01a15484-176a-70a1-814d-785fd68e1975)

## Terms

- **Maintenance exec:** The unattended execution lane described by the maintenance skill.
- **Transfer-in:** Copying the primary checkout's facts and review inputs into a fresh execution worktree before readiness checks.
- **Readiness:** The plan gate run before execute-plan implementation begins.
- **Done setup:** The done skill's setup step that classifies review candidates and writes a run manifest under the done lock.
- **Independent test-scope origin:** The separate backlog item served by the EXEC-PROMPTS entry for the requested test-scope work.
- **Review-candidate classification:** Identifying this run's owned staging docs and foreign candidates before the done setup lock and manifest write.
- **Covered workflow lapse:** An execution omitted a sequence already required by its caller and owning skills, without a missing contract rule.
- **Prompt-log prune receipt:** The existing PLAN-PROMPTS ledger line that witnesses removal of a fully served entry.
- **Plan landing:** The authoring closeout that marks a promoted origin covered and prunes the prompt entry that dispatched this plan.
- **Plan completion:** The archive transition that adds the migrated-origin disposition and ownership-registry row, then deletes the promoted backlog file.
- **Ownership registry:** The document table at `docs/maintenance/document-registry.md` that records document identities and lifecycle states.
- **Skill-gate marker:** The plans-class file `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`, written atomically at mode `0600` before each plan-file write. Derive `project` with the shared `facts_paths.resolve_project_key` for the write-target project root. Derive `session` by running `python3 ~/.ai-playbook/scripts/session_channel.py`; map an empty or whitespace-only result to `no-session`, otherwise use the first 16 hexadecimal characters of SHA-1 over the returned value. In this worktree, pass its root as `--cwd` to `skill_gate.py --write-marker`. The recipe is owned by `agents/hooks/skill-gate/README.md`.

## Why

The maintenance execution prompt already requires transfer-in before readiness and run setup, then calls the done skill after clean execution. The done skill already requires review-candidate classification before setup writes the run manifest. The backlog row records an omitted sequence, so retaining it as an open contract gap would duplicate existing instructions.

## Gist & Examples

TLDR: close the covered bootstrap origin, for simplicity, so the queue reflects a missing contract only when the contract is actually missing.

Before: A fresh-worktree run omits the documented transfer and classification steps, blocks at setup, and leaves an open origin that suggests the classifier or transfer contract is defective.

After: The plan landing marks the origin covered and prunes this plan's own prompt-log entry with a receipt. The plan's later completion verifies the contracts, records the origin disposition in the archived plan, and deletes the backlog row. No runtime instruction or classifier changes.

Edge cases: Keep the independent test-scope origin open; preserve dead-root disposition and warning-only inherited state; if execution-time source evidence contradicts this plan, stop the covered-origin deletion and report the mismatch for a new investigation.

## Outcome

The authoring landing marks this origin covered and prunes this plan’s own prompt-log entry with the required receipt. Plan completion later records the disposition in the archived plan and deletes the backlog row.

- Existing transfer and classification instructions remain unchanged.
- The prompt-log entry is removed by its owning authoring landing step.
- Plan completion folds and deletes only this origin while preserving the independent test-scope origin.

Gate delta: no gates, validators, locks, ledgers, or ceremonies are added or removed; the sole task rechecks source coverage before origin deletion, with no later task or dispatch paused.

## Design Invariants

- Transfer-in remains owned by the Worktree-first standard and runs before readiness and run setup.
- Review-candidate classification remains owned by done Step 0 and precedes lock acquisition and manifest writing.
- The setup keeps fail-closed manifest ownership, supported dead-root dispositions, and warning-only inherited-state behavior.
- The independent test-scope origin remains open and untouched.
- No classifier, transfer implementation, dispatch template, done setup rule, gate, or validator is changed.

## Assumptions

- The current maintenance execution template composes the existing transfer-in and done workflow in order; basis: its per-execution worktree paragraph requires full transfer-in before PRE-STEP, then invokes done only after clean execution, and done Step 0 owns pre-lock classification.
- The frozen prompt selects covered-origin closure when this composition already exists; basis: `docs/history/backlog/PLAN-PROMPTS.md`, `maintenance-exec-setup-transfer-order`.
- The lifecycle assigns the covered flip and prompt-entry prune to plan landing, then the disposition fold and backlog deletion to plan completion; basis: `agents/skills/plans/SKILL.md`, Plan Lifecycle.

Decision points requiring a grill: none remain.

## Evaluation Criteria

- **Contract order:** The current source still requires transfer-in before readiness and run setup, and candidate classification before lock acquisition and manifest writing.
- **Origin closure:** Plan landing marks only this origin covered and prunes this plan's dispatch entry; plan completion folds its disposition into the completed plan, records ownership, and deletes the backlog file.
- **Boundaries:** The independent test-scope origin remains open; no classifier, transfer contract, or runtime setup behavior changes.
- **Audit:** `python3 scripts/check_prompt_log_origins.py` passes after the closure lands.

## Done when

The source order is rechecked, plan landing has covered this origin and pruned its dispatch entry, and plan completion archives the plan, folds the origin disposition, deletes the backlog row, and passes the prompt-log origin audit.

## Ship when

The plan is reviewed, archived, and landed with its origin disposition and review artifacts preserved through the normal plan closeout.

## Review Scope

- In scope: the evidence-backed disposition of `docs/history/backlog/2026-10-21-maintenance-exec-bootstrap-blocker.md`, its `maintenance-exec-setup-transfer-order` entry in `docs/history/backlog/PLAN-PROMPTS.md`, and the completion-time ownership record in `docs/maintenance/document-registry.md`.
- Review concerns: current instruction order, exact origin-to-entry pairing, plan-landing receipt, completion disposition and ownership rows, and preservation of the independent test-scope origin.
- Out of scope: manual edits to maintenance dispatch, Worktree-first transfer-in, done setup, classifier behavior, test runner behavior, additional prompt-log entries, or any new machinery.

## Validation Commands

- `python3 scripts/check_prompt_log_origins.py`
- `bash scripts/scan-public-hygiene.sh`

### Task 1: Close the covered bootstrap origin

Files:
- `docs/history/backlog/2026-10-21-maintenance-exec-bootstrap-blocker.md`
- `docs/maintenance/document-registry.md`

- [x] Recheck that transfer-in precedes readiness and run setup, and that review candidates are classified before done setup writes the manifest. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify plan landing marked this origin covered and pruned only this plan's dispatch entry with its receipt; do not repeat that prune. [class: IMPLEMENTATION_REQUIRED]
- [x] At plan completion, fold the origin disposition into the archived plan, append the ownership-registry row, and delete only this backlog file. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the independent test-scope origin open and leave the cited runtime contracts unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the prompt-log origin audit and public-hygiene scan. [class: REPOSITORY_TEST]
- [x] Commit the origin disposition with the completed plan archive. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-21-maintenance-exec-bootstrap-blocker.md: covered by this plan; the execution rechecked the source contract order (the Worktree-first standard owns transfer-in before readiness and run setup; done Step 0 owns review-candidate classification before lock acquisition and the manifest write), confirmed the plan landing's covered flip and the prompt-log prune receipt, and deleted the row at completion. No runtime contract changed. The independent test-scope origin remains open.
