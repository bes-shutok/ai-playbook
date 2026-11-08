# Learn Step 1.9 can mistake a general lesson for project-issue coverage

- **Filed:** 2026-11-08, learn Step 1.8 capture-freshness re-probe
- **Status:** open
- **Workflow:** learn skill (`agents/skills/learn/step-1-extract.md`), Step 1.9
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class
- **Severity:** Medium
- **Skill/step:** `agents/skills/learn/step-1-extract.md`, Step 1.9 project issue backlog capture
- **Environment context:** Codex, 2026-11-08, canonical repository skill copy
- **Suspected root area:** Step 1.9 candidate coverage classification when an existing lesson describes the general defect family but does not track the concrete project fix
- **Source reference:** `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md`, Task 2; related project row `docs/history/backlog/2026-11-08-execution-claim-fixture-restores-caller-environment.md`
- **Dedup probe:** searched open backlog filenames and bodies plus both rolling logs for Learn Step 1.9 capture omissions, lesson-as-coverage dismissals, and project-row commit gaps. `docs/history/backlog/2026-11-02-primary-tree-backlog-writes-no-commit-leg.md` covers a missing commit leg after capture, not a candidate dismissed before filing; no row covers this classification miss.

Driving force: reliability.

## Observed versus expected

The Task 2 boundary note recorded no project backlog row because lesson #232 was judged to cover environment leakage. The run's feature note describes a concrete test-fixture cleanup that discarded a caller's environment value. Lesson #232 explains the general state-restoration principle, but does not track or dispatch the required fixture change. The final capture-freshness re-probe caught the mismatch and filed the project issue separately.

Step 1.9 should keep a concrete unfixed code issue as a project backlog candidate unless an exact row, covering plan, or landed patch owns that fix. Shared vocabulary or a general lesson about the failure family is not a fix-completion witness.

## Suggested correction

Clarify Step 1.9's dedupe/coverage distinction in the existing capture rule: match project candidates by their fix surface and completion witness, not only by a shared general principle. Keep Step 1.8's self-omission re-probe; this witness shows why it must compare earlier capture outcomes against the concrete unfixed work in the final evidence set.

## Why not fixed now

This session corrected the capture by filing the distinct project issue row and its investigation prompt. Editing the learn skill is outside this cleanup and closeout pass; the wording change belongs to a later skills-corpus authoring run.
