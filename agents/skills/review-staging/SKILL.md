---
name: review-staging
description: >
  Gold-source spec for review staging docs:
  file naming under {reviews_dir} and the standardized Markdown hierarchy.
---

# Review Staging (Gold Source)

## Finding-construction recipe (copy before drafting)

Draft every staging pair from the minimal-valid example pair below instead of from memory: copy it, fill the fill-order fields, and run the preflight while drafting, so the first hard-validator run grades substance instead of format. The sections that follow (**Inputs**, **Staged Markdown hierarchy**, **JSON sidecar**) are the schema of record; this recipe inlines one copyable example plus the three closed vocabularies the validator enumerates, and restates no other shape.

<!-- canonical-example:staging-doc begin -->
````markdown
# Plan review: demo-telemetry-export (r1)

## Metadata
- Type: Plan Review
- Record kind: canonical
- Date: 2026-10-05
- URL or Artifact: docs/plans/2026-10-05-demo-telemetry-export.md
- Depth: full
- Domains: telemetry
- Round: r1
- Review mode: fresh-adversarial
- Changed-risk signals: none
- Boundary-contract checklist: not applicable (no boundary families)
- Prior findings supplied as filter: no
- Last fix commit: none
- Witness ledger: N/A (no public mutators)
- Coverage: clean
- Release-gate ledger: none
- Panel mode: full
- Source digest: 6efc6d44f8bb26085ae7d14c67f6dca615cfb65dcb31c127e0e2504f7316beee
- Findings: 1
- Status: STAGED

## Review Statistics

### Panel
| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| correctness-completeness | quality, implementation | none | complete | 1 | 1 | 0 | no |
| testing | testing | none | complete | 0 | 0 | 0 | no |
| design-simplicity | architecture, simplification | none | complete | 0 | 0 | 0 | no |
| contract-docs | documentation | none | complete | 0 | 0 | 0 | no |
| risk | security | none | complete | 0 | 0 | 0 | no |

### Counts
- Workers launched: 5
- Workers skipped: 0
- Raw findings (all workers): 1
- Staged findings: 1
- Discarded during synthesis: 0
- Solo staged (unique agent origin): 1
- Echo staged (multi-agent dedup): 0

### Deduplication groups
None (each staged finding had a single agent origin).

### Discarded findings
None.

### Severity calibration
None (agent severities matched staged severities).

### Triage outcomes
| Worker | Lens | Staged | Fixed | Dropped | Deferred | Pending |
|--------|------|--------|-------|---------|----------|---------|
| correctness-completeness | quality | 1 | 0 | 0 | 0 | 1 |

## Findings

### Critical

None.

### High

None.

### Medium

#### F1. Digest re-bound without re-deriving the reviewed bytes
- **Severity**: Medium
- **Blocking**: true
- **Consequence**: A folded plan ships under a digest that no longer matches its reviewed bytes, so the round certifies a stale tree and the follow-up executes unreviewed changes.
- **Reachability**: common
- **Blast radius**: single-service
- **Confidence**: verified
- **Pattern**: quality#stale-digest-rebind
- **Workers**: correctness-completeness
- **Triage**: pending
- **Anchor**: Step 3.5, digest binding paragraph
- **Source**: [Prose]

#### Comment (posted as-is when approved)
Recompute the source digest from the plan's current bytes after every fold before staging the round, so the recorded digest always matches the bytes this round actually reviewed.

#### Analysis (not posted)
Verified against the reviewed artifact at the cited anchor: the fold path rewrites the plan but reuses the pre-fold digest. Reachability is common because every fold triggers the path; severity is Medium because the follow-up catches the mismatch at its own gate.

---

### Low

None.

### Overflow manifest
None.

### Soften watchlist
None.

## Summary

Verdict: ready=no (one blocking finding pending; the loop cannot close this round).
````
<!-- canonical-example:staging-doc end -->

<!-- canonical-example:stats-sidecar begin -->
```json
{
  "schema_version": 1,
  "review_type": "Plan Review",
  "date": "2026-10-05",
  "artifact_slug": "demo-telemetry-export",
  "round": "r1",
  "depth": "full",
  "domains": ["telemetry"],
  "panel_mode": "full",
  "selection_reason": null,
  "source_kind": "plan",
  "source_digest": "6efc6d44f8bb26085ae7d14c67f6dca615cfb65dcb31c127e0e2504f7316beee",
  "escalation_reason": null,
  "review_mode": "fresh-adversarial",
  "risk_signals": [],
  "prior_findings_filter": false,
  "last_fix_commit": null,
  "record_kind": "canonical",
  "coverage": {
    "outcome": "clean",
    "material_lens_set": ["architecture", "documentation", "implementation", "quality", "security", "simplification", "testing"],
    "completed": ["architecture", "documentation", "implementation", "quality", "security", "simplification", "testing"],
    "missing": []
  },
  "counts": {
    "workers_launched": 5,
    "raw_findings": 1,
    "staged_findings": 1,
    "discarded": 0,
    "solo_staged": 1,
    "echo_staged": 0
  },
  "panel": [
    {"worker": "correctness-completeness", "lenses": ["quality", "implementation"], "parent_worker": null, "descendant_launches": [], "status": "complete", "raw": 1, "solo": 1, "echo": 0, "relaunch": false},
    {"worker": "testing", "lenses": ["testing"], "parent_worker": null, "descendant_launches": [], "status": "complete", "raw": 0, "solo": 0, "echo": 0, "relaunch": false},
    {"worker": "design-simplicity", "lenses": ["architecture", "simplification"], "parent_worker": null, "descendant_launches": [], "status": "complete", "raw": 0, "solo": 0, "echo": 0, "relaunch": false},
    {"worker": "contract-docs", "lenses": ["documentation"], "parent_worker": null, "descendant_launches": [], "status": "complete", "raw": 0, "solo": 0, "echo": 0, "relaunch": false},
    {"worker": "risk", "lenses": ["security"], "parent_worker": null, "descendant_launches": [], "status": "complete", "raw": 0, "solo": 0, "echo": 0, "relaunch": false}
  ],
  "deduplication_groups": [],
  "discarded": [],
  "severity_calibration": [],
  "triage_outcomes": [
    {"worker": "correctness-completeness", "lens": "quality", "staged": 1, "fixed": 0, "dropped": 0, "deferred": 0, "pending": 1}
  ],
  "findings": [
    {
      "id": 1,
      "severity": "Medium",
      "blocking": true,
      "consequence": "A folded plan ships under a digest that no longer matches its reviewed bytes, so the round certifies a stale tree and the follow-up executes unreviewed changes.",
      "reachability": "common",
      "blast_radius": "single-service",
      "confidence": "verified",
      "pattern": "quality#stale-digest-rebind",
      "workers": ["correctness-completeness"],
      "triage": "pending",
      "theme": "Stale digest re-bind"
    }
  ],
  "overflow": [],
  "soften_watchlist": [],
  "verdict": "no"
}
```
<!-- canonical-example:stats-sidecar end -->

- Closed enums: confidence: verified | strong-evidence | hypothesis; reachability: expected | common | plausible-edge | theoretical; blast radius: global | multi-service | single-service | local

Fill order (one pass, top to bottom):

