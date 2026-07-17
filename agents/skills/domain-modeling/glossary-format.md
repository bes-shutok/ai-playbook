# Glossary format

Vendored from [mattpocock/skills `domain-modeling` `CONTEXT-FORMAT.md`](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/CONTEXT-FORMAT.md) (MIT). Adapted for `docs/maintenance/glossary.md` and legacy `CONTEXT.md`.

## Structure

```md
# {Context or Service Name}

{One or two sentence description of what this context is and why it exists.}

## Language

**Order**:
{A one or two sentence description of the term}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others under `_Avoid_`.
- **Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) do not belong even if the project uses them extensively. Before adding a term, ask: is this unique to this context, or a general programming concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.
- **No implementation detail.** Do not treat the glossary as a spec, scratch pad, or ADR store.

## Single vs multi-context repos

**Single context (most repos):** One glossary file (`docs/maintenance/glossary.md` on doc-hierarchy repos, or root `CONTEXT.md` on small/legacy repos).

**Multiple contexts:** A context map at the repo root lists contexts, where they live, and how they relate:

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) ; receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md) ; generates invoices and processes payments

## Relationships

- **Ordering → Fulfillment**: Ordering emits `OrderPlaced` events; Fulfillment consumes them to start picking
```

Infer which structure applies:

- If a context map exists, read it to find per-context glossaries
- If only one glossary file exists, single context
- If neither exists, create the glossary lazily when the first term is resolved

When multiple contexts exist, infer which one the current topic relates to. If unclear, ask.
