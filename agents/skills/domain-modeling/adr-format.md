# ADR format

Vendored from [mattpocock/skills `domain-modeling` `ADR-FORMAT.md`](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/ADR-FORMAT.md) (MIT). Paths aligned with `doc-hierarchy` (`maintenance/project-decisions.md`).

## Location

| Layout | File |
|--------|------|
| Doc-hierarchy (preferred) | `docs/maintenance/project-decisions.md` |
| Legacy | `docs/maintenance/project-decisions.md`, then `docs/project-decisions.md` |

Create the file lazily when the first ADR is needed. **Do not** create `docs/maintenance/decisions/` or other numbered-file ADR directories on doc-hierarchy repos.

If `docs/adr/` already exists on a legacy repo, treat it as read-only history; append new ADRs to `project-decisions.md`.

## File structure

Use one markdown file with sequentially numbered section headings:

```md
# Project decisions

Architectural and domain decisions for this service. Newest entries append at the bottom.

## ADR-0001: {Short title}

{1-3 sentences: context, decision, and why.}

## ADR-0002: {Short title}

{Body...}
```

Each ADR can be a single paragraph under its heading. The value is in recording *that* a decision was made and *why*, not in filling out sections.

## Optional subsections

Only include these when they add genuine value. Most ADRs will not need them.

- **Status** line under the heading (`proposed | accepted | deprecated | superseded by ADR-NNNN`) when decisions are revisited
- **Considered options** when rejected alternatives are worth remembering
- **Consequences** when non-obvious downstream effects need to be called out

## Numbering

Read `project-decisions.md`, find the highest existing `## ADR-NNNN` number, and increment by one. Use four-digit zero padding (`0001`, `0002`, …).

## When to offer an ADR

All three must be true:

1. **Hard to reverse**; the cost of changing your mind later is meaningful
2. **Surprising without context**; a future reader will look at the code and wonder "why on earth did they do it this way?"
3. **The result of a real trade-off**; there were genuine alternatives and you picked one for specific reasons

If a decision is easy to reverse, skip it. If it is not surprising, nobody will wonder why. If there was no real alternative, there is nothing to record beyond "we did the obvious thing."

### What qualifies

- **Architectural shape.** Monorepo vs polyrepo; event-sourced write model vs CRUD.
- **Integration patterns between contexts.** Domain events vs synchronous HTTP.
- **Technology choices that carry lock-in.** Database, message bus, auth provider, deployment target (not every library).
- **Boundary and scope decisions.** Which context owns customer data; explicit no-s are as valuable as yes-s.
- **Deliberate deviations from the obvious path.** Manual SQL instead of an ORM because X.
- **Constraints not visible in the code.** Compliance, partner API latency contracts.
- **Rejected alternatives when the rejection is non-obvious.**
