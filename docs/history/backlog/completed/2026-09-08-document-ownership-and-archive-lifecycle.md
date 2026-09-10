# Backlog: document ownership and immutable archive lifecycle

Status: done
Workflow: backlog
Origin: User feedback during implementation-plan authoring on 2026-09-08
Severity: High
Scope: `agents/skills/doc-hierarchy/SKILL.md`, `agents/skills/doc-hierarchy-upkeep/SKILL.md`, `agents/skills/plans/SKILL.md`, `agents/skills/rfc-design/SKILL.md`, `agents/skills/receiving-review/SKILL.md`, `agents/skills/review-plan/SKILL.md`, `agents/skills/done/SKILL.md`, `agents/skills/confluence-page-sync/SKILL.md`, and the project documentation templates or validation scripts they own
Related: completed backlog item `2026-09-01-single-sot-for-cross-cutting-contract-rules.md`

## Problem

Documentation upkeep treats historical plans, completed investigations, and old proposals as if they were living documents. A path rename or contract clarification then edits several already-completed artifacts to repair links or restate the current design. This changes the historical record, expands a small documentation task into unrelated churn, and makes it unclear which document is authoritative.

The existing single-SOT policy addresses duplicate living prose, but it does not provide a complete lifecycle for closing a document, freezing it, moving it to context, preserving its discoverability, or handling links after the freeze.

## Goal

Define one project-agnostic document lifecycle that makes ownership and mutability explicit:

- each idea or contract has one canonical source of truth;
- living SOT documents may change while their owning work is active;
- completed plans, completed investigations, superseded proposals, and review records become immutable historical artifacts;
- context and archive paths are excluded from routine contract synchronization and review staleness findings;
- future changes create or update the successor SOT and pointers, not the old historical body.

## Terms

Vocabulary is harmonized with the repository glossary (`docs/maintenance/glossary.md`) per the 2026-09-08 grill; this document's original "historical artifact" and "frozen context" wording folds into existing terms:

- **Living SOT:** the one document or wire/schema source that owns the current normative rule for an idea (glossary term).
- **Completed history artifact:** the glossary term covering what this item originally called "historical artifact" and "frozen context"; a completed plan, investigation, proposal, RFC, or non-mirror context file recording what was known or decided at a point in time. "Frozen context" is simply a completed history artifact under `docs/history/context/`, not a separate state.
- **Pointer:** a short link or index entry that names the current SOT without copying its normative prose.
- **Document identity:** a stable capability or concept identifier, independent of a temporary ticket, branch, or implementation task (glossary term).
- **Ownership registry:** the central registry defined in the glossary; one Layer 2 file mapping document identity to the living SOT, completed history artifacts, and aliases.

## Proposed lifecycle

1. **Classify before editing.** Determine whether the target is a living SOT, active implementation plan, historical artifact, external mirror, or frozen context. Do not perform routine edits on a historical artifact to make it agree with current behavior.
2. **Declare ownership at creation.** New design documents carry a stable capability identity, owner, status, canonical flag, and successor or supersedes links where applicable. Ticket IDs may be provenance, but must not be the document's durable identity.
3. **Close and freeze in one transition.** When the work completes, archive the plan and mark it immutable in the same lifecycle operation. A completed investigation or proposal receives the same transition when its active work ends.
4. **Use successor documents for change.** If a historical conclusion is superseded, create or update the current SOT and record a pointer or successor relation. Do not rewrite the old body to make it describe the new conclusion.
5. **Use an ownership registry for discovery.** Maintain one small repository-level registry or generated index mapping stable document identity to current SOT, historical artifacts, and aliases. Link validation resolves aliases through this registry instead of requiring edits to every historical file.
6. **Make archival moves explicit.** A move to `history/context/`, `plans/completed/`, or an equivalent archive is a deliberate lifecycle action with a manifest entry, reason, date, and source path. It is not an incidental result of fixing a broken link.
7. **Separate mirrors from source.** External mirrors may refresh from their source-of-truth under the synchronization policy. A mirror refresh must not rewrite completed local plans, investigations, or non-mirror context.

## Mutability policy

| Document state | Normal edits | How current changes are recorded |
|---|---|---|
| Draft / active SOT | Allowed within owner and review workflow | Edit the SOT |
| Active implementation plan | Allowed until completion | Edit the plan and its minimal living pointers |
| Completed plan / investigation / proposal | Forbidden | Create a successor or update the current SOT |
| Frozen non-mirror context | Forbidden | Create a new current document and pointer |
| External mirror | Only through sync workflow | Refresh the mirror from its external source |
| Factual corruption or secret leak | Emergency exception with explicit approval and audit note | Minimal corrective edit, preserving the original text where safe |

“Broken link” alone is not a sufficient reason to edit an immutable document. Link repair belongs in the ownership registry, a current index, or a successor pointer.

## Suggested implementation

Prefer extending existing hierarchy and lifecycle skills before creating a new skill:

- `doc-hierarchy`: define document states, stable identities, archive/context semantics, and the ownership registry shape.
- `doc-hierarchy-upkeep`: refuse routine edits to immutable artifacts and update only the current SOT plus minimal pointers.
- `plans` and `done`: record the completion transition, archive active plans, and freeze them without post-completion wording edits.
- `rfc-design`: require a stable capability identity, canonical-owner declaration, and successor relation before publication or closure.
- `receiving-review` and `review-plan`: classify historical findings as immutable context and point to the current SOT instead of rewriting old artifacts.
- `confluence-page-sync`: distinguish live source pages from mirrors and never infer permission to edit local historical artifacts from a sync mismatch.

Add a small validation tool or shared validator that:

