---
name: review-staging
description: >
  Gold-source spec for review staging docs:
  file naming under {reviews_dir} and the standardized Markdown hierarchy.
---

# Review Staging (Gold Source)

## Inputs (provided by caller skill)

Caller must provide:
1. `review_type` (human label), for example `Confluence Review`, `RFC Review`, `Plan Review`, `Branch Review`, `PR Review`
2. `page_or_artifact_title` (string) used in the top-level header
3. `page_or_artifact_slug` (kebab or slug), used in filenames
4. `mode_or_round` (string), for example `review-local`, `light`, `full`, or `r1`
5. `anchor` text for each finding (caller decides)
6. A list of findings, each with:
   - `severity`: `Critical` | `High` | `Medium` | `Low`
   - `blocking`: boolean, independent from severity
   - `consequence`: tangible harmful outcome
   - `reachability`: `expected` | `common` | `plausible-edge` | `theoretical`
   - `blast_radius`: `global` | `multi-service` | `single-service` | `local`
   - `confidence`: `verified` | `strong-evidence` | `hypothesis`
   - `worker_severity`: severity the worker returned when it differs from staged (omit when equal)
   - `pattern`: canonical Pattern ID in form `<lens>#<kebab-slug>` (for example `quality#null-handling`, `documentation#prose-verbose-comment`, `consistency#stale-cross-reference`); see **Pattern id format** for the allowed owner set. Use `unknown#<slug>` when the agent did not tag one. Legacy `prose-clarity#<slug>` (and other legacy-only owners such as `concurrency#<slug>`) remain readable in historical reviews only; new findings use `documentation#prose-<slug>` or `documentation#missing-<slug>`, and findings from the conditional risk lenses (`concurrency`, `premortem`) are staged under the `risk` worker's base lens owner as `security#<slug>`
   - `workers`: one or more worker ids that reported the issue
   - `source_tag`: `[Prose]` | `[Premortem]` | `[Code]` (omit when not applicable)
   - `comment` (posted text) and `analysis` (not posted)
   - `triage`: `pending` | `fixed` | `dropped` | `deferred` (set after triage; default `pending` at review pass)
7. **Review context** (in `## Metadata` when applicable):
   - `Depth`: `light` | `full` (RFC/plan reviews)
   - `Domains`: comma-separated tags from diff/plan (for example `concurrency`, `SQL`, `auth`, `docs-only`)
   - `Round`: `r1`, `r2`, … when part of a loop
   - `Panel mode`: `full` | `focused`
   - `Selection reason`: required for focused panels
   - `Source digest`: SHA-256 of reviewed content
   - `Escalation reason`: required only for a sixth worker
8. **Review Statistics** (required on every review, including zero-finding rounds):
   - Panel rows: every actual worker launch or skip, with loaded lenses, `parent_worker`, and Solo/Echo counts
   - Deduplication, discarded findings, severity calibration, and triage outcomes by worker and lens
   - Overflow manifest for credible non-blocking candidates not fully expanded

## Documentation paths

Read `{reviews_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0).

Do not use `docs/tmp/` for the primary review staging document. Use `{tmp_dir}` only for ephemeral scratch files when a caller explicitly needs it.

## File naming rules

Primary staging doc path:

`{reviews_dir}/YYYY-MM-DD-<review-kind>-<artifact-slug>-<mode_or_round>.md`

Where:
- `<review-kind>` is a short stable token chosen by the caller, for example `confluence-review`, `rfc-review`, `plan-review`, `branch-review`
- `<artifact-slug>` is the caller-provided slug
- `<mode_or_round>` must be stable and specific enough to avoid collisions in the same day, for example `light`, `full`, `review-local`, `r1`

Create `{reviews_dir}` if it does not exist.

## Canonical record and supersession

There is one canonical Markdown record and one matching sidecar for each review pass. Before creating a file, enumerate and read all matching records and sidecars for the PR. Existing focused or partial records are inputs to the current pass and must be merged or updated, not copied into a sibling primary file for another lens.

If more than one matching record already exists, select one canonical record, add `Supersedes` and `Superseded by` metadata links, and mark every non-canonical record `SUPERSEDED`. A superseded record is historical only and is never eligible for posting. The canonical path must be selected before review workers launch and must remain the only path used for synthesis, triage, and posting.

Create a new suffixed record only for an explicitly requested new review round, or when the prior record is final or posted and the current review is genuinely a new round. A worker lens does not by itself justify a new primary record.

## Orchestrator recording rules

Every review orchestrator (plan, branch, PR, RFC, Confluence) **must** populate `## Review Statistics` while synthesizing findings, not after the fact from memory.

