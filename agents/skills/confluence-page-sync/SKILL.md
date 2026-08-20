---
name: confluence-page-sync
description: >
  Publish and synchronize local Markdown documents (RFCs, TDDs, design documents) to
  Confluence: full-body page updates, parent/child page creation, Mermaid diagram
  integrity, stored-HTML verification, and the repository sync manifest (Confluence
  version and source revision ledger). Owns the write side of the Confluence
  relationship; NOT a review skill (use review-confluence-doc to review a published
  page). Trigger phrases: "publish to Confluence", "sync RFC to Confluence",
  "update Confluence page", "create child page".
---

# Confluence Page Sync

Owns every write-side Confluence operation for repository documents: publishing a local RFC, TDD, or design document as a Confluence page, refreshing an existing page from the repository copy, creating parent/child page structures, verifying diagram integrity in the stored HTML, and recording the sync result in the repository's sync manifest.

## Core Concepts

- **Source of truth vs rendered derivative:** the repository document is the source of truth; the Confluence page is a rendered derivative. Sync direction is always repository to page. The page is never treated as the authoritative copy while a repository source exists.
- **Sync manifest / ledger:** repository-side record of each published page: Confluence `version.number`, last-modified timestamp, source revision, and sync status. Conventional location: `docs/maintenance/confluence-sync-manifest.json`, validated by `confluence-mirror-hygiene.sh validate` (see Step 4).
- **Single-rendering pair:** a Mermaid fenced source block plus exactly one rendering representation on the published page (native fenced-block render, extension node, or image embed). The duplicate-detection gate asserts one rendering representation per intended diagram; a fenced block rendered natively alongside an extension macro or image embed of the same source is a duplicate diagram defect, not a fallback.

## Documentation paths

Read `{tmp_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Fetched-page HTML and conversion scratch files go under `{tmp_dir}`; the durable artifacts of this skill are the Confluence pages themselves, the sync manifest, the page mirrors under `docs/history/context/confluence/` in the repository, and the page-id rows it adds to `docs/history/context/confluence/README.md` when that index exists.

## Configuration (from facts document)

This skill reads environment-specific values from the user's facts/profile document (e.g., `facts.md` or equivalent). Never hardcode personal paths, org names, or domains in the skill itself.

| Key | Purpose | Example |
|-----|---------|---------|
| `atlassian_domain` | Default Atlassian cloud domain when the user provides no full page URL | `acme.atlassian.net` |
| `confluence_mirror_hygiene_script` | Location of the manifest validator script | `~/.ai-playbook/scripts/confluence-mirror-hygiene.sh` |

If a key is missing from `.ai-playbook/facts.md`, follow `using-skills` Step 0 (bootstrap only when Terms triggers fire); ask the user only when resolution is ambiguous.

## Workflow

### Publication and diagram integrity

1. Publish the complete document body in one intentional update. Do not test connectivity by replacing a live page with a short stub.
2. Preserve Mermaid diagrams as fenced `mermaid` source blocks when the target Confluence space natively renders Mermaid code blocks. Do not add a second Mermaid extension macro or image embed for the same source block: Confluence can render the fenced block and the extension independently, producing duplicate diagrams.
3. If the target page already uses native Mermaid extension blocks, inspect the stored HTML before editing. Reuse that representation only when the source code block and extension are a known single-rendering pair. After publishing, verify the page has exactly one rendering representation per intended diagram: no duplicate extension/image derivative alongside a natively rendered Mermaid block.
4. Verify the published page through HTML, not only the editor preview. Count Mermaid source blocks, Mermaid extension nodes, and image embeds. For a native fenced-block target, expected counts are: one Mermaid source block per diagram, zero Mermaid extension nodes, and zero generated image embeds. Also confirm that the page still contains the full body.
5. Record the resulting Confluence `version.number`, last-modified timestamp, source revision, and sync status in the repository's existing sync manifest or ledger. Set `synced` only after the full-body update and HTML verification succeed.

These checks apply after any full-body replacement because Confluence stores presentation derivatives (for example, Mermaid extension nodes) alongside source content and can retain or duplicate them when the body is reconstructed.

### Step 0 – Pre-requisite: Verify Atlassian integration

1. Verify your environment's **Atlassian integration** provides BOTH capabilities this skill needs: page fetch (read existing page content and stored HTML) and page update (create and replace page content).
2. If the integration is unavailable, or it can fetch pages but cannot update them:
   ```
   ⚠️  Atlassian integration is not available.

   Install and authenticate Confluence/Atlassian access for your agent environment,
   then retry this workflow. See user AGENTS.md or your agent setup docs if present.
   ```
   STOP and wait for the user.
3. If calls fail with OAuth refresh errors (`invalid_grant`, `Invalid refresh token`, `OAuth token refresh failed`), tell the user to re-authenticate the Atlassian integration, then retry.
4. When the integration is authenticated with both capabilities, proceed to Step 1.

### Step 1 – Resolve the target page and parent page

Accept the page reference in any of these forms (same acceptance as `review-confluence-doc` Step 1):
- A Confluence page URL (e.g., `https://acme.atlassian.net/wiki/spaces/~SPACE-KEY~/pages/123456/My+RFC`)
- A page title + space key
- A page ID

When creating a new page or child pages, resolve the parent page the same way: from a parent page URL, a parent title + space key, or a parent page ID.

