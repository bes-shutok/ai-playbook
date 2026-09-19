# Backlog: scope the HOST CAVEAT durability claim in zcode.md's REFUTED-flip verdict line

Captured: 2026-09-19 (P12 execute-plan review r5, contract-docs lens; deferred at the round-5 cap instead of a sixth-round digest mutation)

## Finding

`agents/skills/maintenance/zcode.md` (Automation primitive verification, REFUTED parent-to-child flip verdict line) ends with: "The witnessing turn's fired child carries a matching HOST CAVEAT sentence in its re-arm duty payload." Read against the canonical payload source of record (both blueprints in `agents/skills/maintenance/prompt-templates.md`), the sentence asserts the caveat is already durable; it is not: the blueprints contain no caveat text, and the owning backlog item `2026-09-19-recycling-update-flip-refuted-delete-plus-create.md` still lists the durable caveat rewrite as an open fix item. A maintainer triaging that item could conclude the durable rewrite already landed and skip it, leaving future child payloads without the verifiable-echo guard against the silent dark-loop hazard.

## Suggested fix (fold into the owning item)

Scope the claim to the one-off instance, for example: "the witnessing turn's fired child carries a matching HOST CAVEAT sentence in its one-off assembled payload only (the canonical blueprints do not yet; tracked by the recycling-update-flip backlog item)" — or land the durable caveat rewrite from the owning item and keep the sentence as-is. Either way, close this item together with `2026-09-19-recycling-update-flip-refuted-delete-plus-create.md`.

## Why deferred

Round 5 is the execute-plan max_review_rounds cap; the fix is a one-sentence clarification whose durable counterpart is already owned by the open high-priority recycling item above. Deferring avoids a sixth review round for a single Low-severity sentence while keeping the residual durably tracked (receiving-review backlog capture).
