---
name: doc-hierarchy-migrate
description: >-
  Execute company service documentation hierarchy migration (Steps 0→6):
  classify, git mv, merge architecture topics, scaffold greenfield repos, patch
  instructions, verify layout. Use when migrating, reorganizing, or scaffolding
  service docs. Trigger phrases — "migrate docs", "reorganize docs", "run
  doc-hierarchy", "doc hierarchy migration", "scaffold service docs", "fix doc
  hierarchy". Schema reference:
  doc-hierarchy. Post-migration upkeep: doc-hierarchy-upkeep.
---

# Doc Hierarchy Migration

**Canonical references:** [content-ownership.md](../doc-hierarchy/content-ownership.md) · [schema](../doc-hierarchy/SKILL.md) · [classification](../doc-hierarchy/migration-map.md) · [templates](../doc-hierarchy/instruction-templates.md) · [verify](scripts/verify-doc-hierarchy.sh)

## When to use

- Migrate, reorganize, scaffold, or repair service `docs/`.
- Legacy paths remain (`docs/plans/`, `docs/<module>/`, `docs/examples/`, root `project-guidelines.md`).
- **Not** routine Layer 1/2 updates → [`doc-hierarchy-upkeep`](../doc-hierarchy-upkeep/SKILL.md).

## Execution contract

**Prerequisite (before any gate):** Resolve `{skill_install}` to the absolute path of the directory containing this file (the skill install root). Export it as `SKILL_INSTALL`. All gate commands below use `"$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh"`.

1. Read [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal).
2. Copy checklist into the response; run steps in order.
3. Run gates with `REPO_ROOT` set to the **service repo root**; invoke the script from the skill install path:

   `REPO_ROOT=<service-repo> "$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh" {phase}`

   Do not set `REPO_ROOT` to the skill install directory. Paste output before claiming done.
4. Skill edits and repo migration are **separate sessions**.

```
Migration progress:
(Step 1 is intentionally omitted — Step 0 is audit/classify; relocation starts at Step 2.)

- [ ] Step 0: Audit and classify
- [ ] Step 2: Git moves (+ 2b greenfield scaffold when needed)
- [ ] Step 3: Merge into architecture/*.md
- [ ] Step 4: Flatten history/feature-notes
- [ ] Step 5: Layer 1 README + instruction files
- [ ] Step 6: Reference update + verify (full)
```

## Repair / partial migration

1. `REPO_ROOT=<service-repo> "$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh" audit`
2. Map each `FAIL:` to owning step; re-run **only** failing steps.
3. No ad-hoc `git mv` outside the active step.

## Step 0: Audit and classify