1. **Panel:** one row per actual worker launch or explicitly skipped base worker. Columns: `Worker`, `Lenses`, `Parent worker`, `Status`, `Raw`, `Solo`, `Echo`, `Relaunch`. Flatten descendants into additional rows. The five full-panel workers declare `descendant_launches`, normally `[]`.
2. **During dedup:** list every contributing worker and lens for the kept finding.
3. **During discard:** record Worker, Pattern, Worker severity, reason, and lead ownership.
4. **Severity calibration:** record worker and lens when returned severity differs from staged severity.
5. **Counts:** recompute from Panel + tables; staged finding count must match `## Findings` entries.
6. **Zero-finding rounds:** still write the full `## Review Statistics` section (Panel + Counts + explicit `None` rows where applicable).
7. **Synthesis stats are immutable:** Panel, Deduplication groups, Discarded findings, Severity calibration, and Counts describe the review pass only; do not rewrite them during triage.
8. **Triage outcomes:** roll up per worker and lens. Map `done` to `fixed`, `drop` to `dropped`, and retain pending/deferred.
9. **Pattern:** workers return a lens-prefixed Pattern ID (`lens#kebab-slug`); use `unknown#<slug>` only when the catalog cannot be identified (a bare `unknown` value fails the canonical-pattern gate).
10. **Budget:** fully expand every Critical, every blocking finding, up to five additional non-blocking High/Medium findings per worker, and up to two additional non-blocking Low findings per worker.
11. **Overflow:** additional credible non-blocking candidates go under `### Overflow manifest` with Worker, Pattern, Anchor, Severity, Confidence, and one-line Consequence.
12. **Soften watchlist:** when the review is part of a `review-loop` (or any multi-round branch review), include `### Soften watchlist` under `## Review Statistics`. Carry forward open rows from the previous round; update statuses after workers reaffirm or restage. Use `None.` when the run has no softened findings yet.

### Discard reason codes (use exactly one per discarded row)

| Code | When to use |
|------|-------------|
| `duplicate` | Same root issue as another raw finding; Notes name `staged #N` |
| `already-mitigated` | Artifact already addresses the issue |
| `false-positive` | Assumption or evidence invalid after orchestrator check |
| `out-of-scope` | Outside review scope or diff |
| `prior-review` | Already raised in a prior round and unchanged |
| `insufficient-evidence` | Agent return missing evidence or concrete fix |
| `severity-merged` | Folded into a stronger staged finding; Notes name `staged #N` |
| `noise` | Style/formatting only with no correctness impact |
| `assumption-invalid` | Failed orchestrator assumption check (§4.2 equivalent) |
| `downstream-pr` | Fix or discussion lives in a downstream PR |
| `agent-failed` | Agent timeout, empty, or unusable return |
| `agent-skipped` | Agent intentionally not launched; list under Panel with Status `skipped`, not here |
| `invalid-anchor` | File, line, section, or excerpt anchor wrong after orchestrator check |
| `excerpt-mismatch` | Quoted excerpt not found in artifact (document reviews) |
| `wrong-owner` | Same root cause as another raw finding, but this agent is not the tiered lead (see `review-agents/review-panel-selection.md`); Notes must name `lead: <agent-id>` |
| `softened-reaffirmed` | Prior soften watchlist item re-checked; still intentional; Notes cite soften reason |

