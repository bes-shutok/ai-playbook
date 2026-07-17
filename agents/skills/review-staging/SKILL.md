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
   - `severity`: staged severity per caller skill (document: `Critical` | `Suggestion` | `Advisory`; code: `Critical` | `High` | `Medium` | `Low`)
   - `agent_severity`: severity the sub-agent returned when it differs from staged (omit when equal)
   - `pattern`: catalog pattern id in form `<agent>#<kebab-slug>` (for example `quality#null-handling`, `documentation#prose-verbose-comment`, `concurrency#transaction-scope`); use `unknown` when the agent did not tag one. Legacy `prose-clarity#<slug>` remains valid in historical reviews; new findings use `documentation#prose-<slug>` or `documentation#missing-<slug>`
   - `agents`: one or more sub-agent ids that reported the issue
   - `source_tag`: `[Prose]` | `[Premortem]` | `[Code]` (omit when not applicable)
   - `comment` (posted text) and `analysis` (not posted)
   - `triage`: `pending` | `fixed` | `dropped` | `deferred` (set after triage; default `pending` at review pass)
7. **Review context** (in `## Metadata` when applicable):
   - `Depth`: `light` | `full` (RFC/plan reviews)
   - `Domains`: comma-separated tags from diff/plan (for example `concurrency`, `SQL`, `auth`, `docs-only`)
   - `Round`: `r1`, `r2`, … when part of a loop
8. **Review Statistics** (required on every review, including zero-finding rounds):
   - Panel rows: every sub-agent launched or skipped (includes **Solo** / **Echo** staged counts per agent)
   - Deduplication groups: which agents reported the same root issue before merge
   - Discarded findings: raw agent returns removed during synthesis, each with reason code and **Pattern**
   - Severity calibration: rows where agent severity differs from staged severity
   - Triage outcomes: per-agent rollup after `receiving-code-review` or equivalent (placeholder until triage runs)

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

1. **Panel:** one row per sub-agent file launched (`quality`, `implementation`, …) or explicitly skipped. Columns: `Status`, `Raw`, `Solo`, `Echo`, `Relaunch`. `Raw` = findings returned before dedup (0 when "No findings"). `Solo` = staged findings where that agent is the only origin (not in a multi-agent dedup group). `Echo` = staged findings where that agent shares a dedup group with another agent.
2. **During dedup:** when two or more agents describe the same root issue, add one row to **Deduplication groups** listing every contributing agent and the staged finding number you kept.
3. **During discard:** for every raw finding not staged, add one row to **Discarded findings** with exactly one reason code, **Pattern**, and **Agent severity**. Keep `Theme` to one short phrase (under 12 words). For tiered-ownership merges, use `wrong-owner` on non-lead agent returns and put `lead: <agent-id>` in **Notes**.
4. **Severity calibration:** when agent severity differs from staged severity for a kept finding, add one row per contributing agent to **Severity calibration** (`upgraded` or `downgraded`). Omit rows when severities match.
5. **Counts:** recompute from Panel + tables; staged finding count must match `## Findings` entries.
6. **Zero-finding rounds:** still write the full `## Review Statistics` section (Panel + Counts + explicit `None` rows where applicable).
7. **Synthesis stats are immutable:** Panel, Deduplication groups, Discarded findings, Severity calibration, and Counts describe the review pass only; do not rewrite them during triage.
8. **Triage outcomes:** at review pass, write `### Triage outcomes` with `Pending triage` or per-agent Staged counts and zeros for Fixed/Dropped/Deferred/Pending. After triage (`receiving-code-review`, plan fold, PR triage), update this table and each finding's **Triage** field. Map finding **Status** to **Triage**: `done` → `fixed`; `drop` → `dropped`; `pending` → `pending`; `deferred` → `deferred`.
9. **Pattern:** sub-agents should return `pattern` in their structured output; orchestrator copies it to findings and discarded rows. When missing, infer best-effort from agent file section heading or use `unknown`.

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
- Findings: <staged count>
- Status: STAGED

## Review Statistics

### Panel
| Agent | Status | Raw | Solo | Echo | Relaunch |
|-------|--------|-----|------|------|----------|
| quality | complete | 2 | 1 | 1 | no |
| premortem | skipped | 0 | 0 | 0 | no |

Status values: `complete`, `failed`, `relaunch-complete`, `skipped`, `timeout`.

### Counts
- Agents launched: <N>
- Agents skipped: <N>
- Raw findings (all agents): <N>
- Staged findings: <N>
- Discarded during synthesis: <N>
- Solo staged (unique agent origin): <N>
- Echo staged (multi-agent dedup): <N>

### Deduplication groups
| Staged # | Agents | Theme |
|----------|--------|-------|
| 1 | quality, concurrency | Race on profile status re-read |

When none: `None (each staged finding had a single agent origin).`

### Discarded findings
| Agent | Agent severity | Pattern | Theme | Reason | Notes |
|-------|----------------|---------|-------|--------|-------|
| quality | Medium | quality#config-binding | Config binding gap | wrong-owner | lead: implementation |

When none: `None.`

### Severity calibration
| Staged # | Agent | Agent severity | Staged severity | Delta |
|----------|-------|----------------|-----------------|-------|
| 1 | quality | Low | Medium | upgraded |

When none: `None (agent severities matched staged severities).`

