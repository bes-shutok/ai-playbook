# Plan: Retain Accurate Gate-Removal Branch Reports

Backlog origin: docs/history/backlog/2026-10-21-gate-removal-task2-review-deferred.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/YYYY-MM-DD-plan-review-gate-removal-task2-review-residues-r*.md
Authoring claim: docs/tmp/authoring-claims/2026-10-21-gate-removal-task2-review-deferred.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)
Execution budget: 3h total, largest task 1.5h

## Terms

- Branch-only closeout: `gate-removal --branch` adjudication of a branch with no linked worktree.
- Ancestry-accounted: the branch tip is an ancestor of the destination's history.
- Proven branch OID: the branch tip OID captured and rechecked by the gate for the reported closeout.
- Resolved branch OID: the branch tip OID read by the sweep for a candidate skipped before gate adjudication; it is not rechecked by the gate.
- Retained branch: a branch that remains available for operator resolution because closeout evidence is incomplete or a guard requires preservation.
- Fail-open setup sweep: setup continues after the residue sweep reports a failure, preserving the existing setup outcome.

## Why

Branch closeout text can claim a live worktree and migrated artifacts during branch-only adjudication, which has no linked worktree. The done setup summary can also omit retained-branch evidence emitted by the sweep, leaving operators without the branch identity, disposition, OID, or retention reason.

## Gist & Examples

TLDR: correct gate-removal reports for code-quality by stating verified branch evidence and preserving retained-branch details in setup output.

Before (today): Given a branch-only closeout whose branch tip is part of the destination history, the report says a live worktree binds the branch and its artifacts were migrated, although branch-only mode has no linked worktree. Given a retained branch reported by the setup sweep, setup filters out its name and retention reason.

After (this plan): Under those same conditions, the branch-only report names only the branch, its proven tip, and the ancestry result. The setup summary relays each retained branch's name, disposition, branch tip when available, and reason.

Edge cases: retained and skipped branches keep their reasons and branch OID when available; existing `OUTCOME` and removal behavior stay stable.

## Outcome

Closeout reports accurately distinguish branch evidence from worktree evidence, and the setup summary exposes the sweep's retained-branch details.

- Branch-only ancestry reports state the branch identity, proven OID, and ancestry result without asserting worktree or artifact facts.
- The setup summary carries each retained-branch identity, disposition, OID when known, and retention reason emitted by the sweep.
- Existing gate results, removal authority, branch-retention behavior, and the fail-open setup-sweep path remain unchanged.
- Formal-only residuals from the origin remain durably open in a separate backlog item before the origin is closed.

Gate delta: none. This plan changes report wording and forwarding only; it adds no gate, state, or refusal path.

## Assumptions

- A shared ancestry statement limited to the branch identity, proven OID, and ancestry result is the simplest accurate rendering for both worktree and branch-only modes; basis: `_gate_branch_closeout` computes those values for both modes, while the current shared sentence adds worktree-only claims.
- The setup sweep remains fail-open and report-only; basis: `cmd_setup`'s current sweep path and the done boundary contract.

Decision points requiring a grill: maintenance-selected receipt: use a shared evidence-only ancestry statement and preserve existing dispositions; source: `_gate_branch_closeout` and the origin's mode distinction; date: 2026-10-29; affected sections: Gist & Examples, Outcome, Task 1; maintenance-selected receipt: split unrelated formal-only findings into a separate open backlog record before origin closure; source: the origin's mixed review-residue list and the personal profile's formal-hardening deferral; date: 2026-10-29; affected sections: Outcome, Task 3, Review Scope.

Scope extensions (grilled): unrelated formal-only parser, environment, pin, fixture, naming, and wording work: omit-extension (maintenance-selected arm).

## Evaluation Criteria

**Quality dimensions:**
- Correctness: branch-only reports do not claim worktree registration or artifact migration.
- Observability: setup preserves each retained branch's identity, disposition, branch OID when available, and reason.
- Safety: existing refusals, retention, and removal authorization remain unchanged.

**Done when:**
- Focused regression coverage proves accurate ancestry wording and retained-branch details in setup output.
- The setup summary remains fail-open and no gate outcome or removal authority changes.
- Out-of-scope formal residues have a separate open backlog record before the origin is closed.

**Ship when:** None; this is local shared-skill report behavior.

## Review Scope

**Explicit must-fix:**
- Branch-only ancestry output must not assert worktree or artifact facts.
- Setup output must preserve the sweep's retained-branch identity, disposition, OID when known, and reason.
- Current gate outcomes and deletion authority remain unchanged.
- The origin's unrelated formal residues remain durably recorded after the real-fix work is complete.