When using `wrong-owner`, the orchestrator keeps the lead agent's finding (or merges into dedup group) and discards non-lead copies. Do not use `duplicate` when tiered ownership identifies a lead agent; use `wrong-owner` so aggregation can count ownership misses per agent.

### Pattern id format

Canonical form: `<lens>#<kebab-slug>`. The owner must be a declared shared review lens: `quality`, `implementation`, `testing`, `architecture`, `simplification`, `documentation`, `security`; or the assigned abstract-review lens `consistency`; or the explicit `unknown` owner when the catalog cannot be identified. The slug names the pattern family (for example `quality#edge-case-empty-input`, `security#injection`, `consistency#invariant-task-contradiction`).

Historical compatibility: legacy owners such as `prose-clarity` and `concurrency` stay readable in historical (versionless/legacy) records but are rejected in version-1 sidecars. Colon-prefixed body tags such as `shrink:` are presentation text in finding bodies, never Pattern IDs; their canonical sidecar mapping is defined in the originating catalog (for example `simplification.md`).

Sub-agents should pick the closest pattern from their catalog; the orchestrator may normalize spelling but must keep the ID canonical. Markdown `- **Pattern**:` bullets and sidecar `pattern` values must carry the same canonical ID for the same finding (conservation).

## Staged Markdown hierarchy (required)

The staging doc must follow this structure exactly, including required headings:

```markdown
# <Review Type>: <Page or artifact title>

## Metadata
- Type: <caller-provided type label>
- Date: YYYY-MM-DD
- URL or Artifact: <caller-provided url or "<inline draft>">
- Depth: light | full *(omit when not applicable)*
- Domains: concurrency, SQL *(omit when unknown)*
- Round: r1 *(omit on first non-loop review)*
- Panel mode: full | focused
- Selection reason: <required for focused>
- Source digest: <sha256>
- Guideline pack: overlay=<id>; company=<path or none>; project=<path or none>; shared=<paths>; hints=<section/rule hints by worker> *(omit when Step 2.5 not applicable; when company-scoped, company and project are the paired convention sources)*
- Escalation reason: <required for sixth worker>
- Findings: <staged count>
- Status: STAGED

## Review Statistics

### Panel
| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| correctness-completeness | quality, implementation | none | complete | 2 | 1 | 1 | no |
| risk | security | none | complete | 0 | 0 | 0 | no |

Status values: `complete`, `failed`, `relaunch-complete`, `skipped`, `timeout`.

### Counts
- Workers launched: <N>
- Workers skipped: <N>
- Raw findings (all workers): <N>
- Staged findings: <N>
- Discarded during synthesis: <N>
- Solo staged (unique agent origin): <N>
- Echo staged (multi-agent dedup): <N>

### Deduplication groups
| Staged # | Workers | Lenses | Theme |
|----------|---------|--------|-------|
| 1 | correctness-completeness, risk | quality, concurrency | Race on profile status re-read |

When none: `None (each staged finding had a single agent origin).`

### Discarded findings
| Worker | Worker severity | Pattern | Theme | Reason | Notes |
|--------|-----------------|---------|-------|--------|-------|
| correctness-completeness | Medium | quality#config-binding | Config binding gap | wrong-owner | lead lens: implementation |

When none: `None.`

### Severity calibration
| Staged # | Worker | Lens | Worker severity | Staged severity | Delta |
|----------|--------|------|-----------------|-----------------|-------|
| 1 | correctness-completeness | quality | Low | Medium | upgraded |

When none: `None (agent severities matched staged severities).`

### Triage outcomes
| Worker | Lens | Staged | Fixed | Dropped | Deferred | Pending |
|--------|------|--------|-------|---------|----------|---------|
| correctness-completeness | quality | 1 | 0 | 0 | 0 | 1 |

Before triage: write zeros for Fixed/Dropped/Deferred and set Pending = Staged, or one line `Pending triage.` After triage: recompute per agent from finding **Triage** fields.

## Findings

### Critical

#### F1. <short title>
- **Severity**: Critical | High | Medium | Low
- **Blocking**: true | false
- **Consequence**: <tangible outcome>
- **Reachability**: expected | common | plausible-edge | theoretical
- **Blast radius**: global | multi-service | single-service | local
- **Confidence**: verified | strong-evidence | hypothesis
- **Worker severity**: Low *(omit when equal to Severity)*
- **Pattern**: quality#race-condition
- **Workers**: correctness-completeness, risk
- **Triage**: pending
- **Anchor**: <section heading or nearby prose anchor text>
- **Source**: [Prose] | [Premortem] | [Code]

#### Comment (posted as-is when approved)
<Self-contained, suggestion-tone explanation.>

#### Analysis (not posted)
<Verification trail and severity rationale.>
---

### High

None.

### Medium

None.

### Low

None.

### Overflow manifest
| Worker | Pattern | Anchor | Severity | Confidence | Consequence |
|--------|---------|--------|----------|------------|-------------|

### Soften watchlist
| Round | Pattern / finding | Anchor | Prior fix | Soften reason | Status |
|-------|-------------------|--------|-----------|---------------|--------|
| r24 | architecture#exception-ownership | ProfileTransportConverter | InvalidPropertyValueException | Restore consent-owned mapping | open |

When none: `None.`
```

