---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology or ubiquitous language, record an architectural decision, or when another skill needs to maintain the domain model.
metadata:
  upstream: "https://github.com/mattpocock/skills/tree/main/skills/engineering/domain-modeling"
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the *active* discipline: challenge terms, invent edge-case scenarios, and write glossary entries and decisions down the moment they crystallise. (Merely *reading* the glossary for vocabulary is not this skill; that is a one-line habit any skill can do. This skill is for when you are changing the model, not just consuming it.)

## Path resolution (Step 0)

Before writing, resolve where domain docs live:

1. Read `.ai-playbook/facts.md` when it exists (`using-skills` Step 0).
2. If the repo is **doc-hierarchy migration-complete** (`doc-hierarchy` skill signal), use:
   - **Glossary (terms only):** `docs/maintenance/glossary.md`
   - **Domain narrative (workflows, entities, invariants):** `docs/architecture/domain-model.md` via `doc-hierarchy-upkeep` when behavior changes; during design sessions, note gaps but do not duplicate full domain-model content into the glossary
   - **Architectural decisions:** `docs/maintenance/project-decisions.md` (append numbered `## ADR-NNNN` sections; create file lazily)
3. **Legacy layouts** (no migration-complete signal): prefer existing files on disk in this order:
   - Glossary: `docs/maintenance/glossary.md`, then `docs/glossary.md`, then root `CONTEXT.md`
   - Decisions: `docs/maintenance/project-decisions.md`, then `docs/project-decisions.md`, then existing numbered files under `docs/adr/` (append new entries to `project-decisions.md` when that file exists; do not start a parallel ADR tree)
4. If none exist, create the glossary file for the active layout when the first term is resolved (doc-hierarchy: `docs/maintenance/glossary.md`; small/legacy repos: root `CONTEXT.md` is acceptable).

Do not introduce root `CONTEXT.md` on migration-complete company service repos; use `docs/maintenance/glossary.md`.

## File roles

| File | Holds | Must not hold |
|------|-------|---------------|
| Glossary (`glossary.md` or `CONTEXT.md`) | Ubiquitous language: term definitions, `_Avoid_` aliases | Implementation detail, specs, scratch notes |
| `domain-model.md` | Workflows, entities, invariants, boundaries (doc-hierarchy) | Ad-hoc term definitions (link to glossary) |
| `project-decisions.md` | Irreversible or surprising trade-offs as `## ADR-NNNN` entries | Obvious or easily reversed choices; do not create `maintenance/decisions/` or other parallel ADR trees |

Glossary format: [glossary-format.md](glossary-format.md). ADR format: [adr-format.md](adr-format.md).

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing glossary, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y; which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account'; do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible; which is right?"

### Update the glossary inline

When a term is resolved, update the glossary file right there. Do not batch these up; capture them as they happen.

### Offer ADRs sparingly

Only offer to append an ADR section to `project-decisions.md` when the three criteria in [adr-format.md](adr-format.md) (When to offer an ADR) all hold. If any is missing, skip the ADR.

## Integration Points

### With `doc-hierarchy` / `doc-hierarchy-upkeep`
On migration-complete repos, glossary and `project-decisions.md` belong under `docs/maintenance/`; domain narrative belongs in `docs/architecture/domain-model.md`. Canonical paths: `doc-hierarchy/migration-map.md`. After a design session that changes behavior or contracts, invoke `doc-hierarchy-upkeep` in the same PR when applicable.

### With `rfc-design` skill
RFC `# Terminology` is reader-facing design vocabulary for one feature. This skill maintains the **project** glossary and decisions. When grilling or designing an RFC, update the repo glossary for new ubiquitous terms; keep RFC Terminology scoped to that document.

### With `grilling` / `grill-with-docs` skills
`grill-with-docs` runs `grilling` with this skill active throughout. Apply glossary and ADR updates during the interview, not after shared understanding is confirmed.

### With `grilling` skill (standalone)
After `grilling` reaches shared understanding, offer to capture resolved terms and decisions using this skill before implementation starts.