1. Materialize plan-review pairs only at the selector-emitted path: legacy `YYYY-MM-DD-plan-review-<artifact-slug>-r<N>.md` or identity-qualified `YYYY-MM-DD-plan-review-<artifact-slug>-p<8-hex-token>-r<N>.md`, with the `.stats.json` sidecar beside it.
2. Metadata block first: Type, Date (writing time), the freshness quartet (`Review mode`, `Changed-risk signals`, `Prior findings supplied as filter`, `Last fix commit`), `Record kind: canonical`, `Witness ledger`, `Coverage`, `Panel mode`, `Source digest` (a real SHA-256 of the exact reviewed bytes, recomputed for every round), `Findings`, `Status: STAGED`.
3. Then findings: one `#### F<N>. <short title>` block per staged finding under its severity group, ascending numeric id within the group, each field bullet spelled from the closed enums above (worker attribution names the reporting worker ids; `Triage: pending` at review pass).
4. Respect the budget while expanding: every Critical and every blocking finding per worker, plus up to five additional non-blocking High/Medium and up to two additional non-blocking Low findings per worker; every further credible candidate goes to the sidecar `overflow` list mirrored as the `### Overflow manifest` table instead of `## Findings` (recording rules 10 and 11), and never a Critical or blocking finding.
5. Fill `## Review Statistics` while synthesizing (Panel with Solo/Echo, Counts, Deduplication groups, Discarded findings, Severity calibration, Triage outcomes), and mirror the pair in the sidecar skeleton: counts, panel rows, and a findings array carrying the same fields as the Markdown bullets.
6. Preflight at drafting time, before the round's hard gate: `python3 ~/.ai-playbook/scripts/validate_review_staging.py --preflight <staging-path>` (the report-only mode reports every stage's findings together in one pass, the missing sidecar's required-field inventory included; it has no pass/fail exit posture). Fix every named finding and re-run until the report is clean; the round's `--hard` gate still grades substance and is never replaced.

### Record validation levels

The validator runs at two levels, partitioned by round class:

- **Lint level:** the `--preflight` report-only pass whose findings the orchestrator resolves before the round is reported complete; this is the lint level for non-certification rounds.
- **Full validation:** the `--hard` pass with the source context; the level for certification rounds, round-close, and the execution and finalization gates.

**Soft plain-run reading rule:** the plain soft run (neither `--hard` nor `--preflight`) reports and never gates: its exit stays 0 even on a findings-bearing record, while its final `OUTCOME:` label and JSON `outcome` field carry the truthful verdict (`fail` on a findings-bearing record), so a caller that gates on a result must invoke the `--hard` form; preflight keeps its inventory posture where findings never move its exit or its label.

**Round-class decision rule:** a round that could record the certifying clean verdict (any fresh-adversarial round with zero staged unresolved blocking findings, and any round in doubt) runs the full `--hard` source-context gate; lint is reserved for rounds whose staged record carries unresolved blocking findings and that cannot record the certifying verdict.

**Series sweep (plan-review closes, warning-only):** at every non-certification plan-review round close, after the round's own validation pass (lint or full), sweep every earlier pair whose `extensions.plan_identity` or legacy `URL or Artifact` resolves to the same source-plan path; omit other plans sharing the slug. Revalidate each member with `--preflight --source-plan <the plan under review>`, excluding the round being closed; stale earlier digests surface as report-only findings. Echo each member path before its pass; group any non-clean result into one warning and echo its report; then report the count, including a named zero. Resolve findings through the existing record-side repair class, never a re-round. Certification closes run no sweep; full seal validation owns that boundary. Advisory only: the sweep never blocks, changes exit status or verdict; its admission and removal row is `scripts/machinery_registry.json` (`duty:review-staging-series-sweep`).

**Protected certification catches and the code-family residual:** the ledger's review-staging-validator entry names the certification catches this partition protects; a code-family loop that terminates without certifying rests on a lint-only record, which is that family's recorded residual.

