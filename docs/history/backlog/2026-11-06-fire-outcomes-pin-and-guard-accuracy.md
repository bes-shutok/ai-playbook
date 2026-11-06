# Backlog: fire-outcomes pin literal and live-guard accuracy residuals

Driving force: reliability (residual review findings from the 2026-11-06 automation-fire-time-failure-verification Task 1 intermediate review; all low, non-blocking).

Cluster: closeout-recovery

Findings captured:

1. Weak pin literal: the `mode=ro` pin in `scripts/check_maintenance_pins.sh` (post-fire family) matches two occurrences in `scripts/maintenance_fire_outcomes.py` (docstring + operative URI), so dropping the operative occurrence while the docstring survives keeps the pin green. Tighten to a single-occurrence-anchored literal or pin the operative line's context.
2. Vacuous live-guard legs: the memory-index hermeticity guard legs in `scripts/test_maintenance_fire_outcomes.py` watch `~/.claude|~/.codex|~/.agents|~/.cursor/MEMORY.md` paths that do not exist on this host, so those assertions are None==None here; the real live index home differs and hardcoding it would violate the no-personal-paths rule. Consider a configured-path injection or dropping the vacuous legs.
3. Live-digest guard race: the watched live scheduler-state file is actively written by running maintenance automations; a write landing inside the suite's short window false-fails the byte-unchanged assertion. Accepted risk today; document or narrow the window if a false red appears.

Accept when: the pin grammar anchors the operative occurrence, and the guard legs are either genuinely live or explicitly documented as structural-only.