## Comment and Analysis depth requirements

Caller must ensure each finding's:
- `#### Comment` is self-contained, suggestion-tone, and contains enough detail to act without follow-up chat (depth depends on severity, following the same intent as other review skills).
- `#### Analysis` contains verification trail and severity rationale. It is never posted.

**Comment vs Analysis split:** Comment is author-facing (code/contract/behavior only). Analysis holds reviewer process notes (other finding IDs, follow-up tickets, triage history, joint-config ownership). When the user narrows a staged ask (for example "PII comment only"), edit Comment to that scope only; do not expand into adjacent soft asks. See `doing-code-review` §4.12.

**Snippet format in finding bodies:** prefer inline backtick spans for short snippets; keep any fenced snippet free of heading-like lines and of severity-group-like text anywhere in a line (for example `### Low` or `### Medium`, even mid-line as inline prose). Finding-block splitting and metadata parsing are fence-aware: a properly fenced snippet is safe even if its content contains severity-heading-like (`### Medium`) or finding-heading-like (`#### F9.`) lines; they are treated as quoted content. An UNCLOSED fence triggers a partial re-parse from the fence opener (classification before the opener is preserved; from the opener onward, finding-header lines (and severity-group headings, for metadata parsing) reset fence state so later findings still parse). The severity-group heading scan, however, remains fence-blind and matches the literal `### {Severity}` string anywhere in the document, so keep fenced snippets free of heading-like lines and severity-group-like text as the simple producer rule.

**Quoted field bullets in Comment/Analysis prose:** when quoting another finding's field bullet inside a `#### Comment` or `#### Analysis` body, describe the quoted field in words (for example "its Pattern bullet stages ..."). The conservation parser reads metadata bullets only between the finding header and the first level-four sub-heading of any name (Comment and Analysis are the common ones) and skips fenced code blocks, so reworded prose and fenced examples are safe; all field bullets must sit between the finding header and the first sub-heading regardless of its title, and the parser overwrites the finding's parsed field when a dashed bold field marker appears in that metadata region, so never place an illustrative `- **Field**:` bullet between the finding header and the first sub-heading.

## Severity and ordering

All callers use `review-agents/severity-calibration.md`. Findings appear under `### Critical`, `### High`, `### Medium`, and `### Low` in that exact order. Within a group, order by **ascending finding ID** only (stable discovery order). Do not reorder by blocking, blast radius, reachability, or confidence.

