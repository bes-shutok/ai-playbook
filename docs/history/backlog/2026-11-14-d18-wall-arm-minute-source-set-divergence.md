# Backlog: D-18's quota-wall arming shape binds the probe epoch only; the quota leg's mid-run wall arm adds the displayed-string fallback as a second minute source

- **Filed:** 2026-11-14, execute-plan Phase 3 review over the indefinite-operation-loop-continuation-duties run (branch delta review, correctness-completeness worker)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fence-class
- **Origin class:** textual source-set divergence between a directive's bound arming shape and the boundary arm that satisfies it
- **Skill/step:** `docs/maintenance/operator-directives.md` (D-18's quota-wall arming sentence and its bound Reset-anchored successor bullet in `agents/skills/maintenance/zcode-scheduling-primitives.md`)
- **Driving force:** automation
- **Cluster:** docs/history/backlog/2026-11-13-mid-run-usage-wall-resume-carrier-arm.md (the row whose covering plan landed the arm); the arm itself is landed and operative, this row owns only the directive-side wording

## Observed versus expected

**Observed:** D-18's record binds the loop-exit:quota-wall arming shape to the probe epoch only ("arms the reset-anchored successor at the probe's `reset_at_epoch` plus the standing arming margin", the Reset-anchored successor bullet reading the same), while the landed mid-run wall arm (quota-policy.md Step 4) adds a second sanctioned minute source for the same exit class (the displayed reset string read as GMT+8 when the probe output is unusable) and asserts its arming "satisf[ies] the D-18 arming order instead of duplicating it". At a loop-owned boundary whose probe is dead at the wall, a turn resolving the exit through D-18's record alone finds no sanctioned minute source in the directive text; the instants coincide when both sources exist, so the divergence is textual, not behavioral, on the normal path.

**Expected:** one clause in D-18's quota-wall sentence (or the bound Reset-anchored successor bullet) naming the quota leg's mid-run wall arm conversion (the probe's `reset_at_epoch`, else the displayed reset as GMT+8 per the standing operator note) as the sanctioned minute source for the wall-arm route, so the directive's bound shape and the boundary arm name the same source set.

## Reproduction evidence (trimmed)

- Phase 3 branch-delta review finding, 2026-11-14: the delta touches neither referenced home; both quote-verified against operator-directives.md (~line 192), zcode-scheduling-primitives.md line 20, and quota-policy.md line 17.

## Environment context

- zcode runtime; the operator's standing GMT+8 note is user-level (see the timezone-conversion row filed 2026-11-13).

## Suspected root area

The directive's bound arming shape predates the mid-run wall arm's second minute source; the directive names one producer where the boundary arm sanctions two.
