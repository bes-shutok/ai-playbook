# Backlog: scope Cursor's session-id REQUIRED sentence to the bridge condition (raced-twin panel residual)

Status: open
Workflow: backlog
Priority: medium
Origin class: self-serving
Class: skill-text
Driving force: reliability
Skill/step: `agents/hooks/skill-gate/README.md` (Marker WRITE RECIPE item 5), `agents/skills/execute-plan/run-setup.md` (Plan-file edits (skill-gate)), `agents/hooks/skill-gate/README.md` (learn-class recipe item 5), `agents/skills/plans/SKILL.md` (Writing paragraph)
Severity: medium
Source reference: raced-twin ad-hoc panel r1 over the discarded branch 2026-11-18-skill-gate-marker-recipe, 2026-11-18.
Cluster: docs/history/backlog/EXEC-PROMPTS.md

## Problem

The landed landing a229e1e2d marks `--session-id "$SID"` REQUIRED "on session-id runtimes (Claude, Cursor)" unconditionally in README item 5, the execute-plan Plan-file edits paragraph, and plans Step 0.2. The README's own observability section records Cursor without the session bridge as `keying=project-only` (the adapter omits the flag and consults `no-session`), so on bridge-less Cursor the bare write already matches and the REQUIRED instruction is wrong there - the reverse silent mismatch. A raced twin session's three-lens r1 panel (correctness/consistency/scope) converged on this as a Medium before its change-set was discarded at the race.

Related uncovered siblings from the same discarded panel: (1) the learn-class WRITE RECIPE item 5 restatement still shows the bracketed optional flag without the required sentence while claiming "Steps 1-3, 5, and 6 are IDENTICAL to the plans recipe"; (2) the plans **Writing** paragraph says only "run the recipe CLI from inside the worktree", which does not move the session payload cwd on adapters that key the consult from it; (3) run-setup states the worktree cwd move as fact while no execute-plan step owns the move (plans Step 0.2 orders it for the authoring lane only).

## Expected

README item 5 and the run-setup clause scope Cursor to "with the session bridge - without the bridge both sides key `no-session` and a bare marker already matches"; the learn recipe item 5 carries the same scoped sentence; the plans Writing paragraph points at the Step 0.2 cwd-move duty.

## Evidence and orientation

- README lines ~449-450: `keying=env-var` = "Claude steady state; Cursor with optional session bridge installed"; `keying=project-only` = "Codex steady state; Cursor/agy without bridge at v9".
- `scripts/skill_gate.py::_derive_session_component`: absent/empty session id maps to literal `no-session` on both write and consult paths; cursor.sh omits `--session-id` when its derived SID is empty.
- Witness of the race: peer landing a229e1e2d + prune 36ae399b1 served the entry; the twin branch's gated change-set (three surfaces + rows + folds, r2/r3 records ready=yes zero blocking) was discarded unlanded.

## Rejected alternatives

- Land the twin branch's full change-set after the race: rejected - the entry is served and pruned by the peer landing; landing a duplicate change-set over served bytes doubles review cost for a residual one row scopes.
- Make `--write-marker` derive the session id itself: rejected in the origin row - gate-core change for a cost the text arm removes.

## Why not fixed now

The racing session stood down per the lesson-250 raced-pick rule: verify served arms from disk, discard the duplicate change-set, complete only the uncovered remainder - and the remainder's edit deserves its own reviewed landing.