**Triage presentation freeze** (see `review-agents/severity-calibration.md` § Ordering): update Status / Triage / Comment / Analysis / Severity in place. If severity changes, move that finding into the correct section and keep ID order there. Do not reshuffle siblings. Sidecar `findings` array must use the same order as the markdown (severity sections, then ascending id). Triage may also re-evaluate a finding's **Blocking** value when an authorizing rule directs it (for example `receiving-review` **Fix-risk triage when fixes regenerate findings**): rewrite the Blocking bullet in place, record the rationale on the finding's Analysis section, and mirror the flip in the sidecar `findings[].blocking`; synthesis tables stay immutable.

A review is clean only when no unresolved finding has `blocking: true`.

## Output discipline

Staging doc is the deliverable. If a caller needs to post Confluence comments immediately, the caller must still write staging docs first (unless explicitly documented otherwise in that caller skill).

**Hard gate:** do not report review results to the user until the staging doc includes `## Review Statistics` with Panel (including Solo/Echo), Counts, Deduplication groups, Discarded findings (with Pattern), Severity calibration, and Triage outcomes placeholder populated (use explicit `None` rows when empty), **and** the matching `.stats.json` sidecar exists (unless Metadata documents a skip reason).

**Validator:** orchestrators may run `python3 ~/.ai-playbook/scripts/validate_review_staging.py --hard <staging-path>` before reporting. Cursor hooks (`review-staging-gate.sh`) warn after Write via `postToolUse`, deny review-loop commits when validation fails, and may inject a `stop` follow-up for recent stub rounds.

## JSON sidecar (required for aggregation)

Orchestrators **must** write a machine-readable sidecar next to every staging doc:

`{reviews_dir}/YYYY-MM-DD-<review-kind>-<artifact-slug>-<mode_or_round>.stats.json`

Same basename as the `.md` file. Write the sidecar in the same pass as the `.md` file (do not defer). Skip only when the orchestrator cannot emit valid JSON without guessing; in that case record `Stats sidecar: skipped (<reason>)` under `## Metadata` and treat the review as incomplete for panel-tuning aggregation.

Minimum schema:

```json
{
  "schema_version": 1,
  "review_type": "Branch Review",
  "date": "2026-07-13",
  "artifact_slug": "feature-x",
  "round": "r1",
  "depth": "full",
  "domains": ["concurrency", "SQL"],
  "panel_mode": "full",
  "selection_reason": null,
  "source_kind": "code",
  "source_digest": "<lowercase 64-char hex SHA-256 of the exact reviewed bytes - compute a real digest; placeholder values like this one fail the validator, and the all-zero or empty-bytes digests are syntactically valid but hash nothing>",
  "escalation_reason": null,
  "counts": {
    "workers_launched": 5,
    "raw_findings": 5,
    "staged_findings": 3,
    "discarded": 2,
    "solo_staged": 1,
    "echo_staged": 2
  },
  "panel": [
    {"worker": "correctness-completeness", "lenses": ["quality", "implementation"], "parent_worker": null, "descendant_launches": [], "status": "complete", "raw": 2, "solo": 1, "echo": 1, "relaunch": false}
  ],
  "deduplication_groups": [
    {"staged": 1, "workers": ["correctness-completeness", "risk"], "lenses": ["quality", "concurrency"], "theme": "Race on profile status re-read"}
  ],
  "discarded": [
    {"worker": "correctness-completeness", "worker_severity": "Medium", "pattern": "quality#config-binding", "theme": "Config binding gap", "reason": "wrong-owner", "lead_worker": "correctness-completeness", "lead_lens": "implementation"}
  ],
  "severity_calibration": [
    {"staged": 1, "worker": "correctness-completeness", "lens": "quality", "worker_severity": "Low", "staged_severity": "Medium", "delta": "upgraded"}
  ],
  "triage_outcomes": [
    {"worker": "correctness-completeness", "lens": "quality", "staged": 1, "fixed": 0, "dropped": 0, "deferred": 0, "pending": 1}
  ],
  "findings": [
    {"id": 1, "severity": "Medium", "blocking": true, "consequence": "Concurrent update can lose a persisted state change", "reachability": "common", "blast_radius": "single-service", "confidence": "verified", "pattern": "quality#race-condition", "workers": ["correctness-completeness", "risk"], "triage": "pending", "theme": "Race on profile status re-read"}
  ],
  "overflow": [],
  "soften_watchlist": [
    {"round": "r24", "pattern": "architecture#exception-ownership", "anchor": "ProfileTransportConverter", "prior_fix": "InvalidPropertyValueException", "soften_reason": "Restore consent-owned mapping", "status": "open"}
  ]
}
```

