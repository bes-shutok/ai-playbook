# Payload placeholder-set pin parity: the unblock payload set and payload-directive placement have no pins-suite guard

- **Filed:** 2026-10-29 (execute-plan Step 1.2b intermediate review, window-dispatch-hardening Task 3)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (warning-only machinery parity; no witnessed catch; admission row required before any blocking pin)
- **Origin class:** review finding (off-plan; two independent Step 1.2b workers, Task 3 of docs/history/plans/2026-10-28-window-dispatch-hardening.md)
- **Class:** fence-class (placeholder-drift mechanical protection parity across the three dispatch payloads)
- **Driving force:** reliability (secondary: automation)

Cluster: docs/history/backlog/2026-10-29-new-duty-span-pin-witnesses.md (shared surface: maintenance duty and payload pins in the same pins suite)
## Observed versus expected

The maintenance pins suite carries placeholder-set pins for exactly two of the three dispatch payload blueprints: the execution blueprint's inner block set and the authoring body set (the `## Authoring child` span), both restated 2026-10-29 to include `{EFFORT_DIRECTIVE}`. The unblock payload (`agents/skills/maintenance/template-unblock.md`) carries the same class of fill-in spec (its set is `{EFFORT_DIRECTIVE}`, `{REPO_ROOT}` after the same change) with no set pin, and all three set pins are placement-blind: a silent removal of any payload's effort-directive line, or of the unblock legend line, fails nothing in the suite; the only guards are one-time plan validation greps.

Expected: symmetric mechanical protection against the placeholder-drift class across all three payloads, or a recorded decision that the asymmetry is accepted.

## Environment context

Playbook repo, run worktree on branch 2026-10-28-window-dispatch-hardening, post-Task-3 tree; pins suite green with the two restated pins (differential HEAD-vs-tree run proved exactly those two pins changed).

## Suspected root area

`scripts/check_maintenance_pins.sh` placeholder-set pin block (region-scoped pins near the authoring/execution template checks); admission per the Machinery admission protocol: a new pin lands warning-only and needs a registry-removal row with sunset and promotion criteria; no incident witness exists yet, so this stays a backlog row, never a mid-lane gate addition.

2026-10-29 addendum (Phase 3 r1 testing lens, window-dispatch-hardening): the set pins are also placement-blind for legend lines, so the owning work should cover directive-line and legend-line placement, not only set membership.