If no page reference is provided, ask the user: "Please provide the Confluence page URL, or the page title and space key." For a new page, also ask for the parent page reference when the target parent is not already recorded in the sync manifest.

Extract:
- Site / `cloudId` (from URL domain, or `atlassian_domain` from the facts document)
- `pageId` (from URL path or by searching by title in the given space)

### Step 2 – Publish, update, or create pages

1. **Existing page:** publish the complete document body in one intentional update (publication rule 1).
2. **New page:** create it under the resolved parent page with the full document body in one intentional create; record the new page ID and title.
3. **Child pages:** when the document has parts that belong on separate pages (appendices, sub-documents), create one child page per part under the resolved parent. Each child page follows the same publication rules and gets its own verification pass (Step 3).
4. Record every created child page ID in the parent document's manifest entry; each child page's title and mirror live in the child's own entry (Step 4), so later syncs can find and update them.

### Step 3 – Verify the published page

Verification is mandatory before any ledger entry may be marked `synced` (publication rule 4).

1. Fetch the stored HTML of the published page: the persisted representation Confluence serves, not the editor preview and not the submitted source.
2. Count in the stored HTML:
   - Mermaid fenced source blocks
   - Mermaid extension nodes
   - Image embeds
3. Expected counts: publication rule 4 for native fenced-block targets, rule 3 for known single-rendering-pair targets.
4. Confirm the page still contains the full body: the section headings and non-diagram content of the source document are present.
5. If any count or the body check fails, remediate and re-verify before proceeding; do not record the page as `synced`.

### Step 4 – Update the sync manifest (ledger)

1. Record the ledger fields from publication rule 5 for each published, updated, or created page, plus the page ID and title for newly created pages (including child page IDs). Each created page, including each child page, gets its own manifest entry; for a parent, list the child page IDs only (each child's title and mirror live in its own entry; the parent list is the child IDs recorded by earlier syncs plus the child pages this sync creates). Each manifest entry lives in the top-level `pages` array; the mirror hygiene script (the schema authority for the manifest shape) reads `page_id`, `slug`, `title`, `local_path`, and `layer2_targets` from each entry, and the entry also records the publication-rule-5 ledger fields (`confluence_version`, last-modified timestamp, `source_revision`, `sync_status`).
2. Write into the repository's existing sync manifest, conventional location `docs/maintenance/confluence-sync-manifest.json`; page mirrors live under `docs/history/context/confluence/` per `doc-hierarchy`.
3. Set the sync status per publication rule 5: `synced` only after the full-body update and HTML verification (Step 3) both succeed; otherwise record `pending` with the reason.
4. Write or refresh the mirror for every page in the entry: for each page newly added to the manifest (newly created pages, including child pages, and existing pages synced for the first time), write its mirror file `docs/history/context/confluence/{page_id}-{slug}.md` with the published body plus the standard mirror frontmatter (`confluence_page_id`, `confluence_title`, `confluence_version`, `confluence_url`, `space_key`, `synced_at`, `sync_status`, `layer2_targets`; the mirror hygiene script is the schema authority and also rejects a nonstandard `path:` key), and record the mirror's repository-relative path as `local_path` in that page's manifest entry; when `docs/history/context/confluence/README.md` exists, also add the page id (with title and mirror path) to that index; for each updated page, refresh the existing mirror's body and its `confluence_version`, `synced_at`, and `sync_status` fields. The item 5 validation fails on any manifest entry whose mirror file is missing or whose page id is absent from the README index (`missing mirror file`, `confluence README missing page id`), so a created page without its mirror or index row dead-ends there.
5. Validate the manifest with the repository's mirror hygiene check (`confluence-mirror-hygiene.sh validate`; resolve the script from the `confluence_mirror_hygiene_script` facts key or the repository's `scripts/` copy) after updating it.

## Integration Points

### With `rfc-design` and `tdd-design` skills (publication handoff)
`rfc-design` authors and edits local Markdown RFCs; when the user asks to publish or sync the result to Confluence, this skill takes over (page updates, Mermaid diagram integrity, ledger). This skill does not author or restructure the local document. `tdd-design` hands off TDD publication the same way.

### With `review-confluence-doc` skill (review redirect)
Publishing, page updates, and diagram-integrity checks are owned here; `review-confluence-doc` reviews published pages and posts comments, and redirects write-side requests to this skill. This skill does not review or comment on page content.

### With `doc-hierarchy` skill (manifest and mirror placement)
The sync manifest lives under `docs/maintenance/` and page mirrors under `docs/history/context/confluence/` per `doc-hierarchy`; `confluence-mirror-hygiene.sh validate` checks both. Fetch and HTML scratch files go under `{tmp_dir}` read from the facts TOML per `using-skills` Step 0.

### With `done` and `docs-branch` skills (session-end sync hygiene)
`done` Step 2.65 validates the sync manifest and mirrors at session end; `docs-branch` prunes stale Confluence publish snapshots from the docs worktree via the same hygiene script; when their guidance says to republish or refresh a page, run that through this skill's publication rules and Step 3 verification before recording `synced`.

## Guidelines

- This skill writes to Confluence by design. Never accept a review-only request here; route page reviews and feedback to `review-confluence-doc`.
- Publication rule 1 applies to every update: no stub-page connectivity tests.
- Ask the user before creating a new top-level page or moving child pages under a different parent.
- Report each sync result with the page title, page ID, resulting `version.number`, and sync status.
