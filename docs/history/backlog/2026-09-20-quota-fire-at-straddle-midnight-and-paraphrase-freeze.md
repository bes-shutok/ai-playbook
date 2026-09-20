# Quota probe fire-at: straddle-midnight edge and successor paraphrase freeze

- **Status:** open
- **Date:** 2026-09-20
- **Origin:** review r2 of the scheduler-operations-discipline plan execution (findings F9 and F12-paraphrase, deferred per the review-loop backlog-deferral default (ADR-0002 context; these are not the two regenerating classes, deferred as bounded robustness residuals with owner and trigger))
- **Owner:** maintenance quota leg
- **Trigger:** (a) a pricing_cache `peak_window` value whose window start falls before the straddle span crosses midnight (for example a start earlier than 01:00 UTC+8 with `--straddle-minutes 60`), or (b) the next planned edit to `agents/skills/maintenance/prompt-templates.md`'s successor deviation bullet.

## Content

Two accepted-but-deferred robustness residuals from the P6 fire-at mode:

1. **F9: straddle band cannot cross midnight.** `_fire_at_is_peak` in `scripts/quota_window_probe.py` computes the band `(start_minutes - straddle_minutes) <= minute_of_day < end_minutes` on the fire instant's own weekday; when `start - straddle < 0`, a fire late on the previous weekday within N minutes of a midnight-crossing window start is not reported peak. Unreachable with the tracked seed (14:00-18:00 UTC+8, straddle 60). Fix sketch: when `start - straddle < 0`, also count `minute_of_day >= 1440 - (straddle - start)` as peak when the previous calendar day is Mon-Fri, and anchor the deferred window end on the window-start day; add boundary tests.
2. **F12-paraphrase: successor deviation-bullet paraphrase is deliberately unpinned.** The r1 F8 fix pinned the execution blueprint's fire-time sentence via a blueprint-unique span and froze the superseded `never inside a deferred window` span, but a revert of the deviation bullet's paraphrase (`honoring the quota leg's runtime-fit, deferred-window, peak-pricing, and floor rules`) back to the old two-rule wording would keep every pin green. Freezing a self-described paraphrase was judged over-pinning; revisit at the next planned touch of that bullet (pin it then, when its wording is being edited anyway).
