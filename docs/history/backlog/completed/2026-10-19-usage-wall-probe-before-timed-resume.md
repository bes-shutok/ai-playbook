# Probe the runtime usage wall before riding a timed resume carrier

Status: done (covered by docs/history/plans/completed/2026-10-20-usage-wall-probe-before-timed-resume.md, executed and landed 2026-10-21)
Priority: high
Class: fix-class
Origin class: operator order
Driving force: efficiency

- Added: 2026-10-19
- Origin: operator order 2026-10-19 ("Create a backlog in ai-playbook, investigate it and look up for a workaround and do it"), on the second witnessed wall-strand of the smme certification lane

## Witness

2026-10-19 15:19+01:00, the smme authoring resume: the r2 review panel's correctness-completeness and contract-docs workers were refused at launch by the runtime usage wall ([1308] limit reached for 5 hour, reset nominally 2026-10-19T17:53:54+01:00). The pause posture armed a one-shot resume carrier at 18:05 (reset plus buffer) and the lane went idle for the wall's remainder. At 15:56, 2h14m before the nominal reset, a hardened probe (one trivial sub-agent dispatch) ran clean: the wall had already self-lifted, so the lane resumed in-session and the armed carrier was deleted by its owner as the duplicate-in-waiting it had become. Second witness of the self-lift: the 2026-10-17 08:09 arm record ("cap had self-lifted, no fallback"). The nominal reset timestamp is not evidence of the wall's live state; only a probe is.

Related resilience landing the same afternoon: e06fa7c0f staged the round record before folding findings (the fold-commit-staged-record-precondition), the other half of the same strand this lane hit.

## Cost

The pause posture as it stands rides the wall's nominal reset unconditionally: a lane that could resume immediately sits idle for the remaining window (this incident: about 2 hours of authoring-lane idle plus a fresh-session re-derivation handoff), and the armed carrier becomes a duplicate-in-waiting racing the resumed lane if the operator or another actor continues first. The budget-gate protocol's own wait-for-reset arm already knows the correct shape ("re-run the probe, and the fresh report governs the boundary; continue proceeds") but that arm covers probe-driven budget-gate pauses, not the unexpected launch-refusal wall the review loop actually hits mid-panel.

## Ask

Adjudicate and fix the wall-pause posture: before any timed resume carrier fires for a usage-wall pause, run a cheap hardened probe (one trivial sub-agent dispatch); a clean probe lifts the pause in-session immediately (delete the armed carrier as the owner, record the resolution in the pause record); a refused probe leaves the timed carrier standing. Land the probe-first arm beside the existing pause protocol rather than as a new surface.