Use `"soften_watchlist": []` when the run has no softened findings. Multi-round / review-loop orchestrators must carry `open` rows forward.

The `panel` array in the minimum-schema example above is truncated for readability (one row shown); a real full-panel run carries one row per launched worker, so `counts.workers_launched` matches the non-skipped panel rows. Do not copy the example's counts/panel pairing verbatim, and do not copy its `source_digest` value either: the example digest is an explicit placeholder (a copyable valid hex digest would pass the syntax gate while hashing nothing, so only a hand-computed real digest keeps the placeholder tripwire a tripwire).

### Version-1 sidecar contract

A sidecar that declares `"schema_version": 1` is a version-1 record and must satisfy the complete top-level contract below. Every active producer emits version-1 sidecars.

Required top-level fields (all must be present; enum-typed fields use `null` when not applicable):

| Field | Type / behavior |
|-------|-----------------|
| `schema_version` | integer `1` |
| `review_type` | string |
| `date` | string `YYYY-MM-DD` |
| `artifact_slug` | string |
| `round` | round identifier: string (for example `"r1"`) or integer; producers pick one form per review and stay consistent |
| `panel_mode` | `"full"` \| `"focused"` |
| `selection_reason` | string or `null`; required non-null when `panel_mode` is `focused` |
| `source_kind` | `"plan"` \| `"rfc"` \| `"document"` \| `"code"` |
| `source_digest` | lowercase 64-char hex SHA-256 of the exact reviewed bytes |
| `escalation_reason` | string or `null`; required non-null when a sixth worker launched |
| `counts` | object; `workers_launched` must match non-skipped panel rows, `staged_findings` must match `findings` length |
| `panel` | array of worker rows (`worker`, `lenses`, `parent_worker`, `descendant_launches`, `status`, counts) |
| `deduplication_groups` | array (may be empty) |
| `discarded` | array (may be empty); `wrong-owner` rows carry `lead_worker` + `lead_lens` (or `lead_agent`) |
| `severity_calibration` | array (may be empty) |
| `triage_outcomes` | per-worker/lens rollup: array of rows (as in the minimum-schema example) or an object rollup; the validator checks presence, not shape |
| `findings` | array; each row carries `id` (unique integer; uniqueness is enforced for all current-format records, versionless and version-1 alike), `severity`, `blocking` (real boolean), `consequence`, `reachability`, `blast_radius`, `confidence`, and a canonical `pattern` |
| `overflow` | array; never contains a Critical or blocking finding |
| `soften_watchlist` | array; `[]` when none |

Optional top-level fields: `depth` (string), `domains` (list), `extensions` (object). Any other top-level field is rejected; future extensions belong inside the object-valued `extensions` (a non-object `extensions` value is rejected).

Canonical Pattern IDs (version-1): findings, overflow items, and discarded rows that carry a pattern must use `<lens>#<kebab-slug>` with an owner from the declared set in **Pattern id format**. A version-1 finding must also carry the same canonical `pattern` in its Markdown `- **Pattern**:` bullet; a missing or differing Markdown Pattern is a conservation error.