### Triage outcomes
| Agent | Staged | Fixed | Dropped | Deferred | Pending |
|-------|--------|-------|---------|----------|---------|
| quality | 1 | 0 | 0 | 0 | 1 |

Before triage: write zeros for Fixed/Dropped/Deferred and set Pending = Staged, or one line `Pending triage.` After triage: recompute per agent from finding **Triage** fields.

## Findings

### 1. <short title>
- **Severity**: Critical | Suggestion | Advisory
- **Agent severity**: Low *(omit when equal to Severity)*
- **Pattern**: quality#race-condition
- **Agents**: quality, concurrency
- **Triage**: pending
- **Anchor**: <section heading or nearby prose anchor text>
- **Source**: [Prose] | [Premortem] | [Code]

#### Comment (posted as-is when approved)
<Self-contained, suggestion-tone explanation.>

#### Analysis (not posted)
<Verification trail and severity rationale.>
---
```

## Comment and Analysis depth requirements

Caller must ensure each finding's:
- `#### Comment` is self-contained, suggestion-tone, and contains enough detail to act without follow-up chat (depth depends on severity, following the same intent as other review skills).
- `#### Analysis` contains verification trail and severity rationale. It is never posted.

## Per-finding severity mapping conventions (caller-owned)

This skill does not enforce how callers classify issues. It only enforces the output severity values:

- **Code review** (`doing-code-review`): `Critical` | `High` | `Medium` | `Low` per `review-agents/severity-calibration.md`
- **Document review** (Confluence, etc.): `Critical` | `Suggestion` | `Advisory`
- **RFC review** (`rfc-design`): `Block` | `Mitigate` | `Monitor` | `Accept`
- **Plan review** (`review-plan`): `Critical` | `Suggestion` | `Advisory`

Orchestrators record **Severity calibration** when agent severity differs from staged severity. Missing agent severity on code-review findings is treated as **Low** until verified (`doing-code-review` Step 3).

Document/plan severities (Confluence, plan review):
- `Critical`: blocks implementation or merge
- `Suggestion`: improves quality, usually requires action
- `Advisory`: monitor-level or optional notes

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
  "counts": {
    "agents_launched": 10,
    "raw_findings": 5,
    "staged_findings": 3,
    "discarded": 2,
    "solo_staged": 1,
    "echo_staged": 2
  },
  "panel": [
    {"agent": "quality", "status": "complete", "raw": 2, "solo": 1, "echo": 1, "relaunch": false}
  ],
  "deduplication_groups": [
    {"staged": 1, "agents": ["quality", "concurrency"], "theme": "Race on profile status re-read"}
  ],
  "discarded": [
    {"agent": "quality", "agent_severity": "Medium", "pattern": "quality#config-binding", "theme": "Config binding gap", "reason": "wrong-owner", "lead_agent": "implementation", "notes": "lead: implementation"}
  ],
  "severity_calibration": [
    {"staged": 1, "agent": "quality", "agent_severity": "Low", "staged_severity": "Medium", "delta": "upgraded"}
  ],
  "triage_outcomes": [
    {"agent": "quality", "staged": 1, "fixed": 0, "dropped": 0, "deferred": 0, "pending": 1}
  ],
  "findings": [
    {"id": 1, "severity": "Medium", "agent_severity": "Low", "pattern": "quality#race-condition", "agents": ["quality", "concurrency"], "triage": "pending", "theme": "Race on profile status re-read"}
  ]
}
```

Markdown staging doc remains the primary human artifact. Triage skills update `triage_outcomes` and finding `triage` in the sidecar when they update the `.md` file.

**Aggregation fields:** include `lead_agent` on discarded rows when `reason` is `wrong-owner`. Weekly panel-tuning scripts can sum `wrong-owner` counts per agent to identify merge-into candidates.

## Integration Points

Provider skill for staged review hierarchy and statistics. Consumers **must** follow this spec:

| Consumer skill | Staging path pattern | Notes |
|----------------|---------------------|-------|
| `review-plan` | `{reviews_dir}/YYYY-MM-DD-plan-review-<slug>-r<N>.md` | Document severities; map to plan actions in Step 5 |
| `doing-code-review` | `{reviews_dir}/YYYY-MM-DD-PR-*`, `YYYY-MM-DD-branch-review-*`, or execute-plan `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` | Code severities; optional `Status` per finding for PR triage |
| `review-loop` | Same as `doing-code-review` branch / execute-plan patterns with `-r<N>` | Requires statistics every round, including clear rounds |
| `receiving-code-review` | Updates existing staging under `{reviews_dir}/` | Triage Status→Triage map, Triage outcomes table, and matching `.stats.json` sidecar |
| `rfc-design` | `{reviews_dir}/YYYY-MM-DD-rfc-review-<slug>-<mode>.md` | May keep caller-specific severity labels in findings; statistics section still required |
| `review-confluence-doc` | `{reviews_dir}/YYYY-MM-DD-confluence-review-<slug>.md` | Tag `[Prose]` / `[Premortem]` / `[Code]` in Source field |
| `execute-plan` Phase 3 | `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` | Not `-plan-review-r`; review logs reference staging path with statistics |
| `done` | Session-touched staging under `{reviews_dir}/` | Step 2.64 validates before docs-branch sync |