**Fill-order subordination:** the fill-order step-6 `--hard` sentence above is subordinated to this partition: its full-strength gate applies at certification rounds, round-close, and the execution and finalization gates; non-certification rounds whose staged record carries unresolved blocking findings run the lint-level pass; a round in doubt or able to certify runs full. The peer half of the partition is named by reference: review-plan's standing Step 4 mechanical-gate sentence is subordinated by that skill's own owning checkbox in plan 2026-10-09-review-loop-round-budget (Task 2), not by this subsection.

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
   - `Review mode`: `fresh-adversarial` | `targeted` | `verification-only`; a clean verdict contradicts `verification-only`
   - `Changed-risk signals`: comma list of changed-risk signals (public API, cross-service call, generated or nullable model, serializer or message converter, security or rollout boundary) or `none`; this Metadata line uses the prose names of the five signal classes, while the sidecar `risk_signals` list uses their kebab-case forms (`public-api`, `cross-service-call`, `generated-or-nullable-model`, `serializer`, `security-or-rollout-boundary`)
   - `Boundary-contract checklist`: `populated` | `not applicable (no boundary families)`; required when the Boundary-contract coverage floor triggers (changed scope touches one of its boundary families, per `review-agents/review-panel-selection.md`)
   - `Prior findings supplied as filter`: `no`; a clean verdict contradicts `yes`
   - `Last fix commit`: commit sha of the last accepted fix preceding this round, or `none`
   - `Witness ledger`: `<populated | N/A (no public mutators)>`; a non-null last fix commit on a post-fix round requires the populated-or-N/A witness shape (see the Metadata template and `### Witness ledger`)
   - `Release-gate ledger`: `<rows or none>`
   - `Panel mode`: `full` | `focused`
   - `Selection reason`: required for focused panels
   - `Source digest`: SHA-256 of reviewed content
   - `Escalation reason`: required only for a sixth worker

   The four freshness lines above (`Review mode`, `Changed-risk signals`, `Prior findings supplied as filter`, `Last fix commit`) are mechanically required only for records dated on or after `EXTENDED_SIDECAR_MIN_DATE` (Markdown surface: the staging filename's leading date), and the `Witness ledger` / `Release-gate ledger` lines are shape declarations validated through their sections rather than unconditionally required Metadata.
8. **Review Statistics** (required on every review, including zero-finding rounds):
   - Panel rows: every actual worker launch or skip, with loaded lenses, `parent_worker`, and Solo/Echo counts
   - Deduplication, discarded findings, severity calibration, and triage outcomes by worker and lens
   - Overflow manifest for credible non-blocking candidates not fully expanded

## Documentation paths

Read `{reviews_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Absent key or file ⇒ stop and surface the gap: the facts block is the single source for review paths; never guess a location.

Do not use `docs/tmp/` for the primary review staging document. Use `{tmp_dir}` only for ephemeral scratch files when a caller explicitly needs it.

The optional `review_retention_months` TOML key (integer number of calendar months, default 3) sets how long a review record stays in scope before it is past the retention window; `scripts/review_retention.py` reads that key and reports past-window record candidates in its default dry-run mode, so run the dry run first and prune only through the helper's manifest-gated, pairing-aware path.

## File naming rules

Primary staging doc path:

`{reviews_dir}/YYYY-MM-DD-<review-kind>-<artifact-slug>-<mode_or_round>.md`

Where:
- `<review-kind>` is a short stable token chosen by the caller, for example `confluence-review`, `rfc-review`, `plan-review`, `branch-review`
- `<artifact-slug>` is the caller-provided slug; when the reviewed source is a plan, it MUST be the plan's canonical artifact slug (the readiness-gate feature slug lowercased; an uppercase story key stays in the plan filename and title, never in the artifact slug) so the round stays discoverable through the readiness validator's `*-plan-review-<artifact-slug>[-p<identity-token>]-r*.md` shape, which the plans skill's per-round name binding check enforces after every round
- `<mode_or_round>` must be stable and specific enough to avoid collisions in the same day, for example `light`, `full`, `review-local`, `r1`

Create `{reviews_dir}` if it does not exist.

## Canonical record and supersession

There is one canonical Markdown record and one matching sidecar for each review pass. Before creating a file, enumerate and read all matching records and sidecars for the PR. Existing focused or partial records are inputs to the current pass and must be merged or updated, not copied into a sibling primary file for another lens.

If more than one matching record already exists, select one canonical record, add `Supersedes` and `Superseded by` metadata links, and mark every non-canonical record `SUPERSEDED`. A superseded record is historical only and is never eligible for posting. The canonical path must be selected before review workers launch and must remain the only path used for synthesis, triage, and posting.

Selection is mechanical: before workers launch, every orchestrator runs `scripts/review_record_selection.py select` with the resolved reviews directory, artifact slug, and digest; plan reviews also pass `--kind plan-review --source-plan <path>`. Use only emitted paths and copy emitted `plan_identity` to `extensions.plan_identity` in the sidecar. New plan-review names carry `-p<identity-token>` derived from the repository-relative source-plan path; legacy pairs resolve identity from `URL or Artifact`. Plan readiness filters by that path and still uses `source_digest` only for freshness. Slugs preserve case only for non-plan review kinds; plan slugs use the canonical lowercased feature slug. A post-certification plan rename still refuses at the corrections anchor because it compares artifact paths exactly; revert the rename or re-certify. The helper refuses (exit 1) when the existing record's sidecar `source_digest` differs from the supplied digest and no decision is supplied; resolve the refusal only with `--explicit-new-round` or the explicit archival operation, never by rewriting the prior record. Before any permitted same-pass replacement (`new-round`), invoke `backup` and record the printed path as `Backup of prior record:`. After staging the successor, run `mark-superseded`; the validator rejects dangling or mismatched links. When copying a prior record, strip its `Superseded by:` line from the successor before validation.

Orphan recovery: when the selection refusal names an orphaned record half (a canonical Markdown whose `.stats.json` sidecar is missing, for example after an interrupted synthesis), the block is fail-closed by design: never hand-write the missing sidecar and never let the partial record validate. Recover through the helper's `recover-orphan` subcommand with `--record` (the orphan path) plus the same `--slug` and optional `--kind` the `select` subcommand takes (the slug and kind are never inverse-parsed from the orphan's name); for `--kind plan-review`, also pass `--source-plan <path>` so the recovery stays within that plan series. The helper refuses before any mutation when the record has a sidecar twin (not an orphan), does not exist, or already carries the `.orphan-` infix (already preserved); the orphan must also carry its `Source digest:` Metadata line, which feeds the fresh pair's allocation. Otherwise it renames the orphan byte-identical to `<original stem>.orphan-<UTCtimestamp>.md` (a name no canonical discovery, selection, or validation shape matches) and allocates the fresh canonical pair for the same slug and kind through the same allocation logic as `select`. Stage the fresh record and add the receipt's `Orphan recovery: <path>` Metadata line verbatim (the path is repo-relative so the printed line passes the validator's orphan-recovery link format gate, which refuses a malformed link). Retention: the preserved orphan remains in the retention scan as an unpaired-retained unit that is reported every run and never auto-pruned, so it requires explicit handling at prune review, unlike backup copies which prune as pairs.

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
12. **Soften watchlist:** when the review is part of a `review-loop` (or any multi-round branch review), include `### Soften watchlist` under `## Review Statistics`. The sidecar `soften_watchlist` array, together with the `### Soften watchlist` Markdown section rendered in the same round's record, is the source of truth for row state: the section renders the sidecar rows and carries them forward by rendering the carried rows, never holding parallel state. Update statuses after workers reaffirm or restage. Use `None.` when the run has no softened findings yet.
13. **Delta-round record semantics:** a delta (focused post-fold) round's record fixes its source surface like any fresh round: its Source digest is the SHA-256 of the post-fold whole plan bytes (recording compatibly with `scripts/review_record_selection.py`'s differing-digest new-round path), the fold-diff scope is named in the Selection reason, and `panel_mode` stays focused.
14. **Fan-out findings:** A fan-out finding, per the fan-out policy in `review-panel-selection`, records the canonical home and the list of peer restatements in its Analysis; peers resolve by pointer conversion or one pointer-cleanup backlog item, not as independent contract bugs.

### Certification-residual routing

Certification-round non-blocking findings are recorded in the terminal record's overflow section (the existing sidecar field) with durable backlog capture (a backlog row for every consequence-bearing residual), never force a re-round, and never enter the soften watchlist, whose fix-keyed shape and closure obligations stay untouched.

### Cap-closure sidecar extension

When the operator explicitly authorizes closure at a plan loop's configured round cap without a clean round, the final round's sidecar records the cap-closure terminal shape in `extensions.cap_closure`. Reaching the cap alone does not prompt for or enact closure. This generic shape removes project-specific limits. Unresolved blocking findings remain a rejection condition. The extension has these required keys:

- `plan_section` (exactly `## Residual findings (cap closure)`)
- `round` (int or string, equal to the sidecar `round` after string normalization and normalizing to at least `CAP_CLOSURE_MIN_ROUND` = 3)
- `residuals` (non-negative int, booleans excluded; counts the section-body entries carrying the `accepted` disposition, and the readiness probe enforces the tie)
- `pre_fold_digest` (lowercase hex64, written before folding, differing from the re-bound `source_digest`)

The plan section's contract is the cap-round disposition ledger: every staged finding of the cap round is listed with its disposition (`folded` or `accepted`). This is a `version-1-only` extension, fail-closed at the version boundary: versionless legacy sidecars carrying `cap_closure` are rejected. The validator's section-literal constant is the shape's single owner and holds the bare heading (the declaration value carries the `## ` prefix).

### Corrections sidecar extension (declared-when-present)

A current-v1 sidecar may declare `extensions.corrections`, the array of certification-correction rows that re-bind the round's `source_digest` through graded, script-produced hops instead of a fresh round (the graded-review-certification contract; `scripts/corrections_record.py` is the shape owner and both validators consume its schema and verifier legs, so never spell the row shape by hand here). Declared-when-present rules the validator enforces:

