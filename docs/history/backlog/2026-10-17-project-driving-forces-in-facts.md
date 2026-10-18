# Backlog: use project-type priority_order defaults in bootstrap

- **Filed:** 2026-10-17
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** operator direction
- **Class:** design
- **Driving force:** project fit; use project-type defaults in the single `priority_order` profile field
- **Skill/step:** `agents/skills/bootstrap-ai-playbook/SKILL.md`, Project profile setup
- **Cluster:** (none; prior cluster row resolved by fa9352ca9)

## Problem

The local facts update exposed a gap in the shared bootstrap contract: the company projects have now been set to the operator's requested ranking, but bootstrap still presents the generic priority profile for a new or incomplete project. The earlier framing treated project motivations as a separate `driving_forces` field. The operator clarified that the profile should use one ranked `priority_order` field instead. Pet projects still need the requested automation and simplicity defaults through that same field.

## Expected

Bootstrap uses `priority_order` as the single profile field for project-type defaults and adds no separate `driving_forces` field. The company default order is exactly `[readability, security, efficiency, code quality]`. Pet defaults prioritize automation and simplicity. Bootstrap presents the type-appropriate profile during setup, preserves explicit confirmation and override behavior, and does not silently overwrite an existing confirmed order.

## Evidence

- `agents/skills/bootstrap-ai-playbook/SKILL.md`, Facts File Shape and Project profile setup: the profile currently contains `priority_order` and `deferred_classes`, but the presented default is generic and does not vary by `project_type`.
- `projects/.ai-playbook/agent_workflow_guidelines.md`, rule 68: `priority_order` is the project's ranked list of finding priorities, and an unspecified project uses the section 64 ordering.
- `docs/history/plans/completed/2026-09-22-project-priority-profiles.md`: the profile was introduced for project-specific priority and deferral behavior.
- `docs/history/plans/completed/2026-10-04-bootstrap-project-profile-setup.md`: bootstrap profile setup made these settings operator-confirmed.
- The operator's correction on this item sets company priorities in this single field and rejects a separate `driving_forces` field.

## Alternatives

- Keep a separate `driving_forces` field alongside `priority_order`: reject because the operator clarified the company values belong in the single ranked profile field (this backlog row, Expected).
- Use the company ranking `[readability, security, efficiency, code quality]` in `priority_order`: recommend, as this is the operator's explicit order (this backlog row, Expected).
- Keep the generic bootstrap default and update only current project facts: reject because new or incomplete projects would continue to receive the generic order (`agents/skills/bootstrap-ai-playbook/SKILL.md`, Project profile setup).
- Add a validator or mandatory confirmation gate for the vocabulary: reject because the request is to supply defaults in an existing confirmed interview, and no witnessed incident supports new blocking machinery (`AGENTS.md`, Machinery admission protocol).
