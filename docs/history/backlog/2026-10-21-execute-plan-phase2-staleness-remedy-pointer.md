# Execute-plan Phase 2 lacks the progress-tick staleness remedy class

- **Filed:** 2026-10-21, execute-plan run of plan-validation-command-undefined-repo (landed 28127e322)
- **Status:** open
- **Workflow:** backlog
- **Priority:** moderate (every multi-task plan hits the failure at Phase 2; the skill's named remedy is the wrong class)
- **Cluster:** docs/history/backlog/2026-10-21-execute-plan-exec-r-record-production-duty.md (same surface and defect class: execute-plan skill text omits a duty its landing gates enforce)
- **Origin class:** self-serving
- **Class:** fix-class (the skill's Phase 2 failure arm says "treat as a new fix iteration (implement sub-agent on the failing scope)", which sends the executor to invent implementation work for a failure whose only real remedy is a fresh plan-review re-bind round; default shape name the sanctioned exit)
- **Driving force:** correctness (primary), consistency (secondary)
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Phase 2 (Plan Completion) failure arm
- **Source reference:** lesson 165 in `docs/maintenance/development_lessons.md` (full-mode readiness stales on progress ticks; run pre-round at task boundaries, full mode after the Phase 2 re-bind); the witnessed Phase 2 pause of this run (manifest `docs/tmp/execute-plan/plan-validation-command-undefined-repo/manifest.md`, Phase 2 row and Pause note) resolved by a focused plan-review round r4; capture hygiene: `scan-public-hygiene.sh --files` pass
- **Why not fixed now:** skill-text edits in this repository land through the authoring loop, not ad-hoc session edits; filed for routing
- **Dedup probe:** searched open backlog filenames and Problem text for `progress-tick`, `stales`, `re-bind`, `Phase 2`; the lesson corpus owns the rule (lesson 165) and no open backlog row owns the skill-text gap; no merge

## Problem

When Phase 2's full-mode `plan_readiness.py` exits 1 because the boundary commits ticked the plan checkboxes (progress-tick sidecar staleness, lesson 165), the Phase 2 failure arm's only guidance is "treat as a new fix iteration (implement sub-agent on the failing scope)". There is no implementable scope: the plan bytes are correct and complete, and the sanctioned remedy is a fresh focused plan-review re-bind round whose record re-binds the latest-review digest to the ticked bytes (the shape today's landed siblings and this run's r4 round used). An executor following the text literally either invents a no-op implementation task or stops; this run burned a pause-and-investigate cycle deriving the remedy from corpus history.

## Suggested fix

Add one or two sentences to the Phase 2 failure arm: name the progress-tick staleness class (a full-mode exit whose only delta since the latest review round is task-checkbox ticks), point at lesson 165's rule, and name the sanctioned remedy (a fresh focused plan-review round over the current plan bytes whose record re-binds the digest, per the review-plan round-close seal duty) as the class's exit, keeping the implement-sub-agent arm for genuinely failing scopes. Byte-payment per the file's growth rules.