Historical compatibility (schema classification): a sidecar without `schema_version` is never a version-1 schema error; it is legacy compatibility input, classified by shape: `legacy-worker-shaped` (versionless with per-worker `worker` rows), `legacy-panel-mode` (versionless with `panel_mode` or `counts.workers_launched`), or `legacy` (any other versionless record). When several shape markers are present on the same versionless record, the classifier checks the panel-mode markers FIRST, so a record carrying both per-worker rows and `panel_mode`/`counts.workers_launched` classifies `legacy-panel-mode`, not `legacy-worker-shaped`; derive adapter routing from the exported classifier (`classify_sidecar_schema`), never from the listing order here. Legacy classification does not exempt a record from re-validation: a versionless worker-shaped or panel-mode record run through the `--hard` validator is still held to the current payload gates (panel shape, source digest, descendant flattening), so expect current-contract errors on bare historical records. A sidecar with an explicit unsupported `schema_version` is rejected outright.

`source_kind` declares what `source_digest` hashes: `"code"` (the stored diff bytes), `"plan"` / `"rfc"` / `"document"` (the reviewed document's UTF-8 bytes). Producers SHOULD set it; `review-plan` (and other document reviewers) MUST set it. When `source_kind` is declared, `source_digest` must be a lowercase 64-char hex SHA-256 (placeholders like `"<sha256>"` fail the validator). The `--source-plan` flag on `validate_review_staging.py` recomputes the plan's digest and fails hard on a mismatch (the sibling `--source-rfc` and `--source-doc` flags do the same for RFC and generic document reviews, type-checking the sidecar's `source_kind`), so a digest recorded before a fold of the reviewed artifact is rejected as stale. In multi-round loops, re-derive the digest from the current round's reviewed artifact for every round; never copy a digest from a prior round's staging doc (the copy misattributes findings to a stale tree, and only a recompute flag can catch it).

Legacy sidecars keep `agent`, `agents`, and caller-specific severity labels. New sidecars use worker rows and the four shared severities.

## Integration Points

Provider skill for staged review hierarchy and statistics. Consumers **must** follow this spec:

| Consumer skill | Staging path pattern | Notes |
|----------------|---------------------|-------|
| `review-plan` | `{reviews_dir}/YYYY-MM-DD-plan-review-<slug>-r<N>.md` | Shared severities and blocking-aware plan actions; inlines sidecar schema (Step 3) and runs `--hard` validator gate before reporting round complete |
| `doing-code-review` | `{reviews_dir}/YYYY-MM-DD-PR-*`, `YYYY-MM-DD-branch-review-*`, or execute-plan `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` | Code severities; optional `Status` per finding for PR triage |
| `review-loop` | Same as `doing-code-review` branch / execute-plan patterns with `-r<N>` | Requires statistics every round, including clear rounds |
| `receiving-review` | Updates existing staging under `{reviews_dir}/` | Triage Status→Triage map, Triage outcomes table, matching `.stats.json` sidecar, and authorized Blocking re-evaluation (see Triage presentation freeze) |
| `review-reconciliation` | Supplements the affected canonical record under `{reviews_dir}/` or the caller's linked note | Adds recurrence and closure evidence; never replaces immutable round findings or certifies its own refactor |
| `rfc-design` | `{reviews_dir}/YYYY-MM-DD-rfc-review-<slug>-<mode>.md` | Shared severities; statistics section required |
| `review-confluence-doc` | `{reviews_dir}/YYYY-MM-DD-confluence-review-<slug>.md` | Tag `[Prose]` / `[Premortem]` / `[Code]` in Source field |
| `execute-plan` Phase 3 | `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` | Not `-plan-review-r`; review logs reference staging path with statistics |
| `done` | Session-touched staging under `{reviews_dir}/` | Step 2.64 validates before docs-branch sync |
