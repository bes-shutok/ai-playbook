# Backlog: the clocked-order launchd launcher composes bare `zcode`, which launchd's default PATH cannot resolve

- **Filed:** 2026-11-20, exec-records walk session (turn-start re-arm duty diagnosis; operator-parked machinery repair)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** witnessed defect (three same-day launch-failed orders, launcher exit 127)
- **Skill/step:** the clocked-order plist composer behind `scripts/execute_plan_runtime.py --operation clocked-order-schedule` (generated plists under `~/.ai-playbook/runtime/launchd/clocked-order-<hash>/`)
- **Cluster:** docs/history/backlog/2026-11-20-fire-outcomes-adapter-unadmitted-runtime-sibling.md (deleted covered 2026-11-20, landing 1b370cb39; the deployment surface this defect degrades)

## Observed versus expected

Observed: every clocked order that fired on 2026-11-20 failed at launch with exit 127 and stderr `/bin/sh: zcode: command not found` (co-5894878 at 13:05Z, co-06ae935 and co-f8fee2 at 17:38Z; err.log captured for co-f8fee2's label ai-playbook.clocked-order.3f1f1b45293c). The generated plist's ProgramArguments run `/bin/sh -c "... zcode --prompt '...'"`, and the `zcode` binary lives under the user home's `.local/bin` (outside launchd's default PATH of /usr/bin:/bin:/usr/sbin:/sbin; the interactive-shell `command -v zcode` resolves it). The fire reaches the sentinel touch and the absolute-pathed python3.15 calls (which is why `clocked-order-clear-fire` still records launch-failed honestly), then dies on the bare `zcode` invocation, so the payload session never starts. The ledger leaves the order `armed` with `payload_recovery_outcome: pending`, and armed future orders (co-d181dd at 2026-11-20T20:00Z, co-6e57d1b at 2026-11-21T03:44Z) will fail identically unless their plists are patched or the composer is fixed.

Expected: the generated plist resolves `zcode` by absolute path (or exports a PATH containing its directory) at compose time, so a fired order actually launches the payload session.

## Suggested direction

Fix the plist composer to emit the absolute `zcode` path (resolved at compose time via the invoking shell's `command -v zcode`, refusing the arm when unresolved, or an exported PATH line). Patching the three generated plists is a per-order workaround only; the composer fix is the durable repair and needs a plan per the bounded-repair rule (machinery edit mid-lane without a plan is out of authority; diagnosed and parked 2026-11-20 ~17:45Z by sess_4f54f501). Note the ZCode-native scheduler is unaffected: recurring parent automation-6f58457a and native one-shots fire normally, so the loop stays lit while this defect stands.

## Machinery admission

No new machinery: the composer and the launch-failed ledger record already own the detection; this row owns the compose-time resolution fix. The stalled-order treatment (cross-check then darkness re-arm per the Recurring automation recipe) already covers the operational side.

## Rejected alternatives

- Patch each generated plist by hand and reload launchd: rejected as the primary remedy because it repairs generated state per order, not the composer, and every future order re-introduces the defect (evidence: three same-day failures across two lineages)
- Swap the chain default back to automation-primitive creates: rejected because the chain exists precisely for cap-bound automation-born sessions, and the create path is unavailable to exactly those sessions (evidence: agents/skills/maintenance/zcode-recurring-recipe.md chain-default sentence)

## Evidence

- err.log, 2026-11-20T17:38:05Z: `/bin/sh: zcode: command not found` (34 bytes, ai-playbook.clocked-order.3f1f1b45293c.err.log)
- `command -v zcode` in an interactive shell resolves under the user home's `.local/bin`; plist ProgramArguments[2] contains bare `zcode --prompt` between absolute-pathed python3.15 calls
- launchctl list rows: `127 ai-playbook.clocked-order.5aff50a37d89` (the 13:05Z failure still loaded at diagnosis time)

## Acceptance

- A freshly armed clocked order fires and actually starts its payload session (no exit 127), and the composer refuses to arm an order when the `zcode` absolute path cannot be resolved.

## Dedup probe

Searched open backlog rows and docs/maintenance/development_lessons.md for launchd, clocked-order launcher, and exit-127 phrasing: no open row owns the composer defect; the stall-classification text covers the operational response only.
