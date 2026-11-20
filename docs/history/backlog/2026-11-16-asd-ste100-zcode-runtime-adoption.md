# Backlog: zcode verifies and adopts the shared ASD-STE100 output policy

- **Filed:** 2026-11-16, operator request
- **Status:** covered (docs/history/plans/2026-11-19-asd-ste100-zcode-runtime.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** operator directive
- **Class:** agent-runtime adoption
- **Driving force:** consistency (primary), clarity (secondary)
- **Dependency:** complete `docs/history/backlog/2026-11-16-asd-ste100-codex-canonical-policy-and-skill-corpus.md` first
Required agent type: zcode
Cluster: docs/history/backlog/2026-11-16-asd-ste100-codex-canonical-policy-and-skill-corpus.md; docs/history/backlog/2026-11-16-asd-ste100-claude-runtime-adoption.md

## Problem

The canonical runtime map does not list a verified zcode skill adapter. The shared user-level instruction setup does identify `~/.zcode/AGENTS.md` as a thin import of `docs/AGENTS.md`, but it does not record whether zcode applies that imported writing policy to all responses or how the active zcode runtime exposes shared skills. A shared instruction change alone may therefore leave a runtime-specific gap.

## Expected

Only a zcode agent performs this work. It verifies the active zcode instruction and skill-loading paths, then checks zcode output against the canonical ASD-STE100 policy on representative tasks. If the canonical import and shared skill source cover the behavior, record that evidence and make no duplicate policy copy. If a zcode-specific gap remains, add the smallest zcode-owned adapter at the verified runtime surface and update `projects/.ai-playbook/agent-runtime-layout.md` with the observed wiring.

## Suggested fix

After the Codex canonical policy lands, inspect the active zcode entrypoint and skill registry from a zcode session. Check one short response, one structured response, and one response with exact technical literals. Correct only a demonstrated zcode-specific gap. Do not edit `docs/AGENTS.md` or shared skills; those belong to the Codex-owned backlog item. Do not infer runtime paths from the agent name.

## Evidence and orientation

- `projects/.ai-playbook/agent-runtime-layout.md`: zcode has no verified execute-plan adapter; the runtime map requires observed sources before documenting agent-specific behavior.
- `docs/AGENTS.md`, **Verify wiring**: `~/.zcode/AGENTS.md` is a thin import of the canonical instruction source.
- `docs/history/backlog/2026-11-16-asd-ste100-codex-canonical-policy-and-skill-corpus.md`: canonical policy and shared skill conversion.

## Rejected alternatives

- Copy the full policy into zcode instructions before checking the import: rejected because the known zcode entrypoint is a thin import and a duplicate can drift (`docs/AGENTS.md`, **Verify wiring**).
- Change shared skills during this task: rejected because the Codex-owned backlog has the shared corpus scope; duplicating that edit creates overlapping ownership (the Codex backlog’s **Scope arms**).
- Assume zcode has the same skill loading as Claude or Codex: rejected because the runtime map records no verified zcode adapter (`projects/.ai-playbook/agent-runtime-layout.md`, runtime adapter table).

## Why not fixed now

The canonical policy is not yet in place, and zcode runtime behavior must be verified by a zcode session. This work follows the shared prerequisite.
