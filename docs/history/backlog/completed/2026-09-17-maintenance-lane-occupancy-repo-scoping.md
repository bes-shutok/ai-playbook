# Backlog: maintenance lane-occupancy classifier is not repo-scoped

Status: open
Origin: 2026-09-16-maintenance-scheduler-liveness r5 review (finding R-1, High, non-blocking; pre-existing on main, not introduced by the plan)

## Problem

The G1e/G1a widened-arm catch-all classifies "each remaining automation" with no repo-root containment, and the execution-marker match uses a relative plans-dir substring. In a multi-repo fleet on one host, a foreign repository's 2h parent automation falls into "anything else occupies both lanes", its fire/last-run times always sit inside the 5h child-lane spacing window, and every repo's turns record endless D3 no-ops: the loop runs but never dispatches, with no turn_error, no tripwire, no self-heal.

## Consequence

Silent fleet-wide dispatch starvation once two or more loop repos (or any foreign plan-ish automation) share one host account. This is the exact darkness the maintenance loop exists to prevent, reached without any crashed child.

## Fix sketch

One clause: restrict the widened arm's step (3) classification to automations whose prompt contains the resolved repository root, mirroring the r2-hardened recognition matchers (title + prompt opening + repo-root containment). Audit the execution-marker match for the same containment. Add a discriminating pin.

## Witnesses

r5 risk premortem: "a second repository arms the loop; within one day, every repo records endless G1e/G1a D3 no-ops because foreign 2h parents constantly sit inside each repo's 5h spacing window."
