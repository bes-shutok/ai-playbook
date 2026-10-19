# Light boundary r1 review follow-ups: stale done-setup directives and deferred shrink set

- **Filed:** 2026-10-19, Phase 3 r1 review address pass of the done-final-only-learn-intermediate plan run; source reference `docs/history/plans/2026-10-18-done-final-only-learn-intermediate.md` (r5-certified)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** review finding
- **Class:** fix-class
- **Skill/step:** `AGENTS.md` (Agent-Specific Runtime Safety); `docs/maintenance/development_lessons.md` #81; `agents/skills/receiving-review/SKILL.md` (Step 1.2b consumer row); the five light-boundary skills' prose economy
- **Driving force:** maintainability
- **Dedup probe:** keyword search "done boundary setup", "light boundary", "task's done commit" over open backlog filenames and problem bodies; the residue row `2026-10-18-runtime-scripts-home-residue.md` tracks the runner-side class and names this row for the receiving-review span; no other open row covers these surfaces, no merge.

## Observed versus expected

Observed (Phase 3 r1 full panel, five lenses, over the branch diff 7bd4fbe26..d28c59c0d plus the address pass): the light boundary landed, but four surface groups still carry old-cadence or unpriced text outside the folded set. (1) `AGENTS.md` "Run the done boundary setup as the first worktree action before editing any owned file" and `docs/maintenance/development_lessons.md` #81's trigger clause ("a run whose commits go through the done boundary") still direct the per-run done setup at worktree start, while the landed cadence runs done setup once at the final closeout; a future worktree run holds two contradictory first-action instructions. (2) `agents/skills/receiving-review/SKILL.md` tells Step 1.2b workers that "repository-file captured items ride the task's done commit", a commit class that no longer exists mid-run (the plan's accepted stale list covered only the learn Step 1.8 mentions). (3) Six design-simplicity shrink findings (duplicate Hard Gate 25 precondition, Step 1.4 residual row-reference sentence, the third placement-universality statement, the done Step 1 vs Integration Points near-identical clause, the Step 1.9/1.8 failure-paragraph twin, the review-loop round-row copied leg list) were deferred: several touch plan-pinned literals, and a shrink that breaks a validation pin is inadmissible mid-run. (4) Three plan-scoped testing findings (preservation pins under-cover the frozen Steps 5-7 roster; the plan's negative bookkeeping greps fail open on grep rc=2; the done-when em-dash claim scopes five skill dirs while lessons and plan added lines sit ungated) are accepted deviations against the digest-frozen plan, actionable only in a post-landing plan edit.

Expected: every first-action directive names the landed ordering (done setup is the final closeout's first action; worktree runs start with the run's own Phase 0 setup and closeout-baseline capture); the Step 1.2b consumer row's ride target reads the task's boundary commit; the shrink set lands pin-safe in one prose-economy pass; the plan's pins and negative guards are widened when the plan text is next legally editable.

## Suggested next step

One small plan or ad-hoc pass: reword `AGENTS.md` line 73 and add a supersession note to lesson #81; reword the receiving-review span to the boundary commit; run the six pin-safe shrinks with the validation block re-run as the fence; widen the plan's pins and negative guards at the next plan-text edit window. The receiving-review span may also ride the next receiving-review-owning change instead.

## Phase 3 r2 certification residuals (added 2026-10-19, certifying round over bf0943426)

The r2 fresh-adversarial round returned zero blocking findings and four new non-blocking residuals, all tracked here rather than folded (no skill-text edits after the certified digest): (1) `scripts/check_maintenance_pins.sh` placement pin anchors "committed right after the change", a span the branch's done rewrite removed, so the warning-only suite prints an unsuppressed advisory red each run while exiting 0; re-key the pin to its canonical home (execute-plan SKILL.md's immediate-commit span) or retire it with a recorded-red entry. (2) done SKILL.md's frontmatter rider-commit list omits the Step 1.9 off-tree backlog row class that done Step 1 and learn SKILL.md both sanction; one-phrase summary fix. (3) `agents/skills/maintenance/templates-CHANGELOG.md` lacks an entry for the blueprint reword; append at the next maintenance-template edit. (4) review-loop's new standalone exit-closeout rule duplicates the done four-leg list from the Consumes done entry 37 lines below; cut the parenthetical and keep the anchor in the same pin-safe prose pass as the r1 shrink set.
