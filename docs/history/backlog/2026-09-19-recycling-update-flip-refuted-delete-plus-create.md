# Backlog: recycling-update flip refuted live: migrate re-arm/successor duties to delete-plus-create

Captured: 2026-09-19 (scheduler turn 05:43Z, live dispatch witness)
Status: open
Priority: high

Workflow: backlog

## What was witnessed

The turn reshaped the armed parent record (automation-98b59285) into the P13 execution one-shot with one `CronUpdate` (the dispatch ladder's primary recycling path, `agents/skills/maintenance/zcode.md` step 2). The call reported success ("Updated automation ...") and the echoed record took the new `recurring: false`, title, and prompt, but landed `enabled: false`, `lifecycleStatus: completed`, with the stale parent `nextRunAt` (the old cadence's next fire, 08:15 local) and the old `cronExpr`. A confirm listing verified the record could never fire. The delete-plus-create fallback then produced a correctly armed one-shot (automation-a33d3dc2, verified `enabled: true`, future `nextRunAt`).

This refutes the parent-to-child flip direction the overlay's "Automation primitive verification" section carried as unverified since 2026-09-16 (verdict line recorded in that section). The child-to-parent direction (the re-arm duty's main restore path) is unverified and now presumed suspect by symmetry.

## Why it matters

Both child payloads' load-bearing automation legs are written around recycling updates: the re-arm duty's steps (1)/(3) ("update that one record into the parent form with one update-primitive call") and the successor duty's primary reshape leg. A garbled-but-"successful" update is not a refusal, so the duties' existing fallbacks (which key on refusal) do not trigger; the loop goes dark silently. The witnessing turn patched only its own fired payload with a HOST CAVEAT sentence (treat any recycling update whose echoed record is not verifiably the intended form as a refusal, take delete-plus-create).

## Suggested fix

1. Rewrite the dispatch ladder primary path (zcode.md step 2) to delete-plus-create as the operative path; keep recycling only as an optimization re-enabled after a live verified flip.
2. Rewrite both blueprints in `agents/skills/maintenance/prompt-templates.md`: re-arm duty steps (1)/(3) and the successor duty's primary leg gain the caveat as durable text (verifiable-echo-or-delete-plus-create), registered in the deviations list.
3. Verify the child-to-parent direction live via the overlay's probe recipe (fresh unbound chat, throwaway record) before any recycling path is re-enabled; record the verdict per the section's recording rule.

## Acceptance

- A one-shot probe record survives both flip directions with a correct `enabled` state and future `nextRunAt`, or the overlay records both directions refuted and every duty text uses delete-plus-create only.
- A fired child's re-arm produces an ENABLED parent with a future `nextRunAt` matching the recipe cadence, witnessed in the listing.
