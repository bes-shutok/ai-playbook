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
   - `pattern`: catalog pattern id in form `<agent>#<kebab-slug>` (for example `quality#null-handling`, `documentation#prose-verbose-comment`, `concurrency#transaction-scope`); use `unknown` when the agent did not tag one. Legacy `prose-clarity#<slug>` remains valid in historical reviews; new findings use `documentation#prose-<slug>` or `documentation#missing-<slug>`
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
9. **Pattern:** workers return a lens-prefixed pattern; use `unknown` only when the catalog cannot be identified.
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

`<agent-id>#<kebab-slug>` where `<agent-id>` matches the agent file name (without `.md`) and `<kebab-slug>` names the pattern family (for example `quality#edge-case-empty-input`, `security#injection`, `concurrency#race-condition`). Sub-agents should pick the closest pattern from their catalog; orchestrator may normalize spelling.

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

## Severity and ordering

All callers use `review-agents/severity-calibration.md`. Findings appear under `### Critical`, `### High`, `### Medium`, and `### Low` in that exact order. Within a group, order by **ascending finding ID** only (stable discovery order). Do not reorder by blocking, blast radius, reachability, or confidence.

**Triage presentation freeze** (see `review-agents/severity-calibration.md` § Ordering): update Status / Triage / Comment / Analysis / Severity in place. If severity changes, move that finding into the correct section and keep ID order there. Do not reshuffle siblings. Sidecar `findings` array must use the same order as the markdown (severity sections, then ascending id).

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
  "review_type": "Branch Review",
  "date": "2026-07-13",
  "artifact_slug": "feature-x",
  "round": "r1",
  "depth": "full",
  "domains": ["concurrency", "SQL"],
  "panel_mode": "full",
  "selection_reason": null,
  "source_kind": "code",
  "source_digest": "<sha256>",
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

`source_kind` declares what `source_digest` hashes: `"code"` (the stored diff bytes), `"plan"` / `"rfc"` / `"document"` (the reviewed document's UTF-8 bytes). Producers SHOULD set it; `review-plan` (and other document reviewers) MUST set it. When `source_kind` is declared, `source_digest` must be a lowercase 64-char hex SHA-256 (placeholders like `"<sha256>"` fail the validator). The `--source-plan` flag on `validate_review_staging.py` recomputes the plan's digest and fails hard on a mismatch, so a digest recorded before a fold of the reviewed artifact is rejected as stale.

Legacy sidecars keep `agent`, `agents`, and caller-specific severity labels. New sidecars use worker rows and the four shared severities.

## Integration Points

Provider skill for staged review hierarchy and statistics. Consumers **must** follow this spec:

| Consumer skill | Staging path pattern | Notes |
|----------------|---------------------|-------|
| `review-plan` | `{reviews_dir}/YYYY-MM-DD-plan-review-<slug>-r<N>.md` | Shared severities and blocking-aware plan actions; inlines sidecar schema (Step 3) and runs `--hard` validator gate before reporting round complete |
| `doing-code-review` | `{reviews_dir}/YYYY-MM-DD-PR-*`, `YYYY-MM-DD-branch-review-*`, or execute-plan `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` | Code severities; optional `Status` per finding for PR triage |
| `review-loop` | Same as `doing-code-review` branch / execute-plan patterns with `-r<N>` | Requires statistics every round, including clear rounds |
| `receiving-review` | Updates existing staging under `{reviews_dir}/` | Triage Status→Triage map, Triage outcomes table, and matching `.stats.json` sidecar |
| `rfc-design` | `{reviews_dir}/YYYY-MM-DD-rfc-review-<slug>-<mode>.md` | Shared severities; statistics section required |
| `review-confluence-doc` | `{reviews_dir}/YYYY-MM-DD-confluence-review-<slug>.md` | Tag `[Prose]` / `[Premortem]` / `[Code]` in Source field |
| `execute-plan` Phase 3 | `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` | Not `-plan-review-r`; review logs reference staging path with statistics |
| `done` | Session-touched staging under `{reviews_dir}/` | Step 2.64 validates before docs-branch sync |
