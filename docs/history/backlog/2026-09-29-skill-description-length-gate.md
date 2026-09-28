Status: open
Priority: high
Workflow: backlog
Class: tooling
Driving force: reliability
Origin class: witnessed-incident (2026-09-29: the execute-plan skill missing from the agent skill registry; root cause an over-cap frontmatter description grown by a plan-landing commit; the same session's full-corpus scan found no mechanical check exists anywhere)

# Mechanical SKILL.md description-length gate

## Problem

`how-to-write-skills` Frontmatter Requirements documents the 1024-character description cap, but nothing enforces it. The `execute-plan` skill silently disappeared from the agent's skill list: a plan-landing commit had grown its folded description to 1167 characters, and the runtime drops over-limit skills at registration with no error. Diagnosis required diffing the on-disk skill set against the loaded skill list and knowing the cap exists. A full-corpus scan found exactly one over-limit skill and one near-limit skill (956 characters), so the next description edit there repeats the incident.

## Observed versus expected

- Observed: the cap exists only as a comment and a prose rule; a skill that crosses it vanishes silently, and no scan, gate, or validator measures folded description length.
- Expected: a mechanical check fails (or warns) when any SKILL.md frontmatter description exceeds the cap, so the failure surfaces at authoring or hygiene time instead of as a missing skill at runtime.

## Suggested fix

Extend the public hygiene scan (or a sibling check script wired into the done pre-commit sweep gate run) with a description-length arm: parse each SKILL.md frontmatter (bound the parse to the closing `---` fence; folded `>`/`|` block scalars fold to single-spaced text), measure the folded description, and fail over 1024 characters. Report near-limit files (over ~950) as warnings so chronic growers are visible before they trip. The parse bound matters: a greedy indented-line match swallows fenced code blocks in the body and reports absurd lengths.

## Environment

Witnessed 2026-09-29 in the skills repo: execute-plan at 1167 characters (silent drop; trimmed to 922 in the same session), agterm at 956 (loads, next candidate). The runtime drops over-limit skills without a registry error; the loaded-list-versus-disk diff was the only signal. Canonical rule location: agents/skills/how-to-write-skills/SKILL.md Frontmatter Requirements (Validation Rules), where the silent-drop consequence is now documented.
