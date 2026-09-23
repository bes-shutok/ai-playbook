# Backlog: plans authoring rule 36's duplicate-insertion simulation is one-directional

Captured: 2026-09-23 (source: p50 scheduler state-durability leftovers authoring session, review round r3)
Status: open
Priority: high
Workflow: backlog

## Which skill and step

`agents/skills/plans/SKILL.md`, Validation Commands authoring rule 36 ("Region-scope exact-count pins when a sanctioned edit can duplicate the phrase across surfaces").

## Observed vs expected

Observed: during a plan review loop, a fold added a new whole-file count gate (expected count 2) whose searched span was a strict superstring context of an EXISTING gate's span (expected count 1, the anchor needle). Both gates targeted the same file. Post-landing simulation showed the file carrying the anchor span three times (the anchor bullet plus the two mandated join entries), so the older count-1 gate became deterministically unsatisfiable while the new count-2 gate passed. The blind re-probe worker caught it as a blocking regression only at the NEXT round; the fold's own mechanical audit (bash syntax check, RED-today re-run, pin-span uniqueness over the plan text) did not include a joint post-task satisfiability simulation of ALL count gates over the same target file.

Expected: rule 36's "simulate the duplicate once at authoring time" step runs in both directions. When a fold adds any gate or insertion touching a file that already carries count gates, the authoring simulation applies ALL prescribed insertions for that file to a temp copy and runs the COMPLETE count-gate set against it (old and new gates together), verifying every expected count simultaneously - not only the new gate against the old spans.

## Reproduction evidence (trimmed)

- Gate A: `count1 file 'Anchor phrase'` (expect 1) pinning a prescribed bullet's opening anchor.
- Fold adds: gate B counting `'the Anchor phrase'` (expect 2) over the same file, because a sibling writer-join task appends two list entries each carrying that phrase.
- Post-task file: anchor bullet (1) + join entries (2) = the superstring count for gate A reads 3; gate A fails on the first post-task execution while gate B passes.
- The review round staging the fold verified "gate B's count is satisfiable" without re-simulating gate A; the regression surfaced one round later as blocking.

## Environment context

Runtime: zcode agent session; playbook repo, worktree at main 206a7f7b plus the fold revisions; vendored runtime equals repo copy. Date 2026-09-23. The plan under review is `docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md` (the anchor gate and the writer-join gate live in its Validation Commands block; the fix applied there re-anchored the older gate's needle to a date-qualified span, count 1, jointly satisfiable with the join gate's count 2).

## Suspected root area

Rule 36's text scopes the simulation to "the duplicate" of the NEW insertion against existing pins. The rule should name the joint direction: every fold that adds or moves a count obligation on a file re-simulates the file's full count-gate set (existing plus new) against a temp copy carrying all prescribed insertions, in the same mechanical-audit pass rule 22 already mandates for pin/text contracts. Sibling surface to check for the same one-directional wording: the review-plan testing lens's fold-verification checklist.
