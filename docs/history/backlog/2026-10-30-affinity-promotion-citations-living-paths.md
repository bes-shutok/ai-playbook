# Backlog: affinity promotion records cite the witness origin's living path

Filed: 2026-10-30
Status: open
Priority: medium

- **Class:** fix-class
- **Origin class:** Phase 3 review round 1 (code-review r1, finding F1, Medium deferred) over plan docs/history/plans/2026-10-27-agent-type-affinity-before-plan-work.md
- **Driving force:** correctness; secondary: simplicity

## Observed versus expected

Observed: three new permanent records cite the promotion catch's evidence as the covered row's living path `docs/history/backlog/2026-10-26-session-channel-zcode-runtime-derivation-empty.md` - the gate liveness ledger `agent-type-affinity-check` catch row's `evidence`, the machinery registry `protocol:agent-type-affinity-check` active note, and the shared contract's Enforcement-mode paragraph in `projects/.ai-playbook/agent-runtime-layout.md`. That origin's designed fate is deletion at its covering plan's completion pass and no durable twin exists yet, so the citations point at a path that will not exist; the repo citation rule requires the durable home, never the deleted living path. The registry row's re-point duty covers only its plan `witness.ref`, not these origin citations.

Expected: the three citations name a durable home (the covering plan path, or the origin's completed/ twin once it exists), or the registry re-point duty is extended to the origin citations.

## Suggested investigation

When the covering plan's completion pass lands (creating the completed/ twin or deleting the row), sweep the three citation sites and re-point to the durable home in the same change.