- Absent means absent; an explicit `null` is a schema error, never a silent absence; an empty array is a schema error (a declared record always carries at least one hop).
- Rows are produced only by the classifier CLIs' `--emit-row` (`scripts/plan_delta_classifier.py` for plan bytes, `scripts/code_delta_classifier.py` for committed code fixes), never hand-authored by the editing session.
- Two row kinds: `script-verified` (every hunk carries an exempt class: `checkbox-flip`, `whitespace`, or `typography` on plan bytes; `comment-only` on code diffs) and `operator-acked` (unclassified hunks covered by a complete operator ack receipt whose witness resolves out of band and whose classifier-gap row exists under this repository's `docs/history/backlog/`).
- The code family mirrors its certified range in `extensions.certified_range` (`{"base": <commit>, "head": <commit>}`), which the validator requires to equal the range recorded in the certification seal `.ai-playbook/review-certs/<artifact-slug>.md`; both extensions are `version-1-only` and fail closed on versionless records.
- The staging validator's stale-digest gate grades the declared chain: it re-derives every hop's bytes from git and re-runs the classifier itself, anchors the declared digest at the seal entry's round-start digest, and refuses with distinct routing-safe reasons (`corrections verification:` prefixed) a bare digest rewrite, a hop commit dated before the seal entry round-close commit, an unbound or vacuous hop, and a hunk the classifier cannot prove exempt.

Consumers of the graded shapes beside this validator: the plans skill's graded rules (folds and post-certification deltas), the `execute-plan` Step 0.5 and Phase 3 digest gates, and the `review-plan` and `done` gates; each grades the same `extensions.corrections` rows through the same verifier, so a row recorded for one gate is evidence for all of them.

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
- Record kind: canonical | reconciliation | worker-evidence | legacy-import *(required for records dated on or after `RECORD_KIND_SIDECAR_MIN_DATE`; see `### Record kinds (RECORD_KIND_SIDECAR_MIN_DATE)`)*
- Date: YYYY-MM-DD
- URL or Artifact: <caller-provided url or "<inline draft>">
- Depth: light | full *(omit when not applicable)*
- Domains: concurrency, SQL *(omit when unknown)*
- Round: r1 *(omit on first non-loop review)*
- Review mode: fresh-adversarial | targeted | verification-only
- Changed-risk signals: <comma list or none>
- Boundary-contract checklist: <populated | not applicable (no boundary families)>
- Prior findings supplied as filter: no
- Last fix commit: <sha or none>
- Witness ledger: <populated | N/A (no public mutators)>
- Coverage: clean | replacement-covered | degraded | failed
- Release-gate ledger: <rows or none>
- Panel mode: full | focused
- Selection reason: <required for focused>
- Source digest: <sha256>
- Guideline pack: overlay=<id>; company=<path or none>; project=<path or none>; shared=<paths>; hints=<section/rule hints by worker> *(omit when Step 2.5 not applicable; when company-scoped, company and project are the paired convention sources)*
- Escalation reason: <required for sixth worker>
- Findings: <staged count>
- Status: STAGED
- Supersedes: <prior record Markdown path, relative to this record> *(supersession rounds only; the validator resolves it against this record's directory)*
- Superseded by: <successor record Markdown path, relative to the prior record> *(supersession rounds only; lives in the PRIOR record's Metadata and is written by the selection helper `mark-superseded`, not by hand; a round copy strips this line from the successor before validation)*
- Backup of prior record: <backup Markdown path printed by the selection helper `backup`> *(supersession rounds only)*

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

### Witness ledger
| Mutator / boundary | Input partitions | Transformation | Wire boundary & serializer | Downstream outcomes | Mode & deployed default | Doc examples | Discriminating assertion |
|--------------------|------------------|----------------|----------------------------|---------------------|------------------------|-------------|---------------------------|
| <mutator or boundary> | <absent, explicit-null, valid, invalid, protected, filtered where applicable> | <index, identity, or ordering transformation> | <actual downstream wire boundary and serializer configuration> | <success, partial-failure, malformed-response, no-call behavior> | <rollout or compatibility mode and deployed default> | <normative documentation examples describing the path> | <exact assertion or structural guard> |

One row per changed public mutator and each directly affected downstream boundary. Each row names the input partitions exercised (absent, explicit-null, valid, invalid, protected, filtered where applicable), any index, identity, or ordering transformation the path performs, the actual downstream wire boundary and serializer configuration in effect, the downstream success, partial-failure, malformed-response, and no-call behavior, the rollout or compatibility mode and its deployed default, the normative documentation examples describing the path, and the exact discriminating assertion or structural guard backing each claim (the observation that would fail for the most likely implementation mistake).

**Witness quality bar:** a row citing only a test name, a list position, a status code, or a manually configured fixture fails the quality bar when the invariant at risk is index preservation, wire serialization, downstream response, or mode preservation; the row must instead name the discriminating assertion or structural guard itself.

**Witness empty shape:** when the diff has no changed public mutator, the Metadata carries `Witness ledger: N/A (no public mutators)` instead of `### Witness ledger` rows; a post-fix round that has neither a populated `### Witness ledger` nor that N/A line fails the gate (mirroring the mutator failure-mode matrix's `N/A: no mutating APIs in this plan` and the Release-gate ledger's `none` line). `<...>` placeholder rows in the template table never count as populated evidence.

### Attempt ledger

One row per bounded worker attempt (initial launch, bounded retry, or replacement launch), mirrored by `coverage.attempts[]` in the sidecar; the row count must agree with `len(coverage.attempts[])`. Rows use the shape `| <attempt_id> | <worker> | <outcome> | <contributed_coverage> |` under the header `| attempt | worker | outcome | contributed_coverage |`. Omit the whole subsection (with zero rows) when `coverage.attempts[]` is absent or empty.

### Coverage sidecar contract (COVERAGE_SIDECAR_MIN_DATE)

A version-1 sidecar dated on or after `COVERAGE_SIDECAR_MIN_DATE` with `source_kind` `plan` must carry a valid `coverage` object; records dated earlier are accepted-legacy and exempt, and other source kinds validate `coverage` when present and never require it (the coverage obligation applies only when source_kind is `plan`). The obligation is also canonical-only: it applies to `record_kind` `canonical` records only; `reconciliation`, `worker-evidence`, and `legacy-import` records never require `coverage` (a `coverage` object on them is still validated when present). The object schema:
- `outcome`: one of `"clean", "replacement-covered", "degraded", "failed"`.
- `material_lens_set`: the lenses this round owns as material; non-empty when the record's `panel[]` carries launched workers. The validator never infers materiality from lens names.
- `completed`: lenses completed by this round; each must be evidenced by a `complete` `panel[]` row or a contributing `attempts[]` record.
- `replacement[]`: entries with `lens`, `original_artifact`, `original_sidecar`, `original_failure` linking the replaced lens to the original round.
- `inherited_coverage[]`: entries with `lens`, `artifact`, `sidecar` linking a lens completed by a prior round of the same loop.
- `missing`: uncovered material lenses; verdict `yes` requires it empty.
- `attempts[]`: one record per bounded attempt with `attempt_id`, `worker`, `lenses`, `started_at`, `deadline`, `elapsed`, `outcome` (`complete`, `failed`, `timeout`, `cancelled`, `malformed-output`), `failure_class`, `usage_state`, `admission_state`, `admission_error_class`, `execution_mode`, `attempt_number`, `retry_of`, `contributed_coverage`, and the local-equivalence evidence fields `prompt_scope`, `artifact`, `sidecar`.
- `retry_budget`: `per_attempt_timeout_minutes`, `per_worker_max`, `wall_clock_ceiling_minutes`, `exhausted`, `exhaustion_reason`.

Cross-field rules enforced by the validator: verdict `yes` requires `outcome` `clean` or `replacement-covered`, an empty `missing`, and every material lens covered by `completed` union `replacement[].lens` union `inherited_coverage[].lens`; outcome `degraded` or `failed` requires verdict `no`; `clean` forbids `replacement[]` entries; `replacement-covered` requires a non-empty `replacement[]`; a `failed`/`timed-out` panel row's lenses must appear in `missing`, `replacement[].lens`, or `completed`; a `failed` or `malformed-output` attempt requires a `failure_class`; an attempt with a capacity admission blocker must not record `usage_state: exhausted`; `retry_budget.exhausted: true` requires an `exhaustion_reason` naming a retryable class; and a complete attempt for a lens already in `replacement[]` must carry `contributed_coverage: false`. Attempt telemetry must not include prompts, authentication material, provider payloads, or review content that is not already part of the staged artifact (structurally enforced: no free-form content keys exist in the schema).

#### Legacy compatibility and rollout

Records dated before `COVERAGE_SIDECAR_MIN_DATE` remain valid without a `coverage` object and may satisfy `ready=yes` under the existing gates; no historical sidecar is rewritten. The grandfathering cannot be claimed by a sidecar date backdated below the constant while the staging filename is dated on or after it (mirroring the freshness-fields fence checks). Consumers keying on `coverage.outcome` must treat its ABSENCE as not-yet-covered rather than degraded. The coverage obligation is plan-source-scoped: branch and document review producers (`doing-code-review`, `rfc-design`, `review-confluence-doc`) are unchanged post-landing and may adopt `coverage` in a follow-up (validated when present, never required for their source kinds). Rollout for in-flight reviews: a review loop straddling the landing commit records coverage only for rounds staged after landing; the grace window is intentional and matches the freshness-fields precedent, and a replacement linked to a pre-constant original is accepted on the recorded `original_failure` (the grandfathered-link rule), so a straddling loop with evidence present is not forced into degraded.

### Record kinds (RECORD_KIND_SIDECAR_MIN_DATE)

Every version-1 record declares its kind with the top-level sidecar field `record_kind`, mirrored as the Markdown Metadata `Record kind:` line. The field is one of `"canonical"`, `"reconciliation"`, `"worker-evidence"`, `"legacy-import"`. The kind is read from the declared field and its Metadata twin only; it is never inferred from the filename. A version-1 record whose `date` is on or after `RECORD_KIND_SIDECAR_MIN_DATE` must declare the field, and the twin line is required when the staging filename's leading date is on or after the constant (mirroring the freshness-lines fence); records dated earlier are accepted-legacy and exempt, and the grandfathering cannot be claimed by a sidecar date backdated below the constant while the staging filename is dated on or after it (both mixed-fence directions fail, mirroring the freshness-fields fence checks). A pre-fence record may declare the field voluntarily and its value is validated when present. A post-fence record without the field fails rather than silently downgrading to any kind. When both surfaces declare, they must agree; a disagreement fails.

Minimum contract per kind (validator-enforced):

- `canonical`: the full review-staging record shape. Every current gate applies unchanged, and `canonical` is the only kind eligible for a clean verdict or a readiness gate.
- `reconciliation`: a reconciliation pass record. It must carry the six `review-reconciliation` output-contract sections (`Trigger`, `Recurrence map`, `Invariant and witness ledger`, `Changes made or proposed`, `Decision requests`, `Handoff`) as Markdown section headings. The canonical finding-hierarchy gates (severity groups, finding conservation, full-panel completion) and the coverage obligation do not apply.
- `worker-evidence`: a focused or partial record carrying one worker's evidence. The sidecar carries the four top-level fields `worker`, `lens`, `status`, `source_ref` (each a non-empty string), mirrored as the Metadata lines `Worker:`, `Lens:`, `Worker status:`, and `Source:` (the `Worker status:` label avoids colliding with the template's `- Status: STAGED` line, and the anchored `Source:` label parse cannot match the template's `- Source digest:` line). The canonical finding-hierarchy gates and the coverage obligation do not apply.
- `legacy-import`: a historical import, accepted as-is with no minimum contract beyond the kind declaration. The canonical finding-hierarchy gates and the coverage obligation do not apply.

No non-canonical kind is ever eligible for a clean verdict: a `verdict: yes` sidecar or a Markdown clean-round phrase on a `reconciliation`, `worker-evidence`, or `legacy-import` record fails, and only `canonical` records certify a clean exit. Each cross-kind failure (missing twin line, wrong kind, stale digest, invalid Pattern ID) reports one actionable error naming the owning producer mapped from `source_kind` (`plan` to `review-plan`, `rfc` to `rfc-design`, `document` to `review-confluence-doc`, `code` to `doing-code-review`).

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

## Release-gate ledger

Optional; include this section only when a plan explicitly assigns a boundary to later work. One entry per deferred boundary, recording:

- the missing capability and its owner
- the current code path and configuration that would be unsafe without it
- the deployment mode permitted before completion
- the exact condition that makes the future path shippable
- the classification, exactly one of: implementation blocker, release blocker owned elsewhere, non-blocking follow-up
- the accepted-residual rationale: why deferring the boundary is acceptable now (one sentence; per the `execute-plan` Step 3.4 clear-round gate, which requires this field)

Example entry (uses the recognized line shape):

- missing capability: boundary protection explicitly assigned to a later task; owner: the later task
- unsafe path today: unguarded downstream call under the permissive compatibility mode
- permitted deployment before completion: feature-flagged rollout only
- shippable when: the boundary check is enforced and covered by tests
- classification: release blocker owned elsewhere
- accepted-residual rationale: the permissive mode is reachable only from an internal test surface, so the exposure window is bounded

When no deferred boundary exists, Metadata carries `- Release-gate ledger: none`.
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

A review is clean only when no unresolved finding has `blocking: true`. A clean verdict contradicts Metadata `Review mode: verification-only` and `Prior findings supplied as filter: yes` (the validator fails such a round): the round that closes a loop re-traverses the complete current diff from first principles, so it is staged `fresh-adversarial` with the filter `no`.

## Synthesis-time hard gates

While synthesizing the staging doc and its sidecar, satisfy all seven obligations below before reporting the round; the validator fails the record when any of obligations 1 through 6 is missing (each has a validator arm), while obligation 7 is producer discipline for running the plan's Validation Commands and has no record state for the validator to observe.

1. **Closed confidence enum.** Give every finding a `Confidence` of `hypothesis`, `strong-evidence`, or `verified` and nothing else; take each discarded row's reason from the discard reason codes table (`duplicate`, `already-mitigated`, `false-positive`, `out-of-scope`, `prior-review`, `insufficient-evidence`, `severity-merged`, `noise`, `assumption-invalid`, `downstream-pr`, `agent-failed`, `agent-skipped`, `invalid-anchor`, `excerpt-mismatch`, `wrong-owner`, `softened-reaffirmed`); and set the sidecar `review_mode` field to `fresh-adversarial`, `targeted`, or `verification-only`, with a clean verdict contradicting `verification-only`. Map a near-miss value to the closed confidence enum instead of inventing a fourth level or downgrading to dodge a gate.
2. **Kebab-case risk signals.** Fill the sidecar `risk_signals` list only with the kebab-case tags `public-api`, `cross-service-call`, `generated-or-nullable-model`, `serializer`, and `security-or-rollout-boundary` (empty list when none), and keep the Metadata `Changed-risk signals` line on the prose names of those same five classes.
3. **Per-worker finding budget with overflow.** Fully expand every Critical and every blocking finding per worker, plus up to five additional non-blocking High/Medium and up to two additional non-blocking Low findings per worker; send every further credible candidate to the sidecar `overflow` list (mirrored as the `### Overflow manifest` table) instead of the findings conservation set, and never place a Critical or blocking finding in overflow.
4. **Finding block shape and order.** Write each finding as a `#### F<N>. <short title>` block whose field bullets include `- **Severity**:` and `- **Blocking**:` (beside Consequence, Reachability, Blast radius, Confidence, Pattern, Workers, Triage, Anchor), and stage blocks under the severity groups `### Critical`, `### High`, `### Medium`, `### Low` in exactly that order, ascending finding ID within a group.
5. **Freshness Metadata lines.** For records dated on or after `EXTENDED_SIDECAR_MIN_DATE`, include the Metadata lines `Review mode`, `Changed-risk signals`, `Prior findings supplied as filter`, and `Last fix commit`, and mirror them as the sidecar fields `review_mode`, `risk_signals`, `prior_findings_filter`, and `last_fix_commit`.
6. **Post-fix witness ledger.** On a round whose `Last fix commit` is non-null, populate the `### Witness ledger` rows (one per changed public mutator and directly affected downstream boundary) or declare `Witness ledger: N/A (no public mutators)` in Metadata; a post-fix round carrying neither shape fails the gate.
7. **Fence stripping for plan validation blocks.** When extracting a plan's Validation Commands bash block to run it, strip the opening and closing fence lines first, and never paste the fenced block inside a command substitution; an unstripped fence wedges bash because the unterminated fence line swallows the rest of the script.

## Output discipline

Staging doc is the deliverable. If a caller needs to post Confluence comments immediately, the caller must still write staging docs first (unless explicitly documented otherwise in that caller skill).

**Hard gate:** do not report review results to the user until the staging doc includes `## Review Statistics` with Panel (including Solo/Echo), Counts, Deduplication groups, Discarded findings (with Pattern), Severity calibration, and Triage outcomes placeholder populated (use explicit `None` rows when empty), **and** the matching `.stats.json` sidecar exists (unless Metadata documents a skip reason).

**Validator:** orchestrators may run `python3 ~/.ai-playbook/scripts/validate_review_staging.py --hard <staging-path>` before reporting, and branch on the outcome contract (scripts/OUTCOME_CONTRACT.md): exit 0 with the final `OUTCOME: pass` line means the record is valid (soft-mode warnings ride inside the pass); exit 1 with `OUTCOME: fail` is a modeled invalid record, so fix the named findings and re-run before reporting; exit 3 with `OUTCOME: tool_error` means the check could not run reliably (a usage violation, or an unreadable input path that the error names), so stop, fix the invocation or the input, and re-run; exit 2 is reserved for indeterminate, and a run that emits no final `OUTCOME:` line counts as tool error per the contract's no-line rule, so on either shape stop and re-derive the record's state from disk, never report the round complete. A `--json` run carries the outcome as the JSON `outcome` field instead of the stdout line. Cursor hooks (`review-staging-gate.sh`) warn after Write via `postToolUse`, deny review-loop commits when validation fails, and may inject a `stop` follow-up for recent stub rounds.

## JSON sidecar (required for aggregation)

Orchestrators **must** write a machine-readable sidecar next to every staging doc:

`{reviews_dir}/YYYY-MM-DD-<review-kind>-<artifact-slug>-<mode_or_round>.stats.json`

Same basename as the `.md` file. Write the sidecar in the same pass as the `.md` file (do not defer). Skip only when the orchestrator cannot emit valid JSON without guessing; in that case record `Stats sidecar: skipped (<reason>)` under `## Metadata` and treat the review as incomplete for panel-tuning aggregation.

**Usage capture (production write path):** at the START of staging a review round (before launching the round's workers), run `python3 ~/.ai-playbook/scripts/review_usage_capture.py mint` and carry the printed JSON through the round; record `review-run-id: <review_run_id>` and `review-started-at-ms: <minted_at_ms>` in the staging record's metadata block, the two values taken from the mint output VERBATIM, never re-derived (`review_usage_capture.py` is reached via `~/.ai-playbook/scripts/` (symlinked entries into this repo's `scripts/`), so the script is available once the repo commit lands). When writing a `.stats.json` sidecar, run `python3 ~/.ai-playbook/scripts/review_usage_capture.py --json --review-run-id <review_run_id> --review-started-at-ms <minted_at_ms>` and merge its output as the top-level `usage` field when it prints one. When it prints nothing (foreign runtime, unreadable store, not a git work tree), write the sidecar without `usage` and proceed unchanged; never estimate or hand-author a `usage` record. The bare `--json` form (without the identity arguments) is a pre-fence fallback for a round that lost its mint; its record stays non-attributable. A canonical record dated on or after the validator constant `USAGE_MINT_PAIR_MIN_DATE` (`2026-10-06`) validates only with this minted pair present or the `usage-attribution: bare-capture-fallback` Metadata marker, so a skipped mint must be recorded as the marker, never left silent. The marker is exclusive: it cannot coexist with either mint-pair field. On or after `SELF_HEAL_STATE_MIN_DATE`, a canonical record must also carry self-heal state bound to a minted `review-run-id`; the bare fallback therefore cannot complete a post-fence canonical record.

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
  "review_mode": "fresh-adversarial",
  "risk_signals": ["public-api", "serializer"],
  "prior_findings_filter": false,
  "last_fix_commit": null,
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

Use `"soften_watchlist": []` when the run has no softened findings. Multi-round / review-loop orchestrators must carry `open` rows forward. The sidecar array is the state of record (the source of truth beside its same-round rendering); a row-count mismatch between the pair's halves is a defect the parity arm flags, and the arm is a deliberate count-mirror that does not adjudicate same-count content drift.

The `panel` array in the minimum-schema example above is truncated for readability (one row shown); a real full-panel run carries one row per launched worker, so `counts.workers_launched` matches the non-skipped panel rows. Do not copy the example's counts/panel pairing verbatim, and do not copy its `source_digest` value either: the example digest is an explicit placeholder (a copyable valid hex digest would pass the syntax gate while hashing nothing, so only a hand-computed real digest keeps the placeholder tripwire a tripwire).

### Version-1 sidecar contract

A sidecar that declares `"schema_version": 1` is a version-1 record and must satisfy the complete top-level contract below. Every active producer emits version-1 sidecars.

Required top-level fields (all must be present; enum-typed fields use `null` when not applicable):

| Field | Type / behavior |
|-------|-----------------|
| `schema_version` | integer `1` |
| `review_type` | string |
| `date` | string `YYYY-MM-DD` |
| `artifact_slug` | string; lowercase kebab token (letters and digits joined by single hyphens), the certification seal filename stem |
| `round` | round identifier: string (for example `"r1"`) or integer; producers pick one form per review and stay consistent |
| `panel_mode` | `"full"` \| `"focused"` |
| `selection_reason` | string or `null`; required non-null when `panel_mode` is `focused` |
| `source_kind` | `"plan"` \| `"rfc"` \| `"document"` \| `"code"` |
| `source_digest` | lowercase 64-char hex SHA-256 of the exact reviewed bytes |
| `escalation_reason` | string or `null`; required non-null when a sixth worker launched |
| `review_mode` | `"fresh-adversarial"` \| `"targeted"` \| `"verification-only"`; required for records dated on or after the validator constant `EXTENDED_SIDECAR_MIN_DATE` (`2026-09-09`) |
| `risk_signals` | list of changed-risk signal tags (`[]` when none); tags are the kebab-case forms of the five signal classes (`public-api`, `cross-service-call`, `generated-or-nullable-model`, `serializer`, `security-or-rollout-boundary`); required for records dated on or after `EXTENDED_SIDECAR_MIN_DATE` |
| `prior_findings_filter` | boolean; `false` for a clean verdict; required for records dated on or after `EXTENDED_SIDECAR_MIN_DATE` |
| `last_fix_commit` | commit sha string or `null` (`null` when no accepted fix precedes the round); required for records dated on or after `EXTENDED_SIDECAR_MIN_DATE` |
| `counts` | object; `workers_launched` must match non-skipped panel rows, `staged_findings` must match `findings` length |
| `panel` | array of worker rows (`worker`, `lenses`, `parent_worker`, `descendant_launches`, `status`, counts) |
| `deduplication_groups` | array (may be empty) |
| `discarded` | array (may be empty); `wrong-owner` rows carry `lead_worker` + `lead_lens` (or `lead_agent`) |
| `severity_calibration` | array (may be empty) |
| `triage_outcomes` | per-worker/lens rollup: array of rows (as in the minimum-schema example) or an object rollup; the validator checks presence, not shape |
| `findings` | array; each row carries `id` (unique integer; uniqueness is enforced for all current-format records, versionless and version-1 alike), `severity`, `blocking` (real boolean), `consequence`, `reachability`, `blast_radius`, `confidence`, and a canonical `pattern` |
| `overflow` | array; never contains a Critical or blocking finding |
| `soften_watchlist` | array; `[]` when none |
| `record_kind` | one of `"canonical"` \| `"reconciliation"` \| `"worker-evidence"` \| `"legacy-import"`; date-fenced required field: mandatory for records dated on or after the validator constant `RECORD_KIND_SIDECAR_MIN_DATE` (`2026-09-20`), voluntary and validated on earlier records; mirrored as the Metadata `Record kind:` line (schema in `### Record kinds (RECORD_KIND_SIDECAR_MIN_DATE)` below); never inferred from the filename, and never a silent legacy downgrade (a post-fence record without the field fails, it is not re-typed as legacy) |

Date-fenced top-level field: `coverage` (object; required for `source_kind` `plan` records dated on or after `COVERAGE_SIDECAR_MIN_DATE`, permitted and validated otherwise; schema in `### Coverage sidecar contract (COVERAGE_SIDECAR_MIN_DATE)` below). Optional top-level fields: `depth` (string), `domains` (list), `verdict` (string `yes` or `no`; the plan-review producer writes it alongside the `## Summary`), `extensions` (object), `usage` (shape owned by the capture module; the validator accepts the key only). Any other top-level field is rejected; future extensions belong inside the object-valued `extensions` (a non-object `extensions` value is rejected). On a `rejects unknown top-level field` validator error naming a field the current contract defines, use the validator-copy refresh recovery: refresh the installed validator copy from `scripts/validate_review_staging.py` and retry.

Run-wide self-heal state: for canonical records whose filename and sidecar `date` are on or after `SELF_HEAL_STATE_MIN_DATE` (`2026-10-09`), require `extensions.convergence.self_heal_attempt`. Its `status` is `unused`, `consumed`, or `unknown`; `unknown` records missing or malformed prior-round evidence and cannot authorize self-heal. `run_id` is a 32-character lowercase hex ID stable across an artifact chain, normally initialized from r1's minted `review-run-id`; if prior state or identity evidence is missing or malformed, the recovery round records `unknown` with its own minted `review-run-id` as an explicit recovery exception, which does not start a new artifact chain, and later rounds carry that `unknown` state and ID unchanged. A consumed state also carries `round` (`rN`) and a lowercase SHA-256 `source_digest`. The consuming round must equal the current round and its digest must equal that sidecar's `source_digest`; later records carry the consumed state unchanged. An unnumbered canonical filename is a singleton r1 and must declare sidecar round 1; any continuation uses `-rN`. Resolve predecessor rounds by the stable filename stem without the date prefix, so a chain can continue across calendar dates. A post-fence canonical record without a minted `review-run-id`, including the documented bare-capture usage fallback, cannot establish self-heal state and fails closed. A prior record that combines the fallback marker with either mint-pair field is malformed identity evidence and requires the recovery round to record `unknown`; that unknown state is carried unchanged and never authorizes self-heal. A current post-fence record must have calendar-valid filename and sidecar dates or validation fails; malformed current dates cannot authorize either `unused` or `unknown`. For predecessor trust, a calendar-invalid filename date or sidecar date, or a missing/malformed sidecar `source_digest`, makes that predecessor unavailable/malformed evidence and requires `unknown`; this rule does not change the general version-1 date field's shape-only validation. Pre-fence historical records remain valid without this member. A missing, malformed, or legacy prior record on resume requires `status:"unknown"` with the current round's `review-run-id`; this recovery exception replaces the unavailable chain identity without creating a new artifact chain. An `unused` allowance is rejected and policy pauses before another automatic attempt.

Extended-field grandfathering and cross-field rule: the four extended freshness fields (`review_mode`, `risk_signals`, `prior_findings_filter`, `last_fix_commit`) are required only on version-1 records whose `date` is on or after the validator constant `EXTENDED_SIDECAR_MIN_DATE` (`2026-09-09`, the day after this contract landed); a version-1 record dated earlier is accepted-legacy and exempt from them. The Markdown twin of this freshness fence keys on the staging filename's leading `YYYY-MM-DD` (the sidecar fence keys on the record's `date` field). The validator rejects either mixed-fence direction: a sidecar dated earlier than a post-fence staging filename cannot claim the exemption (the exemption is stripped), and a pre-fence filename with a post-fence sidecar date fails the date-disagreement error. Cross-field rule: a clean verdict with a non-null `last_fix_commit` requires `review_mode: fresh-adversarial` (a `targeted` label on a post-fix clean round bypasses the fresh-adversarial mandate), and `prior_findings_filter` must be `false` for a clean verdict; the Markdown Metadata mirrors the same freshness lines (`Review mode`, `Prior findings supplied as filter`), where a clean verdict contradicts `verification-only` mode or filter `yes`.

Canonical Pattern IDs (version-1): findings, overflow items, and discarded rows that carry a pattern must use `<lens>#<kebab-slug>` with an owner from the declared set in **Pattern id format**. A version-1 finding must also carry the same canonical `pattern` in its Markdown `- **Pattern**:` bullet; a missing or differing Markdown Pattern is a conservation error.

Historical compatibility (schema classification): a sidecar without `schema_version` is never a version-1 schema error; it is legacy compatibility input, classified by shape: `legacy-worker-shaped` (versionless with per-worker `worker` rows), `legacy-panel-mode` (versionless with `panel_mode` or `counts.workers_launched`), or `legacy` (any other versionless record). When several shape markers are present on the same versionless record, the classifier checks the panel-mode markers FIRST, so a record carrying both per-worker rows and `panel_mode`/`counts.workers_launched` classifies `legacy-panel-mode`, not `legacy-worker-shaped`; derive adapter routing from the exported classifier (`classify_sidecar_schema`), never from the listing order here. Legacy classification does not exempt a record from re-validation: a versionless worker-shaped or panel-mode record run through the `--hard` validator is still held to the current payload gates (panel shape, source digest, descendant flattening), so expect current-contract errors on bare historical records. A sidecar with an explicit unsupported `schema_version` is rejected outright.

Panel profile for panel-era records (date-fenced reduced path): a staging record whose date (the staging filename's leading `YYYY-MM-DD`, falling back to the sidecar `date` field) is on or before the validator constant `PANEL_PROFILE_MAX_DATE` (`2026-09-19`, inclusive) validates under the documented reduced path instead of the full hard contract. The reduced path enforces the anti-stub core only: the Markdown and sidecar pair parses; a `## Metadata` section and a `## Findings` section exist (heading-text prefix match, so suffixed era headings such as `## Findings (zero blocking)` count); the sidecar carries a verdict; the sidecar's counts agree with its own findings array length when both are present; and whole-document finding conservation by document order over every recognized finding block in the Findings section plus round-append sections alike (for this leg the validator recognizes the panel header shapes `### N. <title> (Severity)` and `### R<N>-F<M>. <title> (Severity)`, with the severity taken from the parenthesized suffix). Report every other gate, present or future, as a warning that never contributes to the exit code; when the document parses into zero recognized blocks while the sidecar lists findings (the pipe-table era layout), report the unparsed conservation leg as a warning, never an error. The record date alone selects the path: do not route by schema shape and do not maintain a per-gate waiver list, because era-mismatched format conformance is exactly what the window exists to excuse. A record dated after the window, or undated, keeps the full contract unchanged.

`source_kind` declares what `source_digest` hashes: `"code"` (the stored diff bytes), `"plan"` / `"rfc"` / `"document"` (the reviewed document's UTF-8 bytes). Producers SHOULD set it; `review-plan` (and other document reviewers) MUST set it. When `source_kind` is declared, `source_digest` must be a lowercase 64-char hex SHA-256 (placeholders like `"<sha256>"` fail the validator). The `--source-plan` flag on `validate_review_staging.py` recomputes the plan's digest and fails hard on a mismatch (the sibling `--source-rfc` and `--source-doc` flags do the same for RFC and generic document reviews, type-checking the sidecar's `source_kind`), so a digest recorded before a fold of the reviewed artifact is rejected as stale. The stale judgment is round-anchored, not exact-match alone: when the sidecar's round has an on-disk certification seal entry (`.ai-playbook/review-certs/<artifact-slug>.md`), the accepted stale shapes beside the exact-match rule are a declared digest equal to the seal entry's round-start digest with the current bytes matching that digest too (the honest clean shape: the reviewed bytes are the round's certified bytes) and a declared digest carried by a verified `extensions.corrections` chain (a verified re-bind passes beside a naming warning and never rewrites the declared digest), while a declared digest matching neither refuses as an unwitnessed sidecar digest mutation (the disk home detects digest mutation against the current seal file only, the committed-history witness being retired); when no seal entry resolves for the round (a certification predating the seal file, or the seal file absent from this worktree), the check stays today's exact-match rule with a named degradation warning. For code reviews the `--source-code-repo` and `--source-code-plan` flags grade the same way over the certified range's repository. In multi-round loops, re-derive the digest from the current round's reviewed artifact for every round; never copy a digest from a prior round's staging doc (the copy misattributes findings to a stale tree, and only a recompute flag can catch it).

Legacy sidecars keep `agent`, `agents`, and caller-specific severity labels. New sidecars use worker rows and the four shared severities.

## Integration Points

Provider skill for staged review hierarchy and statistics. Consumers **must** follow this spec:

| Consumer skill | Staging path pattern | Notes |
|----------------|---------------------|-------|
| `review-plan` | selector-emitted `{reviews_dir}/YYYY-MM-DD-plan-review-<slug>[-p<identity-token>]-r<N>.md` | Shared severities and blocking-aware plan actions; carries a stable-core summary of the sidecar schema and runs the validator before reporting round complete; declares `record_kind` on current records |
| `plans` (Plan Quality Gate) | selector-emitted plan-review path | Orchestrator-side consumer: re-runs the validator before folding; a staging-record defect is repaired in that round by its producer, never deferred to closeout |
| `doing-code-review` | `{reviews_dir}/YYYY-MM-DD-PR-*`, `YYYY-MM-DD-branch-review-*`, or execute-plan `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` | Code severities; optional `Status` per finding for PR triage; declares `record_kind` (sidecar field + Metadata `Record kind:` twin) on records dated on or after `RECORD_KIND_SIDECAR_MIN_DATE`; its Step 1 review-artifact preflight (item 4) mandates `scripts/review_record_selection.py select` before workers launch |
| `review-loop` | Same as `doing-code-review` branch / execute-plan patterns with `-r<N>` | Requires statistics every round, including clear rounds; runs the record selection helper (`scripts/review_record_selection.py select`) before workers launch |
| `receiving-review` | Updates existing staging under `{reviews_dir}/` | Triage Status→Triage map, Triage outcomes table, matching `.stats.json` sidecar, and authorized Blocking re-evaluation (see Triage presentation freeze). A returned-for-ask record is NOT a Status or Triage value: record the literal marker `returned-for-ask` on the finding's Analysis section (with the question to relay); Status and Triage stay `pending` and the Blocking value is unchanged until the user decides. |
| `review-reconciliation` | Supplements the affected canonical record under `{reviews_dir}/` or the caller's linked note | Adds recurrence and closure evidence; never replaces immutable round findings or certifies its own refactor; declares `record_kind` (sidecar field; Metadata twin via the universal review-staging template) on the supplemental record |
| `rfc-design` | `{reviews_dir}/YYYY-MM-DD-rfc-review-<slug>-<mode>.md` | Shared severities; statistics section required; declares `record_kind` (sidecar field; Metadata twin via the universal review-staging template) on records dated on or after `RECORD_KIND_SIDECAR_MIN_DATE` |
| `review-confluence-doc` | `{reviews_dir}/YYYY-MM-DD-confluence-review-<slug>.md` | Tag `[Prose]` / `[Premortem]` / `[Code]` in Source field; declares `record_kind` (sidecar field; Metadata twin via the universal review-staging template) on records dated on or after `RECORD_KIND_SIDECAR_MIN_DATE` |
| `execute-plan` Phase 3 | `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` | Not `-plan-review-r`; review logs reference staging path with statistics |
| `done` | Session-touched staging under `{reviews_dir}/` | the landing sweep's review-staging gate validates before docs-branch sync |
