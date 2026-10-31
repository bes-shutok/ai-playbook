# Plan: Give the empty-owned-set refusal an attainable remedy
Backlog origin: docs/history/backlog/2026-10-21-gate-removal-empty-owned-set-remedy.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-27-plan-review-gate-removal-empty-owned-set-remedy-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-21-gate-removal-empty-owned-set-remedy.md (session 01a17c5c-b1b6-7c02-8203-5bc9bf7f9ab3)

## Terms

- **Empty owned set**: The `gate-removal` refusal reached when the plan header has no review-record citation and the optional claims file names no record paths.
- **Claims file**: A newline-delimited file whose nonempty lines name review-record paths for `gate-removal` to verify.

## Why

When the owned set is empty, `gate-removal` currently recommends running capture and migrate, but migration cannot create a missing plan-header citation or claims-file entry. A caller needs to add an attainable review-record input before retrying the same fail-closed gate.

## Gist & Examples

Title: Give the empty-owned-set refusal an attainable remedy

TLDR: Replace the unattainable capture-and-migrate advice on the empty-owned-set refusal with the citation or claims-file input that can satisfy it.

Before: The refusal recommends migration even though the plan has no citation and the claims file contributes no record path.

After: The refusal tells the caller to add a `Plan review record:` or `Plan review:` citation, or supply a `--claims` file listing review-record paths, then retry the gate.

Edge cases: Keep the empty-set refusal and exit outcome fail-closed; preserve the migrate remedy for absent records and worktree-only sibling records, and preserve the citation-correction remedy for paths outside the reviews home.

## Outcome

Give the empty-owned-set refusal its own actionable remedy line. Keep the existing gate condition, exit code, and refusal outcome unchanged. The diagnostic probe against the current command reproduced the empty-set refusal and its capture-and-migrate advice; the source shows that the claims file contributes nonempty record paths to the same owned-set calculation.

The smallest design changes one diagnostic string and its focused regression assertions. A separate admission path or a new gate is unnecessary: `--claims` already supplies record paths, and an ordinary plan can carry a review citation in its header.

## Gate delta

No gate or refusal behavior changes. The empty-owned-set refusal remains blocking with exit 1 and `OUTCOME: fail`; only its remedy text changes.

## Assumptions

- A citation or claims-file entry must name review records that exist under the primary reviews home before `gate-removal` can pass. Evidence: the current gate verifies both inputs against that home after the empty-set check.
- The capture-and-migrate remedy remains correct for missing review records and worktree-only stats siblings. Evidence: those later refusal classes print `_GATE_REMEDY_LINE` after identifying absent records.
- The citation-specific remedy remains correct for citations that resolve outside the reviews home. Evidence: the refused-citation branch prints `_GATE_CITATION_REMEDY_LINE`.
- Adding a `--claims`-only admission form for an absent plan charter is outside this origin's Expected behavior; this plan only makes the existing empty-set refusal actionable. Evidence: the origin asks for a separate remedy line and does not require changing operand admission.

Decision points requiring a grill: none remain.

## Evaluation Criteria

- **Correctness:** Empty owned sets remain refused, and the diagnostic names a citation or claims-file input that can make the set nonempty. Other refusal classes retain their class-specific remedy.
- **Maintainability:** Keep the remedy adjacent to the empty-set branch and assert its class-specific wording in the existing command test.
- **Scope control:** Change no admission, artifact-ownership, identity, or removal checks; do not add machinery.
- **Done when:** The command emits the actionable remedy for empty sets, its regression test distinguishes that message from the migration remedy, and the existing worktree-closeout test suite passes.
- **Ship when:** No external release or human-owned prerequisite applies.

## Review Scope

**Explicit must-fix:**
- `scripts/worktree_closeout_migrate.py` (Task 1)
- `scripts/test_worktree_closeout_migrate.py` (Task 1)

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_worktree_closeout_migrate.py'
python3 scripts/plan_readiness.py docs/history/plans/2026-10-27-gate-removal-empty-owned-set-remedy.md
```

### Task 1: Give empty-owned-set refusals their own remedy

Context surface: `cmd_gate_removal`'s empty-owned-set branch, class-specific refusal messages, and its existing command-level test.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

- [x] Empty-owned-set refusal still returns exit 1 with `OUTCOME: fail`, and its remedy names adding a `Plan review record:` or `Plan review:` citation, or passing `--claims` with record paths, before retrying `gate-removal`. [class: IMPLEMENTATION_REQUIRED]
- [x] Missing records and worktree-only stats siblings retain the capture-and-migrate remedy; citations or claims outside the reviews home retain the citation-correction remedy. [class: REPOSITORY_TEST]
- [x] The focused test distinguishes the empty-set remedy from the capture-and-migrate remedy while preserving assertions for the refusal class and final outcome. [class: REPOSITORY_TEST]
- [x] Commit: `fix: make empty gate-removal remedy actionable` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

The covering plan's origin row `docs/history/backlog/2026-10-21-gate-removal-empty-owned-set-remedy.md` is deleted at this archive per the covered-row rule; this section is the row's durable home. The row's 2026-10-27 witness (the ad-hoc-run shape with no first-class input form: no plan file means the owned-set extraction reads no citations, and the `--branch`/`--worktree` mutual exclusion forces two invocations) is out of this plan's Expected behavior by the row's own scope-out and remains an open low-priority friction; any revival starts from this section. The landing commit of this archive is the witness for the deletion.