**Backlog source records:**
- `docs/history/backlog/2026-10-21-gate-removal-task2-review-deferred.md` (Task 3)
- `docs/history/backlog/` (Task 3)

**Production code:**
- `scripts/worktree_closeout_migrate.py` (Task 1)
- `scripts/worktree_closeout_migrate.py` (Task 2)
- `scripts/done_run.sh` (Task 2)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` (Task 1)
- `scripts/test_worktree_closeout_migrate.py` (Task 2)
- `scripts/test_done_run_wrapper.py` (Task 2)

**Out of scope; reject unless plan-related:**
- New retention state, registries, or gates; reason: current manifests and gate output remain the source of truth.
- Changes to branch adjudication, `OUTCOME` classification, or removal authority; reason: this plan corrects reporting only.
- Formal-only parser, environment, pin, fixture, naming, and wording residuals; reason: the personal profile defers formal-hardening and the plan first preserves those findings in a separate open backlog item.

## Validation Commands

At execution, run the focused existing regression suites for worktree closeout reporting and the done setup wrapper, then run:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py scripts/test_done_run_wrapper.py -q
python3 scripts/plan_readiness.py docs/history/plans/2026-10-29-gate-removal-task2-review-residues.md --pre-round
```

### Task 1: State only verified ancestry evidence

Context surface: the `Branch-only closeout` and `Proven branch OID` terms, and this task.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`

Evidence:
- `_gate_branch_closeout` handles worktree and branch-only modes; its ancestry-accounted report currently says one live worktree binds the branch and migrated artifacts were verified.
- Branch-only mode has no linked worktree. The helper already receives `branch_only` and emits the same proven branch OID and ancestry result.

Acceptance:
- [ ] Given a branch-only closeout with an ancestry-accounted tip, expect the report to name the branch, proven OID, and ancestry result without claiming a live worktree or migrated artifacts. Given an ancestry-accounted closeout with a linked worktree, expect the report to state only verified branch facts. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given either closeout mode, expect the structured disposition, existing guard results, and removal instructions to remain intact. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add focused regression coverage: given ancestry-accounted branch-only and linked-worktree closeouts, expect each report to preserve the proven OID and avoid claims unsupported by that mode. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: report gate-removal ancestry accurately` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Preserve retained-branch evidence in setup output

Context surface: the `Retained branch` term, and this task.

Files:
- `scripts/done_run.sh`
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_done_run_wrapper.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `cmd_setup` in `scripts/done_run.sh`
- `_sweep_branch_report_line` in `scripts/worktree_closeout_migrate.py`
- `cmd_sweep` in `scripts/worktree_closeout_migrate.py`

Evidence:
- `cmd_setup` filters the fail-open sweep output to selected prefixes. Skip and retained evidence can be emitted on other lines and is omitted from the setup report.
- `_evaluate_candidate` returns a skip reason with empty info for branch-backed candidates that stop before gate adjudication; `cmd_sweep` then prints only the worktree path and reason and emits no `branch-report` line. The setup filter also excludes these `report:` lines.
- The sweep must resolve the candidate branch OID when available and report an explicit unknown OID otherwise; the setup wrapper relays that observation without reclassifying it.

Acceptance:
- [ ] Given a branch-backed candidate skipped before gate adjudication, expect sweep output to include its branch name, resolved branch OID or `unknown`, and skip reason; expect setup's summary to preserve those fields. Given a candidate with no branch identity, expect the path and skip reason without invented branch data. Given accounted-branch output, expect its existing summary behavior to remain stable. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a missing sweep helper or a sweep command failure, expect setup to continue through its fail-open path and preserve the existing `OUTCOME` classification. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add focused regression coverage: given dirty, post-landing, live-session, and missing-completed-twin skips on branch-backed candidates, expect sweep and setup output to include the branch, OID or `unknown`, and skip reason; given a candidate without a branch identity, expect no invented branch or OID. Given retained and accounted output, expect existing disposition and summary behavior to remain stable. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: retain branch details in setup reports` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Preserve the deferred formal residues

Context surface: the selected backlog origin and this task.

Files:
- `docs/history/backlog/2026-10-21-gate-removal-task2-review-deferred.md`
- `docs/history/backlog/`

Acceptance:
- [ ] Given the selected origin's in-scope report defects and its unrelated formal-only findings, expect a separate open backlog item to preserve every deferred finding's evidence and formal-hardening deferral before the origin is closed. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the separate record is created but Tasks 1 and 2 are incomplete, expect the selected origin to remain open; close it only after the split and both tasks are complete. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: preserve deferred gate-removal residues` [class: IMPLEMENTATION_REQUIRED]
