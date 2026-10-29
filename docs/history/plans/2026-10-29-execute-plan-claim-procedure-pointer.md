# Plan: Repair references to split-out maintenance procedures
Backlog origin: docs/history/backlog/2026-10-11-execute-plan-dangling-execution-claim-pointer.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-29-plan-review-execute-plan-claim-procedure-pointer-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-11-execute-plan-dangling-execution-claim-pointer.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)

## Terms

- **Split-out procedure**: An operative paragraph moved from `maintenance/prompt-templates.md` into a dedicated maintenance module.
- **Module-level reference**: A reference to the remaining pointer stubs or to the historical source of an extracted module, rather than a direction to find an operative procedure in the old file.

## Why

The execute-plan skill points its EXECUTION CLAIM procedure to a file that no longer contains the paragraph. The origin also requires an audit for other links to procedures moved from that file; the operative references must identify their current owning modules.

## Gist & Examples

Title: Repair references to split-out maintenance procedures

TLDR: Point operative instructions to the maintenance modules that now own their procedures, improving code quality by removing stale cross-references.

Before: Execute-plan and maintenance instructions direct readers to procedures and child blueprints in `maintenance/prompt-templates.md`, which now contains only pointer stubs.

After: Procedure references name `template-authoring.md` or `template-execution.md`, and the maintenance index points to the current child modules.

Edge cases: Update only verified operative pointers; preserve changelog history, extracted-module provenance, and references to content that remains in the old file.

## Outcome

Repair the execution-claim pointer and the other verified operative references to maintenance procedures moved out of `prompt-templates.md`.

- Readers reach the current module for each referenced procedure or child blueprint.
- Historical and module-provenance references remain intact, while no operative instruction points to a moved paragraph in the old file.

## Gate delta

No machinery, gate, refusal class, fence, protocol layer, schema field, or dispatch condition is added, removed, or changed.

## Assumptions

- `template-authoring.md` and `template-execution.md` are the current modules for the moved authoring and execution procedures. Evidence: each file contains its corresponding operative child payload and claim instructions.
- The origin's acceptance audit includes verified operative pointers to other paragraphs moved out of `prompt-templates.md`, so this plan fixes them in the same change. Evidence: the origin says to verify that no other pointers to split-out paragraphs remain; the audit found stale references in the files listed in Task 1.
- References in changelogs and extracted-module provenance lines describe history, and the two remaining pointer stubs in `prompt-templates.md` remain its content. Evidence: the changelog is dated historical text, the extracted modules identify their source, and the old file contains only the deferred-corpus and registry-task stubs.
- The source audit is limited to operative links to moved procedures or blueprints. Generic historical mentions and references to the surviving stubs are not defects.

Decision points requiring a grill: none remain.

## Evaluation Criteria

- **Correctness:** Every operative pointer found by the origin audit names the module that currently owns the referenced procedure or blueprint.
- **Scope control:** Change only stale links; preserve procedure text, runtime behavior, historical citations, and references to surviving stubs.
- **Done when:** The EXECUTION CLAIM link resolves to `template-execution.md`; the verified authoring and execution procedure links resolve to their current modules; and a review of remaining audit matches finds only valid history, provenance, or surviving-stub references.
- **Ship when:** No external release or human-owned prerequisite applies.

## Review Scope

**Documentation:**
- `agents/skills/execute-plan/SKILL.md` (Task 1)
- `agents/skills/execute-plan/worktree-first.md` (Task 1)
- `agents/skills/maintenance/SKILL.md` (Task 1)
- `agents/skills/maintenance/failure-cap.md` (Task 1)
- `agents/skills/maintenance/guards.md` (Task 1)
- `agents/skills/maintenance/scheduling.md` (Task 1)
- `agents/skills/maintenance/state-file.md` (Task 1)
- `agents/skills/maintenance/survey-arms.md` (Task 1)
- `agents/skills/maintenance/template-unblock.md` (Task 1)
- `agents/skills/maintenance/zcode.md` (Task 1)

## Validation Commands

```bash
set -eo pipefail
rg -q 'EXECUTION CLAIM,.*agents/skills/maintenance/template-execution.md' agents/skills/execute-plan/SKILL.md
! rg -q 'EXECUTION CLAIM,.*agents/skills/maintenance/prompt-templates.md' agents/skills/execute-plan/SKILL.md
rg 'prompt-templates.md' agents/skills/ | grep -v template- || test "$?" -eq 1
python3 scripts/plan_readiness.py docs/history/plans/2026-10-29-execute-plan-claim-procedure-pointer.md
```

Review each remaining ripgrep match: history, extracted-module provenance, and references to surviving pointer stubs may remain; an operative direction to a moved procedure may not. The explicit target assertions run before the inventory so a later successful command cannot mask a failed pointer check.

### Task 1: Re-home operative links to the current procedure modules

Context surface: The EXECUTION CLAIM paragraph in `agents/skills/maintenance/template-execution.md`, the AUTHORING CLAIM and pre-execution re-verification duties in `agents/skills/maintenance/template-authoring.md`, the remaining stubs in `agents/skills/maintenance/prompt-templates.md`, and the operative references identified by the origin audit.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/failure-cap.md`
- `agents/skills/maintenance/guards.md`
- `agents/skills/maintenance/scheduling.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/survey-arms.md`
- `agents/skills/maintenance/template-unblock.md`
- `agents/skills/maintenance/zcode.md`

- [ ] The EXECUTION CLAIM, authoring-claim, pre-execution re-verification, execution landing, and pending-landing references each point to the module that owns the referenced procedure. [class: IMPLEMENTATION_REQUIRED]
- [ ] Current child-blueprint references identify the authoring and execution modules; no operative pointer in the listed files directs readers to a procedure or blueprint moved out of the former source file. [class: REPOSITORY_TEST]
- [ ] Historical changelog and extracted-module provenance references remain unchanged, and the surviving pointer-stub references remain accurate. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: repair split maintenance procedure pointers` [class: IMPLEMENTATION_REQUIRED]
