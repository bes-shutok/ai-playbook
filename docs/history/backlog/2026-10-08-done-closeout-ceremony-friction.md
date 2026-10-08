# Backlog: simplify done ceremonies that delay local closeout

- **Filed:** 2026-10-08, operator-directed
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed closeout friction
- **Class:** fix-class
- **Driving force:** simplicity + performance
- **Skill/step:** `agents/skills/done/SKILL.md`, Steps 0, 2, 3, and 6; manifest creation and recovery, docs-branch sync, and pre-commit `archive-ceremony`
- **Related work:** `docs/history/plans/completed/2026-10-07-done-closeout-cost-and-skill-scope.md`

## Problem

The `done` closeout can delay an authorized local commit behind ceremonies for unrelated review and plan artifacts. In this session, an older incomplete run manifest claimed 31 review artifacts. New manifest setup refused to proceed while that boundary remained unresolved. Recovery then refused because 11 claimed review files were absent from the docs branch, even though the user had explicitly directed that docs-branch sync be skipped for this session. The note-backed recovery option did not apply to owned review artifacts, so `done` stopped before lesson capture, the remaining gates, or the requested commit.

This compounds earlier observed friction: `archive-ceremony` treated a deliberately rejected plan as unfinished implementation, and manifest creation treated another worktree's in-progress manifest as an undisposed interrupted run. The existing closeout-cost plan addressed runtime-helper recovery and prose duplication, but its rationale retained the broader guard stack. These sessions expose additional costs in the artifact and recovery dependencies that plan did not cover.

## Evidence

- In a 2026-10-08 closeout, the operator moved a plan to the rejected archive and preserved its contents. The pre-commit `archive-ceremony` gate then failed on its 36 unchecked task boxes and offered only completion checkboxes or a marked backfill record. The gate derives plans from completed, deferred, and rejected archive directories, even though a rejected plan has no implementation work to certify (`scripts/done_sweep_gates_lib.py`).
- A follow-up closeout to commit the plan review certificate could not write its run manifest while a different worktree's `complete:false` manifest remained in the shared done-session directory. The peer manifest later completed. The refusal delayed the certificate commit and required working around the ordinary manifest path. This concurrency case was observed in the same 2026-10-08 session.
- The done manifest writer's comment assumes an incomplete manifest under the shared directory is a past interrupted run because the lock is exclusive per checkout. Separate worktrees have separate checkout locks, so that assumption does not establish that another worktree's manifest is abandoned (`scripts/done_sweep_gates_lib.py`, `write-manifest` undisposed-interrupted handling).
- In the 2026-10-08 closeout, candidate classification refused to write a new manifest while an earlier incomplete manifest remained. That manifest claimed 31 review artifacts; a disk check found 11 absent from the docs branch, while their local ignored copies remained available. Recovery refused on the first absent owned-review path. The user had directed that docs-branch sync be skipped, and the supported note-backed recovery did not cover owned reviews. The closeout therefore stopped before learn, the remaining gates, and the local commit.

## Expected

Review the closeout from the operator's perspective and decide whether to remove or narrow these ceremonies. Compare at least these simpler options:

- Apply checkbox and execution-review requirements only to completed plans; rejected plans should preserve their rejection state without pretending their tasks were executed.
- Let an active peer worktree's manifest coexist with a new run, or use the smallest owner/liveness distinction needed to refuse only genuinely interrupted boundaries.
- Remove either ceremony if its closeout value is not demonstrated by the original incident and current consumers. Do not retain a check only because it already exists, and do not add another ledger, gate, or recovery ceremony to manage it.
- Decouple a local project commit from docs-branch publication of ignored review artifacts, or remove the docs-branch witness as a prerequisite for closing a project run, if the witness does not protect a distinct data-loss or integrity property.
- Reassess whether a run manifest should make all carried review artifacts prerequisites to starting or recovering a new local closeout. Consider removing that dependency when the current run does not change those reviews and their local copies remain intact.

Keep refusals that prevent actual data loss or false completion, but tie them to the artifact's real disposition and owner. The simpler path should let a user-directed local commit complete when docs-branch sync is explicitly deferred, while keeping a genuinely interrupted project run recoverable. Do not add another ledger, gate, or recovery ceremony to manage the simplification; use existing run manifests, session records, and commit history as evidence.

## Source

- Operator request to capture `done` closeout friction observed on 2026-10-08 and assess simplification or removal of current ceremonies.
- Relevant `done` skill steps and session records cited above.