1. Confirm [scope](../doc-hierarchy/SKILL.md#scope) and story branch.
2. Inventory all paths under `docs/` (`find docs -print`); include gitignored `docs/reviews/`.
3. Assign each path one outcome — [migration-map.md § Step 0](../doc-hierarchy/migration-map.md#step-0-classification-outcomes).
4. Classification table in session notes before Step 2.
5. Flags: `REQUIRE_CALLER_CATALOG=1` if OpenAPI/caller catalog; `CLASSIFIED_COMPANY_GUIDELINES=1` if moving mirror.
6. Persist flags to `{tmp_dir}/doc-hierarchy-migrate/session-flags.env` (invoke `resolve-vars` for `{tmp_dir}` if needed):

   ```bash
   REQUIRE_CALLER_CATALOG=0|1
   CLASSIFIED_COMPANY_GUIDELINES=0|1
   ```

   Before Step 2+ gates, `source` this file or re-read Step 0 notes. Multi-session migrations must restore flags from this artifact; export env vars in the same shell session as gate commands when not using the file.
7. Reconcile [migration-map.md](../doc-hierarchy/migration-map.md) against [company-decisions.md Layer 2](../doc-hierarchy/company-decisions.md#layer-2--architecture-and-domain-knowledge-shared-human--ai) — operational exports (Grafana dashboards, runbook attachments) belong under `maintenance/`, not `docs/` root; repair stale KEEP-root rows before Step 2.

## Step 2: Git moves

Move tables and special cases: [migration-map.md](../doc-hierarchy/migration-map.md) (maintenance, history, Step 2 special cases).

**Grafana dashboards:** if `docs/dashboards/` exists at repo root, `git mv docs/dashboards docs/maintenance/dashboards` (Layer 2 maintenance — index from `architecture/operational-guides.md`). Do **not** leave exports at `docs/` root.

**Legacy RFCs:** if `docs/rfcs/` exists at repo root, `git mv docs/rfcs/*.md docs/history/feature-notes/` (flat) and remove the empty directory. Do **not** leave `docs/rfcs/` after migration.

**2b greenfield:** scaffold maintenance + seven architecture placeholders from [instruction-templates.md](../doc-hierarchy/instruction-templates.md).

**Gate:** `REQUIRE_CALLER_CATALOG=... CLASSIFIED_COMPANY_GUIDELINES=... REPO_ROOT=<service-repo> "$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh" step2`

## Step 3: Merge into architecture

Merge table: [migration-map.md Layer 2 merge](../doc-hierarchy/migration-map.md#layer-2-merge-into-architecture-topic-based). Strip PII; delete sources per classification table.

**Gate:** `REPO_ROOT=<service-repo> "$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh" step3`

## Step 4: Flatten Layer 3

Flat `history/feature-notes/` + `proposals/` only. **Gate:** `REPO_ROOT=<service-repo> "$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh" step4`

## Step 5: Layer 1 and instructions

1. `docs/README.md` — [README template](../doc-hierarchy/instruction-templates.md#layer-1-docsreadmemd-skeleton); Layer 1 rules in [company-decisions.md](../doc-hierarchy/company-decisions.md).
2. `project-guidelines.md` — [project-guidelines template](../doc-hierarchy/instruction-templates.md#docsmaintenanceproject-guidelinesmd-section).
3. Patch `AGENTS.md` — [AGENTS template](../doc-hierarchy/instruction-templates.md#agentsmd-documentation-hierarchy-subsection).
4. Patch `user_facts_path` keys; scrub machine paths from repo `facts.md`.
5. No `doc-migration.md` in `history/`.

**Gate:** `REPO_ROOT=<service-repo> "$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh" step5`

## Step 6: Reference update and verify

Fix legacy path strings repo-wide (classification table + `docs/context/`, `docs/plans/`, `docs/proposals/`, `docs/rfcs/`, rogue `docs/<module>/`).

**Gate:** `REPO_ROOT=<service-repo> "$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh" full` — exit 0 required.

## PR description (after migration)

1. Copy the [PR checklist](../doc-hierarchy/company-decisions.md#pr-checklist-team-proposal-accepted) into the PR — check applicable Layer boxes.
2. Follow [PR description rules](../doc-hierarchy/company-decisions.md#pr-description-rules) — no unchecked duplicate of session verify gates; never imply the verify script is vendored in the service repo.
3. Paste gate output in the session/PR comment if useful; do not require reviewers to re-run gates already passed during implementation.

## Anti-patterns

- Ad-hoc moves without this workflow
- Legacy paths on disk or in canonical doc text — only `docs/architecture/`, `docs/maintenance/`, `docs/history/`, and `docs/tmp/` are valid top-level trees (step3 enforces on disk; step6 scans canonical docs and source for forbidden `docs/...` literals, including in "do not recreate" phrasing). Move targets: [migration-map.md](../doc-hierarchy/migration-map.md). If placement is unclear, ask the user before writing.
- Copying or vendoring `verify-doc-hierarchy.sh` into the service repo (`scripts/verify-doc-hierarchy.sh`) — gates run from the skill install only
- Relaxing verify gates in a repo-local copy (removed checks or legacy root whitelists)
- Full `AGENTS.md` replace with templates
- Editing ai-playbook `docs-branch` during service-repo migration
- Reporting complete without `full` gate output
- Step 3 staging cleanup via broad globs such as `architecture/*-*.md` — canonical filenames (`system-overview.md`, `domain-model.md`, `api-contracts.md`, …) match and get deleted; delete only explicit staging basenames (e.g. `event-flows-message-triggers.md`)

## Local verify

Run `scripts/verify-doc-hierarchy.sh self-test` after skill changes. Self-test builds ephemeral mini git repos in a system temp directory (legacy layout must fail `step2`; minimal migrated layout must pass `step2` and `full`; negative cases cover step3, step4, and step6 reference scans), then removes them. GitHub Actions is optional; workflows belong in `.github/workflows/` only if the repo owner wants remote CI.

**Environment:** `REPO_ROOT` (service repo root). `EXTERNAL_DOCS_DOMAIN` — optional hostname for third-party doc URLs that match the rogue `docs/<module>/` scan (for example `kubernetes.io` when code links to `https://kubernetes.io/docs/...`). Built-in exclusions also cover `https?://` URL contexts and `firebase.google.com/docs/`.

## Integration Points

| Consumer / provider | Integration |
|---------------------|-------------|
| `doc-hierarchy` | Schema reference; migration-complete signal definition |
| `doc-hierarchy-upkeep` | Runs verify gates after Layer 1/2 edits on migration-complete repos |
| `resolve-vars` | Default path map applies only after migration-complete signal |
| `plans`, `execute-plan`, `learn`, `done`, `docs-branch` | Receive canonical paths written during Steps 5–6 |

## Related

- [`doc-hierarchy`](../doc-hierarchy/SKILL.md), [`doc-hierarchy-upkeep`](../doc-hierarchy-upkeep/SKILL.md)
- the `resolve-vars` skill, `plans`, `execute-plan`, `learn`, `docs-branch`, `done`
