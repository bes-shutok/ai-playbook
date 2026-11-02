# Backlog: wrong-location-lead-clause amendment absent from SKILL.md after its covering landing

- **Filed:** 2026-11-02, exec session sess_privskills-exec-20261102, during post-landing verification of the private-project-skills landing
- **Status:** open
- **Priority:** medium
- **Origin class:** observed cross-lane landing interaction
- **Class:** fix-class
- **Driving force:** code quality
- **Skill-step:** `agents/skills/how-to-write-skills/SKILL.md` Wrong Location lead Solution line (line ~425)
- **Incident:** landing `e42a0ac786` (wrong-location-lead-clause-contradiction) + completion pass `d4374b9b2`
- **Catch frequency:** once, this verification
- **False-positive cost:** none; the amended clause is already recorded in the covering plan and its row
- **Review date:** 2026-12-02
- **Dedup probe:** the covering plan `docs/history/plans/completed/2026-11-02-wrong-location-lead-clause-contradiction.md` (landed e42a0ac786) owns the amendment design; this row covers only the SKILL.md bytes, not the design.

## Problem

The covering landing `e42a0ac786` and its completion pass `d4374b9b2` touched only backlog records; the SKILL.md hunk in `d4374b9b2` was a stale-byte revert of the private-project-skills landing (`ef52887c4`), carrying none of the lead-clause amendment the plan's task calls for. The amendment's intended lead-clause rewrite ("do not hardcode one vendor directory as canonical in skill text") is therefore still absent from the file after its covering plan landed. The clobbered private-project-skills content was restored by `4dc1ffabe`.

## Expected

The lead Solution line gets the covering plan's amendment (scoped so it does not contradict the tracked project-local sub-section), landed by the session that owns that plan's records or a successor; verify against the covering plan's task text before landing.
