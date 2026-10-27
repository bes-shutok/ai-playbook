# Plan: Plan Authoring Branch Manifest Handoff

Backlog origin: docs/history/backlog/2026-10-27-plan-authoring-branch-manifest-handoff.md
Driving force: efficiency
Plan review record: .ai-playbook/reviews/2026-10-27-plan-review-plan-authoring-branch-manifest-handoff-r*.md
Execution budget: 1.5h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-27-plan-authoring-branch-manifest-handoff.md (session 01a17c5c-b1b6-7c02-8203-5bc9bf7f9ab3)

## Terms

- **Canonical plan slug**: the filename or charter-directory name after the shared date-prefix and extension rules in execute-plan.
- **Migration manifest**: the existing JSON output from `worktree_closeout_migrate.py migrate`, including its branch record.
- **Exact-tree accounting**: the gate's full-tree comparison proving that branch content matches destination history without ancestry.

## Why

Plan-authoring closeout writes its authentic source-branch record under the worktree's done-session directory, while gate-removal looks in the primary checkout's plan-slug directory. The missing handoff leaves the authoring branch retained after the plan and review artifacts have landed, requiring a separate recovery run.

## Gist & Examples

TLDR: Hand off the done-run branch manifest at the shared plan-slug path, so plan closeout can finish branch accounting efficiently.

Before: the done-run manifest records the source branch in the worktree, but plan closeout calls gate-removal without that manifest path. Gate-removal skips branch accounting and retains the branch.

After: done-run writes its existing manifest to the primary checkout's canonical `tmp_dir/execute-plan/<slug>/closeout-migration.json`; plans passes that exact path through `--migration-manifest`. Execute-plan keeps its current slug and default filename contract.

## Outcome

A plan-authoring closeout supplies its existing branch-bound migration record to the existing gate-removal check.

- The manifest lands at the primary plan-slug path and the plans Final Step supplies that path explicitly.
- Existing artifact verification, branch identity, ancestry or exact-tree accounting, and expected-OID deletion remain unchanged.
- Missing or invalid branch evidence keeps the existing refusal or named skip; it never authorizes removal.

Gate delta: no new or changed gate. Reuse the migration helper's current schema and gate-removal's explicit manifest operand.

## Assumptions

Decision points requiring a grill: none remain.

- The one-owned-plan arm's `PLAN_SLUG` calculation in `done_run.sh` is the canonical source for this handoff. Evidence: the existing block derives it before migration.
- The helper can write its existing manifest directly to the primary destination. Evidence: `migrate --manifest` accepts a caller-selected path and appends the latest branch record.
- The canonical `closeout-migration.json` path is shared safely: gate-removal uses the latest branch record, and execute-plan already writes that filename under the same slug. No execute-plan slug change is needed.
- A separate manifest copy step or new schema adds work without improving the current identity and content proof; reusing the helper destination is the simpler design.

## Evaluation Criteria

- Correctness: the done-run producer and plans caller resolve one identical primary manifest path.
- Compatibility: execute-plan's date-prefix stripping and default manifest lookup stay unchanged.
- Safety: the existing branch identity and landed-content proof still control deletion.

Done when focused producer and caller regressions pass, the full affected script suites pass, and plan readiness passes.
Ship when none; this is repository-local workflow behavior.

## Documentation Impact Assessment

Only the plans Final Step caller instruction needs updating. Execute-plan already documents the canonical slug and filename; do not duplicate or change that contract. The new producer and caller details extend existing steps, so add no new top-level section.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/done_run.sh` (Task 1)

**Workflow instructions:**
- `agents/skills/plans/SKILL.md` (Task 2)

**Tests:**
- `scripts/test_done_run_wrapper.py` (Task 1)
- `scripts/test_worktree_closeout_migrate.py` (Task 2)

**Plan-related extension:** findings causally required to complete these handoffs or preserve the stated branch proof remain in scope. Other findings require a direct contract link to this plan.

**Out of scope:**
- Changes to gate-removal behavior or manifest schema; the current caller-selected path and branch checks already exist.
- Changes to execute-plan's slug rule; its current canonical path is the shared destination.
- Empty-owned-set, missing-baseline, and dated-plan lookup incidents; their origins and remedies remain separate.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_worktree_closeout_migrate.py'
```

### Task 1: Write the migration manifest at the primary plan-slug path

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `plan_session_slug` in `scripts/done_run.sh`
- `_cmd_migrate_transfer` in `scripts/worktree_closeout_migrate.py`

- [x] For exactly one owned plan, done-run derives the canonical plan slug and passes the primary checkout's canonical plan-slug manifest destination as the existing `migrate --manifest` operand. [class: IMPLEMENTATION_REQUIRED]
- [x] The run-id manifest and valid baseline-skip path retain their current behavior for non-plan or degraded closeout arms. [class: IMPLEMENTATION_REQUIRED]
- [x] Wrapper regression coverage proves the migration destination is the primary path and preserves the helper's branch record. [class: REPOSITORY_TEST]
- [x] Run the focused wrapper regression and commit the task change. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pass the canonical manifest into plan gate-removal

Files:
- `agents/skills/plans/SKILL.md`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`

- [x] The plans Final Step derives the same canonical path and supplies it with `--migration-manifest` to the existing gate-removal invocation. [class: IMPLEMENTATION_REQUIRED]
- [x] The cited regression coverage confirms the explicit path remains authoritative and the gate still skips when that explicit manifest is absent. [class: REPOSITORY_TEST]
- [x] Replace or shorten the existing plans Final Step wording so the caller change leaves the skill's operative text byte-neutral or shorter, preserving every current closeout duty. [class: IMPLEMENTATION_REQUIRED]
- [x] Execute-plan's shared slug rule and default `closeout-migration.json` lookup remain unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Artifact, branch identity, ancestry or exact-tree, quiesce, and expected-OID removal proof remain required. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused migration-gate regression and commit the task change. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-27-plan-authoring-branch-manifest-handoff.md: covered by this plan (Status: covered recorded at the authoring landing 2f3d4c09f; the origin file deleted at this archive per the origins-closure disposition, this archived plan recording the disposition; the covering execution landing is the witness).
