# Plan: coverage-gate self-exemption accepts byte-identical checkpoint twins

Authoring claim: 2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md (session sess_06232336-1f93-441c-aea2-72855eb1512f)

Backlog origin: docs/history/backlog/2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md
Driving force: correctness (declared outside the closed taxonomy; implemented anyway because the gate's false conflict is a witnessed correctness defect in an existing guard, and park-triage would take it as a real-fix row rather than park it)
Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-coverage-gate-checkpoint-twin-self-exemption-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 1h

## Terms

- coverage gate: `scripts/check_plan_origins_closed.py --check-coverage`, the plans lifecycle's duplicate-origin gate run before landing.
- declaring plan: the plan operand the gate is invoked with; the artifact currently being certified.
- scan surface: the directories `_find_covering_citers` enumerates for citers (active, deferred, completed, and rejected plan directories).
- checkpoint twin: a second on-disk plan file with byte-identical content to the declaring plan at a different path (created when a certification checkpoint commits the plan bytes to main while the authoring worktree still declares them).
- self-exemption: the skip in `_find_covering_citers` that prevents the declaring plan from being reported as its own covering citer.

## Why

The coverage gate's self-exemption is a pure path comparison. When the certification checkpoint has placed identical plan bytes on main, a run from the authoring worktree names the main twin as the covering plan and fails a correct certification. The witnessed workaround (re-running with a primary-checkout operand) is undocumented folklore.

## Gist & Examples

TLDR: the duplicate-origin coverage gate exempts a scanned plan whose bytes equal the declaring plan's when that plan sits directly in the active plans directory, not only an identical path, so a worktree-relative gate run no longer fails on a checkpoint twin.

Before: plan bytes land on main at the certification checkpoint; the gate run from the authoring worktree (`--check-coverage <worktree>/docs/history/plans/<plan>.md`) reports the primary twin as the covering citer and exits 1 on a correct certification.

After: the same worktree-relative run passes, because the scanned twin's bytes equal the declaring bytes and the twin sits on the active scan surface. A twin that differs in bytes from the declaring plan is still reported as a citer, so a genuinely distinct same-origin plan keeps its conflict; a byte-identical copy on a non-active surface (completed, deferred, rejected) is also still reported, so the state-specific remedy the gate exists to emit is never swallowed.

Edge cases: a scanned plan that is unreadable keeps the existing skip; a declaring plan that cannot be read falls back to the path-only comparison (the gate's own text read has already failed by then in practice, so behavior is unchanged for real invocations).

## Outcome

The duplicate-origin coverage gate accepts a byte-identical checkpoint twin as the declaring artifact instead of reporting a false coverage conflict.

- A gate run from an authoring worktree after the certification checkpoint passes without the undocumented primary-path workaround.
- A scanned plan with the same bytes as the declaring plan is exempted when its parent directory is exactly the active plans directory; byte-identical copies on non-active surfaces (completed, deferred, rejected) are still reported.
- A scanned plan citing the same origin whose bytes differ from the declaring plan is still reported as a covering citer.
- Gate delta: none, the change widens `_find_covering_citers`' existing self-exemption predicate (removing the path-only exemption's false-conflict refusal class witnessed 2026-11-02) and adds no gate, refusal class, field, or protocol layer; no machinery is added or removed.

## Assumptions

- The declaring plan and its checkpoint twin hold byte-identical content in the witnessed failure (basis: backlog row evidence, checkpoint d75130dcd and landing e79617d9 for plan 2026-11-02-maintenance-self-heal-first-on-blocks).
- Byte equality is the right granularity: any content difference (even a one-byte mutation) means a genuinely edited plan that must still be flagged (basis: the backlog row's requirement that a twin differing in bytes still counts as a citer).
- The exemption is intentionally scoped to the exact active plans directory (the twin's parent directory must be the active plans directory itself, never a subdirectory): the checkpoint twin lives there, and non-active surfaces carry decided plans whose remedy must survive byte identity (basis: the gate's REMEDY_BY_STATE remedies). This directory-exact scoping also avoids the double-scan's effect on the exemption decision: the pre-existing rglob recursion still double-scans completed/, deferred/, and rejected/ under the active label, and the non-active-twin checkbox pins that two-line report behavior as unchanged; only the exemption, never the scan surface, is scoped.

Decision points requiring a grill: none remain.

## Standing constraints

- Python in `scripts/` follows `projects/.ai-playbook/python_guidelines.md`; repo-local trusted scripts run with plain `python3`.
- The script's outcome contract (`scripts/OUTCOME_CONTRACT.md`) semantics are unchanged: the fix only widens the exemption predicate, never the exit codes or output shapes.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the exemption matches byte-identical twins whose parent directory is exactly the active plans directory, still flags bytes-differing citers, and still flags byte-identical copies on non-active surfaces
- maintainability: the predicate change is localized to `_find_covering_citers` with no new module-surface or config

**Done when:**
- the automated twin tests (mkdtemp fixture with a byte-identical twin at a second path) pass and are RED before the predicate change, the RED demonstrated through the subprocess driver (the twin fixture run expects exit 1 naming the twin before the fix, exit 0 after)
- the second Validation Command is a smoke check only: it exercises the gate end-to-end with the new predicate compiled in as a regression tripwire and is not the authoritative verification

**Ship when:**
- none, repository-internal change only

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_plan_origins_closed.py` (Task 1)

**Tests:**
- `scripts/test_check_plan_origins_closed.py` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/check_prompt_log_origins.py`; separate gate, separate fix family
- `docs/maintenance/development_lessons.md`; lessons are harvested by the learn flow, not edited by this plan

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_plan_origins_closed.py -q
python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md --repo-root .
```

### Task 1: Byte-identical self-exemption in `_find_covering_citers`

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_plan_origins_closed.py`
- `scripts/test_check_plan_origins_closed.py`

Primary class anchors:
- `_find_covering_citers` in `scripts/check_plan_origins_closed.py`

Implementation notes (decisions recorded, not guesses): the declaring plan's bytes are read once with `read_bytes()` at the `run_check_coverage_mode` call site and passed into `_find_covering_citers`; that read is wrapped in `except OSError` yielding a None sentinel (no declaring bytes available - a directory operand naturally lands here via IsADirectoryError, and the path-only comparison alone applies); the comparison is raw `read_bytes()` equality on both operands (never the errors='replace' decoded text), and each scanned plan is read ONCE as bytes with both the equality comparison and the decoded text (decode with errors='replace' from the same bytes) derived from that single read, so the predicate and origin extraction observe one snapshot; the directory-exact comparison is performed on resolved paths (`plan.parent.resolve() == active_plans_dir.resolve()`, the active dir itself resolved at scan_dirs construction); the content-equality exemption applies only when a scanned citer's bytes equal the declaring bytes AND the citer's parent directory is exactly the active plans directory (never a subdirectory of it); unbounded `read_bytes()` size is accepted for this trusted repo-local gate (no size cap added).
- [x] `_find_covering_citers` delivers `byte-identical twin exemption on the active surface`: given the active plans directory itself holding a plan whose raw bytes (read_bytes) equal the declaring plan's bytes at a different path, expects the twin to be skipped (not reported as a covering citer) [class: IMPLEMENTATION_REQUIRED]
- [x] `_find_covering_citers` delivers `bytes-differing twin still flags`: given a scan surface holding a plan citing the same origin whose bytes differ from the declaring plan's by a minimal one-byte mutation landing in the plan body outside the origins block, expects the conflict to be reported [class: REPOSITORY_TEST]
- [x] `_find_covering_citers` delivers `byte-identical non-active twin still flags`: given byte-identical twins of the declaring plan in the completed directory AND in the deferred and rejected subdirectories, expects each twin to yield two conflict lines (one under the active-pass default first-landed-wins remedy, one under the twin's state-specific remedy, the pre-existing rglob double scan), so the test asserts remedy presence per twin rather than a conflict count [class: REPOSITORY_TEST]
- [x] `run_check_coverage_mode` delivers `directory declaring plan keeps path-only exemption`: given a well-formed directory-shaped declaring plan (PLAN.md charter with a resolving origins line plus a tasks/ file with a `### Task N:` heading) placed outside the active plans scan surface, driven subprocess-style through --check-coverage, expects exit 0, the 'coverage gate clean' output naming no covering citer, no crash, no traceback, no content comparison [class: REPOSITORY_TEST]
- [x] `run_check_coverage_mode` delivers `directory fixture vacuous arms stay excluded`: neither a bare directory (refused by the plan-shape gate) nor a no-origins or unresolvable-origins charter (printing the 'no origins' trivially-clean line) satisfies the exercised checkbox, so the pinned clean output can only come from the exercised path-only branch [class: REPOSITORY_TEST]
- [x] `_find_covering_citers` delivers `path-equal plan stays exempt`: given the declaring plan itself on the scan surface, expects the existing skip (no self-report) [class: REPOSITORY_TEST]
- [x] `_find_covering_citers` delivers `unreadable scan-surface citer keeps the existing skip`: given a scan-surface citer file made unreadable (chmod 000, restored in cleanup), expects the citer to be neither reported nor crashed and the exit contract shape preserved, the test carrying a `@unittest.skipIf(not hasattr(os, "geteuid") or os.geteuid() == 0, "chmod 000 is still readable as root")` guard honored under both the pytest collector and the plain unittest runner [class: REPOSITORY_TEST]
- [x] Run → expect RED: the behavior's failing check (tests, fixtures, and commands are selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: exempt byte-identical checkpoint twins from the coverage gate's self-exemption` [class: IMPLEMENTATION_REQUIRED]
