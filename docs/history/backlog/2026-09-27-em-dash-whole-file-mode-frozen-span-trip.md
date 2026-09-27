Status: open
Priority: high

# Whole-file em-dash gate modes structurally trip on pre-existing committed violations in files a plan must edit

**Skill/step:** `scripts/check-no-em-dash.sh` whole-file modes (`touched`, `file`), as selected by execute-plan Validation blocks and by the `done` skill's pre-commit em-dash-scan gate ("`check-no-em-dash.sh touched` over touched prose").

**Observed:** an execute-plan task editing `agents/skills/maintenance/SKILL.md` ran the plan-prescribed whole-file gate `check-no-em-dash.sh touched`; it exited 1 even though the task's added lines carried zero em dashes (`added-lines` mode exited 0 on the same file). The file carries four pre-existing committed em dashes (lines 63, 163, 189, 262 at the run base) inside spans the plan froze (some sit on pinned writer-class lines), so removing them would have violated the stronger edit-scope constraint. Any task touching this file trips the whole-file gate structurally; the working remedy was the `added-lines` mode, which faithfully binds the plan's stated property ("no em dashes anywhere in edited text").

**Expected:** one of (a) the script gains an explicit exempt-baseline affordance for whole-file modes (a recorded pre-existing violation set excluded from the count), or (b) the gate-selecting guidance (plan Validation authoring, the done skill's pre-commit gate text) names `added-lines` as the required mode when the target file carries known pre-existing violations in frozen spans, with the pre-existing set tracked as its own follow-up. This mirrors the lessons-corpus #85 remedy: separate the per-task gate from the broad command; the broad command is a known-pre-existing-condition item, not a blocker for the new-work task.

**Pending decision (flagged for closeout by the run):** either sanction the four pre-existing em dashes in `agents/skills/maintenance/SKILL.md` as an exempt baseline for whole-file modes, or schedule a dedicated de-em-dash pass over those spans (the pins suite's frozen-span and region-count constraints must be revisited in the same change).

**Reproduction:** in a checkout where `agents/skills/maintenance/SKILL.md` carries committed em dashes outside the edit, edit any other span of the file and run `bash scripts/check-no-em-dash.sh touched`; exit 1 reporting the pre-existing lines. `bash scripts/check-no-em-dash.sh added-lines agents/skills/maintenance/SKILL.md` exits 0.

**Environment:** ai-playbook repo, worktree `exec/deferred-residual-dispositions`, 2026-09-27; repo copy `scripts/check-no-em-dash.sh` (no separate runtime deployment involved).

**Suspected root area:** gate mode selection guidance (plan Validation authoring, done pre-commit em-dash-scan text) plus a missing exempt-baseline affordance in the script's whole-file modes.

**Origin class:** execute-plan implement deviation (Task 8 worker log, deferred-residual-dispositions run, commit 816647ee).
