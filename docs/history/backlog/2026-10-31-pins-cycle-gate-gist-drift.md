# Backlog: the maintenance pins suite fails at HEAD on the cycle-gate advisory pin after the maintenance-autopilot-continuation landing

- **Cluster:** docs/history/backlog/2026-10-28-hard-mode-clause-pointer-residuals.md (same pins-suite drift-guard surface), docs/history/backlog/completed/2026-10-15-plan-prompts-prune-end-anchor-overreach.md (founding pins-suite witness)
- **Filed:** 2026-10-31, focused plan-review round r1 over the pending-receipt-removal-audit-promotion completion pass (finding F1, reviewer session zcode-exec-20261031-praudit)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** execution-run finding
- **Class:** fix-class

## Problem

`bash scripts/check_maintenance_pins.sh` exits 1 at current HEAD on exactly one pin: the "Cycle gate gist and budget are advisory" pin (scripts/check_maintenance_pins.sh:3661) greps an advisory sentence in `agents/skills/maintenance/SKILL.md` that was rewritten by landing fda4548ac (execute-plan: land maintenance-autopilot-continuation). The receipt-repair scope pins and the rest of the suite are green; the full suite also passed at the pending-receipt-removal-audit-promotion landing commit b6b0f7e21, so the failure is downstream drift from that later landing, not from this surface.

## Expected

The pinned advisory sentence is re-aimed to the rewritten SKILL.md wording (or the pin's fragment is re-derived from the live text), and the pins suite returns `OUTCOME: pass` at HEAD.

## Constraint

The pin fix is not ad-hoc-eligible (guard-bearing surface, `scripts/check_maintenance_pins.sh` is on the ad-hoc denylist); it routes through a plan or the owning lane's next change to the maintenance SKILL.md cycle-gate text.