- detects duplicate canonical identities and multiple declared SOTs;
- rejects writes to immutable paths unless an explicit factual-corruption override is present;
- validates archive manifests, successor links, and alias mappings;
- checks that living documents point to the current SOT rather than copying its full rule;
- reports stale links with a suggested registry alias or successor target, without editing historical files.

Use repository-local metadata or a generated index rather than hardcoding project-specific paths into shared skills. The metadata must support existing repositories that do not yet have a registry, with a migration command that inventories candidates and asks for ownership only where classification is genuinely ambiguous.

## One-time migration for existing repositories

The implementing plan should first inventory documents changed only for path repair or post-completion reinterpretation. For each candidate, classify it as:

- keep as a living SOT;
- archive under the repository's completed-history path;
- move to frozen context;
- preserve in place and register an alias; or
- leave unchanged because it is an authoritative historical record.

The migration must be one bounded, reviewable change. It may move files and add registry metadata, but it must not rewrite historical bodies merely to restate the current design. Existing links are handled by aliases or current index pointers. After migration, routine documentation upkeep must not reopen the same historical files.

## Acceptance criteria

- A document's state, stable identity, and SOT status are discoverable from the ownership registry (one lookup, not a per-file search); living SOT documents may additionally carry an optional one-line status header, but the registry is the mechanism.
- The workflow identifies exactly one current SOT per idea and converts other living copies to pointers or archives them.
- Completed plans, investigations, proposals, and non-mirror context are protected from routine edits.
- A broken historical link produces an alias or successor recommendation, not an automatic edit to the historical artifact.
- Plan completion archives and freezes the plan in one lifecycle transition.
- RFC closure and proposal supersession preserve the old body and establish a successor/current-SOT relation.
- Confluence mirror refresh remains allowed only for mirror files and does not mutate local historical records.
- Validators cover duplicate SOT declarations, immutable-path writes, missing archive metadata, stale aliases, and successor cycles.
- A one-time migration plan exists for repositories with historical path-repair churn; it does not require changing every historical file in one product feature.
- The process is tool-agnostic, project-agnostic, and contains no private service names, ticket prefixes, domains, or machine paths.

## Non-goals

- Do not create a single mega-document for all designs.
- Do not delete historical evidence merely because it is superseded.
- Do not make frozen external mirrors immutable when the mirror contract requires refresh.
- Do not change push, branch, review, or user-approval authorization.

## Why not implement now

This is a cross-skill documentation lifecycle change. It should be implemented as a dedicated ai-playbook plan with its own migration fixture and validator tests, then applied to product repositories incrementally. It should not be improvised as part of a product feature's documentation cleanup.

## Grill decisions (2026-09-08)

Resolved in a grill-with-docs session; glossary and `project-decisions.md` (ADR-0003) updated inline. These decisions bind the implementing plan.

1. **Scope (ADR-0003):** the lifecycle is part of the doc-hierarchy schema, binding service repos automatically once migration-complete; the ai-playbook instruction repo adopts it by convention for its own `docs/` tree without requiring the migration-complete signal. No third scope class.
2. **Registry form:** one central registry file (no per-doc frontmatter mechanism). Archival stays a pure `git mv` plus a registry row; the frozen artifact's bytes never change. Registry updates ride existing lifecycle transitions (plan completion, backlog archival, RFC closure); never a separate ritual. Alias/redirect stub files remain banned (verify script already deletes them); aliases live only in the registry.
3. **Validator:** a new standalone script in the repo scripts layer (sibling of `confluence-mirror-hygiene.sh`), wired into `done` as a numbered step near the mirror-hygiene step. Do not extend `verify-doc-hierarchy.sh` (migration-scoped; fatals on the instructions repo). Two-tier verdict; hard-fail: duplicate identity/SOT declarations, writes under completed-history paths without an explicit override, successor cycles; warn-only: stale aliases and missing registry entries for legacy files (pre-registry repos fail open; the migration command backfills).
4. **Freeze trigger:** explicit, agent-prompted, never time-inferred. Plans freeze deterministically at completion. Investigations, RFCs, and proposals freeze when the owner/user declares it, prompted at natural moments (`rfc-design` on supersession/acceptance, `execute-plan` completion when the doc fed the plan, `doc-hierarchy-upkeep` when a Layer 3 file is still cited as current truth). The validator may nag about living-cited Layer 3 files; it never auto-reclassifies.
5. **Vocabulary:** reuse the glossary ("Completed history artifact" widened; "Living SOT" added; no separate "frozen context" state).
6. **Registry location:** `docs/maintenance/document-registry.md` by default, overridable via an optional facts key (e.g. `doc_registry_rel`), created lazily by the migration command.
7. **Corruption override:** ADR-0001 semantics exactly; explicit user confirmation, minimal corrective edit, plus an audit note (date, reason, approver) in the registry row. No new approval machinery.
8. **Confluence mirrors:** existing sync/mirror-hygiene workflow stands unchanged; `confluence-page-sync` gains an explicit line that sync never licenses edits to local non-mirror history.
9. **Ephemera out of scope:** `docs/history/reviews/` and `docs/tmp/` (gitignored) get no registry entries and no immutability rules.
10. **Superseded documents stop being deleted:** `plans` currently deletes superseded plans; this reverses to archive + `superseded_by` registry entry. Superseded backlog items get `Status: superseded` in `backlog/completed/` instead of deletion.
11. **Skill edit set:** exactly the eight files listed in Scope, with bidirectional Integration Points; `learn` and `docs-branch` untouched.
12. **Dogfood migration:** the implementing plan applies the one-time migration to ai-playbook itself as its fixture before any product repo.
